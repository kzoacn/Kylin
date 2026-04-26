#!/usr/bin/env python3
"""Reference parameter-evaluation script with per-layer HT heights h_vec.

This appendix script mirrors the frozen NGCC parameter set used by the current
repository package:
  - q = 2^64 signatures per key pair
  - each family has its own fixed tuple (h, d, h_vec, a, k, w, len)
  - digest split uses h_0 (lowest layer)
  - HT signing proxy uses sum_i 2^{h_i}
"""

from __future__ import annotations

from functools import lru_cache

import mpmath as mp

mp.mp.dps = 80

Q_SIGS = 2**64
MAX_LAYER_HEIGHT = 32

FAMILIES = (
    {
        "name": "Kylin-128",
        "n": 16,
        "target_classical": 128,
        "ngcc_quantum": 80,
        "h": 65,
        "d": 9,
        "h_vec": (7, 7, 7, 7, 7, 7, 7, 8, 8),
        "a": 13,
        "k": 11,
        "w": 73,
        "len": 22,
    },
    {
        "name": "Kylin-256",
        "n": 32,
        "target_classical": 256,
        "ngcc_quantum": 128,
        "h": 68,
        "d": 10,
        "h_vec": (6, 6, 7, 7, 7, 7, 7, 7, 7, 7),
        "a": 13,
        "k": 22,
        "w": 54,
        "len": 46,
    },
    {
        "name": "Kylin-512",
        "n": 64,
        "target_classical": 512,
        "ngcc_quantum": 256,
        "h": 70,
        "d": 4,
        "h_vec": (17, 17, 18, 18),
        "a": 20,
        "k": 27,
        "w": 64,
        "len": 87,
    },
)


def balanced_profile(h: int, d: int) -> tuple[int, ...]:
    base = h // d
    rem = h % d
    return tuple(base + (1 if i < rem else 0) for i in range(d))


def shift_height(profile: tuple[int, ...], src: int, dst: int, amount: int) -> tuple[int, ...] | None:
    if amount <= 0:
        return profile
    if src == dst:
        return profile
    p = list(profile)
    if p[src] - amount < 1:
        return None
    p[src] -= amount
    p[dst] += amount
    return tuple(p)


def profile_ok(h: int, h_vec: tuple[int, ...]) -> bool:
    if not h_vec:
        return False
    if any(v < 1 for v in h_vec):
        return False
    if sum(h_vec) != h:
        return False
    if max(h_vec) > MAX_LAYER_HEIGHT:
        return False
    # tree_idx fits in 64 bits for the current implementation split.
    if h - h_vec[0] > 64:
        return False
    return True


def generate_profiles(h: int, d: int) -> list[tuple[int, ...]]:
    core = balanced_profile(h, d)
    profiles: set[tuple[int, ...]] = {core}

    top = d - 1
    mid = d // 2
    for candidate in (
        shift_height(core, top, 0, 1),
        shift_height(core, top, 0, 2),
        shift_height(core, 0, top, 1),
        shift_height(core, 0, top, 2),
        shift_height(core, mid, 0, 1),
        shift_height(core, mid, top, 1),
        shift_height(core, top, mid, 1),
        shift_height(core, 0, mid, 1),
    ):
        if candidate is not None and profile_ok(h, candidate):
            profiles.add(candidate)

    return sorted(profiles)


@lru_cache(maxsize=None)
def const_sum_count(length: int, w: int) -> int:
    total = length * (w - 1) // 2
    dp = [0] * (total + 1)
    dp[0] = 1
    for _ in range(length):
        nxt = [0] * (total + 1)
        window = 0
        for idx in range(total + 1):
            window += dp[idx]
            if idx - w >= 0:
                window -= dp[idx - w]
            nxt[idx] = window
        dp = nxt
    return dp[total]


@lru_cache(maxsize=None)
def wotscs_length(message_bits: int, w: int) -> int:
    for length in range(2, 700):
        if mp.log(const_sum_count(length, w), 2) > message_bits:
            return length
    raise RuntimeError(f"failed to find WOTSCS length for {message_bits=} {w=}")


@lru_cache(maxsize=None)
def qhit_distribution(h: int, limit: int = 220) -> tuple[mp.mpf, ...]:
    p = mp.mpf(2) ** (-h)
    q = mp.mpf(Q_SIGS)
    cur = mp.e ** (q * mp.log1p(-p))
    probs = [cur]
    for r in range(limit):
        cur *= ((q - r) / (r + 1)) * (p / (1 - p))
        probs.append(cur)
    return tuple(probs)


@lru_cache(maxsize=None)
def classical_security(n: int, h: int, a: int, k: int) -> mp.mpf:
    total = mp.mpf(2) ** (-8 * n)
    tree_size = mp.mpf(2) ** a
    for r, qprob in enumerate(qhit_distribution(h)):
        total += qprob * (1 - (1 - 1 / tree_size) ** r) ** k
    return -mp.log(total, 2)


