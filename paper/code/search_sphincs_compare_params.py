#!/usr/bin/env python3
"""Retune BPORS+FP Kylin profiles against comparison caps.

The primary q=2^64 128/256-bit profiles can be constrained against either
SLH-DSA-SHAKE or SPHINCS-alpha small-signature parameter sets.  The q=2^24
companions are constrained against the draft SP 800-230 limited-signature-use
parameter sets where exact target security is feasible.  The 512-bit profiles
are constrained to stay within a selected multiple of the 256-bit Kylin profile
costs, then all profiles minimize signature size.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

import search_bpors_kylin_params as bp


@dataclass(frozen=True)
class CapProfile:
    label: str
    baseline: bp.Baseline
    keygen_hashcalls: int
    strict_signature: bool


TARGETS = {
    "Kylin-128": 127.0,
    "Kylin-256": 255.0,
    "Kylin-512": 511.0,
    "Kylin-128-q24": 127.0,
    "Kylin-256-q24": 255.0,
    "Kylin-512-q24": 511.0,
}

EXACT_TARGETS = {
    "Kylin-128": 128.0,
    "Kylin-256": 256.0,
    "Kylin-512": 512.0,
    "Kylin-128-q24": 128.0,
    "Kylin-256-q24": 256.0,
    "Kylin-512-q24": 512.0,
}



def floor_log_base(x: int, base: int) -> int:
    if x < 1:
        raise ValueError("floor_log_base input must be positive")
    out = 0
    power = base
    while power <= x:
        out += 1
        power *= base
    return out


def wots_plus_len(n: int, w: int) -> int:
    if w <= 1 or w & (w - 1):
        raise ValueError(f"WOTS+ baseline w must be a power of two, got {w}")
    log_w = int(math.log2(w))
    len1 = (8 * n + log_w - 1) // log_w
    len2 = floor_log_base(len1 * (w - 1), w) + 1
    return len1 + len2


def slh_cap(
    *,
    name: str,
    label: str,
    q_sigs: int,
    n: int,
    target_bits: float,
    h: int,
    d: int,
    a: int,
    k: int,
    w: int,
) -> CapProfile:
    if h % d != 0:
        raise ValueError(f"{label}: h must be divisible by d for this helper")
    h_vec = (h // d,) * d
    length = wots_plus_len(n, w)
    sig = (1 + (a + 1) * k + h + d * length) * n
    sign = k * (1 << (a + 1)) + bp.sign_ht_hashcalls(h_vec, w, length)
    verify = k * (a + 1) + 1 + bp.verify_ht_hashcalls(h, d, w, length)
    keygen = bp.keygen_hashcalls(h_vec, w, length)
    return CapProfile(
        label,
        bp.Baseline(
            name=name,
            q_sigs=q_sigs,
            n=n,
            target_bits=target_bits,
            h=h,
            d=d,
            h_vec=h_vec,
            a=a,
            k=k,
            w=w,
            length=length,
            sig=sig,
            sign_hashcalls=sign,
            verify_hashcalls=verify,
        ),
        keygen,
        True,
    )


def alpha_cap(
    *,
    name: str,
    label: str,
    q_sigs: int,
    n: int,
    target_bits: float,
    h: int,
    d: int,
    a: int,
    k: int,
    w: int,
    length: int,
) -> CapProfile:
    if h % d != 0:
        raise ValueError(f"{label}: h must be divisible by d for this helper")
    h_vec = (h // d,) * d
    sig = (1 + (a + 1) * k + h + d * length) * n
    sign = k * (1 << (a + 1)) + bp.sign_ht_hashcalls(h_vec, w, length)
    verify = k * (a + 1) + 1 + bp.verify_ht_hashcalls(h, d, w, length)
    keygen = bp.keygen_hashcalls(h_vec, w, length)
    return CapProfile(
        label,
        bp.Baseline(
            name=name,
            q_sigs=q_sigs,
            n=n,
            target_bits=target_bits,
            h=h,
            d=d,
            h_vec=h_vec,
            a=a,
            k=k,
            w=w,
            length=length,
            sig=sig,
            sign_hashcalls=sign,
            verify_hashcalls=verify,
        ),
        keygen,
        False,
    )


EXTERNAL_CAPS = {
    "Kylin-128": slh_cap(
        name="Kylin-128",
        label="SLH-DSA-SHAKE-128s",
        q_sigs=2**64,
        n=16,
        target_bits=TARGETS["Kylin-128"],
        h=63,
        d=7,
        a=12,
        k=14,
        w=16,
    ),
    "Kylin-256": slh_cap(
        name="Kylin-256",
        label="SLH-DSA-SHAKE-256s",
        q_sigs=2**64,
        n=32,
        target_bits=TARGETS["Kylin-256"],
        h=64,
        d=8,
        a=14,
        k=22,
        w=16,
    ),
    "Kylin-128-q24": slh_cap(
        name="Kylin-128-q24",
        label="SLH-DSA-SHAKE-128-24",
        q_sigs=2**24,
        n=16,
        target_bits=TARGETS["Kylin-128-q24"],
        h=22,
        d=1,
        a=24,
        k=6,
        w=4,
    ),
    "Kylin-256-q24": slh_cap(
        name="Kylin-256-q24",
        label="SLH-DSA-SHAKE-256-24",
        q_sigs=2**24,
        n=32,
        target_bits=TARGETS["Kylin-256-q24"],
        h=21,
        d=1,
        a=25,
        k=12,
        w=4,
    ),
}


SPHINCS_ALPHA_CAPS = {
    "Kylin-128": CapProfile(
        "SPHINCS-alpha-SHA2-128s",
        bp.Baseline(
            name="Kylin-128",
            q_sigs=2**64,
            n=16,
            target_bits=TARGETS["Kylin-128"],
            h=63,
            d=9,
            h_vec=(7,) * 9,
            a=13,
            k=12,
            w=73,
            length=22,
            sig=6880,
            sign_hashcalls=537033762,
            verify_hashcalls=2689650,
        ),
        51421086,
        False,
    ),
    "Kylin-256": CapProfile(
        "SPHINCS-alpha-SHA2-256s",
        bp.Baseline(
            name="Kylin-256",
            q_sigs=2**64,
            n=32,
            target_bits=TARGETS["Kylin-256"],
            h=66,
            d=11,
            h_vec=(6,) * 11,
            a=13,
            k=23,
            w=79,
            length=42,
            sig=27232,
            sign_hashcalls=764352612,
            verify_hashcalls=6005448,
        ),
        52048332,
        False,
    ),
}

SPHINCS_ALPHA_PARAMETER_PROXY_CAPS = {
    "Kylin-128": alpha_cap(
        name="Kylin-128",
        label="SPHINCS-alpha-128s",
        q_sigs=2**64,
        n=16,
        target_bits=TARGETS["Kylin-128"],
        h=63,
        d=9,
        a=13,
        k=12,
        w=73,
        length=22,
    ),
    "Kylin-256": alpha_cap(
        name="Kylin-256",
        label="SPHINCS-alpha-256s",
        q_sigs=2**64,
        n=32,
        target_bits=TARGETS["Kylin-256"],
        h=66,
        d=11,
        a=13,
        k=23,
        w=79,
        length=42,
    ),
}


def scenario_for(base: bp.Scenario, targets: dict[str, float]) -> bp.Scenario:
    return bp.Scenario(
        base.name,
        base.q_sigs,
        base.n,
        targets[base.name],
        base.h_min,
        base.h_max,
        base.d_min,
        base.d_max,
        base.w_min,
        base.w_max,
        base.child_k_min,
        base.child_k_max,
        base.bpors_K_min,
        base.bpors_K_max,
        base.bpors_B_min,
        base.bpors_B_max,
    )


def cap_from_candidate(
    name: str,
    source: bp.Candidate,
    multiplier: int,
    targets: dict[str, float],
) -> CapProfile:
    return CapProfile(
        f"{multiplier}x {source.name}",
        bp.Baseline(
            name=name,
            q_sigs=2**64 if not name.endswith("-q24") else 2**24,
            n=64,
            target_bits=targets[name],
            h=source.h,
            d=source.d,
            h_vec=source.h_vec,
            a=source.B,
            k=source.child_k,
            w=source.w,
            length=source.length,
            sig=multiplier * source.sig,
            sign_hashcalls=multiplier * source.sign_hashcalls,
            verify_hashcalls=multiplier * source.verify_hashcalls,
        ),
        multiplier * source.keygen_hashcalls,
        False,
    )


def cap_from_external_limit(
    name: str,
    source: CapProfile,
    multiplier: int,
    targets: dict[str, float],
) -> CapProfile:
    return CapProfile(
        f"{multiplier}x maximum profile below {source.label}",
        bp.Baseline(
            name=name,
            q_sigs=2**64 if not name.endswith("-q24") else 2**24,
            n=64,
            target_bits=targets[name],
            h=source.baseline.h,
            d=source.baseline.d,
            h_vec=source.baseline.h_vec,
            a=source.baseline.a,
            k=source.baseline.k,
            w=source.baseline.w,
            length=source.baseline.length,
            sig=multiplier * (source.baseline.sig - 1),
            sign_hashcalls=multiplier * source.baseline.sign_hashcalls,
            verify_hashcalls=multiplier * source.baseline.verify_hashcalls,
        ),
        multiplier * source.keygen_hashcalls,
        False,
    )


def lower_bounds_from_candidate(c: bp.Candidate, multiplier: int) -> dict[str, int]:
    return {
        "sig": (c.sig + multiplier - 1) // multiplier,
        "keygen_hashcalls": (c.keygen_hashcalls + multiplier - 1) // multiplier,
        "sign_hashcalls": (c.sign_hashcalls + multiplier - 1) // multiplier,
        "verify_hashcalls": (c.verify_hashcalls + multiplier - 1) // multiplier,
    }


def candidate_fallback(c: bp.Candidate) -> dict[str, object]:
    return {
        "q_sigs": c.q_sigs,
        "n": c.n,
        "target_bits": c.target_bits,
        "h": c.h,
        "d": c.d,
        "h_vec": c.h_vec,
        "K": c.K,
        "B": c.B,
        "t": c.t,
        "child_k": c.child_k,
        "mmax": c.mmax,
        "w": c.w,
        "length": c.length,
        "sig": c.sig,
    }


def cap_with_target(cap: CapProfile, target_bits: float) -> CapProfile:
    baseline = cap.baseline
    return CapProfile(
        cap.label,
        bp.Baseline(
            name=baseline.name,
            q_sigs=baseline.q_sigs,
            n=baseline.n,
            target_bits=target_bits,
            h=baseline.h,
            d=baseline.d,
            h_vec=baseline.h_vec,
            a=baseline.a,
            k=baseline.k,
            w=baseline.w,
            length=baseline.length,
            sig=baseline.sig,
            sign_hashcalls=baseline.sign_hashcalls,
            verify_hashcalls=baseline.verify_hashcalls,
        ),
        cap.keygen_hashcalls,
        cap.strict_signature,
    )


def cap_with_signature_limit(cap: CapProfile, signature_limit: int) -> CapProfile:
    baseline = cap.baseline
    return CapProfile(
        f"{cap.label} (signature cap relaxed for exact classical security)",
        bp.Baseline(
            name=baseline.name,
            q_sigs=baseline.q_sigs,
            n=baseline.n,
            target_bits=baseline.target_bits,
            h=baseline.h,
            d=baseline.d,
            h_vec=baseline.h_vec,
            a=baseline.a,
            k=baseline.k,
            w=baseline.w,
            length=baseline.length,
            sig=signature_limit,
            sign_hashcalls=baseline.sign_hashcalls,
            verify_hashcalls=baseline.verify_hashcalls,
        ),
        cap.keygen_hashcalls,
        False,
    )


def configure_search(
    active_caps: dict[str, CapProfile],
    notes: str,
    fallbacks: dict[str, dict[str, object]] | None = None,
    lower_bounds: dict[str, dict[str, int]] | None = None,
) -> None:
    bp.ACTIVE_BASELINES = {name: cap.baseline for name, cap in active_caps.items()}
    bp.ACTIVE_FALLBACKS = fallbacks if fallbacks is not None else dict(bp.SECURE_BPORS_FALLBACKS)
    bp.ACTIVE_SIGN_COST_SLACK = 1.0
    bp.ACTIVE_VERIFY_COST_SLACK = 1.0
    bp.ACTIVE_ENFORCE_SIGN_CAP = True
    bp.ACTIVE_WIDE_BPORS = True
    bp.ACTIVE_TAU_FLOOR = 0.0
    bp.ACTIVE_Q24_TAU_FLOOR = 0.0
    bp.INITIAL_SIG_HEADROOM = 1
    bp.ACTIVE_SIGNATURE_CAPS = {
        name: (cap.baseline.sig, cap.strict_signature)
        for name, cap in active_caps.items()
    }
    bp.ACTIVE_KEYGEN_CAPS = {
        name: cap.keygen_hashcalls for name, cap in active_caps.items()
    }
    bp.ACTIVE_METRIC_LOWER_BOUNDS = lower_bounds if lower_bounds is not None else {}
    bp.ACTIVE_NOTES = notes


def print_caps(active_caps: dict[str, CapProfile]) -> None:
    for name, cap in active_caps.items():
        sig_op = "<" if cap.strict_signature else "<="
        print(
            f"[cap] {name}: {cap.label}, sig {sig_op} {cap.baseline.sig}, "
            f"keygen<={cap.keygen_hashcalls}, "
            f"sign<={cap.baseline.sign_hashcalls}, "
            f"verify<={cap.baseline.verify_hashcalls}",
            flush=True,
        )


def search_with_seed(
    name: str,
    scenario: bp.Scenario,
    active_caps: dict[str, CapProfile],
    fallbacks: dict[str, dict[str, object]],
    notes: str,
    keep: int,
    lower_bounds: dict[str, dict[str, int]] | None = None,
) -> tuple[bp.Candidate, list[bp.Candidate]]:
    best: bp.Candidate | None = None
    merged: list[bp.Candidate] = []
    for round_idx in range(1, 11):
        print(f"[search] {name} focused round {round_idx}", flush=True)
        configure_search(active_caps, notes, fallbacks, lower_bounds)
        bp.ACTIVE_WIDE_BPORS = False
        current, kept = bp.search_scenario(scenario, keep)
        merged.extend(kept)
        print(
            f"  round {round_idx} sig={current.sig} "
            f"sign={current.sign_hashcalls} verify={current.verify_hashcalls} "
            f"bitsec={current.bitsec:.6f}",
            flush=True,
        )
        if best is not None and current.sig >= best.sig:
            break
        best = current
        fallbacks[name] = candidate_fallback(current)
    if best is None:
        raise RuntimeError(f"no focused seed found for {name}")
    return best, sorted(set(merged), key=bp.rank_key)[:keep]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write CSV outputs")
    parser.add_argument("--sync-params", action="store_true", help="rewrite params.h files")
    parser.add_argument("--keep", type=int, default=120, help="candidate rows to keep per profile")
    parser.add_argument(
        "--tier512-multiplier",
        type=int,
        default=2,
        help="cap 512-bit profiles at this multiple of the selected 256-bit profile",
    )
    parser.add_argument(
        "--q64-cap-source",
        choices=("slh-dsa", "sphincs-alpha"),
        default="slh-dsa",
        help="external cap source for the q=2^64 128/256-bit profiles",
    )
    parser.add_argument(
        "--exact-targets",
        action="store_true",
        help="require exact 128/256/512 classical security targets",
    )
    args = parser.parse_args()

    targets = EXACT_TARGETS if args.exact_targets else TARGETS
    scenario_map = {s.name: scenario_for(s, targets) for s in bp.SCENARIOS}
    selected: dict[str, bp.Candidate] = {}
    kept_rows: list[bp.Candidate] = []
    fallbacks: dict[str, dict[str, object]] = dict(bp.SECURE_BPORS_FALLBACKS)

    q64_caps = SPHINCS_ALPHA_CAPS if args.q64_cap_source == "sphincs-alpha" else EXTERNAL_CAPS
    q64_label = "SPHINCS-alpha 2022/059" if args.q64_cap_source == "sphincs-alpha" else "SLH-DSA"
    notes = (
        f"BPORS+FP retuned against {q64_label}/SP 800-230 comparison caps; "
        f"Kylin-512 profiles are capped at {args.tier512_multiplier}x "
        "the selected Kylin-256 profile"
    )

    active_caps: dict[str, CapProfile] = {
        "Kylin-128": cap_with_target(q64_caps["Kylin-128"], targets["Kylin-128"]),
        "Kylin-256": cap_with_target(q64_caps["Kylin-256"], targets["Kylin-256"]),
        "Kylin-128-q24": cap_with_target(EXTERNAL_CAPS["Kylin-128-q24"], targets["Kylin-128-q24"]),
        "Kylin-256-q24": cap_with_target(EXTERNAL_CAPS["Kylin-256-q24"], targets["Kylin-256-q24"]),
    }
    configure_search(active_caps, notes, fallbacks)
    print_caps(active_caps)

    for name in ("Kylin-128", "Kylin-256", "Kylin-128-q24", "Kylin-256-q24"):
        try:
            best, kept = search_with_seed(
                name, scenario_map[name], active_caps, fallbacks, notes, args.keep
            )
        except RuntimeError:
            if name != "Kylin-128-q24" or not args.exact_targets:
                raise
            print(
                "[support] Kylin-128-q24 exact 128-bit security does not fit "
                "the SP 800-230 signature-size cap; keeping keygen/sign/verify "
                "caps and relaxing only the signature cap",
                flush=True,
            )
            active_caps[name] = cap_with_signature_limit(active_caps[name], 8000)
            best, kept = search_with_seed(
                name, scenario_map[name], active_caps, fallbacks, notes, args.keep
            )
        selected[name] = best
        fallbacks[name] = candidate_fallback(best)
        kept_rows.extend(kept)
        cap = active_caps[name]
        print(
            f"  selected sig={best.sig}/{cap.baseline.sig} "
            f"keygen={best.keygen_hashcalls}/{cap.keygen_hashcalls} "
            f"sign={best.sign_hashcalls}/{cap.baseline.sign_hashcalls} "
            f"verify={best.verify_hashcalls}/{cap.baseline.verify_hashcalls} "
            f"bitsec={best.bitsec:.6f} tau={best.tau:.3g} "
            f"h={best.h} d={best.d} h_vec={best.h_profile} "
            f"K={best.K} B={best.B} t={best.t} k={best.child_k} "
            f"mmax={best.mmax} w={best.w} len={best.length}",
            flush=True,
        )

    active_caps["Kylin-512"] = cap_from_candidate(
        "Kylin-512", selected["Kylin-256"], args.tier512_multiplier, targets
    )
    configure_search(active_caps, notes, fallbacks)
    print_caps({"Kylin-512": active_caps["Kylin-512"]})
    best, kept = search_with_seed(
        "Kylin-512", scenario_map["Kylin-512"], active_caps, fallbacks, notes, args.keep
    )
    selected["Kylin-512"] = best
    fallbacks["Kylin-512"] = candidate_fallback(best)
    kept_rows.extend(kept)
    cap = active_caps["Kylin-512"]
    print(
        f"  selected sig={best.sig}/{cap.baseline.sig} "
        f"keygen={best.keygen_hashcalls}/{cap.keygen_hashcalls} "
        f"sign={best.sign_hashcalls}/{cap.baseline.sign_hashcalls} "
        f"verify={best.verify_hashcalls}/{cap.baseline.verify_hashcalls} "
        f"bitsec={best.bitsec:.6f} tau={best.tau:.3g} "
        f"h={best.h} d={best.d} h_vec={best.h_profile} "
        f"K={best.K} B={best.B} t={best.t} k={best.child_k} "
        f"mmax={best.mmax} w={best.w} len={best.length}",
        flush=True,
    )

    active_caps["Kylin-512-q24"] = cap_from_candidate(
        "Kylin-512-q24", selected["Kylin-256-q24"], args.tier512_multiplier, targets
    )
    configure_search(active_caps, notes, fallbacks)
    print_caps({"Kylin-512-q24": active_caps["Kylin-512-q24"]})
    try:
        best, kept = search_with_seed(
            "Kylin-512-q24",
            scenario_map["Kylin-512-q24"],
            active_caps,
            fallbacks,
            notes,
            args.keep,
        )
    except RuntimeError:
        print(
            "[support] Kylin-512-q24 needs a larger Kylin-256-q24 support profile",
            flush=True,
        )
        support_cap = {
            "Kylin-512-q24": cap_from_external_limit(
                "Kylin-512-q24",
                EXTERNAL_CAPS["Kylin-256-q24"],
                args.tier512_multiplier,
                targets,
            )
        }
        print_caps(support_cap)
        support_512, support_kept = search_with_seed(
            "Kylin-512-q24",
            scenario_map["Kylin-512-q24"],
            support_cap,
            fallbacks,
            notes,
            args.keep,
        )
        kept_rows.extend(support_kept)
        lower_bounds = {
            "Kylin-256-q24": lower_bounds_from_candidate(
                support_512, args.tier512_multiplier
            )
        }
        print(
            f"[support] lower bounds for Kylin-256-q24: "
            f"{lower_bounds['Kylin-256-q24']}",
            flush=True,
        )
        support_256_caps = {
            "Kylin-256-q24": cap_with_target(
                EXTERNAL_CAPS["Kylin-256-q24"], targets["Kylin-256-q24"]
            )
        }
        support_256, support_kept = search_with_seed(
            "Kylin-256-q24",
            scenario_map["Kylin-256-q24"],
            support_256_caps,
            fallbacks,
            notes,
            args.keep,
            lower_bounds,
        )
        selected["Kylin-256-q24"] = support_256
        fallbacks["Kylin-256-q24"] = candidate_fallback(support_256)
        kept_rows.extend(support_kept)
        active_caps["Kylin-512-q24"] = cap_from_candidate(
            "Kylin-512-q24", support_256, args.tier512_multiplier, targets
        )
        print_caps({"Kylin-512-q24": active_caps["Kylin-512-q24"]})
        best, kept = search_with_seed(
            "Kylin-512-q24",
            scenario_map["Kylin-512-q24"],
            active_caps,
            fallbacks,
            notes,
            args.keep,
        )

    selected["Kylin-512-q24"] = best
    fallbacks["Kylin-512-q24"] = candidate_fallback(best)
    kept_rows.extend(kept)
    cap = active_caps["Kylin-512-q24"]
    print(
        f"  selected sig={best.sig}/{cap.baseline.sig} "
        f"keygen={best.keygen_hashcalls}/{cap.keygen_hashcalls} "
        f"sign={best.sign_hashcalls}/{cap.baseline.sign_hashcalls} "
        f"verify={best.verify_hashcalls}/{cap.baseline.verify_hashcalls} "
        f"bitsec={best.bitsec:.6f} tau={best.tau:.3g} "
        f"h={best.h} d={best.d} h_vec={best.h_profile} "
        f"K={best.K} B={best.B} t={best.t} k={best.child_k} "
        f"mmax={best.mmax} w={best.w} len={best.length}",
        flush=True,
    )

    if args.write:
        ordered = [
            selected[name]
            for name in (
                "Kylin-128",
                "Kylin-256",
                "Kylin-512",
                "Kylin-128-q24",
                "Kylin-256-q24",
                "Kylin-512-q24",
            )
        ]
        bp.write_candidate_csv(bp.SEARCH_CSV, kept_rows)
        bp.write_candidate_csv(bp.FINAL_CSV, ordered)
        bp.write_candidate_csv(bp.SELECTED_CSV, ordered)
    if args.sync_params:
        bp.sync_params(selected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
