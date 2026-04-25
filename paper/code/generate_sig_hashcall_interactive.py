#!/usr/bin/env python3
"""Generate interactive Pareto-step SIG-hashcall charts with hover metadata.

The output is a self-contained HTML file (no Python plotting dependency) that
shows three charts (Kylin-128/256/512). Hover a point to inspect:
  sig, hashcalls, h, d, h_vec, h0, a, k, w, len, classical_bitsec.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

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
    """Monotone Pareto frontier for minimizing (sig, hashcalls).

    Input must be sorted by sig ascending and contain the best point per sig.
    """
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


def render_html(frontiers: dict[str, list[FrontierPoint]], stats: dict[str, dict[str, int]]) -> str:
    dataset = {}
    for family, points in frontiers.items():
        dataset[family] = {
            "points": [
                {
                    "sig": p.sig,
                    "hashcalls": p.hashcalls,
                    "h": p.h,
                    "d": p.d,
                    "h_vec": list(p.h_vec),
                    "h0": p.h0,
                    "a": p.a,
                    "k": p.k,
                    "w": p.w,
                    "len": p.length,
                    "classical": round(p.classical_bitsec, 6),
                }
                for p in points
            ],
            "stats": stats[family],
        }

    data_json = json.dumps(dataset, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SIG-HashCall Pareto Step Interactive</title>
  <style>
    :root {{
      --bg: #f5f5f5;
      --card: #ffffff;
      --text: #111111;
      --muted: #666666;
      --grid: #d9d9d9;
      --blue: #1f77b4;
      --green: #2ca02c;
      --red: #d62728;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
    }}
    .wrap {{
      max-width: 1300px;
      margin: 0 auto;
      padding: 20px 16px 32px;
    }}
    h1 {{
      margin: 0 0 12px;
      font-size: 24px;
      line-height: 1.25;
    }}
    .meta {{
      color: var(--muted);
      margin-bottom: 18px;
      font-size: 14px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(1, minmax(0, 1fr));
      gap: 14px;
    }}
    .card {{
      background: var(--card);
      border-radius: 10px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      padding: 12px;
      overflow: hidden;
    }}
    .title {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 6px;
    }}
    .title h2 {{
      margin: 0;
      font-size: 18px;
    }}
    .stats {{
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }}
    svg {{
      width: 100%;
      height: auto;
      display: block;
      background: #fff;
    }}
    .axis text {{
      fill: #444;
      font-size: 12px;
    }}
    .axis line, .axis path {{
      stroke: #222;
      stroke-width: 1;
      fill: none;
    }}
    .gridline {{
      stroke: var(--grid);
      stroke-width: 1;
    }}
    .line {{
      fill: none;
      stroke-width: 2;
    }}
    .dot {{
      cursor: pointer;
      stroke: #fff;
      stroke-width: 1;
    }}
    .xlabel, .ylabel {{
      fill: #222;
      font-size: 13px;
    }}
    .tooltip {{
      position: fixed;
      z-index: 999;
      pointer-events: none;
      background: #111;
      color: #fff;
      font-size: 12px;
      line-height: 1.35;
      border-radius: 8px;
      padding: 8px 10px;
      max-width: 360px;
      display: none;
      box-shadow: 0 6px 18px rgba(0,0,0,0.25);
      white-space: pre-line;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Pareto Frontier (Step): SIG vs HashCalls (Interactive)</h1>
    <div class="meta">将鼠标悬停到任意点查看完整参数。当前口径: strict。搜索范围: W=[{s.W_CHOICES[0]},{s.W_CHOICES[-1]}], H=[{s.H_CHOICES[0]},{s.H_CHOICES[-1]}], A=[{s.A_CHOICES[0]},{s.A_CHOICES[-1]}]。</div>
    <div id="charts" class="grid"></div>
  </div>
  <div id="tip" class="tooltip"></div>
  <script>
    const DATA = {data_json};
    const COLORS = {{
      "Kylin-128": getComputedStyle(document.documentElement).getPropertyValue('--blue').trim(),
      "Kylin-256": getComputedStyle(document.documentElement).getPropertyValue('--green').trim(),
      "Kylin-512": getComputedStyle(document.documentElement).getPropertyValue('--red').trim(),
    }};

    const chartsDiv = document.getElementById('charts');
    const tip = document.getElementById('tip');

    function fmt(n) {{
      return Number(n).toLocaleString('en-US');
    }}

    function createSvgEl(tag, attrs = {{}}) {{
      const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
      for (const [k, v] of Object.entries(attrs)) {{
        el.setAttribute(k, v);
      }}
      return el;
    }}

    function showTip(ev, p, family) {{
      tip.style.display = 'block';
      tip.textContent =
`${{family}}
sig: ${{fmt(p.sig)}}
hashcalls: ${{fmt(p.hashcalls)}}
h: ${{p.h}}, d: ${{p.d}}, h_vec: [${{p.h_vec.join(',')}}], h0: ${{p.h0}}
a: ${{p.a}}, k: ${{p.k}}, w: ${{p.w}}, len: ${{p.len}}
classical_bitsec: ${{p.classical}}`;
      const pad = 14;
      const x = Math.min(window.innerWidth - tip.offsetWidth - pad, ev.clientX + 16);
      const y = Math.min(window.innerHeight - tip.offsetHeight - pad, ev.clientY + 16);
      tip.style.left = x + 'px';
      tip.style.top = y + 'px';
    }}

    function hideTip() {{
      tip.style.display = 'none';
    }}

    function drawChart(family, payload) {{
      const points = payload.points;
      const st = payload.stats;
      const color = COLORS[family] || '#333';

      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <div class="title">
          <h2>${{family}}</h2>
          <div class="stats">candidates=${{fmt(st.candidates)}} | unique_sig=${{fmt(st.unique_sig)}} | frontier=${{fmt(st.frontier_points)}} | min_sig=${{fmt(st.min_sig)}}</div>
        </div>
      `;

      const W = 1180, H = 470;
      const m = {{l: 72, r: 26, t: 16, b: 54}};
      const iw = W - m.l - m.r;
      const ih = H - m.t - m.b;

      const xMin = Math.min(...points.map(p => p.sig));
      const xMax = Math.max(...points.map(p => p.sig));
      const yMin = Math.min(...points.map(p => p.hashcalls));
      const yMax = Math.max(...points.map(p => p.hashcalls));

      const xPad = Math.max(1, Math.floor((xMax - xMin) * 0.06));
      const yPad = Math.max(1, Math.floor((yMax - yMin) * 0.08));
      const X0 = xMin - xPad, X1 = xMax + xPad;
      const Y0 = Math.max(0, yMin - yPad), Y1 = yMax + yPad;

      const sx = (v) => m.l + (v - X0) * iw / (X1 - X0);
      const sy = (v) => m.t + ih - (v - Y0) * ih / (Y1 - Y0);

      const svg = createSvgEl('svg', {{viewBox: `0 0 ${{W}} ${{H}}`}});

      const xTicks = 7;
      const yTicks = 6;
      for (let i = 0; i <= xTicks; i++) {{
        const xVal = X0 + (X1 - X0) * i / xTicks;
        const x = sx(xVal);
        svg.appendChild(createSvgEl('line', {{x1: x, y1: m.t, x2: x, y2: m.t + ih, class: 'gridline'}}));
        const txt = createSvgEl('text', {{x: x, y: H - m.b + 18, 'text-anchor': 'middle'}});
        txt.textContent = fmt(Math.round(xVal));
        txt.setAttribute('class', 'axis');
        svg.appendChild(txt);
      }}
      for (let i = 0; i <= yTicks; i++) {{
        const yVal = Y0 + (Y1 - Y0) * i / yTicks;
        const y = sy(yVal);
        svg.appendChild(createSvgEl('line', {{x1: m.l, y1: y, x2: m.l + iw, y2: y, class: 'gridline'}}));
        const txt = createSvgEl('text', {{x: m.l - 8, y: y + 4, 'text-anchor': 'end'}});
        txt.textContent = fmt(Math.round(yVal));
        txt.setAttribute('class', 'axis');
        svg.appendChild(txt);
      }}

      svg.appendChild(createSvgEl('line', {{x1: m.l, y1: m.t + ih, x2: m.l + iw, y2: m.t + ih, class: 'axis'}}));
      svg.appendChild(createSvgEl('line', {{x1: m.l, y1: m.t, x2: m.l, y2: m.t + ih, class: 'axis'}}));

      const stepPts = [];
      if (points.length > 0) {{
        stepPts.push(`${{sx(points[0].sig)}},${{sy(points[0].hashcalls)}}`);
        for (let i = 1; i < points.length; i++) {{
          const prev = points[i - 1];
          const cur = points[i];
          stepPts.push(`${{sx(cur.sig)}},${{sy(prev.hashcalls)}}`);
          stepPts.push(`${{sx(cur.sig)}},${{sy(cur.hashcalls)}}`);
        }}
      }}
      svg.appendChild(createSvgEl('polyline', {{points: stepPts.join(' '), class: 'line', stroke: color}}));

      for (const p of points) {{
        const c = createSvgEl('circle', {{
          cx: sx(p.sig), cy: sy(p.hashcalls), r: 4.2, fill: color, class: 'dot'
        }});
        c.addEventListener('mousemove', (ev) => showTip(ev, p, family));
        c.addEventListener('mouseenter', (ev) => showTip(ev, p, family));
        c.addEventListener('mouseleave', hideTip);
        svg.appendChild(c);
      }}

      const xlabel = createSvgEl('text', {{x: m.l + iw / 2, y: H - 12, 'text-anchor': 'middle', class: 'xlabel'}});
      xlabel.textContent = 'Signature size (bytes)';
      svg.appendChild(xlabel);

      const ylabel = createSvgEl('text', {{
        x: 20, y: m.t + ih / 2, transform: `rotate(-90 20 ${{m.t + ih / 2}})`, 'text-anchor': 'middle', class: 'ylabel'
      }});
      ylabel.textContent = 'Hash calls (proxy)';
      svg.appendChild(ylabel);

      card.appendChild(svg);
      chartsDiv.appendChild(card);
    }}

    for (const family of Object.keys(DATA)) {{
      drawChart(family, DATA[family]);
    }}
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("paper/data/sig_hashcall_pareto_step_interactive.html"),
        help="Output interactive HTML path.",
    )
    args = parser.parse_args()

    frontiers: dict[str, list[FrontierPoint]] = {}
    stats: dict[str, dict[str, int]] = {}
    for family in s.FAMILIES:
        family_frontier, family_stats = build_family_frontier(family)
        frontiers[family.name] = family_frontier
        stats[family.name] = family_stats
        print(
            f"{family.name}: candidates={family_stats['candidates']}, "
            f"unique_sig={family_stats['unique_sig']}, frontier_points={family_stats['frontier_points']}, "
            f"min_sig={family_stats['min_sig']}"
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_html(frontiers, stats), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
