"""Нарезка готовых PNG-экспортов диаграмм под имена медиа вики.

Диаграммы в draw.io уже экспортированы в PNG (docs/diagrams/*.png).
Страницы вики просят отдельные кадры: «актёры», «фигуры», «связи» и т. д.
Вместо того чтобы рисовать что-то заново, скрипт вырезает нужные области
из настоящего экспорта и ужимает их до ширины 1200 px — так на странице
видно ровно тот фрагмент, о котором говорит шаг.

Запуск:
    python tools/capture/diagram-shot.py

Области задаются в списке CROPS: (имя, файл-источник, (x1, y1, x2, y2)).
Координаты — в пикселях исходного PNG. Если нужно отдать файл целиком,
рамка не указывается — картинка только ужимается.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "wiki" / "images"
MAX_WIDTH = 1200

USECASE = ROOT / "docs" / "diagrams" / "usecase.png"
CLASSES = ROOT / "docs" / "diagrams" / "class-model.png"
ACTIVITY = ROOT / "docs" / "diagrams" / "activity-work-order.png"
ERD = ROOT / "db" / "erd" / "er-diagram.png"

CROPS: list[tuple[str, Path, tuple[int, int, int, int] | None]] = [
    # Диаграмма вариантов использования: актёры, фигуры, связи, полный экспорт.
    ("03-actors", USECASE, (250, 70, 1160, 232)),
    ("03-usecase-shapes", USECASE, (290, 240, 575, 700)),
    ("03-usecase-relations", USECASE, (595, 330, 1165, 700)),
    ("03-usecase-export", USECASE, None),
    # Диаграмма классов: блоки, связи, ассоциация, полный экспорт.
    ("05-class-boxes", CLASSES, (30, 80, 600, 300)),
    ("05-class-relations", CLASSES, (600, 80, 1200, 500)),
    ("05-class-association", CLASSES, (300, 500, 900, 800)),
    ("05-class-export", CLASSES, None),
    # Диаграмма деятельности по заявке — одна страница целиком.
    ("20-activity", ACTIVITY, None),
    # ER-диаграмма базы.
    ("06-er-diagram", ERD, None),
]


def save(name: str, source: Path, box: tuple[int, int, int, int] | None) -> str:
    if not source.exists():
        return f"SKIP {name}: нет файла {source.relative_to(ROOT)}"

    image = Image.open(source).convert("RGB")

    if box is not None:
        left, top, right, bottom = box
        right = min(right, image.width)
        bottom = min(bottom, image.height)
        image = image.crop((left, top, right, bottom))

    if image.width > MAX_WIDTH:
        height = round(image.height * MAX_WIDTH / image.width)
        image = image.resize((MAX_WIDTH, height), Image.LANCZOS)

    target = OUT / f"{name}.png"
    image.save(target, "PNG", optimize=True)
    return f"OK   {name}.png  {image.width}x{image.height}  {target.stat().st_size // 1024} КБ"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    if not ERD.exists():
        # ER-диаграмму экспортирует draw.io отдельной командой (см. README).
        print(f"WARN нет {ERD.relative_to(ROOT)} — сначала экспорт draw.io")

    for name, source, box in CROPS:
        print(save(name, source, box))

    return 0


if __name__ == "__main__":
    sys.exit(main())
