#!/usr/bin/env python3
"""Search BPORS+FP-aware Kylin parameter profiles.

The default objective follows the original BPORS retune plan, and the command
line can switch the cap source, cost slack, target bits, and optional forced-
pruning tau floors.  In every mode the search requires the conservative
bucket-thinned BPORS cover estimate to meet the target bit security and then
minimizes total signature size, with smaller sign/verify costs as tie-breaks.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import mpmath as mp

ROOT = Path(__file__).resolve().parents[2]
FINAL_CSV = ROOT / "paper/data/para_kylin_final_6profiles.csv"
SELECTED_CSV = ROOT / "paper/data/para_kylin_selected_6profiles.csv"
BASELINE_CSV = ROOT / "paper/data/para_fors_baseline_6profiles.csv"
SEARCH_CSV = ROOT / "paper/data/param_search_candidates_bpors.csv"

CTR_BYTES = 8
TAU_FLOOR = 1.0e-8
Q24_TAU_FLOOR = 5.0e-7
COST_SLACK = 1.05
MAX_LAYER_HEIGHT = 32
MAX_TREE_BITS = 64
MAX_BPORS_K = 16
MAX_BPORS_B = 16
MAX_CHILD_HEIGHT = 13
BPORS_SAMPLER_BUF_U32 = 512 // 4
DEFAULT_HT_FRONTIER_LIMIT = 80
WIDE_HT_FRONTIER_LIMIT = 500

ACTIVE_BASELINES: dict[str, Baseline]
ACTIVE_FALLBACKS: dict[str, dict[str, object]]
ACTIVE_SIGN_COST_SLACK = COST_SLACK
ACTIVE_VERIFY_COST_SLACK = COST_SLACK
ACTIVE_ENFORCE_SIGN_CAP = True
ACTIVE_WIDE_BPORS = False
ACTIVE_TAU_FLOOR = TAU_FLOOR
ACTIVE_Q24_TAU_FLOOR = Q24_TAU_FLOOR
INITIAL_SIG_HEADROOM = 1
ACTIVE_NOTES = "BPORS+FP retuned under old-FORS 105% sign/verify hashcall caps"
ACTIVE_SIGNATURE_CAPS: dict[str, tuple[int, bool]] = {}
ACTIVE_KEYGEN_CAPS: dict[str, int] = {}
ACTIVE_METRIC_LOWER_BOUNDS: dict[str, dict[str, int]] = {}
SECURITY_MARGIN_BITS = 0.0

mp.mp.dps = 170


@dataclass(frozen=True)
class Scenario:
    name: str
    q_sigs: int
    n: int
    target_bits: float
    h_min: int
    h_max: int
    d_min: int
    d_max: int
    w_min: int
    w_max: int
    child_k_min: int
    child_k_max: int
    bpors_K_min: int
    bpors_K_max: int
    bpors_B_min: int
    bpors_B_max: int


@dataclass(frozen=True)
class Baseline:
    name: str
    q_sigs: int
    n: int
    target_bits: float
    h: int
    d: int
    h_vec: tuple[int, ...]
    a: int
    k: int
    w: int
    length: int
    sig: int
    sign_hashcalls: int
    verify_hashcalls: int


@dataclass(frozen=True)
class Candidate:
    name: str
    q_sigs: int
    n: int
    target_bits: float
    h: int
    d: int
    h_vec: tuple[int, ...]
    K: int
    B: int
    t: int
    child_height: int
    child_k: int
    mmax: int
    ctr_bytes: int
    w: int
    length: int
    sig: int
    bitsec: float
    tau: float
    keygen_hashcalls: int
    sign_hashcalls: int
    verify_hashcalls: int
    baseline_sign_hashcalls: int
    baseline_verify_hashcalls: int

    @property
    def h0(self) -> int:
        return self.h_vec[0]

    @property
    def h_profile(self) -> str:
        return "[" + ",".join(str(v) for v in self.h_vec) + "]"

    @property
    def q_label(self) -> str:
        return format_q(self.q_sigs)


SCENARIOS = (
    Scenario("Kylin-128", 2**64, 16, 127.0, 56, 72, 4, 18, 2, 128, 2, 10, 2, 12, 4, 14),
    Scenario("Kylin-256", 2**64, 32, 255.0, 58, 74, 4, 20, 2, 128, 2, 12, 2, 14, 4, 15),
    Scenario("Kylin-512", 2**64, 64, 511.0, 58, 74, 4, 18, 2, 128, 2, 12, 2, 16, 4, 15),
    Scenario("Kylin-128-q24", 2**24, 16, 127.0, 18, 40, 1, 18, 2, 128, 2, 10, 2, 12, 4, 16),
    Scenario("Kylin-256-q24", 2**24, 32, 255.0, 18, 42, 1, 18, 2, 128, 2, 12, 2, 14, 4, 16),
    Scenario("Kylin-512-q24", 2**24, 64, 511.0, 32, 66, 1, 16, 2, 128, 2, 12, 2, 16, 4, 16),
)


CURRENT_BPORS_UPPER = {
    "Kylin-128": 6616,
    "Kylin-256": 26440,
    "Kylin-512": 84360,
    "Kylin-128-q24": 2872,
    "Kylin-256-q24": 11208,
    "Kylin-512-q24": 47240,
}


SECURE_BPORS_FALLBACKS = {
    "Kylin-128": dict(
        q_sigs=2**64, n=16, target_bits=127.0, h=62, d=7,
        h_vec=(8, 9, 9, 9, 9, 9, 9), K=4, B=7,
        t=128, child_k=6, mmax=95, w=17, length=33,
        sig=6616,
    ),
    "Kylin-256": dict(
        q_sigs=2**64, n=32, target_bits=255.0, h=65, d=8,
        h_vec=(8, 8, 8, 8, 8, 8, 8, 9), K=9, B=8,
        t=66, child_k=5, mmax=187, w=16, length=66,
        sig=26440,
    ),
    "Kylin-512": dict(
        q_sigs=2**64, n=64, target_bits=511.0, h=64, d=8,
        h_vec=(8, 8, 8, 8, 8, 8, 8, 8), K=14, B=8,
        t=256, child_k=5, mmax=415, w=43, length=96,
        sig=84360,
    ),
    "Kylin-128-q24": dict(
        q_sigs=2**24, n=16, target_bits=127.0, h=22, d=1,
        h_vec=(22,), K=2, B=12, t=864, child_k=7, mmax=90,
        w=6, length=52, sig=2872,
    ),
    "Kylin-256-q24": dict(
        q_sigs=2**24, n=32, target_bits=255.0, h=21, d=1,
        h_vec=(21,), K=3, B=14, t=3072, child_k=8, mmax=202,
        w=6, length=102, sig=11208,
    ),
    "Kylin-512-q24": dict(
        q_sigs=2**24, n=64, target_bits=511.0, h=41, d=2,
        h_vec=(20, 21), K=7, B=15, t=224, child_k=10,
        mmax=336, w=12, length=145, sig=47240,
    ),
}


FORS_BASELINES = {
    "Kylin-128": Baseline(
        "Kylin-128", 2**64, 16, 127.0, 65, 9,
        (7, 7, 7, 7, 7, 7, 7, 8, 8), 13, 11, 73, 22,
        6688, 2442880, 7357,
    ),
    "Kylin-256": Baseline(
        "Kylin-256", 2**64, 32, 255.0, 68, 10,
        (6, 6, 7, 7, 7, 7, 7, 7, 7, 7), 13, 22, 54, 46,
        26784, 3223168, 12449,
    ),
    "Kylin-512": Baseline(
        "Kylin-512", 2**64, 64, 511.0, 66, 11,
        (6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6), 13, 49, 97, 79,
        103808, 6198272, 43009,
    ),
    "Kylin-128-q24": Baseline(
        "Kylin-128-q24", 2**24, 16, 127.0, 22, 1, (22,), 24, 6, 4, 67,
        3840, 1329594368, 226,
    ),
    "Kylin-256-q24": Baseline(
        "Kylin-256-q24", 2**24, 32, 255.0, 21, 1, (21,), 25, 12, 4, 131,
        14880, 1268776960, 430,
    ),
    "Kylin-512-q24": Baseline(
        "Kylin-512-q24", 2**24, 64, 511.0, 57, 3, (19, 19, 19), 20, 24, 64, 87,
        52672, 1164963840, 8584,
    ),
}

ACTIVE_BASELINES = FORS_BASELINES
ACTIVE_FALLBACKS = SECURE_BPORS_FALLBACKS


def format_q(q_sigs: int) -> str:
    if q_sigs > 0 and (q_sigs & (q_sigs - 1)) == 0:
        return f"2^{q_sigs.bit_length() - 1}"
    return str(q_sigs)


def tau_floor_for_name(name: str) -> float:
    return ACTIVE_Q24_TAU_FLOOR if name.endswith("-q24") else ACTIVE_TAU_FLOOR


def ceil_log2(x: int) -> int:
    return (x - 1).bit_length()


@lru_cache(maxsize=1)
def wots_length_cache() -> dict[tuple[int, int], int]:
    cache: dict[tuple[int, int], int] = {}
    for path in (ROOT / "paper/data").glob("param_search_candidates_kylin_*.csv"):
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if "n" not in reader.fieldnames or "w" not in reader.fieldnames or "len" not in reader.fieldnames:
                continue
            for row in reader:
                try:
                    n = int(row["n"])
                    w = int(row["w"])
                    length = int(row["len"])
                except (TypeError, ValueError):
                    continue
                cache[(8 * n, w)] = length
    return cache


@lru_cache(maxsize=None)
def const_sum_count(length: int, w: int) -> int:
    total = length * (w - 1) // 2
    dp = [0] * (total + 1)
    dp[0] = 1
    for _ in range(length):
        nxt = [0] * (total + 1)
        window = 0
        for i in range(total + 1):
            window += dp[i]
            if i - w >= 0:
                window -= dp[i - w]
            nxt[i] = window
        dp = nxt
    return dp[total]


@lru_cache(maxsize=None)
def wotscs_length(message_bits: int, w: int) -> int:
    cached = wots_length_cache().get((message_bits, w))
    if cached is not None:
        return cached
    for length in range(2, 700):
        if math.log2(const_sum_count(length, w)) > message_bits:
            return length
    raise RuntimeError(f"failed to find WOTSCS length for {message_bits=} {w=}")


def balanced_profile(h: int, d: int) -> tuple[int, ...]:
    base = h // d
    rem = h % d
    return tuple(base + (1 if i < rem else 0) for i in range(d))


def profile_is_compatible(h: int, h_vec: tuple[int, ...]) -> bool:
    return (
        len(h_vec) > 0
        and sum(h_vec) == h
        and min(h_vec) > 0
        and max(h_vec) <= MAX_LAYER_HEIGHT
        and h - h_vec[0] <= MAX_TREE_BITS
    )


def shift_height(profile: tuple[int, ...], src: int, dst: int, amount: int) -> tuple[int, ...] | None:
    if src == dst:
        return profile
    p = list(profile)
    if p[src] - amount < 1:
        return None
    p[src] -= amount
    p[dst] += amount
    return tuple(p)


@lru_cache(maxsize=None)
def generate_layer_profiles(h: int, d: int) -> tuple[tuple[int, ...], ...]:
    core = balanced_profile(h, d)
    profiles = {core}
    top = d - 1
    mid = d // 2
    for src, dst, amount in (
        (top, 0, 1), (top, 0, 2), (0, top, 1), (0, top, 2),
        (mid, 0, 1), (mid, top, 1), (top, mid, 1), (0, mid, 1),
    ):
        p = shift_height(core, src, dst, amount)
        if p is not None and profile_is_compatible(h, p):
            profiles.add(p)
    return tuple(sorted(profiles))


def sign_ht_hashcalls(h_vec: tuple[int, ...], w: int, length: int) -> int:
    return sum((1 << h_i) * (length * w + 1) for h_i in h_vec)


def verify_chain_steps(length: int, w: int) -> int:
    total = length * (w - 1)
    return total - (total // 2)


def verify_ht_hashcalls(h: int, d: int, w: int, length: int) -> int:
    return d * (verify_chain_steps(length, w) + 1) + h


def keygen_hashcalls(h_vec: tuple[int, ...], w: int, length: int) -> int:
    top = h_vec[-1]
    leaves = 1 << top
    return leaves * (length * (w + 1) + 1) + leaves - 1


def signature_bytes(n: int, h: int, d: int, length: int, K: int, child_k: int, mmax: int) -> int:
    return n + CTR_BYTES + (K * child_k + mmax) * n + (h + d * length) * n


@lru_cache(maxsize=None)
def leaf_heap_set(t: int) -> frozenset[int]:
    h = ceil_log2(t)
    split = t - (1 << (h - 1)) if h > 0 else 0
    leaves: set[int] = set()
    if t == 1:
        leaves.add(1)
        return frozenset(leaves)
    for leaf_idx in range(t):
        if leaf_idx < 2 * split:
            heap = (1 << h) + leaf_idx
        else:
            heap = (1 << (h - 1)) + (leaf_idx - split)
        leaves.add(heap)
    return frozenset(leaves)


@lru_cache(maxsize=None)
def node_leaf_count(t: int, heap: int) -> int:
    leaves = leaf_heap_set(t)
    if heap in leaves:
        return 1
    h = ceil_log2(t)
    if heap >= (1 << h):
        return 0
    return node_leaf_count(t, heap << 1) + node_leaf_count(t, (heap << 1) | 1)


@lru_cache(maxsize=None)
def octopus_dist_for_node(t: int, heap: int, max_k: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    leaves = node_leaf_count(t, heap)
    limit = min(max_k, leaves)
    out: list[dict[int, int]] = [dict() for _ in range(limit + 1)]
    if leaves == 0:
        out[0][0] = 1
    elif heap in leaf_heap_set(t):
        out[0][0] = 1
        if limit >= 1:
            out[1][0] = 1
    else:
        left = octopus_dist_for_node(t, heap << 1, max_k)
        right = octopus_dist_for_node(t, (heap << 1) | 1, max_k)
        for l_count, l_dist in enumerate(left):
            for r_count, r_dist in enumerate(right):
                r_total = l_count + r_count
                if r_total > limit:
                    continue
                if not l_dist or not r_dist:
                    continue
                extra = 0
                if (l_count == 0) ^ (r_count == 0):
                    extra = 1
                for l_size, l_ways in l_dist:
                    for r_size, r_ways in r_dist:
                        out[r_total][l_size + r_size + extra] = (
                            out[r_total].get(l_size + r_size + extra, 0)
                            + l_ways * r_ways
                        )
    return tuple(tuple(sorted(d.items())) for d in out)


@lru_cache(maxsize=None)
def child_auth_distribution(t: int, child_k: int) -> tuple[tuple[int, float], ...]:
    dist = octopus_dist_for_node(t, 1, child_k)[child_k]
    denom = math.comb(t, child_k)
    return tuple((auth, ways / denom) for auth, ways in dist)


@lru_cache(maxsize=None)
def total_auth_cdf(K: int, B: int, t: int, child_k: int) -> tuple[tuple[int, float], ...]:
    child = child_auth_distribution(t, child_k)
    dist = {0: 1.0}
    for _ in range(K):
        nxt: dict[int, float] = {}
        for acc, p_acc in dist.items():
            for auth, p_auth in child:
                nxt[acc + auth] = nxt.get(acc + auth, 0.0) + p_acc * p_auth
        dist = nxt

    cdf: list[tuple[int, float]] = []
    running = 0.0
    for child_total in sorted(dist):
        running += dist[child_total]
        cdf.append((K * B + child_total, min(1.0, running)))
    return tuple(cdf)


def choose_mmax(
    K: int,
    B: int,
    t: int,
    child_k: int,
    max_mmax: int,
    min_tau: float,
) -> tuple[int, float] | None:
    for mmax, tau in total_auth_cdf(K, B, t, child_k):
        if mmax > max_mmax:
            return None
        if tau >= min_tau:
            return mmax, tau
    return None


def tau_at_mmax(K: int, B: int, t: int, child_k: int, mmax_limit: int) -> float:
    tau = 0.0
    for mmax, prob in total_auth_cdf(K, B, t, child_k):
        if mmax > mmax_limit:
            break
        tau = prob
    return tau


@lru_cache(maxsize=None)
def bpors_bitsec(q_sigs: int, n: int, h: int, K: int, B: int, t: int, child_k: int) -> float:
    denom = mp.mpf(math.comb(t, child_k))
    coeffs: list[mp.mpf] = []
    bases: list[mp.mpf] = []
    p_bucket = mp.mpf(2) ** (-B)
    for i in range(child_k + 1):
        ratio = mp.mpf(math.comb(t - i, child_k)) / denom if t - i >= child_k else mp.mpf(0)
        coeffs.append(mp.mpf((-1 if i % 2 else 1) * math.comb(child_k, i)))
        bases.append(1 - p_bucket + p_bucket * ratio)

    p_hit = mp.mpf(2) ** (-h)
    q = mp.mpf(q_sigs)
    prob = (1 - p_hit) ** q
    mass = mp.mpf(0)
    total = mp.mpf(2) ** (-(8 * n))
    powers = [mp.mpf(1) for _ in bases]

    for gamma in range(4000):
        p_child = mp.fsum(c * x for c, x in zip(coeffs, powers))
        if p_child < 0 and abs(p_child) < mp.mpf("1e-120"):
            p_child = mp.mpf(0)
        total += prob * (p_child ** K)
        mass += prob
        if gamma > 500 and 1 - mass < mp.mpf("1e-100"):
            break
        next_gamma = gamma + 1
        prob *= ((q - gamma) / next_gamma) * (p_hit / (1 - p_hit))
        for idx, base in enumerate(bases):
            powers[idx] *= base

    return float(-mp.log(total, 2))


@lru_cache(maxsize=None)
def bpors_bitsec_fast(q_sigs: int, n: int, h: int, K: int, B: int, t: int, child_k: int) -> float:
    """Fast Poisson/float screen for BPORS cover security.

    The exact search still calls ``bpors_bitsec`` before accepting a candidate.
    This helper only filters combinations that are far below the requested
    target, avoiding many expensive high-precision inclusion-exclusion sums.
    """

    denom = float(math.comb(t, child_k))
    p_bucket = math.ldexp(1.0, -B)
    coeffs: list[float] = []
    bases: list[float] = []
    for i in range(child_k + 1):
        ratio = float(math.comb(t - i, child_k)) / denom if t - i >= child_k else 0.0
        coeffs.append(float((-1 if i % 2 else 1) * math.comb(child_k, i)))
        bases.append(1.0 - p_bucket + p_bucket * ratio)

    lam = math.ldexp(float(q_sigs), -h)
    prob = math.exp(-lam)
    powers = [1.0 for _ in bases]
    total = math.ldexp(1.0, -(8 * n))
    limit = max(1000, int(lam + 20.0 * math.sqrt(lam + 1.0) + 100.0))

    for gamma in range(limit):
        p_child = math.fsum(c * x for c, x in zip(coeffs, powers))
        if p_child < 0.0 and abs(p_child) < 1e-14:
            p_child = 0.0
        if p_child > 0.0:
            total += prob * (p_child ** K)
        next_gamma = gamma + 1
        prob *= lam / next_gamma
        if gamma > lam and prob < 1e-320:
            break
        for idx, base in enumerate(bases):
            powers[idx] *= base

    if total <= 0.0:
        return float("inf")
    return -math.log2(total)


def t_candidates(max_t: int, child_k: int) -> list[int]:
    vals: set[int] = set()
    max_t = min(max_t, 1 << MAX_CHILD_HEIGHT)
    multipliers = {
        1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 20, 24, 27, 32, 33,
        35, 40, 46, 48,
    }
    for b in range(1, MAX_CHILD_HEIGHT + 1):
        base = 1 << b
        for c in multipliers:
            t = c * base
            if child_k <= t <= max_t and ceil_log2(t) <= MAX_CHILD_HEIGHT:
                vals.add(t)
    for t in (64, 96, 128, 132, 160, 192, 224, 256, 280, 320, 384,
              448, 512, 640, 736, 768, 896, 1024, 1536, 2048, 3072,
              3456, 4096, 6144, 8192):
        if child_k <= t <= max_t:
            vals.add(t)
    return sorted(vals)


def focused_t_candidates(fallback_t: int, max_t: int, child_k: int) -> list[int]:
    lo = max(child_k, fallback_t // 3)
    hi = min(max_t, max(fallback_t * 3, fallback_t + 512))
    common = {
        64, 80, 96, 112, 128, 132, 160, 192, 216, 224, 256, 264,
        280, 320, 384, 448, 512, 640, 736, 768, 896, 1024, 1120,
        1280, 1536, 2048, 2560, 3072, 3456, 4096, 6144, 8192,
        fallback_t,
    }
    vals = {t for t in t_candidates(max_t, child_k) if lo <= t <= hi}
    vals.update(t for t in common if child_k <= t <= max_t)
    return sorted(vals)


def current_fallback(scenario: Scenario) -> Candidate:
    row = ACTIVE_FALLBACKS[scenario.name]
    h_vec = row["h_vec"]  # type: ignore[assignment]
    K = int(row["K"])
    B = int(row["B"])
    t = int(row["t"])
    child_k = int(row["child_k"])
    mmax = int(row["mmax"])
    w = int(row["w"])
    length = int(row["length"])
    baseline = ACTIVE_BASELINES[scenario.name]
    tau = tau_at_mmax(K, B, t, child_k, mmax)
    h = int(row["h"])
    d = int(row["d"])
    return Candidate(
        scenario.name, scenario.q_sigs, scenario.n, scenario.target_bits,
        h, d, h_vec, K, B, t, ceil_log2(t),
        child_k, mmax, CTR_BYTES, w, length, int(row["sig"]),
        bpors_bitsec(scenario.q_sigs, scenario.n, h, K, B, t, child_k),
        tau, keygen_hashcalls(h_vec, w, length),
        bpors_sign_hashcalls(sign_ht_hashcalls(h_vec, w, length), K, B, t, child_k, tau),
        bpors_verify_hashcalls(verify_ht_hashcalls(h, d, w, length), K, B, t, child_k, mmax),
        baseline.sign_hashcalls, baseline.verify_hashcalls,
    )


def is_feasible(c: Candidate) -> bool:
    return (
        c.bitsec >= c.target_bits + SECURITY_MARGIN_BITS
        and c.tau + 1e-18 >= tau_floor_for_name(c.name)
        and signature_cap_ok(c.name, c.sig)
        and keygen_cap_ok(c.name, c.keygen_hashcalls)
        and metric_lower_bounds_ok(c)
        and c.verify_hashcalls <= math.floor(ACTIVE_VERIFY_COST_SLACK * c.baseline_verify_hashcalls)
        and (
            not ACTIVE_ENFORCE_SIGN_CAP
            or c.sign_hashcalls <= math.floor(ACTIVE_SIGN_COST_SLACK * c.baseline_sign_hashcalls)
        )
    )


def signature_upper_bound(name: str, default_upper: int) -> int:
    cap = ACTIVE_SIGNATURE_CAPS.get(name)
    if cap is None:
        return default_upper
    value, strict = cap
    cap_upper = value if strict else value + 1
    return min(default_upper, cap_upper)


def signature_cap_ok(name: str, sig: int) -> bool:
    cap = ACTIVE_SIGNATURE_CAPS.get(name)
    if cap is None:
        return True
    value, strict = cap
    return sig < value if strict else sig <= value


def keygen_cap_ok(name: str, keygen: int) -> bool:
    cap = ACTIVE_KEYGEN_CAPS.get(name)
    return cap is None or keygen <= cap


def metric_lower_bounds_ok(c: Candidate) -> bool:
    bounds = ACTIVE_METRIC_LOWER_BOUNDS.get(c.name, {})
    return (
        c.sig >= bounds.get("sig", 0)
        and c.keygen_hashcalls >= bounds.get("keygen_hashcalls", 0)
        and c.sign_hashcalls >= bounds.get("sign_hashcalls", 0)
        and c.verify_hashcalls >= bounds.get("verify_hashcalls", 0)
    )


def bpors_sign_base(K: int, B: int, t: int) -> int:
    return K * (1 << B) * (3 * t - 1) + K * ((1 << B) - 1)


def bounded_draw_factor(bound: int) -> float:
    range32 = 1 << 32
    limit = range32 - (range32 % bound)
    return range32 / limit


def expected_distinct_draws(t: int, child_k: int) -> float:
    return sum(t / (t - i) for i in range(child_k))


def sampler_blocks(words: float) -> int:
    return max(1, math.ceil(words / BPORS_SAMPLER_BUF_U32))


def bpors_index_sampler_blocks(K: int, t: int, child_k: int) -> int:
    words = K * expected_distinct_draws(t, child_k) * bounded_draw_factor(t)
    return sampler_blocks(words)


def bpors_bucket_sampler_blocks(K: int) -> int:
    return sampler_blocks(K)


def bpors_sign_hashcalls(ht_sign: int, K: int, B: int, t: int, child_k: int, tau: float) -> int:
    trial_cost = bpors_index_sampler_blocks(K, t, child_k)
    success_cost = bpors_bucket_sampler_blocks(K)
    return ht_sign + bpors_sign_base(K, B, t) + success_cost + math.ceil(trial_cost / tau)


def bpors_verify_hashcalls(ht_verify: int, K: int, B: int, t: int, child_k: int, mmax: int) -> int:
    sampler_cost = bpors_index_sampler_blocks(K, t, child_k) + bpors_bucket_sampler_blocks(K)
    return ht_verify + 2 * K * child_k + mmax + sampler_cost


def parse_h_profile(text: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", text))


def search_scenario(scenario: Scenario, keep_per_scenario: int) -> tuple[Candidate, list[Candidate]]:
    baseline = ACTIVE_BASELINES[scenario.name]
    sign_cap = math.floor(ACTIVE_SIGN_COST_SLACK * baseline.sign_hashcalls)
    verify_cap = math.floor(ACTIVE_VERIFY_COST_SLACK * baseline.verify_hashcalls)
    if not ACTIVE_ENFORCE_SIGN_CAP:
        sign_cap = 10**30
    fallback_candidate = current_fallback(scenario)
    best: Candidate | None = fallback_candidate if is_feasible(fallback_candidate) else None
    upper_sig = best.sig if best is not None else baseline.sig + INITIAL_SIG_HEADROOM
    upper_sig = signature_upper_bound(scenario.name, upper_sig)
    candidates: list[Candidate] = [best] if best is not None else []
    fallback = ACTIVE_FALLBACKS[scenario.name]
    frontier_limit = (
        WIDE_HT_FRONTIER_LIMIT
        if scenario.name == "Kylin-512"
        else DEFAULT_HT_FRONTIER_LIMIT
    )

    w_values = list(range(scenario.w_min, scenario.w_max + 1))
    if scenario.name.endswith("-q24"):
        # q24 rows can afford very large signing work; keep w exhaustive but
        # avoid spending most of the search on signatures already larger than
        # the current BPORS upper bound.
        w_values = list(range(2, 65)) + [72, 80, 88, 96, 112, 128]

    ht_rows: list[tuple[int, int, int, int, int, tuple[int, ...], int, int]] = []
    for h in range(scenario.h_min, scenario.h_max + 1):
        for d in range(max(1, scenario.d_min), min(scenario.d_max, h) + 1):
            profiles = generate_layer_profiles(h, d)
            if not profiles:
                continue
            for w in w_values:
                length = wotscs_length(8 * scenario.n, w)
                for h_vec in profiles:
                    ht_sign = sign_ht_hashcalls(h_vec, w, length)
                    ht_verify = verify_ht_hashcalls(h, d, w, length)
                    ht_keygen = keygen_hashcalls(h_vec, w, length)
                    if ACTIVE_ENFORCE_SIGN_CAP and ht_sign >= sign_cap:
                        continue
                    if ht_verify >= verify_cap:
                        continue
                    if not keygen_cap_ok(scenario.name, ht_keygen):
                        continue
                    wrapper = scenario.n + (h + d * length) * scenario.n + CTR_BYTES
                    if wrapper >= upper_sig:
                        continue
                    ht_rows.append((wrapper, ht_sign, ht_verify, h, d, h_vec, w, length))

    ht_rows.sort()
    frontier: list[tuple[int, int, int, int, int, tuple[int, ...], int, int]] = []
    for row in ht_rows:
        wrapper, ht_sign, ht_verify, h = row[:4]
        dominated = False
        for kept in frontier:
            is_dominated = (
                kept[0] <= wrapper
                and kept[1] <= ht_sign
                and kept[2] <= ht_verify
                and kept[3] >= h
            )
            if is_dominated:
                dominated = True
                break
        if not dominated:
            frontier.append(row)
        if len(frontier) >= frontier_limit:
            break

    fb_K = int(fallback["K"])
    fb_B = int(fallback["B"])
    fb_t = int(fallback["t"])
    fb_child_k = int(fallback["child_k"])
    if not ACTIVE_WIDE_BPORS:
        K_values = range(max(2, fb_K - 2), min(MAX_BPORS_K, fb_K + 2) + 1)
        min_B = max(4, fb_B - 2)
        if scenario.name == "Kylin-512":
            K_values = range(12, 17)
            min_B = 5
        B_values = range(min_B, min(MAX_BPORS_B, fb_B + 2) + 1)
        child_k_values = range(max(2, fb_child_k - 2), min(12, fb_child_k + 2) + 1)
        if scenario.name == "Kylin-512":
            child_k_values = range(5, 8)
    else:
        K_values = range(scenario.bpors_K_min, min(MAX_BPORS_K, scenario.bpors_K_max) + 1)
        B_values = range(scenario.bpors_B_min, min(MAX_BPORS_B, scenario.bpors_B_max) + 1)
        child_k_values = range(scenario.child_k_min, min(12, scenario.child_k_max) + 1)

    for wrapper, ht_sign, ht_verify, h, d, h_vec, w, length in frontier:
                    max_ftselems = (upper_sig - wrapper - 1) // scenario.n
                    if max_ftselems <= 0:
                        continue
                    sign_rem = sign_cap - ht_sign
                    verify_rem = verify_cap - ht_verify
                    for K in K_values:
                        for B in B_values:
                            min_auth = K * B
                            if min_auth >= max_ftselems:
                                continue
                            for child_k in child_k_values:
                                if K * child_k + min_auth > max_ftselems:
                                    continue
                                max_mmax = min(max_ftselems - K * child_k, verify_rem - 2 * K * child_k)
                                if max_mmax < min_auth:
                                    continue
                                sig_lower = signature_bytes(scenario.n, h, d, length, K, child_k, min_auth)
                                if sig_lower >= upper_sig:
                                    continue
                                if ACTIVE_ENFORCE_SIGN_CAP:
                                    max_t_by_sign = (sign_rem - K * ((1 << B) - 1) - 1)
                                    max_t_by_sign //= max(1, K * (1 << B) * 3)
                                else:
                                    max_t_by_sign = 1 << MAX_CHILD_HEIGHT
                                if max_t_by_sign < child_k:
                                    continue
                                if ACTIVE_WIDE_BPORS:
                                    t_values = t_candidates(max_t_by_sign, child_k)
                                else:
                                    t_values = focused_t_candidates(fb_t, max_t_by_sign, child_k)
                                if (
                                    ACTIVE_ENFORCE_SIGN_CAP
                                    and not ACTIVE_WIDE_BPORS
                                    and scenario.name == "Kylin-512"
                                ):
                                    t_values = [
                                        t for t in (
                                            192, 224, 256, 280, 320, 384,
                                            448, 512, 640, 768,
                                        )
                                        if child_k <= t <= max_t_by_sign
                                    ]
                                for t in t_values:
                                    base_sign = bpors_sign_base(K, B, t)
                                    trial_cost = bpors_index_sampler_blocks(K, t, child_k)
                                    success_cost = bpors_bucket_sampler_blocks(K)
                                    fixed_sign = base_sign + success_cost
                                    if ACTIVE_ENFORCE_SIGN_CAP and fixed_sign >= sign_rem:
                                        continue
                                    needed_tau = max(
                                        tau_floor_for_name(scenario.name),
                                        trial_cost / max(1, sign_rem - fixed_sign),
                                    )
                                    pick = choose_mmax(K, B, t, child_k, max_mmax, needed_tau)
                                    if pick is None:
                                        continue
                                    mmax, tau = pick
                                    sig = signature_bytes(scenario.n, h, d, length, K, child_k, mmax)
                                    if sig >= upper_sig:
                                        continue
                                    rough_bitsec = bpors_bitsec_fast(
                                        scenario.q_sigs, scenario.n, h, K, B, t, child_k
                                    )
                                    if rough_bitsec + 1.0 < scenario.target_bits:
                                        continue
                                    bitsec = bpors_bitsec(scenario.q_sigs, scenario.n, h, K, B, t, child_k)
                                    if bitsec < scenario.target_bits + SECURITY_MARGIN_BITS:
                                        continue
                                    sign_cost = ht_sign + fixed_sign + math.ceil(trial_cost / tau)
                                    verify_cost = bpors_verify_hashcalls(ht_verify, K, B, t, child_k, mmax)
                                    keygen_cost = keygen_hashcalls(h_vec, w, length)
                                    if ACTIVE_ENFORCE_SIGN_CAP and sign_cost > sign_cap:
                                        continue
                                    if verify_cost > verify_cap:
                                        continue
                                    if not keygen_cap_ok(scenario.name, keygen_cost):
                                        continue
                                    cand = Candidate(
                                        scenario.name, scenario.q_sigs, scenario.n, scenario.target_bits,
                                        h, d, h_vec, K, B, t, ceil_log2(t), child_k, mmax,
                                        CTR_BYTES, w, length, sig, bitsec, tau,
                                        keygen_cost, sign_cost, verify_cost,
                                        baseline.sign_hashcalls, baseline.verify_hashcalls,
                                    )
                                    if not metric_lower_bounds_ok(cand):
                                        continue
                                    candidates.append(cand)
                                    if best is None or rank_key(cand) < rank_key(best):
                                        best = cand
                                        upper_sig = best.sig

    if best is None:
        raise RuntimeError(f"no feasible BPORS+FP candidate found for {scenario.name}")
    candidates = sorted(set(candidates), key=rank_key)
    return best, candidates[:keep_per_scenario]


def rank_key(c: Candidate) -> tuple[int, int, int, float, int, int, int, int, int]:
    return (c.sig, c.sign_hashcalls, c.verify_hashcalls, -c.bitsec, c.h, c.d, c.w, c.K, c.B)


def write_baseline_csv() -> None:
    fields = [
        "name", "q", "n", "target_bits", "h", "d", "h_profile", "h0",
        "fors_a", "fors_k", "w", "len", "sig",
        "sign_hashcalls", "verify_hashcalls",
    ]
    BASELINE_CSV.parent.mkdir(parents=True, exist_ok=True)
    with BASELINE_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for baseline in FORS_BASELINES.values():
            writer.writerow({
                "name": baseline.name,
                "q": format_q(baseline.q_sigs),
                "n": baseline.n,
                "target_bits": baseline.target_bits,
                "h": baseline.h,
                "d": baseline.d,
                "h_profile": "[" + ",".join(str(x) for x in baseline.h_vec) + "]",
                "h0": baseline.h_vec[0],
                "fors_a": baseline.a,
                "fors_k": baseline.k,
                "w": baseline.w,
                "len": baseline.length,
                "sig": baseline.sig,
                "sign_hashcalls": baseline.sign_hashcalls,
                "verify_hashcalls": baseline.verify_hashcalls,
            })


def candidate_to_row(c: Candidate) -> dict[str, str | int | float]:
    return {
        "name": c.name,
        "q": c.q_label,
        "n": c.n,
        "target_bits": c.target_bits,
        "h": c.h,
        "d": c.d,
        "h_profile": c.h_profile,
        "h0": c.h0,
        "bpors_K": c.K,
        "bpors_B": c.B,
        "bpors_t": c.t,
        "bpors_child_height": c.child_height,
        "bpors_k": c.child_k,
        "bpors_mmax": c.mmax,
        "bpors_ctr_bytes": c.ctr_bytes,
        "w": c.w,
        "len": c.length,
        "sig": c.sig,
        "bitsec": f"{c.bitsec:.6f}",
        "tau": f"{c.tau:.12g}",
        "keygen_hashcalls": c.keygen_hashcalls,
        "sign_hashcalls": c.sign_hashcalls,
        "verify_hashcalls": c.verify_hashcalls,
        "baseline_sign_hashcalls": c.baseline_sign_hashcalls,
        "baseline_verify_hashcalls": c.baseline_verify_hashcalls,
        "notes": ACTIVE_NOTES,
    }


def load_current_profile_rows(
    targets: dict[str, float],
    path: Path = FINAL_CSV,
) -> tuple[dict[str, Baseline], dict[str, dict[str, object]]]:
    baselines: dict[str, Baseline] = {}
    fallbacks: dict[str, dict[str, object]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["name"]
            h_vec = parse_h_profile(row["h_profile"])
            target = targets.get(name, float(row["target_bits"]))
            baselines[name] = Baseline(
                name=name,
                q_sigs=parse_q(row["q"]),
                n=int(row["n"]),
                target_bits=target,
                h=int(row["h"]),
                d=int(row["d"]),
                h_vec=h_vec,
                a=int(row["bpors_B"]),
                k=int(row["bpors_k"]),
                w=int(row["w"]),
                length=int(row["len"]),
                sig=int(row["sig"]),
                sign_hashcalls=int(row["sign_hashcalls"]),
                verify_hashcalls=int(row["verify_hashcalls"]),
            )
            fallbacks[name] = {
                "q_sigs": parse_q(row["q"]),
                "n": int(row["n"]),
                "target_bits": target,
                "h": int(row["h"]),
                "d": int(row["d"]),
                "h_vec": h_vec,
                "K": int(row["bpors_K"]),
                "B": int(row["bpors_B"]),
                "t": int(row["bpors_t"]),
                "child_k": int(row["bpors_k"]),
                "mmax": int(row["bpors_mmax"]),
                "w": int(row["w"]),
                "length": int(row["len"]),
                "sig": int(row["sig"]),
            }
    return baselines, fallbacks


def parse_q(text: str) -> int:
    if "^" in text:
        base, exp = text.split("^", 1)
        if base != "2":
            raise ValueError(f"unsupported q label: {text}")
        return 1 << int(exp)
    return int(text)


def exact_target_map() -> dict[str, float]:
    return {
        "Kylin-128": 128.0,
        "Kylin-256": 256.0,
        "Kylin-512": 512.0,
        "Kylin-128-q24": 128.0,
        "Kylin-256-q24": 256.0,
        "Kylin-512-q24": 512.0,
    }


def write_candidate_csv(path: Path, rows: Iterable[Candidate]) -> None:
    fields = [
        "name", "q", "n", "target_bits", "h", "d", "h_profile", "h0",
        "bpors_K", "bpors_B", "bpors_t", "bpors_child_height", "bpors_k",
        "bpors_mmax", "bpors_ctr_bytes", "w", "len", "sig", "bitsec",
        "tau", "keygen_hashcalls", "sign_hashcalls", "verify_hashcalls",
        "baseline_sign_hashcalls", "baseline_verify_hashcalls", "notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for c in rows:
            writer.writerow(candidate_to_row(c))


def params_h_text(c: Candidate) -> str:
    if len(c.h_vec) != c.d:
        raise ValueError(f"{c.name}: h_vec length does not match d")
    guard = f"""#if SPX_D != {c.d}
