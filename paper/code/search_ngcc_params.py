#!/usr/bin/env python3
"""Search and select NGCC-aligned SPHINCS-alpha parameter families.

The original draft shipped a Sage script tuned to the legacy 128/192/256-bit
NIST-style families. This helper reproduces the same style of exact search in
plain Python and then selects one *common* `(h, d, a, w)` shape across the
three NGCC submission levels.

Selection model:
- tune the single-key security formulas with `q = 2^64` signatures, matching
  the explicit NGCC requirement that one key pair support at least `2^64`
  signed messages;
- map the NGCC 128/80 family to an effective 160-bit classical floor using the
  draft's current generic quantum formula `b_q = b_c / 2`;
- keep a common hypertree/FORS/WOTS shape when possible to simplify the
  specification and implementation;
- among all common shapes, minimize the sum of the per-family balance scores,
  where the balance score measures how far a candidate sits from the
  size/speed minima on that family's Pareto frontier.
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import mpmath as mp

mp.mp.dps = 80

Q_SIGS = 2**64
W_CHOICES = (16, 32, 64)
H_CHOICES = tuple(range(64, 97))
A_CHOICES = tuple(range(8, 17))
SPEED_FACTOR = 32


@dataclass(frozen=True)
class Family:
    name: str
    ngcc_classical: int
    ngcc_quantum: int
    n: int
    target_bits: int


@dataclass(frozen=True)
class Candidate:
    family: Family
    h: int
    d: int
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
    def subtree_height(self) -> int:
        return self.h // self.d

    @property
    def shape(self) -> tuple[int, int, int, int]:
        return (self.h, self.d, self.a, self.w)


FAMILIES = (
    Family("sphincs-a-ngcc-128", 128, 80, 20, 160),
    Family("sphincs-a-ngcc-256", 256, 128, 32, 256),
    Family("sphincs-a-ngcc-512", 512, 256, 64, 512),
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


def divisors(value: int) -> list[int]:
    return [d for d in range(6, value) if value % d == 0]


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


def hash_calls(h: int, d: int, a: int, k: int, w: int, length: int) -> int:
    return k * (2 ** (a + 1)) + d * ((2 ** (h // d)) * (length * w + 1))


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


def enumerate_candidates(family: Family) -> list[Candidate]:
    candidates: list[Candidate] = []
    for h in H_CHOICES:
        ds = divisors(h)
        if not ds:
            continue
        for a in A_CHOICES:
            k = minimal_k(family, h, a)
            if k is None:
                continue
            classical = float(classical_bit_security(family.n, h, a, k))
            quantum = float(quantum_bit_security(family.n, h, a, k))
            for w in W_CHOICES:
                length = wotscs_length(8 * family.n, w)
                for d in ds:
                    candidates.append(
                        Candidate(
                            family=family,
                            h=h,
                            d=d,
                            a=a,
                            k=k,
                            w=w,
                            length=length,
                            classical_bitsec=classical,
                            quantum_bitsec=quantum,
                            sig_bytes=signature_bytes(family.n, h, d, a, k, length),
                            hash_calls=hash_calls(h, d, a, k, w, length),
                        )
                    )
    return candidates


def pareto_frontier(candidates: list[Candidate]) -> list[Candidate]:
    frontier: list[Candidate] = []
    best_speed = math.inf
    for candidate in sorted(candidates, key=lambda c: (c.sig_bytes, c.hash_calls)):
        if candidate.hash_calls < best_speed:
            frontier.append(candidate)
            best_speed = candidate.hash_calls
    return frontier


def frontier_anchor(frontier: list[Candidate]) -> tuple[int, int]:
    return (
        min(candidate.sig_bytes for candidate in frontier),
        min(candidate.hash_calls for candidate in frontier),
    )


def balance_score(candidate: Candidate, min_sig: int, min_speed: int) -> float:
    return max(
        math.log(candidate.sig_bytes / min_sig, 2),
        math.log(candidate.hash_calls / min_speed, 2),
    )


def choose_common_shape(frontiers: dict[str, list[Candidate]]) -> tuple[tuple[int, int, int, int], dict[str, Candidate]]:
    by_family_shape: dict[str, dict[tuple[int, int, int, int], Candidate]] = {}
    anchors: dict[str, tuple[int, int]] = {}
    fastest_by_family: dict[str, int] = {}
    for family_name, frontier in frontiers.items():
        anchors[family_name] = frontier_anchor(frontier)
        fastest_by_family[family_name] = min(candidate.hash_calls for candidate in frontier)
        by_family_shape[family_name] = {candidate.shape: candidate for candidate in frontier}

    common_shapes = set.intersection(*(set(shapes.keys()) for shapes in by_family_shape.values()))
    best_shape: tuple[int, int, int, int] | None = None
    best_candidates: dict[str, Candidate] | None = None
    best_score: tuple[int, int, float, float] | None = None

    for shape in sorted(common_shapes):
        chosen = {family_name: by_family_shape[family_name][shape] for family_name in by_family_shape}
        if any(
            candidate.hash_calls > fastest_by_family[family_name] * SPEED_FACTOR
            for family_name, candidate in chosen.items()
        ):
            continue
        scores = []
        total_sig = 0
        total_speed = 0
        for family_name, candidate in chosen.items():
            min_sig, min_speed = anchors[family_name]
            scores.append(balance_score(candidate, min_sig, min_speed))
            total_sig += candidate.sig_bytes
            total_speed += candidate.hash_calls
        objective = (total_sig, total_speed, sum(scores), max(scores))
        if best_score is None or objective < best_score:
            best_score = objective
            best_shape = shape
            best_candidates = chosen

    if best_shape is None or best_candidates is None:
        raise RuntimeError(
            f"failed to find a common NGCC parameter shape within the {SPEED_FACTOR}x speed cap"
        )

    return best_shape, best_candidates


def write_csv(candidates: dict[str, Candidate], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "ngccclassical",
        "ngccquantum",
        "n",
        "h",
        "d",
        "a",
        "k",
        "w",
        "len",
        "subtree",
        "classical",
        "quantum",
        "pk",
        "sk",
        "sig",
        "hashcalls",
        "q",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for family_name in sorted(candidates):
            candidate = candidates[family_name]
            writer.writerow(
                {
                    "name": candidate.family.name,
                    "ngccclassical": candidate.family.ngcc_classical,
                    "ngccquantum": candidate.family.ngcc_quantum,
                    "n": candidate.family.n,
                    "h": candidate.h,
                    "d": candidate.d,
                    "a": candidate.a,
                    "k": candidate.k,
                    "w": candidate.w,
                    "len": candidate.length,
                    "subtree": candidate.subtree_height,
                    "classical": f"{candidate.classical_bitsec:.1f}",
                    "quantum": f"{candidate.quantum_bitsec:.1f}",
                    "pk": candidate.pk_bytes,
                    "sk": candidate.sk_bytes,
                    "sig": candidate.sig_bytes,
                    "hashcalls": candidate.hash_calls,
                    "q": f"2^{int(math.log2(Q_SIGS))}",
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-csv",
        type=Path,
        help="Write the selected parameter rows to a CSV file.",
    )
    args = parser.parse_args()

    frontiers: dict[str, list[Candidate]] = {}
    for family in FAMILIES:
        frontiers[family.name] = pareto_frontier(enumerate_candidates(family))

    shape, chosen = choose_common_shape(frontiers)

    print("Selected common shape (h, d, a, w):", shape)
    for family_name in sorted(chosen):
        candidate = chosen[family_name]
        print(
            f"{candidate.family.name}: "
            f"n={candidate.family.n}, h={candidate.h}, d={candidate.d}, "
            f"a={candidate.a}, k={candidate.k}, w={candidate.w}, len={candidate.length}, "
            f"classical={candidate.classical_bitsec:.1f}, quantum={candidate.quantum_bitsec:.1f}, "
            f"pk={candidate.pk_bytes}, sk={candidate.sk_bytes}, sig={candidate.sig_bytes}, "
            f"hashcalls={candidate.hash_calls}"
        )

    if args.write_csv:
        write_csv(chosen, args.write_csv)
        print(f"Wrote {args.write_csv}")


if __name__ == "__main__":
    main()
