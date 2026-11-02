#!/usr/bin/env python3
"""LINEA 9×12 — генератор архитектурного альбома: SVG-чертежи и HTML-документ."""

from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DRAW = ROOT / "drawings"
DRAW.mkdir(exist_ok=True)

INK = "#1a1a1a"
WALL = "#1b1b1b"
GLASS = "#8aa7b8"
WOOD = "#c4a574"
GRASS = "#b8c8aa"
PAVE = "#d5cfc4"
CONC = "#c9c4ba"
FURN = "#ddd6cc"
FURN_S = "#8a8074"
PAPER = "#f6f2ea"
DIM = "#3d3d3d"
ACCENT = "#6e4a32"
WATER = "#9bb8c4"
HATCH = "#cfc8bb"


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


class CAD:
    """Чертежный лист: метры, начало в юго-западе, ось Y на север (в SVG переворачивается)."""

    def __init__(self, width_px: int, height_px: int, scale: float, origin_x: float, origin_y: float):
        self.W = width_px
        self.H = height_px
        self.s = scale
        self.ox = origin_x
        self.oy = origin_y
        self.parts: list[str] = []

    def px(self, x: float, y: float) -> tuple[float, float]:
        return self.ox + x * self.s, self.H - (self.oy + y * self.s)

    def add(self, raw: str) -> None:
        self.parts.append(raw)

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=1, opacity=1, extra="") -> None:
        x0, y1 = self.px(x, y)
        _, y0 = self.px(x, y + h)
        self.add(
            f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{w*self.s:.2f}" height="{h*self.s:.2f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}" {extra}/>'
        )

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1, dash=None, cap="butt") -> None:
        a = self.px(x1, y1)
        b = self.px(x2, y2)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" '
            f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="{cap}"{dash_attr}/>'
        )

    def poly(self, pts, fill="none", stroke=INK, sw=1, close=True) -> None:
        d = " ".join(f"{self.px(x,y)[0]:.2f},{self.px(x,y)[1]:.2f}" for x, y in pts)
        extra = " Z" if close else ""
        self.add(
            f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            if close
            else f'<polyline points="{d}" fill="none" stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def circle(self, x, y, r, fill="none", stroke=INK, sw=1) -> None:
        cx, cy = self.px(x, y)
        self.add(
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r*self.s:.2f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def text(self, x, y, label, size=11, fill=INK, anchor="middle", weight=500, angle=0, family="IBM Plex Sans, Segoe UI, sans-serif") -> None:
        px, py = self.px(x, y)
        tr = f' transform="rotate({-angle} {px:.2f} {py:.2f})"' if angle else ""
        self.add(
            f'<text x="{px:.2f}" y="{py:.2f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" font-family="{family}" '
            f'dominant-baseline="middle"{tr}>{esc(label)}</text>'
        )

    def path(self, d, fill="none", stroke=INK, sw=1) -> None:
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def wall(self, x, y, w, h) -> None:
        self.rect(x, y, w, h, fill=WALL, stroke="none")

    def opening(self, x, y, w, h) -> None:
        self.rect(x, y, w, h, fill=PAPER, stroke="none")

    def window_h(self, x, y, length, thick=0.20) -> None:
        self.opening(x, y, length, thick)
        self.line(x, y + thick * 0.35, x + length, y + thick * 0.35, stroke=GLASS, sw=1.6)
        self.line(x, y + thick * 0.65, x + length, y + thick * 0.65, stroke=GLASS, sw=1.6)
        self.line(x, y, x, y + thick, sw=1.2)
        self.line(x + length, y, x + length, y + thick, sw=1.2)

    def window_v(self, x, y, length, thick=0.20) -> None:
        self.opening(x, y, thick, length)
        self.line(x + thick * 0.35, y, x + thick * 0.35, y + length, stroke=GLASS, sw=1.6)
        self.line(x + thick * 0.65, y, x + thick * 0.65, y + length, stroke=GLASS, sw=1.6)
        self.line(x, y, x + thick, y, sw=1.2)
        self.line(x, y + length, x + thick, y + length, sw=1.2)

    def door(self, hinge_x, hinge_y, width, closed_angle_deg, swing_dir=1, sw=1.1) -> None:
        """closed_angle: 0 east, 90 north. swing_dir +1 = CCW."""
        a0 = math.radians(closed_angle_deg)
        a1 = math.radians(closed_angle_deg + 90 * swing_dir)
        x2 = hinge_x + width * math.cos(a1)
        y2 = hinge_y + width * math.sin(a1)
        self.line(hinge_x, hinge_y, x2, y2, sw=sw)
        p0 = self.px(hinge_x, hinge_y)
        p1 = self.px(hinge_x + width * math.cos(a0), hinge_y + width * math.sin(a0))
        p2 = self.px(x2, y2)
        r = width * self.s
        large = 0
        sweep = 0 if swing_dir > 0 else 1
        # SVG y is flipped, invert sweep
        sweep = 1 - sweep
        self.add(
            f'<path d="M {p1[0]:.2f} {p1[1]:.2f} A {r:.2f} {r:.2f} 0 {large} {sweep} {p2[0]:.2f} {p2[1]:.2f}" '
            f'fill="none" stroke="{INK}" stroke-width="0.8" stroke-dasharray="2 2"/>'
        )

    def dim_h(self, x1, x2, y, label, tick=0.18, offset_text=0.22) -> None:
        if x2 < x1:
            x1, x2 = x2, x1
        self.line(x1, y, x2, y, stroke=DIM, sw=0.8)
        self.line(x1, y - tick / 2, x1, y + tick / 2, stroke=DIM, sw=0.8)
        self.line(x2, y - tick / 2, x2, y + tick / 2, stroke=DIM, sw=0.8)
        self.line(x1 - tick * 0.4, y - tick * 0.4, x1 + tick * 0.4, y + tick * 0.4, stroke=DIM, sw=0.7)
        self.line(x2 - tick * 0.4, y - tick * 0.4, x2 + tick * 0.4, y + tick * 0.4, stroke=DIM, sw=0.7)
        self.text((x1 + x2) / 2, y + offset_text, label, size=10, fill=DIM)

    def dim_v(self, y1, y2, x, label, tick=0.18, offset_text=0.28) -> None:
        if y2 < y1:
            y1, y2 = y2, y1
        self.line(x, y1, x, y2, stroke=DIM, sw=0.8)
        self.line(x - tick / 2, y1, x + tick / 2, y1, stroke=DIM, sw=0.8)
        self.line(x - tick / 2, y2, x + tick / 2, y2, stroke=DIM, sw=0.8)
        self.line(x - tick * 0.4, y1 - tick * 0.4, x + tick * 0.4, y1 + tick * 0.4, stroke=DIM, sw=0.7)
        self.line(x - tick * 0.4, y2 - tick * 0.4, x + tick * 0.4, y2 + tick * 0.4, stroke=DIM, sw=0.7)
        self.text(x + offset_text, (y1 + y2) / 2, label, size=10, fill=DIM, angle=90)

    def north(self, x, y, size=1.4) -> None:
        self.poly(
            [(x, y + size), (x - size * 0.28, y - size * 0.15), (x, y + size * 0.15), (x + size * 0.28, y - size * 0.15)],
            fill=INK,
            stroke="none",
        )
        self.text(x, y + size + 0.38, "С", size=13, weight=600)

    def scalebar(self, x, y, meters=5) -> None:
        for i in range(meters):
            fill = INK if i % 2 == 0 else "white"
            self.rect(x + i, y, 1, 0.22, fill=fill, stroke=INK, sw=0.7)
        self.line(x, y, x + meters, y, sw=0.7)
        self.text(x, y - 0.28, "0", size=9, fill=DIM, anchor="middle")
        self.text(x + meters, y - 0.28, f"{meters} м", size=9, fill=DIM, anchor="middle")
        self.text(x + meters / 2, y + 0.48, "масштаб", size=9, fill=DIM)

    def room_label(self, x, y, code, name, area) -> None:
        self.text(x, y + 0.42, code, size=12, weight=600)
        self.text(x, y, name, size=11)
        self.text(x, y - 0.38, area, size=10, fill=DIM)

    def sofa(self, x, y, w, d, rot=0) -> None:
        self.rect(x, y, w, d, fill=FURN, stroke=FURN_S, sw=0.8)
        self.rect(x, y + d * 0.72, w, d * 0.28, fill="#d0c8be", stroke=FURN_S, sw=0.7)

    def table(self, x, y, w, d) -> None:
        self.rect(x, y, w, d, fill="#e8dfd2", stroke=FURN_S, sw=0.8)
        for cx, cy in ((x + 0.12, y + 0.12), (x + w - 0.22, y + 0.12), (x + 0.12, y + d - 0.22), (x + w - 0.22, y + d - 0.22)):
            self.rect(cx, cy, 0.1, 0.1, fill=FURN_S, stroke="none")

    def bed(self, x, y, w, d) -> None:
        self.rect(x, y, w, d, fill="#e6e1d8", stroke=FURN_S, sw=0.8)
        self.rect(x + 0.08, y + d - 0.55, w * 0.42, 0.42, fill="#f2eee8", stroke=FURN_S, sw=0.6)
        self.rect(x + w * 0.50, y + d - 0.55, w * 0.42, 0.42, fill="#f2eee8", stroke=FURN_S, sw=0.6)

    def wc(self, x, y) -> None:
        self.rect(x, y, 0.38, 0.52, fill="white", stroke=INK, sw=0.8)
        self.circle(x + 0.19, y + 0.38, 0.13, stroke=INK, sw=0.8)
        self.rect(x - 0.04, y + 0.48, 0.46, 0.12, fill="white", stroke=INK, sw=0.8)

    def basin(self, x, y, w=0.6, d=0.42) -> None:
        self.rect(x, y, w, d, fill="white", stroke=INK, sw=0.8)
        self.ellipse_like(x + w / 2, y + d / 2, w * 0.32, d * 0.28)

    def ellipse_like(self, x, y, rx, ry) -> None:
        cx, cy = self.px(x, y)
        self.add(
            f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx*self.s:.2f}" ry="{ry*self.s:.2f}" '
            f'fill="none" stroke="{INK}" stroke-width="0.8"/>'
        )

    def car(self, x, y, w=4.4, d=1.85) -> None:
        self.rect(x, y, w, d, fill="#c5cdd4", stroke="#6a737a", sw=0.9)
        self.rect(x + w * 0.12, y + d * 0.18, w * 0.76, d * 0.45, fill="#dfe5ea", stroke="#6a737a", sw=0.6)

    def tree(self, x, y, r=1.3) -> None:
        self.circle(x, y, r, fill="#9cba90", stroke="#6e8b63", sw=0.8)
        self.circle(x, y, 0.18, fill="#6a5340", stroke="none")

    def finish(self, title: str, sheet: str, scale_label: str) -> str:
        header = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.W} {self.H}" width="100%" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>