#error This implementation currently requires explicit per-layer heights for SPX_D == {c.d}
#endif

"""
    height_macros = "\n".join(
        f"#define SPX_TREE_HEIGHT_{i} {h_i}" for i, h_i in enumerate(c.h_vec)
    )
    sum_expr = " + \\\n     ".join(f"SPX_TREE_HEIGHT_{i}" for i in range(c.d))
    array = ", ".join(f"SPX_TREE_HEIGHT_{i}" for i in range(c.d))
    return f"""#ifndef SPX_PARAMS_H
#define SPX_PARAMS_H

#include <stdint.h>

#define SPX_NAMESPACE(s) SPX_##s

#define SPX_N {c.n}
#define SPX_FULL_HEIGHT {c.h}
#define SPX_D {c.d}
#define SPX_BPORS_K {c.K}
#define SPX_BPORS_B {c.B}
#define SPX_BPORS_T {c.t}
#define SPX_BPORS_CHILD_HEIGHT {c.child_height}
#define SPX_BPORS_CH_K {c.child_k}
#define SPX_BPORS_MMAX {c.mmax}
#define SPX_BPORS_CTR_BYTES {c.ctr_bytes}
#define SPX_WOTS_W {c.w}
#define SPX_WOTS_LEN {c.length}

#define SPX_ADDR_BYTES 32

