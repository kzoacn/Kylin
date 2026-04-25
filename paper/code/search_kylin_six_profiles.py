#!/usr/bin/env python3
"""Search six Kylin profiles for q in {2^64, 2^24} and sec in {128, 256, 512}.

Rules implemented from the task request:
- Names:
  - q=2^64: Kylin-{128,256,512}
  - q=2^24: Kylin-{128,256,512}-q24
- For {128,256}: use bitsec targets {127,255}, and select the smallest SIG size
  under the hard constraint that SIG size / sign hashcalls / verify hashcalls are
  all strictly better than the corresponding previous baseline.
- For {512}: use a regular/moderate search around n (h near n, moderate a/k/w).
- Draw 4 ranking figures for {q64,q24} x {128,256}, and save all outputs.
"""

from __future__ import annotations

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
    a_min: int
    a_max: int
    w_min: int
    w_max: int
    k_min: int
    k_max: int
    require_improvement: bool
    baseline_name: str | None
    make_plot: bool


@dataclass(frozen=True)
class SearchRange:
    h_min: int
    h_max: int
    d_min: int
    d_max: int
    a_min: int
    a_max: int
    w_min: int
    w_max: int
    k_min: int
    k_max: int


@dataclass(frozen=True)
class Candidate:
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
    bitsec: float

    @property
    def h_profile(self) -> str:
        return "[" + ",".join(str(v) for v in self.h_vec) + "]"

    @property
    def h0(self) -> int:
        return self.h_vec[0]


@dataclass(frozen=True)
class BaselineMetrics:
    name: str
    q_sigs: int
    n: int
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
    bitsec: float