<rect width="{self.W}" height="{self.H}" fill="{PAPER}"/>
<rect x="18" y="18" width="{self.W-36}" height="{self.H-36}" fill="none" stroke="{INK}" stroke-width="1.4"/>
<rect x="22" y="22" width="{self.W-44}" height="{self.H-44}" fill="none" stroke="{INK}" stroke-width="0.5"/>
<rect x="22" y="{self.H-70}" width="{self.W-44}" height="48" fill="none" stroke="{INK}" stroke-width="0.6"/>
<text x="36" y="{self.H-42}" font-size="13" font-weight="600" font-family="IBM Plex Sans, Segoe UI, sans-serif" fill="{INK}">LINEA 9×12</text>
<text x="36" y="{self.H-24}" font-size="11" font-family="IBM Plex Sans, Segoe UI, sans-serif" fill="{DIM}">{esc(title)}</text>
<text x="{self.W/2:.0f}" y="{self.H-34}" font-size="11" text-anchor="middle" font-family="IBM Plex Sans, Segoe UI, sans-serif" fill="{DIM}">{esc(scale_label)}</text>
<text x="{self.W-36}" y="{self.H-34}" font-size="12" text-anchor="end" font-weight="600" font-family="IBM Plex Sans, Segoe UI, sans-serif" fill="{INK}">{esc(sheet)}</text>
"""
        return header + "\n".join(self.parts) + "\n</svg>\n"


def draw_site() -> str:
    cad = CAD(820, 1320, 22, 120, 250)
    # street
    cad.rect(-3.0, -6.8, 23, 3.6, fill="#bfbfbf", stroke="none")
    cad.rect(-3.0, -3.55, 23, 0.4, fill="#efefef", stroke="none")
    cad.text(8.5, -4.7, "УЛИЦА  (ЮГ)", size=12, fill=DIM)
    # plot
    cad.rect(0, 0, 17, 35, fill="#e7eadf", stroke=INK, sw=1.6)
    # lawn
    cad.rect(0.4, 18.2, 16.2, 16.4, fill=GRASS, stroke="none")
    # driveway (east) + front lawn
    cad.rect(12.15, 0, 4.35, 18.0, fill=PAVE, stroke="none")
    cad.rect(0.4, 0.4, 11.5, 5.4, fill=GRASS, stroke="none")
    # house
    cad.rect(3.0, 6.0, 9.0, 12.0, fill="#f3efe6", stroke=INK, sw=1.8)
    cad.rect(3.0, 12.0, 9.0, 6.0, fill="#d9d3c8", stroke="none", opacity=0.35)  # 2nd floor hint
    cad.rect(3.05, 12.05, 8.9, 5.9, fill="none", stroke=ACCENT, sw=0.8, extra='stroke-dasharray="4 3"')
    # terrace
    cad.rect(3.0, 18.0, 9.0, 4.0, fill=WOOD, stroke=INK, sw=1.0)
    for i in range(1, 9):
        cad.line(3.0 + i, 18.0, 3.0 + i, 22.0, stroke="#b08d5a", sw=0.4)
    # carport — detached, ~1,5 м зазор от восточной стены дома
    cad.rect(13.50, 8.0, 3.2, 6.0, fill="none", stroke=INK, sw=1.3)
    cad.line(13.50, 8.0, 16.70, 14.0, stroke=INK, sw=0.5, dash="3 3")
    cad.line(16.70, 8.0, 13.50, 14.0, stroke=INK, sw=0.5, dash="3 3")
    cad.text(15.1, 14.55, "НАВЕС", size=10, fill=DIM)
    cad.text(15.1, 13.95, "3,2 × 6,0", size=9, fill=DIM)
    cad.dim_h(12.0, 13.5, 7.35, "1,50")
    # pool 6.00 × 3.00 in front-left (fits in 6 m street setback)
    cad.rect(0.7, 1.15, 6.6, 3.7, fill="#d9d4c8", stroke=INK, sw=0.7)
    cad.rect(0.95, 1.4, 6.00, 3.00, fill="#6aa0b8", stroke="#4d7a8c", sw=0.8)
    cad.rect(0.95, 1.4, 6.00, 3.00, fill="none", stroke="#cfe4ee", sw=0.4)
    cad.rect(0.95, 4.4, 6.00, 1.6, fill=WOOD, stroke=INK, sw=0.7)
    cad.text(3.95, 2.9, "БАССЕЙН", size=10, weight=600, fill="white")
    cad.text(3.95, 2.35, "6,00 × 3,00", size=9, fill="white")
    cad.dim_h(0.95, 6.95, 5.05, "6,00")
    cad.car(13.85, 8.55, w=1.90, d=4.80)
    # path to door
    cad.rect(7.7, 0.4, 1.35, 5.6, fill=CONC, stroke="none")
    # entrance mark
    cad.rect(6.7, 6.0, 1.1, 0.12, fill=INK, stroke="none")
    cad.text(7.25, 6.55, "ВХОД", size=9, weight=600)
    # garden elements
    cad.rect(3.4, 22.4, 4.2, 0.35, fill="#6d8b5e", stroke="none")
    cad.rect(12.6, 24.0, 3.6, 2.4, fill="#c5d0b0", stroke=INK, sw=0.6)
    cad.text(14.4, 25.2, "ОГОРОД", size=9, fill=DIM)
    cad.rect(12.8, 28.5, 3.2, 2.8, fill="#d7c7a8", stroke=INK, sw=0.6)
    cad.text(14.4, 29.9, "ДЕТИ / ИГРА", size=9, fill=DIM)
    cad.rect(3.8, 26.4, 2.4, 1.6, fill="#8a6a45", stroke=INK, sw=0.7)
    cad.text(5.0, 27.2, "МАНГАЛ", size=9, fill="white")
    cad.tree(1.5, 21.5, 1.1)
    cad.tree(1.6, 32.6, 1.35)
    cad.tree(8.8, 32.8, 1.5)
    cad.tree(15.4, 32.4, 1.2)
    cad.tree(15.5, 20.6, 1.0)
    cad.rect(0.25, 18.4, 0.55, 16.2, fill="#7f9a6e", stroke="none")
    cad.rect(16.2, 18.4, 0.55, 16.2, fill="#7f9a6e", stroke="none")
    cad.rect(0.25, 34.2, 16.5, 0.55, fill="#7f9a6e", stroke="none")
    # house label
    cad.room_label(7.5, 12.2, "ДОМ", "9,00 × 12,00", "S застр. 108 м²")
    cad.text(7.5, 16.4, "2 ЭТАЖА, H = 7,35 м", size=10, fill=DIM)
    cad.text(7.5, 20.0, "ТЕРРАСА 9,00 × 4,00", size=10, fill=INK)
    # setback dims
    cad.dim_h(0, 3, -0.7, "3,00")
    cad.dim_h(3, 12, -0.7, "9,00")
    cad.dim_h(12, 17, -0.7, "5,00")
    cad.dim_h(0, 17, -1.55, "17,00 — ширина участка")
    cad.dim_v(0, 6, -0.85, "6,00")
    cad.dim_v(6, 18, -0.85, "12,00")
    cad.dim_v(18, 35, -0.85, "17,00")
    cad.dim_v(0, 35, -1.7, "35,00 — длина участка")
    cad.dim_h(3, 12, 35.85, "9,00")
    cad.dim_h(3, 12, 22.55, "4,00", offset_text=0.32)
    cad.north(15.6, 4.6, 1.6)
    cad.scalebar(11.8, 36.9, 5)
    # legend boxes
    cad.rect(0.2, 38.2, 0.55, 0.4, fill="#f3efe6", stroke=INK, sw=0.6)
    cad.text(1.9, 38.4, "дом", size=9, fill=DIM, anchor="start")
    cad.rect(3.6, 38.2, 0.55, 0.4, fill=WOOD, stroke=INK, sw=0.6)
    cad.text(5.3, 38.4, "терраса", size=9, fill=DIM, anchor="start")
    cad.rect(7.4, 38.2, 0.55, 0.4, fill=PAVE, stroke=INK, sw=0.6)
    cad.text(9.3, 38.4, "проезд", size=9, fill=DIM, anchor="start")
    cad.rect(11.2, 38.2, 0.55, 0.4, fill=GRASS, stroke=INK, sw=0.6)
    cad.text(13.0, 38.4, "газон", size=9, fill=DIM, anchor="start")
    cad.rect(14.6, 38.2, 0.55, 0.4, fill="#6aa0b8", stroke=INK, sw=0.6)
    cad.text(16.4, 38.4, "бассейн", size=9, fill=DIM, anchor="start")
    return cad.finish("Генплан земельного участка 17 × 35 м", "А-01", "М 1:200")


def walls_l1(cad: CAD) -> None:
    # exterior 200
    cad.wall(0.00, 0.00, 9.00, 0.20)
    cad.wall(0.00, 11.80, 9.00, 0.20)
    cad.wall(0.00, 0.20, 0.20, 11.60)
    cad.wall(8.80, 0.20, 0.20, 11.60)
    # interior
    cad.wall(3.20, 0.20, 0.12, 3.48)          # office | tambour+wc
    cad.wall(5.08, 0.20, 0.12, 5.00)          # tambour/wc/living | hall
    cad.wall(3.32, 2.00, 1.76, 0.12)          # tambour | wc
    cad.wall(0.20, 3.68, 4.88, 0.12)          # office/wc | living
    cad.wall(5.08, 5.20, 3.72, 0.12)          # hall | pantry/tech
    cad.wall(5.20, 5.32, 0.12, 6.48)          # living | kitchen stack  (upper)
    cad.wall(6.90, 5.32, 0.12, 1.56)          # pantry | tech
    cad.wall(5.20, 6.88, 3.60, 0.12)          # pantry/tech | kitchen
    # openings
    cad.opening(3.70, 0.00, 1.10, 0.20)       # entrance
    cad.opening(5.08, 0.40, 0.12, 0.90)       # tambour -> hall
    cad.opening(3.20, 0.45, 0.12, 0.90)       # office -> tambour
    cad.opening(5.08, 2.35, 0.12, 0.85)       # wc -> hall
    cad.opening(5.08, 3.92, 0.12, 1.16)       # living -> hall
    cad.opening(5.20, 8.70, 0.12, 2.60)       # living -> kitchen, проём 2,60
    cad.opening(5.45, 6.88, 0.90, 0.12)       # kitchen -> pantry
    cad.opening(5.40, 5.20, 0.90, 0.12)       # hall -> pantry
    cad.opening(7.25, 5.20, 0.90, 0.12)       # hall -> tech
    cad.opening(8.80, 5.55, 0.20, 0.90)       # tech outdoor


def windows_l1(cad: CAD) -> None:
    cad.opening(3.70, 0.00, 1.10, 0.20)
    cad.window_h(0.70, 0.00, 1.80, 0.20)      # office south
    cad.window_h(6.40, 0.00, 1.40, 0.20)      # hall south
    cad.window_h(0.40, 11.80, 4.60, 0.20)     # living north — раздвижные
    cad.window_h(5.30, 11.80, 3.30, 0.20)     # kitchen north — раздвижные
    cad.window_v(0.00, 4.40, 2.20, 0.20)      # living west
    cad.window_v(0.00, 8.40, 2.60, 0.20)      # living west garden
    # камин на западной стене между окнами — как на визуализации гостиной
    cad.rect(0.20, 6.70, 0.28, 1.55, fill="#3a3a3a", stroke=INK, sw=0.6)
    cad.window_v(8.80, 8.20, 2.40, 0.20)      # kitchen east
    cad.window_v(8.80, 1.40, 1.40, 0.20)      # hall east, punched
    cad.opening(8.80, 5.55, 0.20, 0.90)


def doors_l1(cad: CAD) -> None:
    cad.door(3.70, 0.00, 1.10, 0, 1)          # entrance swings east inside? hinge west, closed along +x, swing CCW inside
    cad.door(5.08, 0.40, 0.90, 90, 1)         # tambour to hall
    cad.door(3.32, 0.45, 0.90, 90, -1)        # office
    cad.door(5.20, 2.35, 0.85, 90, -1)        # wc
    cad.door(5.45, 7.00, 0.90, 0, 1)          # pantry from kitchen
    cad.door(5.40, 5.32, 0.90, 0, 1)          # pantry from hall
    cad.door(7.25, 5.32, 0.90, 0, 1)          # tech


def furniture_l1(cad: CAD) -> None:
    cad.sofa(0.55, 8.6, 2.9, 0.95)
    cad.rect(1.2, 7.7, 1.3, 0.7, fill="#e8dfd2", stroke=FURN_S, sw=0.7)
    cad.table(0.7, 5.15, 2.2, 1.05)
    # kitchen counters
    cad.rect(7.70, 7.12, 1.10, 4.56, fill="#d9d0c4", stroke=FURN_S, sw=0.8)
    cad.rect(5.35, 10.85, 2.35, 0.83, fill="#d9d0c4", stroke=FURN_S, sw=0.8)
    cad.rect(6.15, 8.35, 2.4, 0.95, fill="#cfc4b4", stroke=FURN_S, sw=0.9)  # island
    cad.text(7.35, 8.82, "остров", size=8, fill=DIM)
    cad.rect(0.45, 0.45, 1.6, 0.55, fill=FURN, stroke=FURN_S, sw=0.7)  # office desk
    cad.rect(2.35, 0.50, 0.55, 0.55, fill=FURN, stroke=FURN_S, sw=0.7)
    cad.wc(3.50, 2.28)
    cad.basin(4.35, 3.22, 0.62, 0.38)
    cad.rect(5.40, 5.50, 1.30, 1.20, fill="#efe8dc", stroke=FURN_S, sw=0.7)
    cad.rect(7.20, 5.50, 1.40, 1.20, fill="#d5d5d5", stroke=FURN_S, sw=0.7)
    cad.text(7.90, 6.10, "ИТП", size=8, fill=DIM)


def stair(cad: CAD, dashed_upper=False) -> None:
    # L-stair SE
    x0, y0 = 6.70, 0.45
    # flight 1 9 treads north, width 1.00
    n = 9
    run = 0.28
    for i in range(n):
        cad.rect(7.70, y0 + i * run, 1.10, run, fill="#ece6dc" if not dashed_upper else "none", stroke=INK, sw=0.6)
    cad.rect(6.70, y0 + n * run, 2.10, 1.00, fill="#ece6dc" if not dashed_upper else "none", stroke=INK, sw=0.8)  # landing
    for i in range(7):
        cad.rect(6.70 + i * 0.28, y0 + n * run, 0.28, 1.00, fill="#e4ddd2" if not dashed_upper else "none", stroke=INK, sw=0.6)
    cad.line(8.25, 0.55, 8.25, 2.85, sw=1.0)
    cad.poly([(8.15, 2.55), (8.25, 2.90), (8.35, 2.55)], fill=INK, stroke="none")
    cad.text(8.25, 1.6, "ВВЕРХ", size=8, fill=DIM, angle=90)


def draw_floor1() -> str:
    cad = CAD(960, 1180, 56, 155, 195)
    cad.rect(-0.15, -0.15, 9.3, 12.3, fill="#efebe3", stroke="none")
    walls_l1(cad)
    windows_l1(cad)
    doors_l1(cad)
    furniture_l1(cad)
    stair(cad)
    # terrace ghost
    cad.rect(0.0, 12.0, 9.0, 0.35, fill=WOOD, stroke=INK, sw=0.6)
    cad.text(4.5, 12.55, "ТЕРРАСА", size=9, fill=DIM)
    cad.room_label(4.45, 1.05, "01", "Тамбур", "3,2 м²")
    cad.room_label(1.70, 1.90, "04", "Кабинет", "10,4 м²")
    cad.room_label(4.20, 2.90, "03", "С/у", "2,8 м²")
    cad.room_label(7.00, 4.35, "02", "Холл / лестница", "18,0 м²")
    cad.room_label(2.55, 7.3, "05", "Гостиная — столовая", "39,0 м²")
    cad.room_label(7.00, 10.0, "06", "Кухня", "17,3 м²")
    cad.text(5.50, 9.95, "проём 2,60", size=8, fill=DIM, angle=90)
    cad.room_label(6.05, 6.05, "07", "Кладовая", "2,7 м²")
    cad.room_label(7.95, 6.05, "08", "Котельная", "2,8 м²")
    cad.dim_h(0, 9, -0.85, "9,00")
    cad.dim_h(0.20, 3.20, -0.45, "3,00")
    cad.dim_h(3.32, 5.08, -0.45, "1,76")
    cad.dim_h(5.20, 8.80, -0.45, "3,60")
    cad.dim_v(0, 12, -0.85, "12,00")
    cad.dim_v(0, 3.80, 9.55, "3,80")
    cad.dim_v(3.80, 12.00, 9.55, "8,20")
    cad.north(10.6, 11.2, 1.1)
    cad.scalebar(10.0, 0.2, 3)
    # section mark
    cad.text(2.4, 12.9, "1", size=11, weight=600, fill="#8b2942")
    cad.line(2.4, -0.2, 2.4, 12.2, stroke="#8b2942", sw=0.9, dash="6 4")
    cad.text(2.4, -0.55, "1", size=11, weight=600, fill="#8b2942")
    return cad.finish("План 1 этажа  ·  отм. ±0,000", "А-02", "М 1:50")


def draw_floor2() -> str:
    cad = CAD(960, 1220, 54, 155, 210)
    cad.rect(-0.15, -0.15, 9.3, 13.6, fill="#efebe3", stroke="none")
    # exterior
    cad.wall(0.00, 0.00, 9.00, 0.20)
    cad.wall(0.00, 11.80, 9.00, 0.20)
    cad.wall(0.00, 0.20, 0.20, 11.60)
    cad.wall(8.80, 0.20, 0.20, 11.60)
    # interior
    cad.wall(5.08, 0.20, 0.12, 11.60)         # запад | восток
    cad.wall(0.20, 3.88, 4.88, 0.12)          # спальня 2 | гардероб/с/у
    cad.wall(0.20, 6.08, 4.88, 0.12)          # гардероб/с/у | мастер
    cad.wall(2.50, 4.00, 0.12, 2.08)          # гардероб | мастер-с/у
    cad.wall(6.38, 5.40, 0.12, 2.80)          # коридор | ванная
    cad.wall(6.50, 5.40, 2.30, 0.12)          # холл | ванная (юг)
    cad.wall(5.20, 8.20, 3.60, 0.12)          # коридор+ванная | спальня 3
    # openings — все жилые из холла/коридора
    cad.opening(5.08, 1.40, 0.12, 0.90)       # холл → спальня 2
    cad.opening(5.08, 6.55, 0.12, 0.90)       # коридор → мастер
    cad.opening(5.45, 8.20, 0.90, 0.12)       # коридор → спальня 3
    cad.opening(6.38, 6.00, 0.12, 0.90)       # коридор → ванная
    cad.opening(1.10, 6.08, 0.90, 0.12)       # мастер → гардероб
    cad.opening(3.20, 6.08, 0.90, 0.12)       # мастер → мастер-с/у
    # windows
    cad.window_h(0.70, 0.00, 1.70, 0.20)
    cad.window_h(5.30, 0.00, 1.20, 0.20)
    cad.window_h(0.70, 11.80, 1.60, 0.20)
    cad.window_h(3.70, 11.80, 1.60, 0.20)
    cad.window_h(6.50, 11.80, 1.60, 0.20)
    cad.window_v(0.00, 0.70, 1.60, 0.20)
    cad.window_v(0.00, 7.20, 2.80, 0.20)
    cad.window_v(8.80, 0.90, 1.40, 0.20)
    cad.window_v(8.80, 9.00, 2.20, 0.20)
    # двери распахиваются в комнаты
    cad.door(5.08, 1.40, 0.90, 90, 1)         # спальня 2
    cad.door(5.08, 6.55, 0.90, 90, 1)         # мастер
    cad.door(5.45, 8.32, 0.90, 0, 1)          # спальня 3
    cad.door(6.50, 6.00, 0.90, 90, -1)        # ванная
    cad.door(1.10, 6.08, 0.90, 0, -1)         # гардероб
    cad.door(3.20, 6.08, 0.90, 0, -1)         # мастер-с/у
    # furniture
    cad.bed(1.35, 0.50, 1.80, 2.10)
    cad.bed(1.15, 8.55, 1.90, 2.20)
    cad.bed(6.20, 8.70, 1.70, 2.00)
    cad.rect(0.40, 4.20, 1.90, 1.70, fill=FURN, stroke=FURN_S, sw=0.7)
    cad.text(1.35, 5.05, "шкафы", size=8, fill=DIM)
    cad.wc(4.35, 4.20)
    cad.basin(2.80, 4.20, 1.10, 0.45)
    cad.rect(2.75, 5.35, 1.05, 0.55, fill="white", stroke=INK, sw=0.8)
    cad.text(3.27, 5.62, "душ", size=8, fill=DIM)
    cad.wc(8.15, 5.65)
    cad.basin(6.65, 5.65, 1.1, 0.45)
    cad.rect(6.70, 6.90, 1.2, 0.70, fill="white", stroke=INK, sw=0.8)
    cad.text(7.30, 7.25, "ванна", size=8, fill=DIM)
    cad.rect(7.55, 4.20, 1.05, 1.00, fill="#e0ddd6", stroke=FURN_S, sw=0.7)
    cad.text(8.07, 4.70, "ст.м.", size=8, fill=DIM)
    # stair void
    cad.rect(6.70, 0.45, 2.10, 3.52, fill="#f6f2ea", stroke=INK, sw=1.0, extra='stroke-dasharray="5 3"')
    cad.line(6.70, 0.45, 8.80, 3.97, stroke=INK, sw=0.6)
    cad.line(8.80, 0.45, 6.70, 3.97, stroke=INK, sw=0.6)
    cad.text(7.75, 2.20, "ПРОЁМ", size=9, fill=DIM)
    cad.text(7.75, 1.75, "ЛЕСТНИЦЫ", size=9, fill=DIM)
    cad.room_label(2.55, 2.10, "13", "Спальня 2", "18,0 м²")
    cad.room_label(1.35, 5.55, "11", "Гардероб", "4,8 м²")
    cad.room_label(3.85, 5.15, "12", "Мастер-с/у", "5,1 м²")
    cad.room_label(2.55, 9.55, "10", "Мастер-спальня", "27,3 м²")
    cad.room_label(7.05, 3.55, "09", "Холл 2 эт.", "14,8 м²")
    cad.text(5.78, 7.15, "кор.", size=8, fill=DIM)
    cad.room_label(7.55, 6.85, "15", "Ванная", "6,4 м²")
    cad.room_label(7.00, 10.15, "14", "Спальня 3", "12,5 м²")
    cad.dim_h(0, 9, -0.85, "9,00")
    cad.dim_v(0, 12, -0.85, "12,00")
    cad.dim_v(0, 4.00, 9.55, "4,00")
    cad.dim_v(4.00, 6.20, 9.55, "2,20")
    cad.dim_v(6.20, 12.00, 9.55, "5,80")
    cad.north(10.6, 11.2, 1.1)
    cad.scalebar(10.0, 0.2, 3)
    cad.line(2.4, -0.2, 2.4, 13.4, stroke="#8b2942", sw=0.9, dash="6 4")
    cad.text(2.4, 13.7, "1", size=11, weight=600, fill="#8b2942")
    cad.text(2.4, -0.55, "1", size=11, weight=600, fill="#8b2942")
    return cad.finish("План 2 этажа  ·  отм. +3,150", "А-03", "М 1:50")


def facade_south(cad: CAD, ox: float, oy: float) -> None:
    """С улицы: запад слева, восток справа. Белый куб, портал, бассейн, навес."""
    def X(v):
        return ox + v
    def Y(v):
        return oy + v
    cad.line(X(-2.4), Y(0), X(14.0), Y(0), sw=1.4)
    cad.rect(X(0), Y(0), 9.0, 0.45, fill="#8d8a84", stroke=INK, sw=0.8)
    cad.rect(X(0), Y(0.45), 9.0, 6.30, fill="#f2efe8", stroke=INK, sw=1.1)
    cad.rect(X(0), Y(6.75), 9.0, 0.60, fill="#2a2a2a", stroke=INK, sw=1.0)
    cad.rect(X(1.4), Y(7.05), 6.2, 0.22, fill="#1c2830", stroke=INK, sw=0.4)
    for i in range(5):
        cad.line(X(1.4 + i * 1.24), Y(7.05), X(1.4 + i * 1.24), Y(7.27), stroke="#0e161c", sw=0.3)
    # двухэтажная тёмная ниша + одноэтажный портал + дверь
    cad.rect(X(3.35), Y(3.60), 2.30, 3.15, fill="#2c3036", stroke=INK, sw=0.8)
    cad.rect(X(2.95), Y(0.45), 3.10, 3.15, fill="#2c3036", stroke=INK, sw=0.9)
    cad.rect(X(3.85), Y(0.45), 1.20, 2.40, fill="#6b4a32", stroke=INK, sw=0.9)
    def win(x, y, w, h):
        cad.rect(X(x), Y(y), w, h, fill="#9fb6c2", stroke=INK, sw=0.9)
        cad.line(X(x + w / 2), Y(y), X(x + w / 2), Y(y + h), stroke=INK, sw=0.4)
    win(0.55, 1.15, 1.35, 1.45)
    win(0.55, 4.35, 1.35, 1.45)
    win(6.55, 4.35, 1.35, 1.45)
    win(7.45, 1.25, 0.90, 1.30)
    # бассейн 6 м по фронту, слева; настил
    cad.rect(X(-2.05), Y(-0.10), 6.00, 0.10, fill="#6aa0b8", stroke="#4d7a8c", sw=0.6)
    cad.rect(X(-2.05), Y(0.00), 6.00, 0.04, fill=WOOD, stroke="none")
    cad.text(X(0.95), Y(-0.42), "бассейн 6×3", size=8, fill=DIM)
    # навес справа, зазор 1,50
    cad.rect(X(10.50), Y(0.0), 3.20, 2.45, fill="none", stroke=INK, sw=1.1)
    cad.line(X(10.50), Y(2.45), X(13.70), Y(2.45), sw=1.3)
    cad.text(X(12.10), Y(1.15), "навес", size=8, fill=DIM)
    cad.dim_h(X(9.0), X(10.50), Y(2.85), "1,50")
    cad.text(X(4.5), Y(-0.72), "ЮЖНЫЙ ФАСАД  ·  улица", size=12, weight=600)
    cad.dim_h(X(0), X(9), Y(-1.70), "9,00")
    cad.dim_v(Y(0), Y(7.35), X(-2.55), "7,35")
    cad.dim_v(Y(0), Y(0.45), X(14.15), "0,45")
    cad.dim_v(Y(0.45), Y(3.60), X(14.15), "3,15")
    cad.dim_v(Y(3.60), Y(6.75), X(14.15), "3,15")
    cad.dim_v(Y(6.75), Y(7.35), X(14.15), "0,60")


def facade_north(cad: CAD, ox, oy) -> None:
    """Из сада смотрим на юг: восток слева, запад справа — как на рис. 3."""
    def X(x_plan):
        return ox + (9.0 - x_plan)
    def Xl(x_plan, w):
        return ox + (9.0 - x_plan - w)
    def Y(v):
        return oy + v
    cad.line(Xl(13.90, 0), Y(0), X(-0.4), Y(0), sw=1.4)
    cad.rect(Xl(0, 9.0), Y(0), 9.0, 0.45, fill="#8d8a84", stroke=INK, sw=0.8)
    cad.rect(Xl(0, 9.0), Y(0.45), 9.0, 6.30, fill="#f2efe8", stroke=INK, sw=1.1)
    cad.rect(Xl(0, 9.0), Y(6.75), 9.0, 0.60, fill="#2a2a2a", stroke=INK, sw=1.0)
    cad.rect(Xl(1.4, 6.2), Y(7.05), 6.2, 0.22, fill="#1c2830", stroke=INK, sw=0.4)
    # терраса на всю ширину 9 м
    cad.rect(Xl(0, 9.0), Y(0.16), 9.0, 0.16, fill=WOOD, stroke=INK, sw=0.6)
    cad.rect(Xl(0, 9.0), Y(3.55), 9.0, 0.14, fill="#2c3036", stroke=INK, sw=0.7)
    def win(x, y, w, h, bars=1):
        cad.rect(Xl(x, w), Y(y), w, h, fill="#8aa7b5", stroke=INK, sw=0.9)
        for i in range(1, bars):
            xx = Xl(x, w) + w * i / bars
            cad.line(xx, Y(y), xx, Y(y + h), stroke=INK, sw=0.4)
    win(0.35, 0.55, 4.70, 2.70, 2)
    cad.rect(Xl(4.90, 0.55), Y(0.55), 0.55, 2.70, fill="#2c3036", stroke=INK, sw=0.7)
    win(5.45, 0.55, 3.20, 2.70, 2)
    win(0.70, 4.25, 1.60, 1.50)
    win(3.70, 4.25, 1.60, 1.50)
    win(6.50, 4.25, 1.60, 1.50)
    # навес восточный = слева, зазор 1,50
    cad.rect(Xl(10.50, 3.20), Y(0.0), 3.20, 2.45, fill="none", stroke=INK, sw=1.1)
    cad.line(Xl(10.50, 3.20), Y(2.45), Xl(10.50, 0), Y(2.45), sw=1.3)
    cad.text((Xl(10.50, 3.20) + Xl(10.50, 0)) / 2, Y(1.15), "навес", size=8, fill=DIM)
    cad.dim_h(Xl(10.50, 3.20) + 3.20, Xl(9.0, 0), Y(2.85), "1,50")
    cad.text(Xl(0, 9.0) + 4.5, Y(-0.72), "СЕВЕРНЫЙ ФАСАД  ·  сад", size=12, weight=600)


def facade_side(cad: CAD, ox, oy, title: str, is_east=True) -> None:
    """Восток: юг слева. Запад: север слева (вид на фасад)."""
    depth = 12.0
    def X(y_plan, w=0):
        if is_east:
            return ox + y_plan
        return ox + (depth - y_plan - w)
    def Y(v):
        return oy + v
    cad.line(ox - 0.5, Y(0), ox + depth + 0.8, Y(0), sw=1.4)
    cad.rect(X(0, depth) if not is_east else X(0), Y(0), 12.0, 0.45, fill="#8d8a84", stroke=INK, sw=0.8)
    cad.rect(X(0, depth) if not is_east else X(0), Y(0.45), 12.0, 6.30, fill="#f2efe8", stroke=INK, sw=1.1)
    cad.rect(X(0, depth) if not is_east else X(0), Y(6.75), 12.0, 0.60, fill="#2a2a2a", stroke=INK, sw=1.0)
    def win(y, z, w, h):
        cad.rect(X(y, w), Y(z), w, h, fill="#9fb6c2", stroke=INK, sw=0.9)
    if is_east:
        win(1.40, 1.20, 1.10, 1.40)
        win(1.40, 4.35, 1.10, 1.40)
        win(8.40, 1.15, 1.40, 1.50)
        win(9.00, 4.35, 1.40, 1.40)
        cad.rect(X(2.00), Y(0), 6.00, 2.45, fill="none", stroke=INK, sw=1.1)
        cad.line(X(2.00), Y(2.45), X(8.00), Y(2.45), sw=1.3)
        cad.text(X(5.00), Y(1.20), "навес 3,2×6", size=9, fill=DIM)
        cad.text(X(5.00), Y(0.72), "отдельно, зазор 1,50", size=8, fill=DIM)
        cad.rect(X(12.00), Y(0.18), 0.35, 0.14, fill=WOOD, stroke=INK, sw=0.5)
        cad.text(X(11.2), Y(-0.42), "терраса", size=8, fill=DIM)
    else:
        win(0.70, 4.35, 1.60, 1.40)
        win(4.40, 1.15, 2.20, 1.50)
        win(7.20, 4.20, 2.80, 2.00)
        win(8.40, 0.70, 2.60, 2.40)
        cad.rect(X(0.0, 3.0), Y(-0.08), 3.0, 0.08, fill="#6aa0b8", stroke="#4d7a8c", sw=0.6)
        cad.text(X(1.5, 0), Y(-0.42), "бассейн", size=8, fill=DIM)
    cad.text(ox + 6.0, Y(-0.72), title, size=12, weight=600)
    cad.dim_h(ox, ox + 12, Y(-1.65), "12,00")


def draw_elevations() -> str:
    cad = CAD(1180, 1020, 28, 95, 100)
    facade_south(cad, 3.4, 16.6)
    facade_north(cad, 24.2, 16.6)
    facade_side(cad, 0.6, 2.4, "ВОСТОЧНЫЙ ФАСАД  ·  проезд", True)
    facade_side(cad, 18.4, 2.4, "ЗАПАДНЫЙ ФАСАД  ·  проход", False)
    cad.scalebar(32.4, 13.2, 4)
    cad.north(16.8, 13.4, 1.15)
    return cad.finish("Фасады", "А-04", "М 1:100")


def draw_section() -> str:
    """Продольный разрез юг→север (глубина дома 12 м + терраса 4 м). Вид на восток."""
    cad = CAD(1180, 840, 40, 240, 160)
    # X = план Y (юг слева, север справа)
    cad.rect(-1.0, -0.9, 18.0, 0.9, fill="#c9c3b4", stroke="none")
    cad.line(-1.0, 0.0, 17.0, 0.0, sw=1.3)
    cad.rect(0.0, -0.9, 0.45, 0.9, fill="#7d7d7d", stroke=INK, sw=0.7)
    cad.rect(11.55, -0.9, 0.45, 0.9, fill="#7d7d7d", stroke=INK, sw=0.7)
    cad.rect(-0.2, -0.35, 12.4, 0.35, fill="#8f8f8f", stroke=INK, sw=0.7)
    cad.rect(0.0, 0.0, 12.0, 0.45, fill="#8d8a84", stroke=INK, sw=0.8)
    # cut walls south / north
    cad.rect(0.00, 0.45, 0.20, 6.30, fill=WALL, stroke="none")
    cad.rect(11.80, 0.45, 0.20, 6.30, fill=WALL, stroke="none")
    cad.rect(0.00, 3.40, 12.00, 0.20, fill=WALL, stroke="none")
    cad.rect(0.00, 6.55, 12.00, 0.20, fill=WALL, stroke="none")
    # L1: office | living
    cad.rect(3.68, 0.45, 0.12, 2.95, fill=WALL, stroke="none")
    cad.rect(0.20, 0.45, 3.48, 2.95, fill="#efe8dc", stroke="none", opacity=0.55)
    cad.rect(3.80, 0.45, 8.00, 2.95, fill="#e7eee4", stroke="none", opacity=0.5)
    # L2: bed2 | wardrobe | master
    cad.rect(3.88, 3.60, 0.12, 2.95, fill=WALL, stroke="none")
    cad.rect(6.08, 3.60, 0.12, 2.95, fill=WALL, stroke="none")
    cad.rect(0.20, 3.60, 3.68, 2.95, fill="#ece6dc", stroke="none", opacity=0.5)
    cad.rect(4.00, 3.60, 2.08, 2.95, fill="#e4ddd2", stroke="none", opacity=0.55)
    cad.rect(6.20, 3.60, 5.60, 2.95, fill="#e8efe6", stroke="none", opacity=0.5)
    # windows
    cad.rect(0.00, 1.10, 0.20, 1.50, fill=GLASS, stroke=INK, sw=0.7)
    cad.rect(0.00, 4.40, 0.20, 1.45, fill=GLASS, stroke=INK, sw=0.7)
    cad.rect(11.80, 0.55, 0.20, 2.70, fill=GLASS, stroke=INK, sw=0.7)
    cad.rect(11.80, 4.20, 0.20, 1.50, fill=GLASS, stroke=INK, sw=0.7)
    cad.rect(0.00, 6.75, 12.00, 0.60, fill="#2a2a2a", stroke=INK, sw=0.8)
    cad.rect(2.5, 7.08, 7.0, 0.18, fill="#1c2830", stroke=INK, sw=0.4)
    cad.rect(12.00, 0.32, 4.00, 0.12, fill=WOOD, stroke=INK, sw=0.8)
    cad.rect(12.00, 0.00, 0.15, 0.32, fill="#7a7a7a", stroke=INK, sw=0.6)
    cad.rect(15.85, 0.00, 0.15, 0.32, fill="#7a7a7a", stroke=INK, sw=0.6)

    def level(z, name):
        cad.line(-4.7, z, -0.3, z, stroke="#8b2942", sw=0.8)
        cad.poly([(-0.3, z), (-0.55, z + 0.12), (-0.55, z - 0.12)], fill="#8b2942", stroke="none")
        cad.text(-4.55, z + 0.28, name, size=10, fill="#8b2942", anchor="start")

    level(0.45, "±0,000  чистый пол 1 эт.")
    level(3.60, "+3,150  чистый пол 2 эт.")
    level(6.40, "+5,950  низ покрытия")
    level(7.35, "+6,900  верх парапета")
    level(0.00, "−0,450  земля")
    cad.text(1.9, 1.85, "04 Кабинет", size=11)
    cad.text(7.6, 1.85, "05 Гостиная", size=11)
    cad.text(1.9, 5.05, "13 Спальня 2", size=11)
    cad.text(5.05, 5.05, "11 Гардероб", size=10)
    cad.text(8.7, 5.05, "10 Мастер-спальня", size=11)
    cad.text(14.0, 0.85, "терраса 9×4", size=10, fill=DIM)
    cad.text(6.0, 7.55, "ФЭМ", size=9, fill=DIM)
    cad.text(6.0, -0.55, "юг", size=10, fill=DIM)
    cad.text(11.5, -0.55, "север", size=10, fill=DIM)
    cad.dim_h(0, 12, 8.35, "12,00")
    cad.dim_h(12, 16, 8.35, "4,00")
    cad.dim_v(0.45, 3.60, 16.7, "3,15")
    cad.dim_v(3.60, 6.75, 16.7, "3,15")
    cad.dim_v(0, 7.35, 17.6, "7,35")
    cad.scalebar(13.2, 7.0, 4)
    return cad.finish("Разрез 1–1  ·  продольный, юг слева, вид на восток", "А-05", "М 1:75")


def draw_axon() -> str:
    cad = CAD(960, 760, 16, 90, 120)
    # simple cabinet axonometric of plot + house
    # plot 17 x 35, iso-ish: x' = x + y*0.5, y' = y*0.5  wait standard military: x'=x+y*0.5, y'=y*0.5
    def iso(x, y, z=0):
        return x + y * 0.55, y * 0.48 + z
    def face(pts, fill, stroke=INK, sw=1):
        cad.poly(pts, fill=fill, stroke=stroke, sw=sw)
    # ground plot
    p = [iso(0, 0), iso(17, 0), iso(17, 35), iso(0, 35)]
    face(p, "#dfe6d4")
    # street
    face([iso(-1, -4), iso(18, -4), iso(18, 0), iso(-1, 0)], "#c0c0c0")
    # garden
    face([iso(0.4, 18), iso(16.6, 18), iso(16.6, 34.6), iso(0.4, 34.6)], GRASS, sw=0.5)
    # terrace
    face([iso(3, 18), iso(12, 18), iso(12, 22), iso(3, 22)], WOOD)
    # driveway
    face([iso(12.2, 0), iso(16.6, 0), iso(16.6, 18), iso(12.2, 18)], PAVE, sw=0.5)
    # house mass L1
    hx, hy, hz1, hz2 = 3, 6, 3.6, 7.35
    def box(x, y, w, d, z0, z1, fill_top, fill_s, fill_e):
        # top
        face([iso(x, y, z1), iso(x + w, y, z1), iso(x + w, y + d, z1), iso(x, y + d, z1)], fill_top)
        # south (front)
        face([iso(x, y, z0), iso(x + w, y, z0), iso(x + w, y, z1), iso(x, y, z1)], fill_s)
        # east
        face([iso(x + w, y, z0), iso(x + w, y + d, z0), iso(x + w, y + d, z1), iso(x + w, y, z1)], fill_e)
    # бассейн слева у улицы
    face([iso(0.95, 1.4, 0), iso(6.95, 1.4, 0), iso(6.95, 4.4, 0), iso(0.95, 4.4, 0)], "#6aa0b8", sw=0.5)
    face([iso(0.95, 4.4, 0), iso(6.95, 4.4, 0), iso(6.95, 6.0, 0), iso(0.95, 6.0, 0)], WOOD, sw=0.5)
    # белый двухэтажный куб
    box(3, 6, 9, 12, 0, 7.35, "#f2efe8", "#ebe6dc", "#d8d2c6")
    # тёмный портал юг
    face([iso(6.0, 6, 0.45), iso(8.9, 6, 0.45), iso(8.9, 6, 3.6), iso(6.0, 6, 3.6)], "#2c3036")
    # ФЭМ
    face([iso(4.2, 7.5, 7.45), iso(10.8, 7.5, 7.45), iso(10.8, 16.5, 7.45), iso(4.2, 16.5, 7.45)], "#1c2830", sw=0.4)
    # навес отдельно, зазор 1,5 м
    box(13.5, 8.0, 3.2, 6.0, 0, 2.45, "#4a4a4a", "#5a5a5a", "#3a3a3a")
    cad.text(iso(8.5, 12, 8.4)[0], iso(8.5, 12, 8.4)[1], "H = 7,35 м", size=10, fill=DIM)
    cad.text(iso(4, -3.2)[0], iso(4, -3.2)[1], "улица", size=11, fill=DIM)
    cad.text(iso(8, 28)[0], iso(8, 28)[1], "сад 17 м", size=11, fill=DIM)
    cad.text(iso(3.8, 2.8)[0], iso(3.8, 2.8)[1], "бассейн", size=9, fill=DIM)
    cad.text(iso(15.0, 10.5)[0], iso(15.0, 10.5)[1], "навес", size=9, fill=DIM)
    cad.scalebar(0.2, 24.5, 5)
    cad.north(20.5, 0.6, 1.4)
    return cad.finish("Аксонометрия участка и объёма", "А-06", "М 1:200")


HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>LINEA 9×12 — архитектурный альбом</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@400;500;600&display=swap" rel="stylesheet"/>
<style>
  :root {
    --ink: #1c1c1c;
    --muted: #5c5852;
    --paper: #f4f0e8;
    --card: #fbf8f2;
    --line: #d9d3c8;
    --accent: #6e4a32;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: var(--paper); color: var(--ink);
    font-family: "IBM Plex Sans", "Segoe UI", sans-serif; line-height: 1.55; }
  img { max-width: 100%; display: block; }
  a { color: var(--accent); }
  .wrap { max-width: 1080px; margin: 0 auto; padding: 0 28px 80px; }
  header.cover { padding: 64px 0 36px; border-bottom: 1px solid var(--ink); }
  .kicker { letter-spacing: .18em; text-transform: uppercase; font-size: 11px; color: var(--muted); }
  h1 { font-family: "IBM Plex Serif", Georgia, serif; font-weight: 500; font-size: 48px; line-height: 1.1; margin: 12px 0 8px; }
  h2 { font-family: "IBM Plex Serif", Georgia, serif; font-weight: 500; font-size: 28px; margin: 48px 0 12px; }
  h3 { font-size: 15px; letter-spacing: .04em; text-transform: uppercase; margin: 28px 0 10px; }
  .lead { font-size: 18px; max-width: 640px; color: var(--muted); }
  .meta { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 36px 0 28px; }
  .meta div { border-top: 1px solid var(--ink); padding-top: 8px; }
  .meta b { display: block; font-size: 20px; font-family: "IBM Plex Serif", serif; font-weight: 500; }
  .meta span { font-size: 12px; color: var(--muted); }
  .hero { margin: 24px 0 8px; }
  .hero img { width: 100%; height: auto; }
  .cap { font-size: 12px; color: var(--muted); margin: 8px 0 28px; }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
  .grid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; }
  figure { margin: 0; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; background: var(--card); }
  th, td { border-bottom: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }
  th { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); font-weight: 600; }
  td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
  .sheet { background: var(--card); border: 1px solid var(--line); padding: 10px; margin: 18px 0 8px; }
  .sheet svg { display: block; width: 100%; height: auto; }
  ul.plain { padding-left: 18px; }
  ul.plain li { margin: 4px 0; }
  .note { font-size: 13px; color: var(--muted); border-left: 2px solid var(--accent); padding: 4px 0 4px 14px; margin: 16px 0; }
  footer { margin-top: 56px; padding-top: 16px; border-top: 1px solid var(--ink); font-size: 12px; color: var(--muted); }
  nav.toc ol { padding-left: 22px; }
  nav.toc a { text-decoration: none; color: var(--ink); }
  nav.toc a:hover { color: var(--accent); }
  @media (max-width: 800px) {
    h1 { font-size: 34px; }
    .meta, .grid2, .grid3 { grid-template-columns: 1fr 1fr; }
  }
  @media (max-width: 560px) {
    .meta, .grid2, .grid3 { grid-template-columns: 1fr; }
    .wrap { padding: 0 16px 48px; }
  }
  @media print {
    body { background: white; }
    .wrap { max-width: none; }
    header.cover { break-after: page; }
    .sheet { break-inside: avoid; }
  }
</style>
</head>
<body>
<div class="wrap">
<header class="cover">
  <div class="kicker">Концептуальный архитектурный проект</div>
  <h1>LINEA 9×12</h1>
  <p class="lead">Современный двухэтажный дом 9 × 12 м на участке 17 × 35 м. Белый куб, тёмный портал входа, плоская кровля с ФЭМ. Первый этаж открыт в сад, второй — приватный, без балкона.</p>
  <div class="meta">
    <div><b>9 × 12 м</b><span>пятно застройки</span></div>
    <div><b>216 м²</b><span>общая площадь двух этажей</span></div>
    <div><b>17 × 35 м</b><span>участок, 595 м²</span></div>
    <div><b>7,35 м</b><span>высота по парапету</span></div>
  </div>
  <div class="hero"><img src="images/01-exterior-street.jpg" alt="Главный фасад со стороны улицы"/></div>
  <p class="cap">Рис. 1. Южный фасад: бассейн 6 × 3 м слева, тёмный портал входа, навес для автомобиля справа.</p>
</header>

<nav class="toc">
  <h2>Содержание альбома</h2>
  <ol>
    <li><a href="#idea">Концепция и посадка на участок</a></li>
    <li><a href="#tep">Технико-экономические показатели</a></li>
    <li><a href="#site">А-01 Генплан</a></li>
    <li><a href="#l1">А-02 План 1 этажа</a></li>
    <li><a href="#l2">А-03 План 2 этажа</a></li>
    <li><a href="#facade">А-04 Фасады</a></li>
    <li><a href="#section">А-05 Разрез 1–1</a></li>
    <li><a href="#axon">А-06 Аксонометрия</a></li>
    <li><a href="#viz">Визуализации</a></li>
    <li><a href="#spec">Конструкции, инженерия, материалы</a></li>
  </ol>
</nav>

<section id="idea">
  <h2>1. Концепция</h2>
  <p>Дом рассчитан на семью из 4 человек. Улица — с южной короткой стороны участка (17 м). Дом ставится пятном 9 м по фронту и 12 м в глубину: слева противопожарный проход 3 м, справа проезд 5 м, спереди палисадник 6 м, сзади сад 17 м.</p>
  <div class="grid2">
    <div>
      <h3>Объём</h3>
      <ul class="plain">
        <li>Два полных этажа, плоская кровля с парапетом.</li>
        <li>Белый двухэтажный объём, тёмный портал входа, плоская кровля с ФЭМ.</li>
        <li>Терраса 9 × 4 м к саду, бассейн 6 × 3 м в палисаднике слева.</li>
        <li>Отдельно стоящий навес 3,2 × 6 м с зазором 1,5 м от восточной стены.</li>
      </ul>
    </div>
    <div>
      <h3>Сценарий жизни</h3>
      <ul class="plain">
        <li>1 этаж — общественный: вход, кабинет, кухня-гостиная в сад.</li>
        <li>2 этаж — спальный: мастер-блок к саду, две детские, общая ванная.</li>
        <li>Бассейн 6 × 3 м слева перед домом, навес 3,2 × 6 м справа с зазором 1,5 м.</li>
        <li>Север участка — газон, мангал, огород, игра.</li>
      </ul>
    </div>
  </div>
  <div class="hero"><img src="images/03-aerial-plot.jpg" alt="Аэрофото участка"/></div>
  <p class="cap">Рис. 2. Посадка дома на участок: бассейн слева у улицы, въезд и навес справа, сад за домом.</p>
</section>

<section id="tep">
  <h2>2. Технико-экономические показатели</h2>
  <table>
    <thead><tr><th>Показатель</th><th class="num">Значение</th></tr></thead>
    <tbody>
      <tr><td>Площадь участка</td><td class="num">17,00 × 35,00 = 595 м²</td></tr>
      <tr><td>Пятно застройки дома</td><td class="num">9,00 × 12,00 = 108 м²</td></tr>
      <tr><td>Коэффициент застройки</td><td class="num">18,2 %</td></tr>
      <tr><td>Общая площадь этажей (брутто)</td><td class="num">216 м²</td></tr>
      <tr><td>Полезная площадь помещений</td><td class="num">≈ 184 м²</td></tr>
      <tr><td>Жилая площадь</td><td class="num">≈ 108 м²</td></tr>
      <tr><td>Терраса (север, на всю ширину дома)</td><td class="num">9,00 × 4,00 = 36 м²</td></tr>
      <tr><td>Навес для автомобиля (отдельно, зазор 1,50 м)</td><td class="num">3,20 × 6,00 = 19,2 м²</td></tr>
      <tr><td>Бассейн</td><td class="num">6,00 × 3,00 = 18 м²</td></tr>
      <tr><td>Высота этажа (пол–пол)</td><td class="num">3,15 м</td></tr>
      <tr><td>Высота помещений в чистоте</td><td class="num">2,80 м</td></tr>
      <tr><td>Высота здания по парапету</td><td class="num">7,35 м от земли</td></tr>
      <tr><td>Отметка чистого пола 1 эт.</td><td class="num">+0,450 от земли</td></tr>
    </tbody>
  </table>
  <p class="note">Отступы от границ: юг (улица) 6,0 м, запад 3,0 м, восток 5,0 м, север 17,0 м. Перед началом проектирования на конкретном участке их нужно сверить с ПЗЗ, ГПЗУ и противопожарными нормами региона.</p>
</section>

<section id="site">
  <h2>3. А-01 Генплан</h2>
  <div class="sheet">SITE_SVG</div>
  <p class="cap">Чертёж А-01. Север — вверх. Улица по южной границе.</p>
  <table>
    <thead><tr><th>Зона участка</th><th>Размер</th><th>Назначение</th></tr></thead>
    <tbody>
      <tr><td>Палисадник / въезд</td><td>17 × 6 м</td><td>Бассейн 6 × 3 м слева, дорожка к входу, проезд справа</td></tr>
      <tr><td>Проезд восточный</td><td>5 × 18 м</td><td>Навес 3,2 × 6 м с зазором 1,5 м от дома, проход к саду</td></tr>
      <tr><td>Проход западный</td><td>3 × 18 м</td><td>Пожарный проход, живая изгородь</td></tr>
      <tr><td>Дом</td><td>9 × 12 м</td><td>Двухэтажный объём</td></tr>
      <tr><td>Сад</td><td>17 × 17 м</td><td>Терраса, газон, мангал, огород, детская зона</td></tr>
    </tbody>
  </table>
</section>

<section id="l1">
  <h2>4. А-02 План 1 этажа</h2>
  <p>Вход с юга в тамбур, далее холл с лестницей. В кухню два пути: широкий проём 2,60 м из гостиной (основной) и дверь холл → кладовая → кухня (хозяйственный). Кабинет у улицы можно закрыть для работы или гостей.</p>
  <div class="sheet">L1_SVG</div>
  <table>
    <thead><tr><th>№</th><th>Помещение</th><th class="num">Площадь</th><th>Примечание</th></tr></thead>
    <tbody>
      <tr><td>01</td><td>Тамбур</td><td class="num">3,2 м²</td><td>Грязевая зона, шкаф для верхней одежды</td></tr>
      <tr><td>02</td><td>Холл / лестница</td><td class="num">18,0 м²</td><td>L-образная лестница, обычные окна на восток и юг</td></tr>
      <tr><td>03</td><td>Гостевой с/у</td><td class="num">2,8 м²</td><td>Унитаз, раковина</td></tr>
      <tr><td>04</td><td>Кабинет</td><td class="num">10,4 м²</td><td>Может работать как гостевая</td></tr>
      <tr><td>05</td><td>Гостиная — столовая</td><td class="num">39,0 м²</td><td>Диван, стол на 8, выход на террасу, проём в кухню 2,60 м</td></tr>
      <tr><td>06</td><td>Кухня</td><td class="num">17,3 м²</td><td>Линейная + остров; вход из гостиной и через кладовую</td></tr>
      <tr><td>07</td><td>Кладовая</td><td class="num">2,7 м²</td><td>Двери из холла и из кухни</td></tr>
      <tr><td>08</td><td>Котельная / ИТП</td><td class="num">2,8 м²</td><td>Тепловой насос, ввод коммуникаций, выход наружу</td></tr>
    </tbody>
  </table>
</section>

<section id="l2">
  <h2>5. А-03 План 2 этажа</h2>
  <p>С лестницы попадаете в холл 09. Из холла четыре двери: спальня 2 (юг), мастер-спальня (запад), общая ванная и спальня 3 (север, в конце короткого коридора). Гардероб и мастер-с/у — только из мастер-спальни.</p>
  <div class="sheet">L2_SVG</div>
  <table>
    <thead><tr><th>№</th><th>Помещение</th><th class="num">Площадь</th><th>Примечание</th></tr></thead>
    <tbody>
      <tr><td>09</td><td>Холл 2 этажа</td><td class="num">14,8 м²</td><td>Лестница, коридор на север к спальне 3 и мастеру</td></tr>
      <tr><td>10</td><td>Мастер-спальня</td><td class="num">27,3 м²</td><td>Окна в сад, без балкона</td></tr>
      <tr><td>11</td><td>Гардеробная</td><td class="num">4,8 м²</td><td>Из мастер-спальни</td></tr>
      <tr><td>12</td><td>Мастер-санузел</td><td class="num">5,1 м²</td><td>Душ, два умывальника, унитаз</td></tr>
      <tr><td>13</td><td>Спальня 2</td><td class="num">18,0 м²</td><td>Детская / гостевая, юг</td></tr>
      <tr><td>14</td><td>Спальня 3</td><td class="num">12,5 м²</td><td>Детская, вид в сад, дверь из коридора</td></tr>
      <tr><td>15</td><td>Ванная общая</td><td class="num">6,4 м²</td><td>Ванна, унитаз, раковина, дверь из коридора</td></tr>
    </tbody>
  </table>
</section>

<section id="facade">
  <h2>6. А-04 Фасады</h2>
  <p>Все фасады — белый двухэтажный куб с тёмным парапетом и ФЭМ. Юг: тёмный портал и бассейн слева, навес справа. Север: раздвижное остекление 1 этажа на всю ширину 9 м, три окна 2 этажа, терраса, навес слева. Восток и запад — пробитые окна, без витража лестницы.</p>
  <div class="sheet">EL_SVG</div>
</section>

<section id="section">
  <h2>7. А-05 Разрез 1–1</h2>
  <p>Продольный разрез через кабинет, гостиную и мастер-спальню. Вид на восток. Показаны отметки полов, парапета и террасы.</p>
  <div class="sheet">SEC_SVG</div>
</section>

<section id="axon">
  <h2>8. А-06 Аксонометрия</h2>
  <div class="sheet">AX_SVG</div>
</section>

<section id="viz">
  <h2>9. Визуализации</h2>
  <div class="grid2">
    <figure>
      <img src="images/02-exterior-garden.jpg" alt="Сад и терраса"/>
      <figcaption class="cap">Рис. 3. Северный фасад из сада: терраса 9 × 4 м, навес слева с зазором, три окна 2 этажа.</figcaption>
    </figure>
    <figure>
      <img src="images/05-exterior-twilight.jpg" alt="Вечерний фасад"/>
      <figcaption class="cap">Рис. 4. Улица в синий час: бассейн слева и тёплый свет входа.</figcaption>
    </figure>
    <figure>
      <img src="images/08-exterior-east.jpg" alt="Восточный фасад"/>
      <figcaption class="cap">Рис. 5. Вид с востока: навес, зазор 1,5 м и белая стена с пробитыми окнами.</figcaption>
    </figure>
    <figure>
      <img src="images/04-interior-living.jpg" alt="Гостиная"/>
      <figcaption class="cap">Рис. 6. Гостиная, вид к саду. Лестница в отдельном холле, не в этом зале.</figcaption>
    </figure>
    <figure>
      <img src="images/06-interior-kitchen.jpg" alt="Кухня"/>
      <figcaption class="cap">Рис. 7. Кухня с островом, связь со столовой и гостиной.</figcaption>
    </figure>
    <figure>
      <img src="images/07-interior-bedroom.jpg" alt="Мастер-спальня"/>
      <figcaption class="cap">Рис. 8. Мастер-спальня 2 этажа, окна в сад, без балкона.</figcaption>
    </figure>
  </div>
</section>

<section id="spec">
  <h2>10. Конструкции, инженерия, материалы</h2>
  <h3>Несущий каркас</h3>
  <ul class="plain">
    <li>Ленточный или плитный фундамент (уточняется по геологии).</li>
    <li>Стены: газобетон 375–400 мм или кирпич с утеплителем 150 мм, EIFS / вентфасад.</li>
    <li>Перекрытие: монолитная ж/б плита 200 мм, шаг стен позволяет обойтись без лишних колонн в гостиной.</li>
    <li>Кровля: плоская, уклон 1,5–2 % к внутренним воронкам, парапет 600 мм, ПВ-мембрана, утепление 200–250 мм.</li>
  </ul>
  <h3>Ограждающие</h3>
  <ul class="plain">
    <li>Штукатурка известково-цементная, белая, на цоколе — архитектурный бетон.</li>
    <li>Портал входа: фиброцемент / штукатурка графит RAL 7016.</li>
    <li>Акценты: дубовая дверь, деревянная терраса.</li>
    <li>Окна: алюминий, тёмная бронза, двухкамерный стеклопакет, Uw ≤ 0,9 Вт/м²K.</li>
  </ul>
  <h3>Инженерия</h3>
  <ul class="plain">
    <li>Отопление: воздух–вода тепловой насос + тёплый пол оба этажа.</li>
    <li>Вентиляция: ПВУ с рекуперацией, кухонный зонт с компенсацией.</li>
    <li>ГВС: бойлер 300 л от теплового насоса, рециркуляция к дальним с/у.</li>
    <li>Электрика: щит в котельной, заложенная трасса под 8–10 кВт ФЭМ на кровле.</li>
    <li>Ливнёвка с кровли — в дождевой сад у северной границы, без сброса на соседей.</li>
    <li>Канализация: выпуск из котельной на восток к септику / ЦК (по наличию сетей).</li>
  </ul>
  <h3>Отделка (концепт)</h3>
  <table>
    <thead><tr><th>Зона</th><th>Пол</th><th>Стены</th><th>Потолок</th></tr></thead>
    <tbody>
      <tr><td>Гостиная, кухня, холл</td><td>Керамогранит 1200×1200, известняк</td><td>Белая штукатурка, ниша камина графит</td><td>Белый, 2,80 м, скрытый карниз</td></tr>
      <tr><td>Спальни</td><td>Инженерная дубовая доска</td><td>Краска, акцентные панели ясень</td><td>Белый, 2,80 м</td></tr>
      <tr><td>Санузлы</td><td>Керамогранит</td><td>Крупноформат + покраска</td><td>Влагостойкий ГКЛ</td></tr>
      <tr><td>Терраса</td><td>Террасная доска ипе / дпк</td><td>—</td><td>Пергола, сталь</td></tr>
    </tbody>
  </table>
  <h3>Состав семьи и вместимость</h3>
  <p>4 постоянных жителя (родители + двое детей), кабинет для удалённой работы. Одно крытое машиноместо под навесом; перед домом слева — бассейн 6 × 3 м в палисаднике глубиной 6 м.</p>
</section>

<footer>
  <p><b>LINEA 9×12</b> — концептуальный архитектурный альбом. Чертежи выполнены в масштабе и с внутренними размерами помещений, но это не рабочая документация: не использовать для строительства без проекта, выполненного лицензированным архитектором и инженерами, с привязкой к ГПЗУ, геологии и нормам конкретной площадки.</p>
  <p>Участок 17 × 35 м, дом 9 × 12 м, 2 этажа, современный стиль. Листы А-01…А-06.</p>
</footer>
</div>
</body>
</html>
"""


def main() -> None:
    sheets = {
        "A-01-site.svg": draw_site(),
        "A-02-floor-1.svg": draw_floor1(),
        "A-03-floor-2.svg": draw_floor2(),
        "A-04-elevations.svg": draw_elevations(),
        "A-05-section.svg": draw_section(),
        "A-06-axon.svg": draw_axon(),
    }
    for name, svg in sheets.items():
        (DRAW / name).write_text(svg, encoding="utf-8")
        print("wrote", name, "bytes", len(svg))

    html = (
        HTML.replace("SITE_SVG", sheets["A-01-site.svg"])
        .replace("L1_SVG", sheets["A-02-floor-1.svg"])
        .replace("L2_SVG", sheets["A-03-floor-2.svg"])
        .replace("EL_SVG", sheets["A-04-elevations.svg"])
        .replace("SEC_SVG", sheets["A-05-section.svg"])
        .replace("AX_SVG", sheets["A-06-axon.svg"])
    )
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    print("wrote index.html", len(html))


if __name__ == "__main__":
    main()
