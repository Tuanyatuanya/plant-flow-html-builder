#!/usr/bin/env python3
"""Generate deterministic plant-layout SVG test images and ground-truth manifests."""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path

W, H = 1600, 900
ZONE_COLORS = {
    "blue": "#d9ebfb", "green": "#ddf3e6", "yellow": "#fff1bf",
    "pink": "#f6dced", "aqua": "#d8f1f2", "gray": "#e8ecee",
}


def zone(zid, label, x, y, w, h, fill="gray"):
    return {"id": zid, "label": label, "bbox": [x, y, w, h], "color": ZONE_COLORS[fill]}


def route(rid, destination, points):
    return {"id": rid, "destination": destination, "waypoints": points}


CASES = [
    {
        "case_id": "test-01-linear-line",
        "title": "TEST 01 · LINEAR ASSEMBLY",
        "difficulty": "easy",
        "zones": [
            zone("receiving", "RECEIVING", 100, 130, 250, 160, "blue"),
            zone("supermarket", "SUPERMARKET", 450, 130, 260, 160, "yellow"),
            zone("assembly", "MAIN ASSEMBLY", 450, 450, 420, 220, "green"),
            zone("quality", "QUALITY GATE", 970, 450, 240, 100, "pink"),
            zone("shipping", "SHIPPING", 970, 650, 240, 130, "aqua"),
        ],
        "flows": [
            {"id":"blue","label":"PRODUCT A","color":"#087fce","source":"receiving","destinations":["shipping"],"speed":55,"routes":[route("blue-main","shipping",[[350,210],[400,210],[400,410],[900,410],[900,715],[970,715]])]},
            {"id":"green","label":"EMPTY CONTAINER RETURN","color":"#10a56a","source":"shipping","destinations":["receiving"],"speed":35,"routes":[route("green-return","receiving",[[970,755],[920,755],[920,820],[80,820],[80,250],[100,250]])]},
        ],
    },
    {
        "case_id": "test-02-three-lane-hall",
        "title": "TEST 02 · THREE-LANE HALL",
        "difficulty": "medium",
        "zones": [
            zone("side_dock", "SIDE-LOAD DOCK", 80, 90, 300, 90, "green"),
            zone("back_dock", "BACK-LOAD DOCK", 900, 90, 260, 90, "green"),
            zone("staking_left", "STAKING AREA", 100, 230, 500, 90, "yellow"),
            zone("staking_right", "STAKING AREA", 650, 230, 500, 90, "yellow"),
            zone("rack", "PALLET RACK AREA", 100, 370, 500, 200, "blue"),
            zone("kitting", "E3 & E4 DP KITTING AREA", 650, 370, 500, 200, "blue"),
            zone("upper_assembly", "NCAR UPPER ASSEMBLY", 100, 650, 280, 130, "green"),
            zone("lower_assembly", "NCAR LOWER ASSEMBLY", 410, 650, 280, 130, "pink"),
            zone("dp_assembly", "E3 & E4 DP ASSEMBLY", 720, 650, 430, 130, "aqua"),
        ],
        "flows": [
            {"id":"blue","label":"PORSCHE E3/E4","color":"#087fce","source":"back_dock","destinations":["dp_assembly"],"speed":60,"routes":[route("blue-dp","dp_assembly",[[1030,180],[1190,180],[1190,620],[935,620],[935,650]])]},
            {"id":"green","label":"NCAR UPPER","color":"#10a56a","source":"side_dock","destinations":["upper_assembly"],"speed":42,"routes":[route("green-upper","upper_assembly",[[230,180],[65,180],[65,620],[240,620],[240,650]])]},
            {"id":"purple","label":"NCAR LOWER","color":"#d83faf","source":"side_dock","destinations":["lower_assembly"],"speed":72,"routes":[route("purple-lower","lower_assembly",[[330,180],[50,180],[50,805],[550,805],[550,780]])]},
        ],
    },
    {
        "case_id": "test-03-branch-and-merge",
        "title": "TEST 03 · BRANCH & MERGE",
        "difficulty": "hard",
        "zones": [
            zone("receiving_a", "RECEIVING A", 80, 110, 220, 140, "blue"),
            zone("receiving_b", "RECEIVING B", 80, 310, 220, 140, "blue"),
            zone("supermarket", "CENTRAL SUPERMARKET", 460, 170, 300, 220, "yellow"),
            zone("line_a", "ASSEMBLY LINE A", 950, 100, 250, 180, "green"),
            zone("line_b", "ASSEMBLY LINE B", 950, 350, 250, 180, "green"),
            zone("quality", "FINAL QUALITY", 600, 600, 260, 120, "pink"),
            zone("outbound", "OUTBOUND", 1040, 650, 180, 100, "aqua"),
        ],
        "flows": [
            {"id":"blue","label":"BODY PARTS","color":"#087fce","source":"receiving_a","destinations":["line_a","line_b"],"speed":58,"routes":[route("blue-line-a","line_a",[[190,110],[190,70],[1075,70],[1075,100]]),route("blue-line-b","line_b",[[300,180],[410,180],[410,550],[1075,550],[1075,530]])]},
            {"id":"green","label":"PURCHASED PARTS","color":"#10a56a","source":"receiving_b","destinations":["quality"],"speed":44,"routes":[route("green-quality","quality",[[300,380],[410,380],[410,660],[600,660]])]},
            {"id":"purple","label":"FINISHED GOODS","color":"#d83faf","source":"supermarket","destinations":["outbound"],"speed":68,"routes":[route("purple-outbound","outbound",[[610,390],[610,570],[970,570],[970,700],[1040,700]])]},
        ],
    },
    {
        "case_id": "test-04-asymmetric-retrofit",
        "title": "TEST 04 · ASYMMETRIC RETROFIT",
        "difficulty": "expert",
        "zones": [
            zone("inbound", "INBOUND DOCK", 90, 80, 250, 100, "blue"),
            zone("high_bay", "HIGH-BAY STORAGE", 90, 240, 320, 260, "yellow"),
            zone("cell_a", "PROCESS CELL A", 500, 100, 220, 160, "green"),
            zone("cell_b", "PROCESS CELL B", 770, 100, 220, 160, "green"),
            zone("shared_tools", "SHARED TOOLING", 500, 340, 180, 160, "gray"),
            zone("inspection", "IN-LINE INSPECTION", 760, 350, 230, 110, "pink"),
            zone("battery", "BATTERY MODULE", 1080, 120, 180, 250, "aqua"),
            zone("maintenance", "MAINTENANCE", 230, 620, 300, 120, "gray"),
            zone("final", "FINAL ASSEMBLY", 770, 580, 400, 160, "green"),
            zone("outbound", "OUTBOUND", 1200, 600, 110, 140, "blue"),
        ],
        "flows": [
            {"id":"blue","label":"STRUCTURE","color":"#087fce","source":"inbound","destinations":["cell_a"],"speed":52,"routes":[route("blue-cell-a","cell_a",[[340,130],[450,130],[450,180],[500,180]])]},
            {"id":"green","label":"BATTERY","color":"#10a56a","source":"inbound","destinations":["battery"],"speed":38,"routes":[route("green-battery","battery",[[250,180],[250,210],[450,210],[450,290],[1040,290],[1040,245],[1080,245]])]},
            {"id":"purple","label":"INSPECTION LOOP","color":"#d83faf","source":"high_bay","destinations":["inspection"],"speed":64,"routes":[route("purple-inspection","inspection",[[410,370],[460,370],[460,530],[875,530],[875,460]])]},
            {"id":"orange","label":"SERVICE PARTS","color":"#ee7a22","source":"maintenance","destinations":["final"],"speed":46,"routes":[route("orange-final","final",[[530,680],[650,680],[650,550],[740,550],[740,660],[770,660]])]},
        ],
    },
    {
        "case_id": "test-05-mixed-mode-plant",
        "title": "TEST 05 · MIXED-MODE PLANT",
        "difficulty": "hard",
        "zones": [
            zone("receiving", "RECEIVING DOCK", 80, 90, 240, 120, "blue"),
            zone("raw_storage", "RAW MATERIAL STORAGE", 80, 300, 300, 260, "yellow"),
            zone("machining", "MACHINING", 470, 100, 260, 180, "green"),
            zone("subassembly", "SUBASSEMBLY", 800, 100, 300, 180, "green"),
            zone("main_assembly", "MAIN ASSEMBLY", 470, 410, 500, 220, "aqua"),
            zone("quality", "QUALITY GATE", 1030, 430, 190, 120, "pink"),
            zone("return_wash", "RETURNABLE WASH", 250, 690, 260, 100, "gray"),
            zone("finished_goods", "FINISHED GOODS", 850, 700, 300, 100, "yellow"),
            zone("shipping", "SHIPPING", 1190, 680, 100, 120, "blue"),
        ],
        "flows": [
            {"id":"blue","label":"PRODUCT A","color":"#087fce","source":"receiving","destinations":["main_assembly"],"speed":56,"routes":[route("blue-main","main_assembly",[[320,150],[420,150],[420,380],[720,380],[720,410]])]},
            {"id":"green","label":"PRODUCT B","color":"#10a56a","source":"raw_storage","destinations":["quality"],"speed":43,"routes":[route("green-quality","quality",[[380,430],[440,430],[440,650],[1000,650],[1000,490],[1030,490]])]},
            {"id":"purple","label":"PACKAGING RETURN","color":"#d83faf","source":"shipping","destinations":["return_wash"],"speed":66,"routes":[route("purple-return","return_wash",[[1190,750],[1160,750],[1160,830],[200,830],[200,740],[250,740]])]},
            {"id":"orange","label":"FINISHED GOODS","color":"#ee7a22","source":"main_assembly","destinations":["finished_goods"],"speed":48,"routes":[route("orange-fg","finished_goods",[[970,560],[1000,560],[1000,670],[1000,700]])]},
        ],
    },
]