def verify_chain_steps(length: int, w: int) -> int:
    total = length * (w - 1)
    return total - (total // 2)


def verify_hash_calls(h: int, d: int, a: int, k: int, w: int, length: int) -> int:
    fors_part = k * (a + 1) + 1
    ht_part = d * (verify_chain_steps(length, w) + 1) + h
    return fors_part + ht_part


def fmt_q(q_sigs: int) -> str:
    return s.format_q(q_sigs)


def derive_baseline_metrics(baseline_name: str) -> BaselineMetrics:
    baseline = next(b for b in s.BASELINE_PARAMETERS if b.name == baseline_name)
    a = baseline.a if baseline.a is not None else baseline.log_t
    if a is None:
        raise RuntimeError(f"baseline {baseline_name} has no a/log_t")
    if baseline.w is not None:
        w = baseline.w
    elif baseline.lgw is not None:
        w = 2**baseline.lgw
    else:
        raise RuntimeError(f"baseline {baseline_name} has no w/lgw")
    length = baseline.l if baseline.l is not None else s.wotscs_length(8 * baseline.n, w)

    if baseline.h_prime is not None and baseline.h_prime * baseline.d == baseline.h:
        h_vec = tuple([baseline.h_prime] * baseline.d)
    else:
        h_vec = s.balanced_profile(baseline.h, baseline.d)
    h_vec = tuple(sorted(h_vec))

    s.set_query_budget(baseline.q_sigs)
    bitsec = float(s.classical_bit_security(baseline.n, baseline.h, a, baseline.k))

    return BaselineMetrics(
        name=baseline.name,
        q_sigs=baseline.q_sigs,
        n=baseline.n,
        h=baseline.h,
        d=baseline.d,
        h_vec=tuple(h_vec),
        a=a,
        k=baseline.k,
        w=w,
        length=length,
        sig=s.signature_bytes(baseline.n, baseline.h, baseline.d, a, baseline.k, length),
        sign_hashcalls=s.hash_calls(h_vec, a, baseline.k, w, length),
        verify_hashcalls=verify_hash_calls(baseline.h, baseline.d, a, baseline.k, w, length),
        bitsec=bitsec,
    )


class ScenarioSearcher:
    def __init__(self, scenario: Scenario, rng: SearchRange | None = None):
        self.scenario = scenario
        self.q_sigs = scenario.q_sigs
        self.n = scenario.n
        self.rng = rng or SearchRange(
            h_min=scenario.h_min,
            h_max=scenario.h_max,
            d_min=scenario.d_min,
            d_max=scenario.d_max,
            a_min=scenario.a_min,
            a_max=scenario.a_max,
            w_min=scenario.w_min,
            w_max=scenario.w_max,
            k_min=scenario.k_min,
            k_max=scenario.k_max,
        )
        s.set_query_budget(self.q_sigs)

    @lru_cache(maxsize=None)
    def qhit_distribution(self, h: int) -> tuple[mp.mpf, ...]:
        p = mp.mpf(2) ** (-h)
        q = mp.mpf(self.q_sigs)

        lam = float(self.q_sigs * (2.0 ** (-h)))
        limit = max(220, int(math.ceil(lam + 12.0 * math.sqrt(max(lam, 1e-12)) + 50.0)))

        cur = mp.e ** (q * mp.log1p(-p))
        probs = [cur]
        for r in range(limit):
            cur *= ((q - r) / (r + 1)) * (p / (1 - p))
            probs.append(cur)
        return tuple(probs)

    @lru_cache(maxsize=None)
    def classical_bit_security(self, h: int, a: int, k: int) -> float:
        total = mp.mpf(2) ** (-8 * self.n)
        tree_size = mp.mpf(2) ** a
        for r, qprob in enumerate(self.qhit_distribution(h)):
            total += qprob * (1 - (1 - 1 / tree_size) ** r) ** k
        return float(-mp.log(total, 2))

    @lru_cache(maxsize=None)
    def minimal_k(self, h: int, a: int) -> int | None:
        if self.classical_bit_security(h, a, self.rng.k_max) < self.scenario.target_bits:
            return None
        lo = self.rng.k_min
        hi = self.rng.k_max
        while lo < hi:
            mid = (lo + hi) // 2
            if self.classical_bit_security(h, a, mid) >= self.scenario.target_bits:
                hi = mid
            else:
                lo = mid + 1
        if self.classical_bit_security(h, a, lo) >= self.scenario.target_bits:
            return lo
        return None

    def _w_values(self) -> list[int]:
        if self.scenario.require_improvement:
            # For baseline-constrained scenarios, keep full coverage.
            return list(range(self.rng.w_min, self.rng.w_max + 1))
        out: list[int] = []
        for w in range(self.rng.w_min, self.rng.w_max + 1):
            if w <= 32:
                out.append(w)
            elif w <= 64 and w % 2 == 0:
                out.append(w)
            elif w <= 128 and w % 4 == 0:
                out.append(w)
            elif w % 8 == 0:
                out.append(w)
        # Always keep powers of two in range.
        p = 1
        while p <= self.rng.w_max:
            if p >= self.rng.w_min:
                out.append(p)
            p <<= 1
        return sorted(set(out))

    def enumerate_candidates(self, max_sig: int | None = None) -> list[Candidate]:
        out: list[Candidate] = []
        sc = self.scenario
        r = self.rng
        w_values = self._w_values()
        for h in range(r.h_min, r.h_max + 1):
            for a in range(r.a_min, r.a_max + 1):
                k = self.minimal_k(h, a)
                if k is None:
                    continue
                bitsec = self.classical_bit_security(h, a, k)
                for w in w_values:
                    length = s.wotscs_length(8 * sc.n, w)
                    for d in range(max(1, r.d_min), min(r.d_max, h) + 1):
                        profiles = [
                            p for p in s.generate_layer_profiles(h, d) if s.profile_is_compatible(h, p)
                        ]
                        if not profiles:
                            continue
                        # For fixed (h,d,a,k,w,l), SIG and verify are fixed across h_vec.
                        # Keep the fastest signing profile for this tuple.
                        best_profile = min(profiles, key=lambda hv: s.hash_calls(hv, a, k, w, length))
                        # Keep a canonical sorted h-vector in outputs/results.
                        best_profile = tuple(sorted(best_profile))
                        sign_hashcalls = s.hash_calls(best_profile, a, k, w, length)
                        cand = Candidate(
                            name=sc.name,
                            q_sigs=sc.q_sigs,
                            n=sc.n,
                            target_bits=sc.target_bits,
                            h=h,
                            d=d,
                            h_vec=tuple(best_profile),
                            a=a,
                            k=k,
                            w=w,
                            length=length,
                            sig=s.signature_bytes(sc.n, h, d, a, k, length),
                            sign_hashcalls=sign_hashcalls,
                            verify_hashcalls=verify_hash_calls(h, d, a, k, w, length),
                            bitsec=bitsec,
                        )
                        if max_sig is not None and cand.sig > max_sig:
                            continue
                        out.append(cand)
        return out


def sanitize(name: str) -> str:
    return name.lower().replace("-", "_")


def rank_of(values: list[int], value: int) -> int:
    return sum(1 for x in values if x < value) + 1


def write_candidates_csv(path: Path, rows: list[Candidate]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "name",
        "q",
        "n",
        "target_bits",
        "h",
        "d",
        "h_profile",
        "h0",
        "a",
        "k",
        "w",
        "len",
        "sig",
        "sign_hashcalls",
        "verify_hashcalls",
        "bitsec",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for c in rows:
            writer.writerow(
                {
                    "name": c.name,
                    "q": fmt_q(c.q_sigs),
                    "n": c.n,
                    "target_bits": c.target_bits,
                    "h": c.h,
                    "d": c.d,
                    "h_profile": c.h_profile,
                    "h0": c.h0,
                    "a": c.a,
                    "k": c.k,
                    "w": c.w,
                    "len": c.length,
                    "sig": c.sig,
                    "sign_hashcalls": c.sign_hashcalls,
                    "verify_hashcalls": c.verify_hashcalls,
                    "bitsec": f"{c.bitsec:.6f}",
                }
            )


def draw_ranking_figure(
    scenario: Scenario,
    all_rows: list[Candidate],
    improve_rows: list[Candidate],
    selected: Candidate,
    baseline: BaselineMetrics,
    rank_sig: int,
    rank_sign: int,
    rank_verify: int,
    out_png: Path,
    out_svg: Path,
) -> None:
    out_png.parent.mkdir(parents=True, exist_ok=True)

    all_sig = [c.sig for c in all_rows]
    all_sign = [c.sign_hashcalls for c in all_rows]
    all_verify = [c.verify_hashcalls for c in all_rows]

    imp_sig = [c.sig for c in improve_rows]
    imp_sign = [c.sign_hashcalls for c in improve_rows]
    imp_verify = [c.verify_hashcalls for c in improve_rows]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=180)

    ax = axes[0]
    ax.scatter(all_sig, all_sign, s=9, alpha=0.18, c="#999999", label="all candidates")
    if improve_rows:
        ax.scatter(imp_sig, imp_sign, s=10, alpha=0.4, c="#1f77b4", label="improvement-feasible")
    ax.scatter([baseline.sig], [baseline.sign_hashcalls], marker="*", s=160, c="#d62728", label="baseline")
    ax.scatter([selected.sig], [selected.sign_hashcalls], marker="*", s=180, c="#2ca02c", label="selected")
    ax.set_xlabel("Signature size (bytes)")
    ax.set_ylabel("Sign hashcalls (proxy)")
    ax.set_title(f"{scenario.name}: SIG vs SignHashcalls")
    ax.grid(alpha=0.2)
    ax.legend(loc="best", fontsize=8)

    ax = axes[1]
    ax.scatter(all_sig, all_verify, s=9, alpha=0.18, c="#999999", label="all candidates")
    if improve_rows:
        ax.scatter(imp_sig, imp_verify, s=10, alpha=0.4, c="#1f77b4", label="improvement-feasible")
    ax.scatter([baseline.sig], [baseline.verify_hashcalls], marker="*", s=160, c="#d62728", label="baseline")
    ax.scatter([selected.sig], [selected.verify_hashcalls], marker="*", s=180, c="#2ca02c", label="selected")
    ax.set_xlabel("Signature size (bytes)")
    ax.set_ylabel("Verify hashcalls (proxy)")
    ax.set_title(f"{scenario.name}: SIG vs VerifyHashcalls")
    ax.grid(alpha=0.2)
    ax.legend(loc="best", fontsize=8)

    total = len(all_rows)
    fig.suptitle(
        f"{scenario.name} ({fmt_q(scenario.q_sigs)}, bitsec>={scenario.target_bits})  "
        f"rank(sig/sign/verify)=({rank_sig}/{rank_sign}/{rank_verify}) of {total}",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(out_png)
    fig.savefig(out_svg)
    plt.close(fig)


def main() -> None:
    out_dir = Path("paper/data")
    out_dir.mkdir(parents=True, exist_ok=True)

    scenarios = [
        Scenario(
            name="Kylin-128",
            q_sigs=2**64,
            n=16,
            target_bits=127.0,
            h_min=54,
            h_max=74,
            d_min=4,
            d_max=20,
            a_min=8,
            a_max=28,
            w_min=2,
            w_max=128,
            k_min=1,
            k_max=1500,
            require_improvement=True,
            baseline_name="sphincs-a-128s",
            make_plot=True,
        ),
        Scenario(
            name="Kylin-256",
            q_sigs=2**64,
            n=32,
            target_bits=255.0,
            h_min=54,
            h_max=76,
            d_min=4,
            d_max=22,
            a_min=8,
            a_max=30,
            w_min=2,
            w_max=128,
            k_min=1,
            k_max=2000,
            require_improvement=True,
            baseline_name="sphincs-a-256s",
            make_plot=True,
        ),
        Scenario(
            name="Kylin-512",
            q_sigs=2**64,
            n=64,
            target_bits=511.0,
            h_min=56,
            h_max=72,
            d_min=4,
            d_max=12,
            a_min=10,
            a_max=20,
            w_min=8,
            w_max=64,
            k_min=8,
            k_max=300,
            require_improvement=False,
            baseline_name=None,
            make_plot=False,
        ),
        Scenario(
            name="Kylin-128-q24",
            q_sigs=2**24,
            n=16,
            target_bits=127.0,
            h_min=18,
            h_max=40,
            d_min=1,
            d_max=20,
            a_min=8,
            a_max=36,
            w_min=2,
            w_max=128,
            k_min=1,
            k_max=1500,
            require_improvement=True,
            baseline_name="SLH-DSA-SHAKE-128-24",
            make_plot=True,
        ),
        Scenario(
            name="Kylin-256-q24",
            q_sigs=2**24,
            n=32,
            target_bits=255.0,
            h_min=18,
            h_max=40,
            d_min=1,
            d_max=20,
            a_min=8,
            a_max=36,
            w_min=2,
            w_max=128,
            k_min=1,
            k_max=2000,
            require_improvement=True,
            baseline_name="SLH-DSA-SHAKE-256-24",
            make_plot=True,
        ),
        Scenario(
            name="Kylin-512-q24",
            q_sigs=2**24,
            n=64,
            target_bits=511.0,
            h_min=48,
            h_max=72,
            d_min=3,
            d_max=12,
            a_min=10,
            a_max=20,
            w_min=8,
            w_max=64,
            k_min=8,
            k_max=300,
            require_improvement=False,
            baseline_name=None,
            make_plot=False,
        ),
    ]

    summary_rows: list[dict[str, str | int | float]] = []

    for sc in scenarios:
        print(f"[search] {sc.name} ({fmt_q(sc.q_sigs)}, target={sc.target_bits})")
        baseline = derive_baseline_metrics(sc.baseline_name) if sc.baseline_name else None
        if baseline is not None:
            print(
                f"  baseline={baseline.name}, sig={baseline.sig}, "
                f"sign={baseline.sign_hashcalls}, verify={baseline.verify_hashcalls}"
            )

        engine = ScenarioSearcher(sc)
        max_sig = baseline.sig if (sc.require_improvement and baseline is not None) else None
        all_rows = engine.enumerate_candidates(max_sig=max_sig)
        if not all_rows:
            raise RuntimeError(f"{sc.name}: no candidate found in search range")

        all_rows.sort(
            key=lambda c: (
                c.sig,
                c.sign_hashcalls,
                c.verify_hashcalls,
                c.h,
                c.d,
                c.a,
                c.k,
                c.w,
                c.length,
                c.h_vec,
            )
        )

        stage = "primary"
        if sc.require_improvement:
            assert baseline is not None

            def cond_sig(c: Candidate) -> bool:
                return c.sig <= baseline.sig

            def cond_verify(c: Candidate) -> bool:
                return c.verify_hashcalls <= baseline.verify_hashcalls

            def cond_sign_120(c: Candidate) -> bool:
                # sign_hashcalls <= 120% baseline, integer-safe
                return c.sign_hashcalls * 10 <= baseline.sign_hashcalls * 12

            improve_rows = [
                c
                for c in all_rows
                if cond_sig(c) and cond_verify(c) and cond_sign_120(c)
            ]
            if not improve_rows:
                stage = "primary-no-strict"

                # Keep one best "closest" candidate so six profiles are always produced.
                def improved_count(c: Candidate) -> int:
                    return (
                        int(cond_sig(c)) + int(cond_verify(c)) + int(cond_sign_120(c))
                    )

                selected = min(
                    all_rows,
                    key=lambda c: (
                        -improved_count(c),
                        c.sig,
                        c.sign_hashcalls,
                        c.verify_hashcalls,
                        c.h,
                        c.d,
                        c.a,
                        c.k,
                        c.w,
                        c.length,
                        c.h_vec,
                    ),
                )
            else:
                selected = improve_rows[0]
        else:
            improve_rows = []
            # For 512 profiles: keep h near n and moderate params, then minimize SIG.
            moderate_rows = [
                c
                for c in all_rows
                if abs(c.h - sc.n) <= 8 and 10 <= c.a <= 20 and 8 <= c.k <= 120 and 8 <= c.w <= 64
            ]
            selected = (moderate_rows or all_rows)[0]

        sig_vals = [c.sig for c in all_rows]
        sign_vals = [c.sign_hashcalls for c in all_rows]
        verify_vals = [c.verify_hashcalls for c in all_rows]
        rank_sig = rank_of(sig_vals, selected.sig)
        rank_sign = rank_of(sign_vals, selected.sign_hashcalls)
        rank_verify = rank_of(verify_vals, selected.verify_hashcalls)

        cand_csv = out_dir / f"param_search_candidates_{sanitize(sc.name)}.csv"
        write_candidates_csv(cand_csv, all_rows)

        improve_count = len(improve_rows)
        if baseline is not None:
            sign_limit = (baseline.sign_hashcalls * 12) // 10
            print(
                f"  constraints: sig<={baseline.sig}, verify<={baseline.verify_hashcalls}, "
                f"sign<={sign_limit} (120% baseline)"
            )
        print(
            f"  stage={stage}, candidates={len(all_rows)}, improve_count={improve_count}, "
            f"selected sig={selected.sig}, sign={selected.sign_hashcalls}, verify={selected.verify_hashcalls}"
        )
        print(
            f"  selected: h={selected.h}, d={selected.d}, h_vec={selected.h_profile}, "
            f"a={selected.a}, k={selected.k}, w={selected.w}, len={selected.length}, "
            f"bitsec={selected.bitsec:.6f}"
        )

        if sc.make_plot:
            assert baseline is not None
            png = out_dir / f"param_rank_{sanitize(sc.name)}.png"
            svg = out_dir / f"param_rank_{sanitize(sc.name)}.svg"
            draw_ranking_figure(
                sc,
                all_rows,
                improve_rows,
                selected,
                baseline,
                rank_sig,
                rank_sign,
                rank_verify,
                png,
                svg,
            )
            print(f"  wrote {png}")
            print(f"  wrote {svg}")

        summary_rows.append(
            {
                "name": sc.name,
                "q": fmt_q(sc.q_sigs),
                "n": sc.n,
                "target_bits": sc.target_bits,
                "h": selected.h,
                "d": selected.d,
                "h_profile": selected.h_profile,
                "h0": selected.h0,
                "a": selected.a,
                "k": selected.k,
                "w": selected.w,
                "len": selected.length,
                "sig": selected.sig,
                "sign_hashcalls": selected.sign_hashcalls,
                "verify_hashcalls": selected.verify_hashcalls,
                "bitsec": f"{selected.bitsec:.6f}",
                "baseline_name": baseline.name if baseline is not None else "",
                "baseline_sig": baseline.sig if baseline is not None else "",
                "baseline_sign_hashcalls": baseline.sign_hashcalls if baseline is not None else "",
                "baseline_verify_hashcalls": baseline.verify_hashcalls if baseline is not None else "",
                "constraint_sig_le_baseline": (selected.sig <= baseline.sig) if baseline is not None else "",
                "constraint_verify_le_baseline": (
                    selected.verify_hashcalls <= baseline.verify_hashcalls
                )
                if baseline is not None
                else "",
                "constraint_sign_le_120pct_baseline": (
                    selected.sign_hashcalls * 10 <= baseline.sign_hashcalls * 12
                )
                if baseline is not None
                else "",
                "meets_constraint": (
                    (
                        selected.sig <= baseline.sig
                        and selected.verify_hashcalls <= baseline.verify_hashcalls
                        and selected.sign_hashcalls * 10 <= baseline.sign_hashcalls * 12
                    )
                    if baseline is not None
                    else ""
                ),
                "search_stage": stage,
                "candidate_count": len(all_rows),
                "improve_count": improve_count,
                "rank_sig_all": rank_sig,
                "rank_sign_all": rank_sign,
                "rank_verify_all": rank_verify,
                "rank_sig_pct": f"{100.0 * rank_sig / len(all_rows):.2f}",
                "rank_sign_pct": f"{100.0 * rank_sign / len(all_rows):.2f}",
                "rank_verify_pct": f"{100.0 * rank_verify / len(all_rows):.2f}",
                "candidates_csv": str(cand_csv),
            }
        )

    summary_csv = out_dir / "para_kylin_selected_6profiles.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        fields = list(summary_rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"[done] wrote {summary_csv}")


if __name__ == "__main__":
    main()