#define SPX_WOTS_BYTES (SPX_WOTS_LEN * SPX_N)
#define SPX_WOTS_PK_BYTES SPX_WOTS_BYTES
#define SPX_WOTS_SUM (SPX_WOTS_LEN * (SPX_WOTS_W - 1) / 2)

{guard}{height_macros}

#define SPX_BOTTOM_TREE_HEIGHT SPX_TREE_HEIGHT_0
#define SPX_TOP_TREE_HEIGHT SPX_TREE_HEIGHT_{c.d - 1}

#define SPX_LAYER_HEIGHT_SUM \\
    ({sum_expr})

#if SPX_LAYER_HEIGHT_SUM != SPX_FULL_HEIGHT
#error Sum of per-layer heights must equal SPX_FULL_HEIGHT
#endif

#define SPX_MAX_TREE_HEIGHT SPX_TOP_TREE_HEIGHT

#if SPX_MAX_TREE_HEIGHT > 32
#error Each XMSS layer height must be at most 32 bits
#endif

#define SPX_TREE_BITS (SPX_FULL_HEIGHT - SPX_BOTTOM_TREE_HEIGHT)
#define SPX_TREE_BYTES ((SPX_TREE_BITS + 7) / 8)
#define SPX_LEAF_BITS SPX_BOTTOM_TREE_HEIGHT
#define SPX_LEAF_BYTES ((SPX_LEAF_BITS + 7) / 8)

