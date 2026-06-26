#!/usr/bin/env python3
"""Reference checker for the frozen Kylin BPORS+FP parameter profiles.

This appendix script mirrors the current repository source of truth,
``paper/data/para_kylin_final_6profiles.csv``.  It verifies the six frozen
primary and companion profiles by recomputing signature size, the conservative
BPORS+FP cover exponent, and the recorded sign/verify hash-call proxies.
"""

from __future__ import annotations

import csv
import math
from math import comb
from pathlib import Path

import mpmath as mp

mp.mp.dps = 120

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "paper/data/para_kylin_final_6profiles.csv"
CTR_BYTES = 8
BPORS_SAMPLER_BUF_U32 = 512 // 4
SECURITY_TOLERANCE = mp.mpf("1e-12")

EXPECTED = {
    "Kylin-128": (2**64, 16, 62, 7, (8, 9, 9, 9, 9, 9, 9), 4, 7, 128, 6, 95, 17, 33, 6616),
    "Kylin-256": (2**64, 32, 65, 8, (8, 8, 8, 8, 8, 8, 8, 9), 9, 8, 66, 5, 187, 16, 66, 26440),
    "Kylin-512": (2**64, 64, 64, 8, (8, 8, 8, 8, 8, 8, 8, 8), 14, 8, 256, 5, 415, 43, 96, 84360),
    "Kylin-128-q24": (2**24, 16, 22, 1, (22,), 2, 12, 864, 7, 90, 6, 52, 2872),
    "Kylin-256-q24": (2**24, 32, 21, 1, (21,), 3, 14, 3072, 8, 202, 6, 102, 11208),
    "Kylin-512-q24": (2**24, 64, 41, 2, (20, 21), 7, 15, 224, 10, 336, 12, 145, 47240),
}


def parse_q(text: str) -> int:
    base, exp = text.split("^")
    if base != "2":
        raise ValueError(f"unsupported q label: {text}")
    return 1 << int(exp)


def parse_h_vec(text: str) -> tuple[int, ...]:
    return tuple(int(x) for x in text.strip("[]").split(",") if x)


def ceil_log2(x: int) -> int:
    return (x - 1).bit_length()


def child_cover_terms(t: int, k: int, B: int) -> tuple[list[mp.mpf], list[mp.mpf]]:
    p_bucket = mp.mpf(2) ** (-B)
    denom = mp.mpf(comb(t, k))
    coeffs: list[mp.mpf] = []
    bases: list[mp.mpf] = []
    for i in range(k + 1):
        ratio = mp.mpf(comb(t - i, k)) / denom if t - i >= k else mp.mpf(0)
        coeffs.append(mp.mpf((-1 if i % 2 else 1) * comb(k, i)))
        bases.append(1 - p_bucket + p_bucket * ratio)
    return coeffs, bases


def bpors_bitsec(q_sigs: int, n: int, h: int, K: int, B: int, t: int, k: int) -> mp.mpf:
    p_hit = mp.mpf(2) ** (-h)
    q = mp.mpf(q_sigs)
    prob = (1 - p_hit) ** q
    mass = mp.mpf(0)
    total = mp.mpf(2) ** (-(8 * n))
    coeffs, bases = child_cover_terms(t, k, B)
    powers = [mp.mpf(1) for _ in bases]

    for gamma in range(2000):
        p_child = mp.fsum(c * x for c, x in zip(coeffs, powers))
        if p_child < 0 and abs(p_child) < mp.mpf("1e-100"):
            p_child = mp.mpf(0)
        total += prob * (p_child**K)
        mass += prob
        if gamma > 500 and 1 - mass < mp.mpf("1e-90"):
            break
        next_gamma = gamma + 1
        prob *= ((q - gamma) / next_gamma) * (p_hit / (1 - p_hit))
        for i, base in enumerate(bases):
            powers[i] *= base

    return -mp.log(total, 2)


def signature_bytes(row: dict[str, str]) -> int:
    n = int(row["n"])
    h = int(row["h"])
    d = int(row["d"])
    K = int(row["bpors_K"])
    k = int(row["bpors_k"])
    mmax = int(row["bpors_mmax"])
    length = int(row["len"])
    return n + CTR_BYTES + (K * k + mmax) * n + (h + d * length) * n


def bounded_draw_factor(bound: int) -> float:
    range32 = 1 << 32
    limit = range32 - (range32 % bound)
    return range32 / limit


def expected_distinct_draws(t: int, k: int) -> float:
    return sum(t / (t - i) for i in range(k))


def sampler_blocks(words: float) -> int:
    return max(1, math.ceil(words / BPORS_SAMPLER_BUF_U32))