def path_d(points):
    return "M" + " L".join(f"{x} {y}" for x, y in points)


def arrow_polygon(points, size=20, half_width=11):
    (px, py), (x, y) = points[-2], points[-1]
    dx, dy = x - px, y - py
    length = math.hypot(dx, dy) or 1
    ux, uy = dx / length, dy / length
    bx, by = x - ux * size, y - uy * size
    nx, ny = -uy * half_width, ux * half_width
    return f"{x},{y} {bx+nx},{by+ny} {bx-nx},{by-ny}"


def svg_for(case):
    zone_shapes, zone_labels = [], []
    for z in case["zones"]:
        x, y, w, h = z["bbox"]
        zone_shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{z["color"]}" stroke="#617782" stroke-width="2"/>')
        words = z["label"].split()
        if len(z["label"]) > 20 and len(words) > 2:
            split = len(words) // 2
            lines = [" ".join(words[:split]), " ".join(words[split:])]
        else:
            lines = [z["label"]]
        cy = y + h / 2 - (len(lines)-1)*11
        tspans = "".join(f'<tspan x="{x+w/2}" dy="{0 if i==0 else 22}">{html.escape(line)}</tspan>' for i, line in enumerate(lines))
        zone_labels.append(f'<text class="zone-label" x="{x+w/2}" y="{cy}">{tspans}</text>')
    route_shapes = []
    for flow in case["flows"]:
        for r in flow["routes"]:
            d = path_d(r["waypoints"])
            route_shapes.append(f'<path d="{d}" fill="none" stroke="#fff" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>')
            route_shapes.append(f'<path d="{d}" fill="none" stroke="{flow["color"]}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>')
            route_shapes.append(f'<polygon points="{arrow_polygon(r["waypoints"])}" fill="{flow["color"]}" stroke="#fff" stroke-width="3" stroke-linejoin="round"/>')
            sx, sy = r["waypoints"][0]
            route_shapes.append(f'<circle cx="{sx}" cy="{sy}" r="8" fill="{flow["color"]}" stroke="#fff" stroke-width="3"/>')
    legend = []
    for i, flow in enumerate(case["flows"]):
        y = 170 + i * 72
        legend_arrow = arrow_polygon([[1310, y], [1368, y]], size=16, half_width=8)
        words = flow["label"].split()
        lines = [flow["label"]]
        if len(flow["label"]) > 18 and len(words) > 1:
            split = max(1, len(words) // 2)
            lines = [" ".join(words[:split]), " ".join(words[split:])]
        tspans = "".join(f'<tspan x="1390" dy="{0 if j==0 else 18}">{html.escape(line)}</tspan>' for j, line in enumerate(lines))
        legend.append(f'<line x1="1310" y1="{y}" x2="1368" y2="{y}" stroke="{flow["color"]}" stroke-width="7"/><polygon points="{legend_arrow}" fill="{flow["color"]}"/><text x="1390" y="{y+5}" class="legend">{tspans}</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#dfe5e7" stroke-width="1"/></pattern></defs>
<style>.zone-label{{font:700 19px Arial,sans-serif;fill:#253944;text-anchor:middle}}.legend{{font:700 15px Arial,sans-serif;fill:#253944}}.small{{font:600 14px Arial,sans-serif;fill:#6c7e87;letter-spacing:1px}}</style>
<rect width="1600" height="900" fill="#f5f7f6"/><rect x="35" y="35" width="1235" height="820" rx="7" fill="url(#grid)" stroke="#566f7b" stroke-width="2"/>
<text x="60" y="72" font-family="Arial,sans-serif" font-size="28" font-weight="800" fill="#183344">{html.escape(case['title'])}</text><text x="1300" y="80" font-family="Arial,sans-serif" font-size="23" font-weight="800" fill="#183344">MATERIAL FLOW</text><text x="1300" y="112" class="small">ARROWS DEFINE DIRECTION</text>
{''.join(zone_shapes)}{''.join(zone_labels)}{''.join(route_shapes)}{''.join(legend)}
<text x="1300" y="820" class="small">TEST DIFFICULTY · {case['difficulty'].upper()}</text></svg>'''


def write_case(output: Path, case: dict) -> None:
    enriched = {**case, "canvas": {"width": W, "height": H}, "evidence": []}
    for flow in case["flows"]:
        enriched["evidence"].append({"field": f"flows.{flow['id']}.direction", "basis": "arrowhead", "confidence": 1.0})
    stem = case["case_id"]
    (output / f"{stem}.svg").write_text(svg_for(case), encoding="utf-8")
    (output / f"{stem}.ground-truth.json").write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for case in CASES:
        write_case(args.output, case)
    suite = {"version": 1, "cases": [{"case_id": c["case_id"], "title": c["title"], "difficulty": c["difficulty"], "image": f"{c['case_id']}.png", "svg": f"{c['case_id']}.svg", "ground_truth": f"{c['case_id']}.ground-truth.json"} for c in CASES]}
    (args.output / "test-suite.json").write_text(json.dumps(suite, indent=2), encoding="utf-8")
    print(f"Generated {len(CASES)} test cases in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
