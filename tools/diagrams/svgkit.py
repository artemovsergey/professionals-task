"""Минимальный генератор SVG и mxGraph (draw.io) из общего описания.

Зачем он нужен: по листу задания каждая UML-диаграмма должна быть в трёх
форматах — PNG, SVG, PDF — плюс редактируемый исходник. Если рисовать каждую
в четырёх видах вручную, через месяц они разойдутся. Поэтому рисуем один раз
в виде простых примитивов, а четыре файла получаем из одного описания.

SVG нужен, чтобы вставить диаграмму в вики и в документацию одной строкой.
mxGraph — редактируемый исходник для Draw.io.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from xml.sax.saxutils import escape

# Палитра совпадает с вики-темой, но на светлом фоне: диаграмму печатают
# и вкладывают в документацию, а чёрный текст на белом читается всегда.
INK = "#1f2429"
MUTED = "#5b6670"
LINE = "#7d8891"
ACCENT = "#2f6fb0"
ACCENT_SOFT = "#dce8f4"
OK = "#2f855a"
WARN = "#b7791f"
BAD = "#c0392b"
PAPER = "#ffffff"
LANE_A = "#f4f6f8"
LANE_B = "#ffffff"


@dataclass
class Canvas:
    """Холст с фиксированным размером. Все координаты — в пикселях."""

    width: int
    height: int
    nodes: list[str] = field(default_factory=list)
    text_index: int = 0

    # ------------------------------ примитивы ------------------------------

    def _add(self, markup: str) -> None:
        self.nodes.append(markup)

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        fill: str = PAPER,
        stroke: str = LINE,
        rx: float = 0,
        width: float = 1,
        dash: str | None = None,
    ) -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self._add(
            f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx:g}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{width:g}"{dash_attr}/>'
        )

    def ellipse(
        self,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        *,
        fill: str = PAPER,
        stroke: str = LINE,
        width: float = 1,
    ) -> None:
        self._add(
            f'<ellipse cx="{cx:g}" cy="{cy:g}" rx="{rx:g}" ry="{ry:g}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{width:g}"/>'
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        stroke: str = LINE,
        width: float = 1,
        dash: str | None = None,
    ) -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self._add(
            f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" '
            f'stroke="{stroke}" stroke-width="{width:g}"{dash_attr}/>'
        )

    def polyline(
        self,
        points: list[tuple[float, float]],
        *,
        stroke: str = LINE,
        width: float = 1,
        dash: str | None = None,
        arrow: bool = False,
    ) -> None:
        coords = " ".join(f"{x:g},{y:g}" for x, y in points)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        marker = ' marker-end="url(#arrow)"' if arrow else ""
        self._add(
            f'<polyline points="{coords}" fill="none" stroke="{stroke}" '
            f'stroke-width="{width:g}"{dash_attr}{marker}/>'
        )

    def path(self, d: str, *, stroke: str = LINE, width: float = 1, dash: str | None = None) -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self._add(
            f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width:g}"{dash_attr}/>'
        )

    def text(
        self,
        x: float,
        y: float,
        value: str,
        *,
        size: int = 13,
        anchor: str = "start",
        weight: str = "normal",
        fill: str = INK,
        italic: bool = False,
    ) -> None:
        # Кириллица в XML обязана быть в UTF-8, а спецсимволы — экранированы:
        # иначе «→» превращается в битую последовательность в Draw.io.
        style = "italic" if italic else "normal"
        self._add(
            f'<text x="{x:g}" y="{y:g}" font-family="Segoe UI, DejaVu Sans, sans-serif" '
            f'font-size="{size}" font-weight="{weight}" font-style="{style}" '
            f'text-anchor="{anchor}" fill="{fill}">{escape(value)}</text>'
        )

    # ------------------------------- сборка -------------------------------

    def to_svg(self, title: str) -> str:
        markers = (
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker></defs>'
        )
        body = "\n  ".join(self.nodes)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
            f'height="{self.height}" viewBox="0 0 {self.width} {self.height}" '
            f'role="img" aria-label="{escape(title)}">\n'
            f"  <title>{escape(title)}</title>\n"
            f'  <rect width="{self.width}" height="{self.height}" fill="{PAPER}"/>\n'
            f"  {markers}\n  {body}\n</svg>\n"
        )


@dataclass
class Drawio:
    """Накопитель mxGraph-разметки. Идентификаторы растут по мере добавления."""

    width: int
    height: int
    counter: int = field(default=0, init=False)
    items: list[str] = field(default_factory=list)
    edges: list[str] = field(default_factory=list)

    def node_id(self) -> int:
        self.counter += 1
        return self.counter

    def shape(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        value: str,
        *,
        style: str = "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#7d8891;",
    ) -> int:
        node = self.node_id()
        self.items.append(
            f'        <mxCell id="{node}" value="{escape(value)}" style="{style}" '
            f'vertex="1" parent="1">\n'
            f'          <mxGeometry x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" as="geometry"/>\n'
            f"        </mxCell>"
        )
        return node

    def connect(self, source: int, target: int, style: str) -> None:
        self.edges.append(
            f'        <mxCell id="e{self.node_id()}" style="{style}" edge="1" '
            f'parent="1" source="{source}" target="{target}">\n'
            f'          <mxGeometry relative="1" as="geometry"/>\n'
            f"        </mxCell>"
        )

    def edge_free(self, x1: float, y1: float, x2: float, y2: float, style: str) -> None:
        node = self.node_id()
        self.items.append(
            f'        <mxCell id="{node}" style="{style}" vertex="1" parent="1">\n'
            f'          <mxGeometry x="{min(x1, x2):g}" y="{min(y1, y2):g}" '
            f'width="{abs(x2 - x1):g}" height="{abs(y2 - y1):g}" as="geometry">\n'
            f'            <mxPoint x="{x1:g}" y="{y1:g}" as="sourcePoint"/>\n'
            f'            <mxPoint x="{x2:g}" y="{y2:g}" as="targetPoint"/>\n'
            f"          </mxGeometry>\n"
            f"        </mxCell>"
        )

    def to_xml(self, name: str) -> str:
        cells = "\n".join(self.items + self.edges)
        return (
            '<mxfile host="app.diagrams.net" type="device">\n'
            f'  <diagram id="{name}" name="{name}">\n'
            '    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" '
            'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" '
            f'pageHeight="827" math="0" shadow="0">\n'
            "      <root>\n"
            '        <mxCell id="0"/>\n'
            '        <mxCell id="1" parent="0"/>\n'
            f"{cells}\n"
            "      </root>\n"
            "    </mxGraphModel>\n"
            "  </diagram>\n"
            "</mxfile>\n"
        )