def bpors_index_sampler_blocks(K: int, t: int, k: int) -> int:
    words = K * expected_distinct_draws(t, k) * bounded_draw_factor(t)
    return sampler_blocks(words)


def bpors_bucket_sampler_blocks(K: int) -> int:
    return sampler_blocks(K)


def bpors_sign_base(K: int, B: int, t: int) -> int:
    return K * (1 << B) * (3 * t - 1) + K * ((1 << B) - 1)


def sign_ht_hashcalls(h_vec: tuple[int, ...], w: int, length: int) -> int:
    return sum((1 << h_i) * (length * w + 1) for h_i in h_vec)


def verify_chain_steps(length: int, w: int) -> int:
    total = length * (w - 1)
    return total - (total // 2)


def verify_ht_hashcalls(h: int, d: int, w: int, length: int) -> int:
    return d * (verify_chain_steps(length, w) + 1) + h


def bpors_sign_hashcalls(row: dict[str, str]) -> int:
    K = int(row["bpors_K"])
    B = int(row["bpors_B"])
    t = int(row["bpors_t"])
    k = int(row["bpors_k"])
    tau = float(row["tau"])
    h_vec = parse_h_vec(row["h_profile"])
    ht_sign = sign_ht_hashcalls(h_vec, int(row["w"]), int(row["len"]))
    trial_cost = bpors_index_sampler_blocks(K, t, k)
    success_cost = bpors_bucket_sampler_blocks(K)
    return ht_sign + bpors_sign_base(K, B, t) + success_cost + math.ceil(trial_cost / tau)


def bpors_verify_hashcalls(row: dict[str, str]) -> int:
    K = int(row["bpors_K"])
    B = int(row["bpors_B"])
    t = int(row["bpors_t"])
    k = int(row["bpors_k"])
    h = int(row["h"])
    d = int(row["d"])
    ht_verify = verify_ht_hashcalls(h, d, int(row["w"]), int(row["len"]))
    sampler_cost = bpors_index_sampler_blocks(K, t, k) + bpors_bucket_sampler_blocks(K)
    return ht_verify + 2 * K * k + int(row["bpors_mmax"]) + sampler_cost


def verify_row(row: dict[str, str]) -> None:
    name = row["name"]
    h_vec = parse_h_vec(row["h_profile"])
    got = (
        parse_q(row["q"]),
        int(row["n"]),
        int(row["h"]),
        int(row["d"]),
        h_vec,
        int(row["bpors_K"]),
        int(row["bpors_B"]),
        int(row["bpors_t"]),
        int(row["bpors_k"]),
        int(row["bpors_mmax"]),
        int(row["w"]),
        int(row["len"]),
        int(row["sig"]),
    )
    if got != EXPECTED[name]:
        raise AssertionError(f"parameter drift for {name}: {got}")
    if sum(h_vec) != int(row["h"]) or len(h_vec) != int(row["d"]):
        raise AssertionError(f"invalid layer-height profile for {name}")
    if int(row["bpors_child_height"]) != ceil_log2(int(row["bpors_t"])):
        raise AssertionError(f"child-height mismatch for {name}")
    if signature_bytes(row) != int(row["sig"]):
        raise AssertionError(f"signature-size mismatch for {name}")
    if bpors_sign_hashcalls(row) != int(row["sign_hashcalls"]):
        raise AssertionError(f"sign hash-call mismatch for {name}")
    if bpors_verify_hashcalls(row) != int(row["verify_hashcalls"]):
        raise AssertionError(f"verify hash-call mismatch for {name}")

    bitsec = bpors_bitsec(
        parse_q(row["q"]),
        int(row["n"]),
        int(row["h"]),
        int(row["bpors_K"]),
        int(row["bpors_B"]),
        int(row["bpors_t"]),
        int(row["bpors_k"]),
    )
    if bitsec + SECURITY_TOLERANCE < mp.mpf(row["target_bits"]):
        raise AssertionError(f"BPORS cover estimate below target for {name}")


def main() -> None:
    seen: set[str] = set()
    with CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            verify_row(row)
            seen.add(row["name"])
            print(
                f"{row['name']}: q={row['q']}, n={row['n']}, h={row['h']}, d={row['d']}, "
                f"h_vec={row['h_profile']}, BPORS=({row['bpors_K']},{row['bpors_B']},"
                f"{row['bpors_t']},{row['bpors_k']},{row['bpors_mmax']}), "
                f"w={row['w']}, len={row['len']}, bitsec={row['bitsec']}, sig={row['sig']}, "
                f"sign={row['sign_hashcalls']}, verify={row['verify_hashcalls']}"
            )
    if seen != set(EXPECTED):
        raise AssertionError(f"profile set mismatch: {sorted(seen)}")


if __name__ == "__main__":
    main()
