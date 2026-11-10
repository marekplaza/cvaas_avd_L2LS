#!/usr/bin/env python3
"""Topology diagram in the style of the containerlab VS Code TopoViewer export.

Node positions come from clab/topology.clab.yml.annotations.json (saved by the
TopoViewer), links and icons from clab/topology.clab.yml. Re-run after moving
nodes in the TopoViewer:

    python3 tools/gen_clab_svg.py      # -> docs/topology-clab.svg
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TOPO = ROOT / "clab" / "topology.clab.yml"
ANNOT = ROOT / "clab" / "topology.clab.yml.annotations.json"
OUT = ROOT / "docs" / "topology-clab.svg"

HALF = 20  # icons are 40 x 40, positions are the top-left corner
EDGE = "#00df2b"
FONT = "-apple-system, system-ui, Segoe UI, Helvetica, Arial, sans-serif"
HEX = ("M29 6.6Q32 4.9 35 6.6L53 17Q56 18.7 56 22.2V41.8Q56 45.3 53 47L35 57.4Q32 59.1 29 57.4"
       "L11 47Q8 45.3 8 41.8V22.2Q8 18.7 11 17Z")
GLYPH = {
    "spine": '<path d="M20 26H44M24 22L20 26L24 30M40 22L44 26L40 30M20 38H44M24 34L20 38L24 42M40 34L44 38L40 42"/>',
    "leaf": '<path d="M28 29L21 22M21 28V22H27M36 29L43 22M37 22H43V28M21 36H43M21 42H43"/>',
    "firewall": '<rect x="20" y="21" width="24" height="22" rx="2.5"/>'
                '<path d="M20 28.3H44M20 35.7H44M32 21V28.3M26 28.3V35.7M38 28.3V35.7M32 35.7V43"/>',
}


def clip(cx: float, cy: float, dx: float, dy: float) -> tuple[float, float]:
    """Point where the ray from the node centre along (dx, dy) leaves the icon box."""
    t = min(HALF / abs(dx) if dx else math.inf, HALF / abs(dy) if dy else math.inf)
    return cx + dx * t, cy + dy * t


def label(x: float, y: float, text: str) -> str:
    w = 6.2 * len(text) + 2
    return (f'<rect x="{x - w / 2:.1f}" y="{y - 6:.1f}" width="{w:.1f}" height="12" rx="4" fill="#1e1e1e"/>'
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="10" font-family="{FONT}" dominant-baseline="central" '
            f'text-anchor="middle" fill="#d4d4d4">{text}</text>')


def main() -> None:
    topo = yaml.safe_load(TOPO.read_text())["topology"]
    pos = {n["id"]: n for n in json.loads(ANNOT.read_text())["nodeAnnotations"]}
    centre = {h: (n["position"]["x"] + HALF, n["position"]["y"] + HALF) for h, n in pos.items()}
    icon = {h: (topo["nodes"][h].get("labels") or {}).get("graph-icon", pos[h].get("icon", "leaf")) for h in pos}

    links = [tuple(e.split(":") for e in l["endpoints"]) for l in topo["links"]]
    pairs: dict[frozenset, list] = defaultdict(list)
    for a, b in links:
        pairs[frozenset((a[0], b[0]))].append((a, b))

    edges, labels = [], []
    for group in pairs.values():
        for k, ((ha, ia), (hb, ib)) in enumerate(group):
            (ax, ay), (bx, by) = centre[ha], centre[hb]
            dx, dy = bx - ax, by - ay
            if len(group) == 1:
                x1, y1 = clip(ax, ay, dx, dy)
                x2, y2 = clip(bx, by, -dx, -dy)
                edges.append(f'<path d="M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}"/>')
                ln = math.hypot(x2 - x1, y2 - y1) or 1
                ux, uy = (x2 - x1) / ln, (y2 - y1) / ln
                labels += [label(x1 + ux * 18, y1 + uy * 18, ia), label(x2 - ux * 18, y2 - uy * 18, ib)]
            else:
                # parallel links (MLAG peer-link): bow them apart
                ln = math.hypot(dx, dy) or 1
                nx, ny = -dy / ln, dx / ln
                off = (k - (len(group) - 1) / 2) * 40
                x1, y1 = clip(ax, ay, dx, dy)
                x2, y2 = clip(bx, by, -dx, -dy)
                mx, my = (x1 + x2) / 2 + nx * off, (y1 + y2) / 2 + ny * off
                edges.append(f'<path d="M {x1:.1f} {y1:.1f} Q {mx:.1f} {my:.1f} {x2:.1f} {y2:.1f}"/>')
                lx, ly = (x1 + 2 * mx + x2) / 4, (y1 + 2 * my + y2) / 4
                labels.append(label(lx, ly - 4, ia if ia == ib else f"{ia}/{ib}"))

    nodes = []
    for h, (cx, cy) in centre.items():
        name = h.replace("marpla-", "")
        w = 6.4 * len(name) + 12
        nodes.append(
            f'<svg x="{cx - HALF}" y="{cy - HALF}" width="40" height="40" viewBox="4 4 56 56">'
            f'<path d="{HEX}" fill="#1e1e1e" stroke="#ddf8ff" stroke-width="2.4" stroke-linejoin="round"/>'
            f'<g fill="none" stroke="#00c9ff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
            f'{GLYPH.get(icon[h], GLYPH["leaf"])}</g></svg>'
            f'<rect x="{cx - w / 2:.1f}" y="{cy + 22}" width="{w:.1f}" height="18.8" rx="3" fill="rgba(0,0,0,0.75)"/>'
            f'<text x="{cx}" y="{cy + 31.4}" font-size="11.2" font-weight="500" font-family="{FONT}" '
            f'dominant-baseline="central" text-anchor="middle" fill="#f5f5f5">{name}</text>')

    xs = [c[0] for c in centre.values()]
    ys = [c[1] for c in centre.values()]
    x0, y0, x1, y1 = min(xs) - 90, min(ys) - 50, max(xs) + 90, max(ys) + 70
    w, h = x1 - x0, y1 - y0
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{x0} {y0} {w} {h}">'
           f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#1e1e1e"/>'
           f'<g fill="none" stroke="{EDGE}" stroke-width="4" opacity="0.5">{"".join(edges)}</g>'
           f'{"".join(labels)}{"".join(nodes)}</svg>\n')
    OUT.write_text(svg)
    print(f"{OUT.relative_to(ROOT)}: {len(centre)} nodes, {len(links)} links")


if __name__ == "__main__":
    main()
