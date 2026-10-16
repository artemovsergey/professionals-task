"""Перевод SVG-диаграмм в PNG и PDF.

Зачем отдельным шагом: лист задания требует по каждой диаграмме три
формата — PNG, SVG, PDF. SVG нужен для вики и документации, PNG встав-
ляется в презентацию, PDF идёт в папку сдачи. Рисовать трижды — значит
гарантированно получить три разные картинки, поэтому все три формата
собираются из одного SVG.

Конвертация идёт через headless-браузер: он умеет растеризовать SVG и
напечатать страницу в PDF без единой внешней библиотеки. Проверено локально
на этой машине; на площадке достаточно открыть SVG в браузере и сохранить.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

# Масштаб растра: 2 — чтобы схема читалась и в документе A4, и в презентации.
SCALE = 2


async def convert(folder: Path, names: list[str]) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        for name in names:
            svg = folder / f"{name}.svg"
            if not svg.exists():
                print(f"  пропущено: {name}.svg не найден")
                continue

            await page.goto(svg.resolve().as_uri())
            box = await page.evaluate(
                "() => { const s = document.querySelector('svg');"
                " return { w: s.width.baseVal.value, h: s.height.baseVal.value }; }"
            )
            await page.set_viewport_size({"width": int(box["w"]), "height": int(box["h"])})

            png = folder / f"{name}.png"
            await page.screenshot(path=str(png), scale="device" if SCALE > 1 else "css")
            await page.pdf(path=str(folder / f"{name}.pdf"), print_background=True, scale=SCALE / 2)
            print(f"  {name}: {int(box['w'])}×{int(box['h'])}, PNG и PDF готовы")
        await browser.close()


def main() -> int:
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/diagrams")
    names = sys.argv[2:] or ["usecase", "activity-work-order", "class-model"]
    print("Конвертация SVG в PNG и PDF")
    asyncio.run(convert(folder, names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())