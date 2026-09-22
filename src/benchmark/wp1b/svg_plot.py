"""Dependency-free SVG line/point chart for the WP-1b cost-quality frontier."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from html import escape

PALETTE: tuple[str, ...] = ("#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2", "#4b5563")


@dataclass(frozen=True)
class Series:
    name: str
    points: Sequence[tuple[float, float]]
    dashed: bool = False


@dataclass(frozen=True)
class Marker:
    name: str
    x: float
    y: float


def _ticks(lo: float, hi: float, n: int = 5) -> list[float]:
    if hi <= lo:
        return [lo]
    step = (hi - lo) / n
    return [lo + i * step for i in range(n + 1)]


def line_chart(
    series: Sequence[Series],
    markers: Sequence[Marker],
    *,
    title: str,
    x_label: str,
    y_label: str,
    width: int = 760,
    height: int = 460,
) -> str:
    xs = [x for s in series for x, _ in s.points] + [m.x for m in markers]
    ys = [y for s in series for _, y in s.points] + [m.y for m in markers]
    x_lo, x_hi = min(xs), max(xs)
    y_lo, y_hi = min(ys), max(ys)
    pad_x = (x_hi - x_lo) * 0.05 or 0.001
    pad_y = (y_hi - y_lo) * 0.08 or 0.01
    x_lo, x_hi, y_lo, y_hi = x_lo - pad_x, x_hi + pad_x, max(0.0, y_lo - pad_y), y_hi + pad_y
    left, right, top, bottom = 70, 190, 40, 55
    pw, ph = width - left - right, height - top - bottom

    def sx(x: float) -> float:
        return left + (x - x_lo) / (x_hi - x_lo) * pw

    def sy(y: float) -> float:
        return top + ph - (y - y_lo) / (y_hi - y_lo) * ph

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" font-family="sans-serif" font-size="12">',
           f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
           f'<text x="{left}" y="22" font-size="14" font-weight="bold">{escape(title)}</text>']
    for t in _ticks(x_lo, x_hi):
        out.append(f'<line x1="{sx(t):.1f}" y1="{top}" x2="{sx(t):.1f}" y2="{top + ph}" stroke="#e5e7eb"/>')
        out.append(f'<text x="{sx(t):.1f}" y="{top + ph + 16}" text-anchor="middle">{t:.4f}</text>')
    for t in _ticks(y_lo, y_hi):
        out.append(f'<line x1="{left}" y1="{sy(t):.1f}" x2="{left + pw}" y2="{sy(t):.1f}" stroke="#e5e7eb"/>')
        out.append(f'<text x="{left - 6}" y="{sy(t) + 4:.1f}" text-anchor="end">{t:.3f}</text>')
    out.append(f'<rect x="{left}" y="{top}" width="{pw}" height="{ph}" fill="none" stroke="#111827"/>')
    out.append(f'<text x="{left + pw / 2:.1f}" y="{height - 12}" text-anchor="middle">{escape(x_label)}</text>')
    out.append(f'<text x="16" y="{top + ph / 2:.1f}" text-anchor="middle" '
               f'transform="rotate(-90 16 {top + ph / 2:.1f})">{escape(y_label)}</text>')
    legend_y = top + 10
    for i, s in enumerate(series):
        color = PALETTE[i % len(PALETTE)]
        pts = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in s.points)
        dash = ' stroke-dasharray="6,4"' if s.dashed else ""
        out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"{dash}/>')
        out.append(f'<line x1="{left + pw + 12}" y1="{legend_y}" x2="{left + pw + 32}" y2="{legend_y}" '
                   f'stroke="{color}" stroke-width="2"{dash}/>')
        out.append(f'<text x="{left + pw + 38}" y="{legend_y + 4}">{escape(s.name)}</text>')
        legend_y += 18
    for j, m in enumerate(markers):
        color = PALETTE[(len(series) + j) % len(PALETTE)]
        out.append(f'<circle cx="{sx(m.x):.1f}" cy="{sy(m.y):.1f}" r="5" fill="{color}" stroke="#111827"/>')
        out.append(f'<circle cx="{left + pw + 22}" cy="{legend_y}" r="5" fill="{color}" stroke="#111827"/>')
        out.append(f'<text x="{left + pw + 38}" y="{legend_y + 4}">{escape(m.name)}</text>')
        legend_y += 18
    out.append("</svg>")
    return "\n".join(out) + "\n"
