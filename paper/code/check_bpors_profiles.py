#!/usr/bin/env python3
"""Check BPORS+FP signature sizes and generic cover exponents.

This script reads paper/data/para_kylin_final_6profiles.csv and recomputes the
signature length and the conservative bucket-thinned BPORS cover estimate used
in the security section.  It is intentionally a checker for the frozen profiles,
not a broad parameter search.
"""

from __future__ import annotations

import csv
from math import comb
from pathlib import Path

import mpmath as mp

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "paper/data/para_kylin_final_6profiles.csv"

mp.mp.dps = 170


def parse_power_of_two(s: str) -> int:
    base, exp = s.split("^")
    if base != "2":
        raise ValueError(f"unsupported q format: {s}")
    return 1 << int(exp)


def child_cover_terms(t: int, k: int, b: int) -> tuple[list[mp.mpf], list[mp.mpf]]:
    p_bucket = mp.mpf(2) ** (-b)
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
    powers = [mp.mpf(1) for _ in coeffs]

    for gamma in range(2000):
        p_child = mp.fsum(c * x for c, x in zip(coeffs, powers))
        if p_child < 0 and abs(p_child) < mp.mpf("1e-120"):
            p_child = mp.mpf(0)
        total += prob * (p_child ** K)
        mass += prob
        if gamma > 500 and 1 - mass < mp.mpf("1e-100"):
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
    ctr = int(row["bpors_ctr_bytes"])
    wots_len = int(row["len"])
    return n + ctr + (K * k + mmax) * n + d * wots_len * n + h * n


def main() -> int:
    with CSV.open(newline="") as f:
        for row in csv.DictReader(f):
            got_sig = signature_bytes(row)
            want_sig = int(row["sig"])
            bitsec = bpors_bitsec(
                parse_power_of_two(row["q"]),
                int(row["n"]),
                int(row["h"]),
                int(row["bpors_K"]),
                int(row["bpors_B"]),
                int(row["bpors_t"]),
                int(row["bpors_k"]),
            )
            print(
                f"{row['name']}: sig={got_sig} "
                f"bitsec={mp.nstr(bitsec, 12)}"
            )
            if got_sig != want_sig:
                raise SystemExit(f"signature-size mismatch for {row['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
