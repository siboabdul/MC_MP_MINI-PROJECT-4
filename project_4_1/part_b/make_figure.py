#!/usr/bin/env python3
"""Generate figures/link_budget_comparison.svg from results/link_budget_results.json.

Standard library only. The SVG opens in any browser; Word 2016+ inserts SVG natively.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "results" / "link_budget_results.json").read_text())

rows    = data["rows"]
names   = [r["technology"] for r in rows]
margins = [r["margin_db"] for r in rows]
batts   = [r["battery_years"] for r in rows]
target  = data["scenario"]["target_years"]
pl      = data["path_loss_db"]
dist    = data["scenario"]["distance_km"]

W, H, PAD = 1200, 520, 80
chart_w   = (W - 3 * PAD) // 2
BAR_W     = 100


def chart(x0, vals, colors, ylabel, title, target_line=None):
    out = []
    out.append(f'<line x1="{x0}" y1="{PAD}" x2="{x0}" y2="{H-PAD}" stroke="black" stroke-width="2"/>')
    out.append(f'<line x1="{x0}" y1="{H-PAD}" x2="{x0+chart_w}" y2="{H-PAD}" stroke="black" stroke-width="2"/>')
    top = max(vals + ([target_line] if target_line else []) + [0]) * 1.20 or 1
    bot = min(vals + [0])
    span = top - bot
    def y(v): return (H - PAD) - (v - bot) / span * (H - 2 * PAD)
    for i, (n, v) in enumerate(zip(names, vals)):
        cx = x0 + 30 + i * (chart_w - 60) / len(vals) + BAR_W / 2
        yv = y(v); y0 = y(0)
        top_y = min(yv, y0); h = abs(yv - y0)
        out.append(f'<rect x="{cx - BAR_W/2:.1f}" y="{top_y:.1f}" width="{BAR_W}" height="{h:.1f}" fill="{colors[i]}"/>')
        ly = top_y - 8 if v >= 0 else top_y + h + 18
        out.append(f'<text x="{cx:.1f}" y="{ly:.1f}" text-anchor="middle" font-family="Arial" font-size="14">{v:.1f}</text>')
        out.append(f'<text x="{cx:.1f}" y="{H-PAD+22}" text-anchor="middle" font-family="Arial" font-size="13">{n}</text>')
    out.append(f'<line x1="{x0}" y1="{y(0):.1f}" x2="{x0+chart_w}" y2="{y(0):.1f}" stroke="black" stroke-width="1"/>')
    if target_line is not None:
        ty = y(target_line)
        out.append(f'<line x1="{x0}" y1="{ty:.1f}" x2="{x0+chart_w}" y2="{ty:.1f}" stroke="black" stroke-dasharray="6,4" stroke-width="1.5"/>')
        out.append(f'<text x="{x0+chart_w-8}" y="{ty-6:.1f}" text-anchor="end" font-family="Arial" font-size="12" fill="#444">target {target_line:g} yr</text>')
    out.append(f'<text x="{x0}" y="{PAD-42}" font-family="Arial" font-size="14" font-weight="bold">{ylabel}</text>')
    out.append(f'<text x="{x0}" y="{PAD-14}" font-family="Arial" font-size="13">{title}</text>')
    return "\n".join(out)


colors_cov = ["#2E86AB" if m > 0 else "#C73E1D" for m in margins]
colors_bat = ["#2E86AB" if y >= target else "#C73E1D" for y in batts]

svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<rect width="{W}" height="{H}" fill="white"/>
{chart(PAD, margins, colors_cov, "Coverage margin (dB)", f"At {dist:g} km (path loss = {pl:.1f} dB)")}
{chart(W//2 + 20, batts, colors_bat, "Battery life (years)", "Battery life on 19,000 mAh cell", target_line=target)}
</svg>
'''

out = ROOT / "figures" / "link_budget_comparison.svg"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(svg)
print(f"Figure written to {out}")
print("Open it with:  start \"\" \"%s\"" % out)