#define SPX_BPORS_MSG_BYTES SPX_N
#define SPX_BPORS_BYTES \\
    (SPX_BPORS_CTR_BYTES + \\
     (SPX_BPORS_K * SPX_BPORS_CH_K + SPX_BPORS_MMAX) * SPX_N)
#define SPX_BPORS_PK_BYTES SPX_N
#define SPX_DGST_BYTES (SPX_BPORS_MSG_BYTES + SPX_TREE_BYTES + SPX_LEAF_BYTES)

#define SPX_BYTES (SPX_N + SPX_BPORS_BYTES + SPX_D * SPX_WOTS_BYTES + \\
                   SPX_FULL_HEIGHT * SPX_N)
#define SPX_PK_BYTES (2 * SPX_N)
#define SPX_SK_BYTES (4 * SPX_N)
#define SPX_SEED_BYTES (3 * SPX_N)

static inline uint32_t spx_tree_height(uint32_t layer)
{{
    static const uint8_t heights[SPX_D] = {{
        {array}
    }};

    return heights[layer];
}}

#include "shake_offsets.h"

#endif
"""


def implementation_dirs(name: str) -> list[Path]:
    if name.endswith("-q24"):
        return [
            ROOT / "Implementations/Additional_Implementation/Reference_Implementation" / name,
            ROOT / "Implementations/Additional_Implementation/Optimized_Implementation" / name,
        ]
    return [
        ROOT / "Implementations/Reference_Implementation" / name,
        ROOT / "Implementations/Optimized_Implementation" / name,
    ]


def sync_params(selected: dict[str, Candidate]) -> None:
    for candidate in selected.values():
        text = params_h_text(candidate)
        for directory in implementation_dirs(candidate.name):
            (directory / "params.h").write_text(text, encoding="utf-8")


def main() -> int:
    global ACTIVE_BASELINES, ACTIVE_FALLBACKS
    global ACTIVE_SIGN_COST_SLACK, ACTIVE_VERIFY_COST_SLACK
    global ACTIVE_ENFORCE_SIGN_CAP, ACTIVE_WIDE_BPORS
    global ACTIVE_TAU_FLOOR, ACTIVE_Q24_TAU_FLOOR, INITIAL_SIG_HEADROOM, ACTIVE_NOTES

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write selected CSV outputs")
    parser.add_argument("--sync-params", action="store_true", help="rewrite implementation params.h files")
    parser.add_argument("--keep", type=int, default=80, help="candidate rows to keep per scenario")
    parser.add_argument(
        "--cap-source",
        choices=("old-fors", "current"),
        default="old-fors",
        help="hash-call caps are taken from old FORS baselines or current final BPORS profiles",
    )
    parser.add_argument(
        "--cap-csv",
        type=Path,
        default=FINAL_CSV,
        help="CSV used when --cap-source=current; defaults to the working final profile CSV",
    )
    parser.add_argument(
        "--fallback-csv",
        type=Path,
        default=None,
        help="optional profile CSV used only as the search fallback/initial upper bound",
    )
    parser.add_argument(
        "--cost-slack",
        type=float,
        default=COST_SLACK,
        help="multiplier applied to both sign and verify caps unless the per-cap options are set",
    )
    parser.add_argument(
        "--sign-cost-slack",
        type=float,
        default=None,
        help="multiplier applied to the signing cap; overrides --cost-slack for signing",
    )
    parser.add_argument(
        "--verify-cost-slack",
        type=float,
        default=None,
        help="multiplier applied to the verification cap; overrides --cost-slack for verification",
    )
    parser.add_argument(
        "--no-sign-cap",
        action="store_true",
        help="do not enforce the signing hash-call cap; verification cap still applies",
    )
    parser.add_argument(
        "--wide-bpors",
        action="store_true",
        help="with --no-sign-cap, search the full BPORS K/B/k/t scenario ranges instead of the focused window",
    )
    parser.add_argument(
        "--exact-targets",
        action="store_true",
        help="use exact 128/256/512 classical target bits instead of legacy 127/255/511 targets",
    )
    parser.add_argument(
        "--tau-floor",
        type=float,
        default=TAU_FLOOR,
        help="minimum forced-pruning tau for primary profiles; use 0 to disable the explicit floor",
    )
    parser.add_argument(
        "--q24-tau-floor",
        type=float,
        default=Q24_TAU_FLOOR,
        help="minimum forced-pruning tau for q=2^24 profiles; use 0 to disable the explicit floor",
    )
    parser.add_argument(
        "--initial-sig-headroom",
        type=int,
        default=1,
        help="extra bytes allowed above the current cap source signature if its profile is infeasible",
    )
    parser.add_argument(
        "--profiles",
        nargs="*",
        default=None,
        help="optional subset of profile names to search",
    )
    args = parser.parse_args()

    targets = exact_target_map() if args.exact_targets else {}
    if args.cap_source == "current":
        ACTIVE_BASELINES, ACTIVE_FALLBACKS = load_current_profile_rows(targets, args.cap_csv)
        if args.fallback_csv is not None:
            _, ACTIVE_FALLBACKS = load_current_profile_rows(targets, args.fallback_csv)
    else:
        ACTIVE_BASELINES = FORS_BASELINES
        ACTIVE_FALLBACKS = SECURE_BPORS_FALLBACKS
    ACTIVE_SIGN_COST_SLACK = args.sign_cost_slack if args.sign_cost_slack is not None else args.cost_slack
    ACTIVE_VERIFY_COST_SLACK = (
        args.verify_cost_slack if args.verify_cost_slack is not None else args.cost_slack
    )
    ACTIVE_ENFORCE_SIGN_CAP = not args.no_sign_cap
    ACTIVE_WIDE_BPORS = args.wide_bpors
    ACTIVE_TAU_FLOOR = args.tau_floor
    ACTIVE_Q24_TAU_FLOOR = args.q24_tau_floor
    INITIAL_SIG_HEADROOM = args.initial_sig_headroom

    source_label = "current BPORS" if args.cap_source == "current" else "old-FORS"
    target_label = (
        " and exact 128/256/512 classical targets" if args.exact_targets else ""
    )
    if args.no_sign_cap:
        cap_label = (
            f"verify hashcall cap ({ACTIVE_VERIFY_COST_SLACK:g}x); "
            "signing cost is not capped"
        )
    else:
        cap_label = (
            f"sign/verify hashcall caps "
            f"({ACTIVE_SIGN_COST_SLACK:g}x/{ACTIVE_VERIFY_COST_SLACK:g}x)"
        )
    if ACTIVE_TAU_FLOOR == 0 and ACTIVE_Q24_TAU_FLOOR == 0:
        tau_label = "; no explicit tau floor"
    else:
        tau_label = (
            f"; tau floors primary={ACTIVE_TAU_FLOOR:g}, "
            f"q24={ACTIVE_Q24_TAU_FLOOR:g}"
        )
    ACTIVE_NOTES = (
        f"BPORS+FP retuned under {source_label} {cap_label}"
        f"{target_label}{tau_label}"
    )

    scenarios = SCENARIOS
    if args.exact_targets:
        target_map = exact_target_map()
        scenarios = tuple(
            Scenario(
                s.name, s.q_sigs, s.n, target_map[s.name], s.h_min, s.h_max,
                s.d_min, s.d_max, s.w_min, s.w_max, s.child_k_min,
                s.child_k_max, s.bpors_K_min, s.bpors_K_max, s.bpors_B_min,
                s.bpors_B_max,
            )
            for s in scenarios
        )
    if args.profiles:
        wanted = set(args.profiles)
        scenarios = tuple(s for s in scenarios if s.name in wanted)
        missing = wanted - {s.name for s in scenarios}
        if missing:
            raise SystemExit(f"unknown profile(s): {', '.join(sorted(missing))}")

    selected: dict[str, Candidate] = {}
    all_kept: list[Candidate] = []
    for scenario in scenarios:
        print(f"[search] {scenario.name}", flush=True)
        best, kept = search_scenario(scenario, args.keep)
        selected[scenario.name] = best
        all_kept.extend(kept)
        print(
            f"  selected sig={best.sig} h={best.h} d={best.d} h_vec={best.h_profile} "
            f"K={best.K} B={best.B} t={best.t} k={best.child_k} "
            f"mmax={best.mmax} w={best.w} len={best.length} "
            f"bitsec={best.bitsec:.6f} tau={best.tau:.3g} "
            f"sign={best.sign_hashcalls}/{best.baseline_sign_hashcalls} "
            f"verify={best.verify_hashcalls}/{best.baseline_verify_hashcalls}",
            flush=True,
        )

    if args.write:
        write_baseline_csv()
        write_candidate_csv(SEARCH_CSV, all_kept)
        write_candidate_csv(FINAL_CSV, selected.values())
        write_candidate_csv(SELECTED_CSV, selected.values())
    if args.sync_params:
        sync_params(selected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
