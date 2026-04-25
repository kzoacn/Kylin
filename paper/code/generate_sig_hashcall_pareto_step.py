#!/usr/bin/env python3
"""Generate per-family SIG-hashcall Pareto-step frontier charts and CSVs."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from paper.code import search_ngcc_params as s


@dataclass(frozen=True)
class FrontierPoint:
    family: str
    sig: int
    hashcalls: int
    h: int
    d: int
    h_vec: tuple[int, ...]
    h0: int
    a: int
    k: int
    w: int
    length: int
    classical_bitsec: float


def pareto_frontier(points_sorted_by_sig: list[FrontierPoint]) -> list[FrontierPoint]:
    frontier: list[FrontierPoint] = []
    best_hashcalls = float("inf")
    for point in points_sorted_by_sig:
        if point.hashcalls < best_hashcalls:
            frontier.append(point)
            best_hashcalls = point.hashcalls
    return frontier


def build_family_frontier(family: s.Family) -> tuple[list[FrontierPoint], dict[str, int]]:
    best_by_sig: dict[int, FrontierPoint] = {}
    total_candidates = 0

    for h in s.H_CHOICES:
        for a in s.A_CHOICES:
            k = s.minimal_k(family, h, a)
            if k is None:
                continue
            classical = float(s.classical_bit_security(family.n, h, a, k))
            for w in s.W_CHOICES:
                length = s.wotscs_length(8 * family.n, w)
                for d in s.layer_count_choices(h):
                    for h_vec in s.generate_layer_profiles(h, d):
                        total_candidates += 1
                        point = FrontierPoint(
                            family=family.name,
                            sig=s.signature_bytes(family.n, h, d, a, k, length),
                            hashcalls=s.hash_calls(h_vec, a, k, w, length),
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
                        old = best_by_sig.get(point.sig)
                        if old is None:
                            best_by_sig[point.sig] = point
                            continue
                        if (
                            point.hashcalls,
                            point.h,
                            point.d,
                            point.a,
                            point.k,
                            point.w,
                            point.length,
                            point.h_vec,
                        ) < (
                            old.hashcalls,
                            old.h,
                            old.d,
                            old.a,
                            old.k,
                            old.w,
                            old.length,
                            old.h_vec,
                        ):
                            best_by_sig[point.sig] = point

    sorted_points = [best_by_sig[k] for k in sorted(best_by_sig)]
    frontier = pareto_frontier(sorted_points)
    stats = {
        "candidates": total_candidates,
        "unique_sig": len(sorted_points),
        "frontier_points": len(frontier),
        "min_sig": min(p.sig for p in frontier),
        "max_sig": max(p.sig for p in frontier),
    }
    return frontier, stats


def write_frontier_csv(path: Path, points: list[FrontierPoint]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "family",
        "sig",
        "hashcalls",
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
                    "hashcalls": p.hashcalls,
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


def draw_step_plot(path_png: Path, path_svg: Path, family: str, points: list[FrontierPoint], color: str) -> None:
    xs = [p.sig for p in points]
    ys = [p.hashcalls for p in points]

    plt.figure(figsize=(8, 5), dpi=180)
    plt.step(xs, ys, where="post", color=color, linewidth=1.8)
    plt.scatter(xs, ys, color=color, s=16, zorder=3)
    plt.xlabel("Signature size (bytes)")
    plt.ylabel("Hash calls (proxy)")
    plt.title(f"Pareto Frontier (Step): SIG vs HashCalls ({family})")
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(path_png)
    plt.savefig(path_svg)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("paper/data"),
        help="Output directory for CSV/PNG/SVG files.",
    )
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    colors = {"Kylin-128": "#1f77b4", "Kylin-256": "#2ca02c", "Kylin-512": "#d62728"}

    for family in s.FAMILIES:
        frontier, stats = build_family_frontier(family)
        tag = family.name.lower().replace("-", "")
        csv_path = args.out_dir / f"sig_hashcall_pareto_step_{tag}.csv"
        png_path = args.out_dir / f"sig_hashcall_pareto_step_{tag}.png"
        svg_path = args.out_dir / f"sig_hashcall_pareto_step_{tag}.svg"

        write_frontier_csv(csv_path, frontier)
        draw_step_plot(png_path, svg_path, family.name, frontier, colors[family.name])

        print(
            f"{family.name}: candidates={stats['candidates']}, unique_sig={stats['unique_sig']}, "
            f"frontier_points={stats['frontier_points']}, min_sig={stats['min_sig']}"
        )
        print(f"  wrote {csv_path}")
        print(f"  wrote {png_path}")
        print(f"  wrote {svg_path}")


if __name__ == "__main__":
    main()