def minimal_k(target_bits: int, n: int, h: int, a: int) -> int:
    upper = 240 if target_bits < 512 else 420
    lower = 10 if target_bits < 512 else 30
    if classical_security(n, h, a, upper) < target_bits:
        raise RuntimeError(f"no feasible k found for n={n}, h={h}, a={a}")

    lo, hi = lower, upper
    while lo < hi:
        mid = (lo + hi) // 2
        if classical_security(n, h, a, mid) >= target_bits:
            hi = mid
        else:
            lo = mid + 1
    return lo


def signature_bytes(n: int, h: int, d: int, a: int, k: int, length: int) -> int:
    return ((a + 1) * k + h + length * d + 1) * n


def hash_calls(h_vec: tuple[int, ...], a: int, k: int, w: int, length: int) -> int:
    return k * (2 ** (a + 1)) + sum((2**layer_h) * (length * w + 1) for layer_h in h_vec)


def digest_bytes(k: int, a: int, h: int, h0: int) -> int:
    tree_bits = h - h0
    return ((k * a + 7) // 8) + ((tree_bits + 7) // 8) + ((h0 + 7) // 8)


def choose_profile(h: int, d: int, a: int, k: int, w: int, length: int) -> tuple[int, ...]:
    profiles = generate_profiles(h, d)
    return min(profiles, key=lambda vec: (hash_calls(vec, a, k, w, length), vec))


def evaluate_family(family: dict[str, int | str | tuple[int, ...]]) -> dict[str, int | float | str]:
    h = int(family["h"])
    d = int(family["d"])
    h_vec = tuple(int(x) for x in family["h_vec"])  # type: ignore[arg-type]
    n = int(family["n"])
    a = int(family["a"])
    k = int(family["k"])
    w = int(family["w"])
    length = int(family["len"])

    return {
        "name": str(family["name"]),
        "n": n,
        "h": h,
        "d": d,
        "h_vec": h_vec,
        "h0": h_vec[0],
        "a": a,
        "k": k,
        "w": w,
        "len": length,
        "classical": float(classical_security(n, h, a, k)),
        "quantum_formula": float(classical_security(n, h, a, k) / 2),
        "ngcc_quantum": int(family["ngcc_quantum"]),
        "pk": 2 * n,
        "sk": 4 * n,
        "sig": signature_bytes(n, h, d, a, k, length),
        "digest_bytes": digest_bytes(k, a, h, h_vec[0]),
        "hashcalls": hash_calls(h_vec, a, k, w, length),
    }


def verify_frozen_parameters(rows: list[dict[str, int | float | str]]) -> None:
    expected: dict[str, tuple[int, int, tuple[int, ...], int, int, int, int]] = {
        "Kylin-128": (65, 9, (7, 7, 7, 7, 7, 7, 7, 8, 8), 13, 11, 73, 22),
        "Kylin-256": (68, 10, (6, 6, 7, 7, 7, 7, 7, 7, 7, 7), 13, 22, 54, 46),
        "Kylin-512": (66, 11, (6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6), 13, 49, 97, 79),
    }
    for row in rows:
        name = str(row["name"])
        if name not in expected:
            raise AssertionError(f"unexpected family: {name}")

        exp_h, exp_d, exp_h_vec, exp_a, exp_k, exp_w, exp_len = expected[name]
        h = int(row["h"])
        d = int(row["d"])
        length = int(row["len"])
        a = int(row["a"])
        k = int(row["k"])
        w = int(row["w"])
        h_vec = tuple(row["h_vec"])  # type: ignore[arg-type]

        if (h, d, h_vec, a, k, w, length) != (exp_h, exp_d, exp_h_vec, exp_a, exp_k, exp_w, exp_len):
            raise AssertionError(f"parameter drift for {name}: {(h, d, h_vec, a, k, w, length)}")

        recomputed_hashcalls = hash_calls(h_vec, a, k, w, length)
        if int(row["hashcalls"]) != recomputed_hashcalls:
            raise AssertionError(f"hashcalls mismatch for {row['name']}")


def main() -> None:
    rows = [evaluate_family(family) for family in FAMILIES]
    verify_frozen_parameters(rows)

    for row in rows:
        print(
            f"{row['name']}: h={row['h']}, d={row['d']}, h_vec={row['h_vec']}, "
            f"a={row['a']}, k={row['k']}, w={row['w']}, len={row['len']}, "
            f"classical={row['classical']:.1f}, ngcc_quantum={row['ngcc_quantum']}, "
            f"formula_quantum={row['quantum_formula']:.1f}, "
            f"pk={row['pk']}, sk={row['sk']}, sig={row['sig']}, "
            f"digest_bytes={row['digest_bytes']}, hashcalls={row['hashcalls']}"
        )


if __name__ == "__main__":
    main()
