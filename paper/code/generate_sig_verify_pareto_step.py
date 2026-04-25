#!/usr/bin/env python3
"""Search Kylin parameters and draw Pareto frontier for SIG vs verify-hashcalls.

This script is intentionally experiment-oriented:
- It can expand search ranges beyond the baseline script defaults.
- Objective is SIG size (x) vs verify hash calls (y).
- Sign-side hashcalls are kept only as a reference column.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mpmath as mp

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from paper.code import search_ngcc_params as s

mp.mp.dps = 80

Q_SIGS = 2**64


@dataclass(frozen=True)
class Point:
    family: str
    sig: int
    verify_hashcalls: int
    sign_hashcalls: int
    h: int
    d: int
    h_vec: tuple[int, ...]
    h0: int
    a: int
    k: int
    w: int
    length: int
    classical_bitsec: float


@dataclass(frozen=True)
class RangeCfg:
    h_values: tuple[int, ...]
    a_values: tuple[int, ...]
    w_values: tuple[int, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", default="Kylin-128", choices=[f.name for f in s.FAMILIES])
    parser.add_argument("--target-bitsec", type=float, default=127.5)
    parser.add_argument("--k-min", type=int, default=1)
    parser.add_argument("--k-max", type=int, default=420)

    parser.add_argument("--h-min", type=int, default=40)
    parser.add_argument("--h-max", type=int, default=80)
    parser.add_argument("--d-min", type=int, default=6)
    parser.add_argument("--d-max", type=int, default=24)
    parser.add_argument("--a-min", type=int, default=6)
    parser.add_argument("--a-max", type=int, default=24)
    parser.add_argument("--w-min", type=int, default=8)
    parser.add_argument("--w-max", type=int, default=160)

    parser.add_argument("--sig-threshold", type=int, default=4000)
    parser.add_argument("--plot-sig-max", type=int, default=18000)
    parser.add_argument("--plot-verify-max", type=int, default=3500000)

    parser.add_argument("--out-dir", type=Path, default=Path("paper/data"))
    parser.add_argument("--tag", default="wide")
    parser.add_argument(
        "--allow-low-h",
        action="store_true",
        help=(
            "Allow h < 60. Use with care: current bit-security routine is tuned for "
            "the submission-style range and low-h scans may overestimate security."
        ),
    )
    return parser.parse_args()


@lru_cache(maxsize=None)
def minimal_k_targeted(
    n: int,
    h: int,
    a: int,
    target_bits: float,
    k_min: int,
    k_max: int,
) -> int | None:
    if classical_bit_security_robust(n, h, a, k_max) < target_bits:
        return None

    lo = k_min
    hi = k_max
    while lo < hi:
        mid = (lo + hi) // 2
        if classical_bit_security_robust(n, h, a, mid) >= target_bits:
            hi = mid
        else:
            lo = mid + 1

    if classical_bit_security_robust(n, h, a, lo) >= target_bits:
        return lo
    return None


@lru_cache(maxsize=None)
def qhit_distribution_robust(h: int) -> tuple[mp.mpf, ...]:
    """Approximate Binomial(q=2^64, p=2^-h) distribution with wide dynamic support.

    The baseline script uses a fixed small truncation limit that is fine for h>=60.
    For lower h (e.g., h=54), lambda=q*p grows and needs a wider support.
    """
    p = mp.mpf(2) ** (-h)
    q = mp.mpf(Q_SIGS)
    lam = float(Q_SIGS * (2.0 ** (-h)))
    limit = max(220, int(math.ceil(lam + 20.0 * math.sqrt(max(lam, 1e-12)) + 80.0)))

    cur = mp.e ** (q * mp.log1p(-p))
    probs = [cur]
    for r in range(limit):
        cur *= ((q - r) / (r + 1)) * (p / (1 - p))
        probs.append(cur)
    return tuple(probs)


@lru_cache(maxsize=None)
def classical_bit_security_robust(n: int, h: int, a: int, k: int) -> mp.mpf:
    total = mp.mpf(2) ** (-8 * n)
    tree_size = mp.mpf(2) ** a
    for r, qprob in enumerate(qhit_distribution_robust(h)):
        total += qprob * (1 - (1 - 1 / tree_size) ** r) ** k
    return -mp.log(total, 2)


def wots_verify_chain_steps(length: int, w: int) -> int:
    # Constant-sum encoding fixes sum(msg[i]) = floor(len*(w-1)/2), hence
    # total verification chain steps = len*(w-1) - floor(len*(w-1)/2).
    total = length * (w - 1)
    return total - (total // 2)


def verify_hash_calls(h: int, d: int, a: int, k: int, w: int, length: int) -> int:
    # Proxy using thash-equivalent calls from verification flow:
    # - FORS pkFromSig: k*(a+1) + 1
    # - HT verify: per layer [wots_pk_from_sig steps + 1 (WOTS pk compression)] + auth path
    #            = d*(ceil(len*(w-1)/2) + 1) + h
    fors_part = k * (a + 1) + 1
    ht_part = d * (wots_verify_chain_steps(length, w) + 1) + h
    return fors_part + ht_part


def pareto_frontier(points_sorted_by_sig: list[Point]) -> list[Point]:
    frontier: list[Point] = []
    best_verify = float("inf")
    for p in points_sorted_by_sig:
        if p.verify_hashcalls < best_verify:
            frontier.append(p)
            best_verify = p.verify_hashcalls
    return frontier


def build_frontier(
    family: s.Family,
    cfg: RangeCfg,
    target_bits: float,
    k_min: int,
    k_max: int,
    d_min: int,
    d_max: int,
) -> tuple[list[Point], list[Point], dict[str, int]]:
    best_by_sig: dict[int, Point] = {}
    all_points: list[Point] = []
    total_candidates = 0

    for h in cfg.h_values:
        for a in cfg.a_values:
            k = minimal_k_targeted(family.n, h, a, target_bits, k_min, k_max)
            if k is None:
                continue
            classical = float(classical_bit_security_robust(family.n, h, a, k))

            for w in cfg.w_values:
                length = s.wotscs_length(8 * family.n, w)
                for d in range(max(1, d_min), min(d_max, h) + 1):
                    profiles = s.generate_layer_profiles(h, d)
                    if not profiles:
                        continue

                    # For SIG/verify-hashcall objectives, h_vec choice does not change
                    # x/y values, so we only keep one valid profile to reduce runtime.
                    h_vec = profiles[0]

                    p = Point(
                        family=family.name,
                        sig=s.signature_bytes(family.n, h, d, a, k, length),
                        verify_hashcalls=verify_hash_calls(h, d, a, k, w, length),
                        sign_hashcalls=s.hash_calls(h_vec, a, k, w, length),
                        h=h,
                        d=d,
                        h_vec=tuple(h_vec),
                        h0=h_vec[0],
                        a=a,
                        k=k,
                        w=w,
                        length=length,
                        classical_bitsec=classical,
                    )
                    total_candidates += 1
                    all_points.append(p)

                    old = best_by_sig.get(p.sig)
                    if old is None or (
                        p.verify_hashcalls,
                        p.h,
                        p.d,
                        p.a,
                        p.k,
                        p.w,
                        p.length,
                        p.h_vec,
                    ) < (
                        old.verify_hashcalls,
                        old.h,
                        old.d,
                        old.a,
                        old.k,
                        old.w,
                        old.length,
                        old.h_vec,
                    ):
                        best_by_sig[p.sig] = p

    sorted_points = [best_by_sig[k] for k in sorted(best_by_sig)]
    frontier = pareto_frontier(sorted_points)

    stats = {
        "candidates": total_candidates,
        "unique_sig": len(sorted_points),
        "frontier_points": len(frontier),
        "min_sig": min((p.sig for p in sorted_points), default=-1),
        "max_sig": max((p.sig for p in sorted_points), default=-1),
    }
    return frontier, all_points, stats


def write_csv(path: Path, points: list[Point]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "family",
        "sig",
        "verify_hashcalls",
        "sign_hashcalls",
        "h",
        "d",
        "h_vec",
        "h0",
        "a",
        "k",
        "w",
        "len",
        "classical_bitsec",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for p in points:
            writer.writerow(
                {
                    "family": p.family,
                    "sig": p.sig,
                    "verify_hashcalls": p.verify_hashcalls,
                    "sign_hashcalls": p.sign_hashcalls,
                    "h": p.h,
                    "d": p.d,
                    "h_vec": "[" + ",".join(str(v) for v in p.h_vec) + "]",
                    "h0": p.h0,
                    "a": p.a,
                    "k": p.k,
                    "w": p.w,
                    "len": p.length,
                    "classical_bitsec": f"{p.classical_bitsec:.6f}",
                }
            )


def draw_plot(
    path_png: Path,
    path_svg: Path,
    family: str,
    points: list[Point],
    target_bits: float,
    plot_sig_max: int,
    plot_verify_max: int,
) -> None:
    draw = [p for p in points if p.sig <= plot_sig_max and p.verify_hashcalls <= plot_verify_max]
    if not draw:
        draw = points

    xs = [p.sig for p in draw]
    ys = [p.verify_hashcalls for p in draw]

    plt.figure(figsize=(8, 5), dpi=180)
    plt.step(xs, ys, where="post", color="#1f77b4", linewidth=1.8)
    plt.scatter(xs, ys, color="#1f77b4", s=16, zorder=3)
    plt.xlabel("Signature size (bytes)")
    plt.ylabel("Verify hash calls (proxy)")
    plt.title(f"Pareto Frontier: SIG vs VerifyHashCalls ({family}, bitsec >= {target_bits})")
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(path_png)
    plt.savefig(path_svg)
    plt.close()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if args.h_min < 60 and not args.allow_low_h:
        raise SystemExit(
            "Refusing h < 60 by default because low-h security estimates can be unstable. "
            "Pass --allow-low-h only for exploratory scans."
        )

    fam = next(f for f in s.FAMILIES if f.name == args.family)
    family = s.Family(fam.name, fam.ngcc_classical, fam.ngcc_quantum, fam.n, args.target_bitsec)

    cfg = RangeCfg(
        h_values=tuple(range(args.h_min, args.h_max + 1)),
        a_values=tuple(range(args.a_min, args.a_max + 1)),
        w_values=tuple(range(args.w_min, args.w_max + 1)),
    )

    frontier, all_points, stats = build_frontier(
        family,
        cfg,
        args.target_bitsec,
        args.k_min,
        args.k_max,
        args.d_min,
        args.d_max,
    )

    tag = args.family.lower().replace("-", "") + f"_target{str(args.target_bitsec).replace('.', '')}_{args.tag}"
    csv_frontier = args.out_dir / f"sig_verify_pareto_step_{tag}.csv"
    png_plot = args.out_dir / f"sig_verify_pareto_step_{tag}.png"
    svg_plot = args.out_dir / f"sig_verify_pareto_step_{tag}.svg"
    csv_under = args.out_dir / f"sig_verify_candidates_siglt{args.sig_threshold}_{tag}.csv"

    write_csv(csv_frontier, frontier)

    under = [p for p in all_points if p.sig < args.sig_threshold]
    under.sort(key=lambda p: (p.sig, p.verify_hashcalls, p.h, p.d, p.a, p.k, p.w, p.length, p.h_vec))
    write_csv(csv_under, under)

    draw_plot(
        png_plot,
        svg_plot,
        family.name,
        frontier,
        args.target_bitsec,
        args.plot_sig_max,
        args.plot_verify_max,
    )

    best_sig = min((p.sig for p in all_points), default=-1)
    best_under = under[0] if under else None

    print(
        f"{family.name}: candidates={stats['candidates']}, unique_sig={stats['unique_sig']}, "
        f"frontier_points={stats['frontier_points']}, min_sig={stats['min_sig']}"
    )
    print(
        f"  search ranges: h=[{args.h_min},{args.h_max}], d=[{args.d_min},{args.d_max}], "
        f"a=[{args.a_min},{args.a_max}], w=[{args.w_min},{args.w_max}]"
    )
    print(f"  wrote {csv_frontier}")
    print(f"  wrote {png_plot}")
    print(f"  wrote {svg_plot}")
    print(f"  wrote {csv_under}")
    print(f"  global best sig in search: {best_sig}")
    if best_under is None:
        print(f"  no candidate with sig < {args.sig_threshold}")
    else:
        print(
            "  best under threshold: "
            f"sig={best_under.sig}, verify_hashcalls={best_under.verify_hashcalls}, "
            f"h={best_under.h}, d={best_under.d}, h_vec={best_under.h_vec}, "
            f"a={best_under.a}, k={best_under.k}, w={best_under.w}, len={best_under.length}, "
            f"classical={best_under.classical_bitsec:.6f}"
        )


if __name__ == "__main__":
    main()
