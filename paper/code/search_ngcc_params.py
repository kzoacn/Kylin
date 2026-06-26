#!/usr/bin/env python3
"""Search and select NGCC-aligned Kylin parameter families with per-layer HT heights.

This script evaluates SPHINCSA/Kylin parameter candidates under the current
single-key NGCC interpretation (default q = 2^64 signatures per key pair).
The query budget q can be overridden from CLI.

Compared to the legacy h/d model, this version supports explicit hypertree
layer-height vectors h_vec = (h_0, ..., h_{d-1}) with:
  - sum(h_i) = h
  - h_0 used for message-digest leaf-index bits
  - signing-time hash-call proxy using sum_i 2^{h_i}

By default (q = 2^64 and no explicit --shape), the script emits the frozen
packaged BPORS+FP rows from paper/data/para_kylin_final_6profiles.csv. The
legacy FORS-oriented search helpers are retained for historical exploration.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Sequence

import mpmath as mp

mp.mp.dps = 80

ROOT = Path(__file__).resolve().parents[2]
CURRENT_FINAL_CSV = ROOT / "paper/data/para_kylin_final_6profiles.csv"
DEFAULT_Q_SIGS = 2**64
Q_SIGS = DEFAULT_Q_SIGS
W_CHOICES = tuple(range(8, 129))
H_CHOICES = tuple(range(60, 71))
A_CHOICES = tuple(range(8, 31))

# Legacy fallback shape used only when --shape is not provided and q != 2^64.
PREFERRED_SHAPE = (70, 10, 14, 64)

# Implementation-facing constraints for generated h-vectors.
# - h - h0 <= 64 keeps tree index extraction in 64-bit path.
# - h_i <= 32 (relaxed from 16) for broader parameter exploration.
MAX_LAYER_HEIGHT = 32


def set_query_budget(q_sigs: int) -> None:
    global Q_SIGS
    if q_sigs <= 0:
        raise ValueError("q must be a positive integer")
    if q_sigs == Q_SIGS:
        return
    Q_SIGS = q_sigs
    # These caches depend on q through q-hit probabilities/security checks.
    qhit_distribution.cache_clear()
    classical_bit_security.cache_clear()
    minimal_k.cache_clear()


def format_q(q_sigs: int) -> str:
    if q_sigs > 0 and (q_sigs & (q_sigs - 1)) == 0:
        return f"2^{q_sigs.bit_length() - 1}"
    return str(q_sigs)


@dataclass(frozen=True)
class Family:
    name: str
    ngcc_classical: int
    ngcc_quantum: int
    n: int
    target_bits: int


@dataclass(frozen=True)
class BaselineParameter:
    name: str
    q_sigs: int
    n: int
    h: int
    d: int
    h_prime: int | None
    log_t: int | None
    a: int | None
    k: int
    w: int | None
    l: int | None
    lgw: int | None
    m: int | None
    bitsec: float | None
    sec_level: str | None
    category: str | None
    bytes_value: int | None


@dataclass(frozen=True)
class Candidate:
    family: Family
    h: int
    d: int
    h_vec: tuple[int, ...]
    a: int
    k: int
    w: int
    length: int
    classical_bitsec: float
    quantum_bitsec: float
    sig_bytes: int
    hash_calls: int

    @property
    def pk_bytes(self) -> int:
        return 2 * self.family.n

    @property
    def sk_bytes(self) -> int:
        return 4 * self.family.n

    @property
    def h0(self) -> int:
        return self.h_vec[0]

    @property
    def tree_bits(self) -> int:
        return self.h - self.h0

    @property
    def digest_bytes(self) -> int:
        return ((self.k * self.a + 7) // 8) + ((self.tree_bits + 7) // 8) + ((self.h0 + 7) // 8)

    @property
    def subtree(self) -> str:
        if all(v == self.h_vec[0] for v in self.h_vec):
            return str(self.h_vec[0])
        return "-"

    @property
    def h_profile(self) -> str:
        return "[" + ",".join(str(v) for v in self.h_vec) + "]"


FAMILIES = (
    Family("Kylin-128", 128, 80, 16, 128),
    Family("Kylin-256", 256, 128, 32, 256),
    Family("Kylin-512", 512, 256, 64, 512),
)


# Fixed external baseline sets kept in code for future tuning/reference.
BASELINE_PARAMETERS = (
    BaselineParameter(
        name="sphincs-a-128s",
        q_sigs=2**64,
        n=16,
        h=63,
        d=9,
        h_prime=7,
        log_t=13,
        a=13,
        k=12,
        w=73,
        l=22,
        lgw=None,
        m=28,
        bitsec=128,
        sec_level="I",
        category="1",
        bytes_value=None,
    ),
    BaselineParameter(
        name="sphincs-a-256s",
        q_sigs=2**64,
        n=32,
        h=66,
        d=11,
        h_prime=6,
        log_t=13,
        a=13,
        k=23,
        w=79,
        l=42,
        lgw=None,
        m=47,
        bitsec=255,
        sec_level="V",
        category="5",
        bytes_value=None,
    ),
    BaselineParameter(
        name="SLH-DSA-SHAKE-128-24",
        q_sigs=2**24,
        n=16,
        h=22,
        d=1,
        h_prime=22,
        log_t=24,
        a=24,
        k=6,
        w=4,
        l=67,
        lgw=2,
        m=21,
        bitsec=127.28077264423924,
        sec_level="I",
        category="1",
        bytes_value=32,
    ),
    BaselineParameter(
        name="SLH-DSA-SHAKE-256-24",
        q_sigs=2**24,
        n=32,
        h=21,
        d=1,
        h_prime=21,
        log_t=25,
        a=25,
        k=12,
        w=4,
        l=131,
        lgw=2,
        m=41,
        bitsec=255.35935186139096,
        sec_level="V",
        category="5",
        bytes_value=64,
    ),
)


@lru_cache(maxsize=None)
def const_sum_count(length: int, w: int) -> int:
    """Count constant-sum WOTSCS encodings with exact DP."""
    total = length * (w - 1) // 2
    dp = [0] * (total + 1)
    dp[0] = 1
    for _ in range(length):
        next_dp = [0] * (total + 1)
        window = 0
        for idx in range(total + 1):
            window += dp[idx]
            if idx - w >= 0:
                window -= dp[idx - w]
            next_dp[idx] = window
        dp = next_dp
    return dp[total]


@lru_cache(maxsize=None)
def wotscs_length(message_bits: int, w: int) -> int:
    for length in range(2, 700):
        if mp.log(const_sum_count(length, w), 2) > message_bits:
            return length
    raise RuntimeError(f"failed to find WOTSCS length for {message_bits=} {w=}")


def layer_count_choices(h: int) -> range:
    """Enumerate feasible HT layer counts without assuming h is divisible by d."""
    # If each layer is at most MAX_LAYER_HEIGHT, we need at least ceil(h / max_h_i)
    # layers. We keep the upper bound compact for runtime and reproducibility.
    min_d = max(6, (h + MAX_LAYER_HEIGHT - 1) // MAX_LAYER_HEIGHT)
    max_d = min(24, h)
    return range(min_d, max_d + 1)


@lru_cache(maxsize=None)
def qhit_distribution(h: int, limit: int = 220) -> tuple[mp.mpf, ...]:
    """Exact small-r binomial distribution for q signatures over 2^h leaves."""
    p = mp.mpf(2) ** (-h)
    q = mp.mpf(Q_SIGS)
    cur = mp.e ** (q * mp.log1p(-p))
    probs = [cur]
    for r in range(limit):
        cur *= ((q - r) / (r + 1)) * (p / (1 - p))
        probs.append(cur)
    return tuple(probs)


@lru_cache(maxsize=None)
def classical_bit_security(n: int, h: int, a: int, k: int) -> mp.mpf:
    total = mp.mpf(2) ** (-8 * n)
    tree_size = mp.mpf(2) ** a
    for r, qprob in enumerate(qhit_distribution(h)):
        total += qprob * (1 - (1 - 1 / tree_size) ** r) ** k
    return -mp.log(total, 2)


def quantum_bit_security(n: int, h: int, a: int, k: int) -> mp.mpf:
    return classical_bit_security(n, h, a, k) / 2


def signature_bytes(n: int, h: int, d: int, a: int, k: int, length: int) -> int:
    return ((a + 1) * k + h + length * d + 1) * n


def hash_calls(h_vec: Sequence[int], a: int, k: int, w: int, length: int) -> int:
    # FORS plus HT signing proxy from the text formulas.
    return k * (2 ** (a + 1)) + sum((2**layer_h) * (length * w + 1) for layer_h in h_vec)


def balanced_profile(h: int, d: int) -> tuple[int, ...]:
    base = h // d
    rem = h % d
    return tuple(base + (1 if i < rem else 0) for i in range(d))


def shift_height(profile: tuple[int, ...], src: int, dst: int, amount: int) -> tuple[int, ...] | None:
    if amount <= 0:
        return profile
    p = list(profile)
    if src == dst:
        return tuple(p)
    if p[src] - amount < 1:
        return None
    p[src] -= amount
    p[dst] += amount
    return tuple(p)


def profile_is_compatible(h: int, h_vec: Sequence[int]) -> bool:
    if not h_vec:
        return False
    if any(v < 1 for v in h_vec):
        return False
    if sum(h_vec) != h:
        return False
    if max(h_vec) > MAX_LAYER_HEIGHT:
        return False
    h0 = h_vec[0]
    if h - h0 > 64:
        return False
    return True


def generate_layer_profiles(h: int, d: int) -> list[tuple[int, ...]]:
    """Generate a small deterministic candidate set of h-vectors.

    We keep the profile space intentionally compact for reproducibility and
    runtime. The balanced profile is always included, and a few near-balanced
    perturbations are added when valid.
    """
    core = balanced_profile(h, d)
    profiles: set[tuple[int, ...]] = {core}

    # Move one/two levels from top to bottom and vice versa as nearby variants.
    top = d - 1
    maybe = [
        shift_height(core, top, 0, 1),
        shift_height(core, top, 0, 2),
        shift_height(core, 0, top, 1),
        shift_height(core, 0, top, 2),
    ]

    # Also perturb around the middle layers to avoid strict end-biased choices.
    mid = d // 2
    maybe.extend(
        [
            shift_height(core, mid, 0, 1),
            shift_height(core, mid, top, 1),
            shift_height(core, top, mid, 1),
            shift_height(core, 0, mid, 1),
        ]
    )

    for candidate in maybe:
        if candidate is not None and profile_is_compatible(h, candidate):
            profiles.add(candidate)

    # Deterministic ordering.
    return sorted(profiles)


@lru_cache(maxsize=None)
def minimal_k(family: Family, h: int, a: int) -> int | None:
    upper = 240 if family.target_bits < 512 else 420
    lower = 10 if family.target_bits < 512 else 30
    if classical_bit_security(family.n, h, a, upper) < family.target_bits:
        return None
    lo = lower
    hi = upper
    while lo < hi:
        mid = (lo + hi) // 2
        if classical_bit_security(family.n, h, a, mid) >= family.target_bits:
            hi = mid
        else:
            lo = mid + 1
    if classical_bit_security(family.n, h, a, lo) >= family.target_bits:
        return lo
    return None


def enumerate_candidates(family: Family, h_choices: Sequence[int] = H_CHOICES) -> list[Candidate]:
    candidates: list[Candidate] = []
    for h in h_choices:
        for a in A_CHOICES:
            k = minimal_k(family, h, a)
            if k is None:
                continue
            classical = float(classical_bit_security(family.n, h, a, k))
            quantum = float(quantum_bit_security(family.n, h, a, k))
            for w in W_CHOICES:
                length = wotscs_length(8 * family.n, w)
                for d in layer_count_choices(h):
                    for h_vec in generate_layer_profiles(h, d):
                        candidates.append(
                            Candidate(
                                family=family,
                                h=h,
                                d=d,
                                h_vec=h_vec,
                                a=a,
                                k=k,
                                w=w,
                                length=length,
                                classical_bitsec=classical,
                                quantum_bitsec=quantum,
                                sig_bytes=signature_bytes(family.n, h, d, a, k, length),
                                hash_calls=hash_calls(h_vec, a, k, w, length),
                            )
                        )
    return candidates


def choose_fixed_shape(
    candidates: dict[str, list[Candidate]],
    shape: tuple[int, int, int, int],
) -> dict[str, Candidate]:
    h, d, a, w = shape
    chosen: dict[str, Candidate] = {}
    for family_name, family_candidates in candidates.items():
        matches = [
            candidate
            for candidate in family_candidates
            if candidate.h == h and candidate.d == d and candidate.a == a and candidate.w == w
        ]
        if not matches:
            raise RuntimeError(f"failed to find fixed shape {shape} for {family_name}")
        # Same signature size for fixed (h,d,a,k,w,l,n); prefer faster profile.
        chosen[family_name] = min(matches, key=lambda c: (c.sig_bytes, c.hash_calls, c.h_vec))
    return chosen


def candidate_fieldnames() -> list[str]:
    return [
        "name",
        "ngccclassical",
        "ngccquantum",
        "n",
        "h",
        "d",
        "h_profile",
        "h0",
        "a",
        "k",
        "w",
        "len",
        "subtree",
        "digest_bytes",
        "classical",
        "quantum",
        "pk",
        "sk",
        "sig",
        "hashcalls",
        "q",
    ]


def baseline_fieldnames() -> list[str]:
    return [
        "name",
        "q",
        "n",
        "h",
        "d",
        "h_prime",
        "log_t",
        "a",
        "k",
        "w",
        "l",
        "lgw",
        "m",
        "bitsec",
        "sec_level",
        "category",
        "bytes",
    ]


def baseline_to_row(baseline: BaselineParameter) -> dict[str, str | int | float]:
    return {
        "name": baseline.name,
        "q": format_q(baseline.q_sigs),
        "n": baseline.n,
        "h": baseline.h,
        "d": baseline.d,
        "h_prime": baseline.h_prime if baseline.h_prime is not None else "",
        "log_t": baseline.log_t if baseline.log_t is not None else "",
        "a": baseline.a if baseline.a is not None else "",
        "k": baseline.k,
        "w": baseline.w if baseline.w is not None else "",
        "l": baseline.l if baseline.l is not None else "",
        "lgw": baseline.lgw if baseline.lgw is not None else "",
        "m": baseline.m if baseline.m is not None else "",
        "bitsec": baseline.bitsec if baseline.bitsec is not None else "",
        "sec_level": baseline.sec_level if baseline.sec_level is not None else "",
        "category": baseline.category if baseline.category is not None else "",
        "bytes": baseline.bytes_value if baseline.bytes_value is not None else "",
    }


def candidate_to_row(candidate: Candidate) -> dict[str, str | int]:
    return {
        "name": candidate.family.name,
        "ngccclassical": candidate.family.ngcc_classical,
        "ngccquantum": candidate.family.ngcc_quantum,
        "n": candidate.family.n,
        "h": candidate.h,
        "d": candidate.d,
        "h_profile": candidate.h_profile,
        "h0": candidate.h0,
        "a": candidate.a,
        "k": candidate.k,
        "w": candidate.w,
        "len": candidate.length,
        "subtree": candidate.subtree,
        "digest_bytes": candidate.digest_bytes,
        "classical": f"{candidate.classical_bitsec:.1f}",
        "quantum": f"{candidate.quantum_bitsec:.1f}",
        "pk": candidate.pk_bytes,
        "sk": candidate.sk_bytes,
        "sig": candidate.sig_bytes,
        "hashcalls": candidate.hash_calls,
        "q": format_q(Q_SIGS),
    }


def current_ngcc_fieldnames() -> list[str]:
    return [
        "name",
        "ngccclassical",
        "ngccquantum",
        "q",
        "n",
        "h",
        "d",
        "h_profile",
        "h0",
        "bpors_K",
        "bpors_B",
        "bpors_t",
        "bpors_k",
        "bpors_mmax",
        "w",
        "len",
        "bitsec",
        "quantum",
        "pk",
        "sk",
        "sig",
        "sign_hashcalls",
        "verify_hashcalls",
    ]


def load_current_ngcc_rows(path: Path = CURRENT_FINAL_CSV) -> list[dict[str, str | int]]:
    levels = {
        "Kylin-128": (128, 80),
        "Kylin-256": (256, 128),
        "Kylin-512": (512, 256),
    }
    rows: list[dict[str, str | int]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            name = row["name"]
            if name not in levels:
                continue
            classical, quantum_level = levels[name]
            n = int(row["n"])
            bitsec = float(row["bitsec"])
            rows.append(
                {
                    "name": name,
                    "ngccclassical": classical,
                    "ngccquantum": quantum_level,
                    "q": row["q"],
                    "n": n,
                    "h": int(row["h"]),
                    "d": int(row["d"]),
                    "h_profile": row["h_profile"],
                    "h0": int(row["h0"]),
                    "bpors_K": int(row["bpors_K"]),
                    "bpors_B": int(row["bpors_B"]),
                    "bpors_t": int(row["bpors_t"]),
                    "bpors_k": int(row["bpors_k"]),
                    "bpors_mmax": int(row["bpors_mmax"]),
                    "w": int(row["w"]),
                    "len": int(row["len"]),
                    "bitsec": f"{bitsec:.3f}",
                    "quantum": f"{bitsec / 2:.3f}",
                    "pk": 2 * n,
                    "sk": 4 * n,
                    "sig": int(row["sig"]),
                    "sign_hashcalls": int(row["sign_hashcalls"]),
                    "verify_hashcalls": int(row["verify_hashcalls"]),
                }
            )
    expected = {"Kylin-128", "Kylin-256", "Kylin-512"}
    got = {str(row["name"]) for row in rows}
    if got != expected:
        raise RuntimeError(f"unexpected current NGCC profile set: {sorted(got)}")
    return rows


def write_current_ngcc_csv(rows: list[dict[str, str | int]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=current_ngcc_fieldnames())
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_baseline_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=baseline_fieldnames())
        writer.writeheader()
        for baseline in BASELINE_PARAMETERS:
            writer.writerow(baseline_to_row(baseline))


def write_selected_csv(candidates: dict[str, Candidate], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=candidate_fieldnames())
        writer.writeheader()
        for family_name in sorted(candidates):
            writer.writerow(candidate_to_row(candidates[family_name]))


def write_matches_csv(candidates: Sequence[Candidate], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=candidate_fieldnames())
        writer.writeheader()
        for candidate in candidates:
            writer.writerow(candidate_to_row(candidate))


def print_baselines() -> None:
    print("Baselines kept in code:")
    for baseline in BASELINE_PARAMETERS:
        print(
            f"{baseline.name}: q={format_q(baseline.q_sigs)}, n={baseline.n}, h={baseline.h}, "
            f"d={baseline.d}, h'={baseline.h_prime if baseline.h_prime is not None else '-'}, "
            f"log_t={baseline.log_t if baseline.log_t is not None else '-'}, "
            f"a={baseline.a if baseline.a is not None else '-'}, k={baseline.k}, "
            f"w={baseline.w if baseline.w is not None else '-'}, "
            f"l={baseline.l if baseline.l is not None else '-'}, "
            f"lgw={baseline.lgw if baseline.lgw is not None else '-'}, "
            f"m={baseline.m if baseline.m is not None else '-'}, "
            f"bitsec={baseline.bitsec if baseline.bitsec is not None else '-'}, "
            f"sec_level={baseline.sec_level if baseline.sec_level is not None else '-'}, "
            f"category={baseline.category if baseline.category is not None else '-'}, "
            f"bytes={baseline.bytes_value if baseline.bytes_value is not None else '-'}"
        )


def sort_key(candidate: Candidate) -> tuple[int, int, int, int, int, int, int, tuple[int, ...]]:
    return (
        candidate.sig_bytes,
        candidate.hash_calls,
        candidate.h,
        candidate.d,
        candidate.a,
        candidate.k,
        candidate.w,
        candidate.h_vec,
    )


def select_matches(
    all_candidates: dict[str, list[Candidate]],
    sig_max: int | None,
) -> dict[str, list[Candidate]]:
    selected: dict[str, list[Candidate]] = {}
    for family_name, family_candidates in all_candidates.items():
        rows = family_candidates
        if sig_max is not None:
            rows = [candidate for candidate in rows if candidate.sig_bytes <= sig_max]
        selected[family_name] = sorted(rows, key=sort_key)
    return selected


def print_selected(
    selected: dict[str, Candidate],
    shape: tuple[int, int, int, int] | None = None,
) -> None:
    print("Query budget q:", format_q(Q_SIGS))
    if shape is None:
        print("Selected frozen packaged profiles (per family).")
    else:
        print("Selected fixed implementation shape (h, d, a, w):", shape)
    for family_name in sorted(selected):
        candidate = selected[family_name]
        print(
            f"{candidate.family.name}: "
            f"n={candidate.family.n}, h={candidate.h}, d={candidate.d}, "
            f"h_vec={candidate.h_profile}, h0={candidate.h0}, "
            f"a={candidate.a}, k={candidate.k}, w={candidate.w}, len={candidate.length}, "
            f"classical={candidate.classical_bitsec:.1f}, "
            f"ngcc_quantum={candidate.family.ngcc_quantum}, "
            f"formula_quantum={candidate.quantum_bitsec:.1f}, "
            f"pk={candidate.pk_bytes}, sk={candidate.sk_bytes}, sig={candidate.sig_bytes}, "
            f"digest_bytes={candidate.digest_bytes}, hashcalls={candidate.hash_calls}"
        )


def print_current_ngcc_rows(rows: list[dict[str, str | int]]) -> None:
    print("Selected frozen packaged BPORS+FP profiles (q=2^64).")
    for row in rows:
        print(
            f"{row['name']}: n={row['n']}, h={row['h']}, d={row['d']}, "
            f"h_vec={row['h_profile']}, BPORS=({row['bpors_K']},{row['bpors_B']},"
            f"{row['bpors_t']},{row['bpors_k']},{row['bpors_mmax']}), "
            f"w={row['w']}, len={row['len']}, bitsec={row['bitsec']}, "
            f"pk={row['pk']}, sk={row['sk']}, sig={row['sig']}, "
            f"sign={row['sign_hashcalls']}, verify={row['verify_hashcalls']}"
        )


def print_matches(
    matched: dict[str, list[Candidate]],
    h_min: int,
    h_max: int,
    sig_max: int | None,
    top: int,
) -> None:
    sig_desc = f"sig <= {sig_max}" if sig_max is not None else "sig unconstrained"
    print(f"Search constraints: q={format_q(Q_SIGS)}, h=[{h_min},{h_max}], {sig_desc}")
    total = 0
    for family_name in sorted(matched):
        rows = matched[family_name]
        total += len(rows)
        print(f"{family_name}: {len(rows)} matches")
        for candidate in rows[:top]:
            print(
                f"  sig={candidate.sig_bytes}, hashcalls={candidate.hash_calls}, "
                f"h={candidate.h}, d={candidate.d}, h_vec={candidate.h_profile}, "
                f"a={candidate.a}, k={candidate.k}, w={candidate.w}, len={candidate.length}, "
                f"classical={candidate.classical_bitsec:.1f}"
            )
    print(f"Total matches: {total}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--print-baselines",
        action="store_true",
        help="Print the fixed baseline parameter sets kept in this script.",
    )
    parser.add_argument(
        "--write-baseline-csv",
        type=Path,
        default=None,
        help="Write baseline parameter sets to a CSV file and exit.",
    )
    parser.add_argument(
        "--search",
        action="store_true",
        help="Run constrained search and print matching candidates instead of fixed-shape selection.",
    )
    parser.add_argument(
        "--h-min",
        type=int,
        default=min(H_CHOICES),
        help="Minimum h for candidate enumeration.",
    )
    parser.add_argument(
        "--h-max",
        type=int,
        default=max(H_CHOICES),
        help="Maximum h for candidate enumeration.",
    )
    parser.add_argument(
        "--sig-max",
        type=int,
        default=None,
        help="Optional signature-size upper bound (bytes) used by --search.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="How many matched rows per family to print in --search mode.",
    )
    parser.add_argument(
        "--write-search-csv",
        type=Path,
        default=None,
        help="Optional CSV path for all matched candidates in --search mode.",
    )
    q_group = parser.add_mutually_exclusive_group()
    q_group.add_argument(
        "--q-bits",
        type=int,
        default=64,
        help="Set q as 2^Q_BITS (default: 64).",
    )
    q_group.add_argument(
        "--q-sigs",
        type=int,
        default=None,
        help="Set q directly as an integer signature-query budget.",
    )
    parser.add_argument(
        "--write-csv",
        type=Path,
        default=None,
        help="Optionally write the selected parameter rows to a CSV file.",
    )
    parser.add_argument(
        "--shape",
        nargs=4,
        metavar=("H", "D", "A", "W"),
        type=int,
        default=None,
        help="Optional fixed shape (h, d, a, w). If omitted with q=2^64, emit frozen packaged profiles.",
    )
    args = parser.parse_args()

    if args.h_min < 1:
        parser.error("--h-min must be >= 1")
    if args.h_max < args.h_min:
        parser.error("--h-max must be >= --h-min")
    if args.top < 1:
        parser.error("--top must be >= 1")
    if args.q_sigs is not None and args.q_sigs <= 0:
        parser.error("--q-sigs must be > 0")
    if args.q_bits < 0:
        parser.error("--q-bits must be >= 0")

    if args.print_baselines:
        print_baselines()
    if args.write_baseline_csv:
        write_baseline_csv(args.write_baseline_csv)
        print(f"Wrote {args.write_baseline_csv}")
    if args.print_baselines or args.write_baseline_csv:
        return

    q_sigs = args.q_sigs if args.q_sigs is not None else 2**args.q_bits
    set_query_budget(q_sigs)
    h_choices = tuple(range(args.h_min, args.h_max + 1))

    shape = tuple(args.shape) if args.shape is not None else None
    if shape is not None and len(shape) != 4:
        parser.error("--shape must provide exactly 4 integers")

    # Default non-search output is the frozen packaged BPORS+FP q=2^64 profile set.
    if not args.search and shape is None and q_sigs == DEFAULT_Q_SIGS:
        rows = load_current_ngcc_rows()
        print_current_ngcc_rows(rows)
        if args.write_csv:
            write_current_ngcc_csv(rows, args.write_csv)
            print(f"Wrote {args.write_csv}")
        return

    all_candidates: dict[str, list[Candidate]] = {}
    for family in FAMILIES:
        all_candidates[family.name] = enumerate_candidates(family, h_choices)

    if args.search:
        matched = select_matches(all_candidates, args.sig_max)
        print_matches(matched, args.h_min, args.h_max, args.sig_max, args.top)
        if args.write_search_csv:
            flat_rows: list[Candidate] = []
            for family_name in sorted(matched):
                flat_rows.extend(matched[family_name])
            write_matches_csv(flat_rows, args.write_search_csv)
            print(f"Wrote {args.write_search_csv}")
        return

    if shape is None:
        shape = PREFERRED_SHAPE

    chosen = choose_fixed_shape(all_candidates, shape)
    print_selected(chosen, shape)

    if args.write_csv:
        write_selected_csv(chosen, args.write_csv)
        print(f"Wrote {args.write_csv}")


if __name__ == "__main__":
    main()
