"""Deterministic static SVG fallbacks for README diagrams (no browser).

Inputs: docs/diagrams/*.mmd (Mermaid source of truth).
Outputs: docs/assets/*.svg deterministic renderings.

This is intentionally a minimal, dependency-free flow layout (nodes as boxes,
edges as polylines). It does NOT claim full Mermaid fidelity; it provides a
legible grayscale-safe static fallback and documents that the .mmd file remains
the source of truth and regeneration procedure.
"""

from __future__ import annotations

import re
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
DIAGRAMS = _PROJECT_DIR / "docs" / "diagrams"
ASSETS = _PROJECT_DIR / "docs" / "assets"

NODE_RE = re.compile(r'([A-Za-z0-9_]+)\["([^"]*)"\]')
EDGE_RE = re.compile(r"\b([A-Za-z0-9_]+)\s*-->\s*([A-Za-z0-9_]+)\b")

BOX_W = 210
BOX_H = 52
H_GAP = 60
V_GAP = 30
PAD = 30
FONT = 'font-family="Helvetica, Arial, sans-serif"'


def _parse_mmd(text: str) -> tuple[dict[str, str], list[tuple[str, str]]]:
    nodes: dict[str, str] = {}
    for name, label in NODE_RE.findall(text):
        nodes[name] = label.replace("<br/>", " ").replace("<br>", " ")
    edges = [(a, b) for a, b in EDGE_RE.findall(text)]
    return nodes, edges


def _layout(nodes, edges):
    """Simple layered layout: root(s) left, children right, deterministic order."""
    succ: dict[str, list[str]] = {}
    indeg: dict[str, int] = {n: 0 for n in nodes}
    for a, b in edges:
        succ.setdefault(a, []).append(b)
        indeg[b] = indeg.get(b, 0) + 1
    for s in succ.values():
        s.sort()

    roots = sorted(n for n in nodes if indeg[n] == 0)
    layer: dict[str, int] = {n: 0 for n in nodes}

    def assign(node: str, depth: int) -> None:
        for c in succ.get(node, []):
            layer[c] = max(layer.get(c, 0), depth + 1)
            assign(c, depth + 1)

    for r in roots:
        assign(r, 0)
    # add unconnected / not-yet-assigned in deterministic order
    for n in sorted(nodes):
        if n not in layer:
            layer[n] = max(layer.values()) + 1 if layer else 0
    # deterministic BFS-like ordering within layers
    queue = list(roots)
    seen = set(roots)
    ordered = list(roots)
    while queue:
        cur = queue.pop(0)
        for c in sorted(succ.get(cur, [])):
            if c not in seen:
                seen.add(c)
                ordered.append(c)
                queue.append(c)
    for n in sorted(nodes):
        if n not in seen:
            ordered.append(n)
    return ordered, layer


def _render_svg(title: str, nodes, edges) -> str:
    ordered, layer = _layout(nodes, edges)
    # column x by layer; row y by deterministic order within layer
    col: dict[str, int] = {}
    row_in_layer: dict[int, int] = {}
    for n in ordered:
        lv = layer[n]
        col[n] = lv
        row_in_layer[lv] = row_in_layer.get(lv, 0) + 1
    max_col = max(col.values()) if col else 0
    widths = {lv: row_in_layer.get(lv, 0) for lv in set(col.values())}
    max_rows = max(widths.values()) if widths else 0
    total_w = PAD * 2 + (max_col + 1) * BOX_W + max_col * H_GAP
    total_h = PAD * 2 + (max_rows + 1) * BOX_H + max_rows * V_GAP

    # deterministic per-layer slot assignment
    layer_slots: dict[int, list[str]] = {}
    for n in ordered:
        layer_slots.setdefault(layer[n], []).append(n)
    pos: dict[str, tuple[float, float]] = {}
    for lv, ns in layer_slots.items():
        count = len(ns)
        for i, n in enumerate(ns):
            y = PAD + i * (BOX_H + V_GAP) + (total_h - 2 * PAD - count * BOX_H - (count - 1) * V_GAP) / 2
            x = PAD + lv * (BOX_W + H_GAP)
            pos[n] = (x, y)

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}">',
        f'<rect width="{total_w}" height="{total_h}" fill="#ffffff"/>',
        f'<text x="{PAD}" y="{PAD - 6}" font-size="13" fill="#333333" {FONT}>'
        f'{title}</text>',
    ]
    for a, b in edges:
        if a not in pos or b not in pos:
            continue
        x1, y1 = pos[a][0] + BOX_W, pos[a][1] + BOX_H / 2
        x2, y2 = pos[b][0], pos[b][1] + BOX_H / 2
        mid = (x1 + x2) / 2
        parts.append(
            f'<polyline points="{x1},{y1} {mid},{y1} {mid},{y2} {x2},{y2}" '
            f'fill="none" stroke="#666666" stroke-width="1.5"/>'
        )
        # arrow head
        parts.append(
            f'<polygon points="{x2 - 7},{y2 - 4} {x2 - 7},{y2 + 4} {x2},{y2}" '
            f'fill="#666666"/>'
        )
    for n, (x, y) in pos.items():
        label = nodes[n]
        parts.append(
            f'<rect x="{x}" y="{y}" width="{BOX_W}" height="{BOX_H}" rx="6" '
            f'fill="#f2f4f7" stroke="#444444" stroke-width="1.5"/>'
        )
        lines = label.split(" ") if label else [""]
        # wrap into up to 3 lines
        wrapped: list[str] = []
        for word in (label.split() if label else []):
            if wrapped and len(wrapped[-1]) + 1 + len(word) <= 26:
                wrapped[-1] += " " + word
            else:
                wrapped.append(word)
        lines = (wrapped[:3] or [""])
        n_lines = len(lines)
        for i, ln in enumerate(lines):
            ty = y + BOX_H / 2 - (n_lines - 1) * 8 + i * 16 + 4
            parts.append(
                f'<text x="{x + BOX_W / 2}" y="{ty}" text-anchor="middle" font-size="12" '
                f'fill="#111111" {FONT}>{ln}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    DIAGRAMS.mkdir(parents=True, exist_ok=True)
    for mmd in sorted(DIAGRAMS.glob("*.mmd")):
        nodes, edges = _parse_mmd(mmd.read_text(encoding="utf-8"))
        svg = _render_svg(mmd.stem.replace("_", " ").title(), nodes, edges)
        out = ASSETS / f"{mmd.stem}.svg"
        out.write_text(svg, encoding="utf-8")
        print(f"{mmd.name}: nodes={len(nodes)} edges={len(edges)} -> {out.name} ({len(svg)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
