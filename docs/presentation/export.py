"""Экспорт презентации из HTML в PDF.

Слайды лежат в slides.html и свёрстаны под страницу 1280 на 720 точек.
Playwright печатает их через page.pdf с нулевым полем, поэтому каждый
<section class="slide"> становится отдельной страницей.

Запуск:
    python3 tools/diagrams/topng.py            # если нужен и PNG, и PDF
    python3 docs/presentation/export.py        # только PDF презентации
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "slides.html"
TARGET = HERE / "slides.pdf"

WIDTH = 1280
HEIGHT = 720


async def export() -> int:
    if not SOURCE.exists():
        print(f"Нет файла {SOURCE}", file=sys.stderr)
        return 1

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        # file:-протокол браузер открывает локально, в отличие от MCP-сервера.
        await page.goto(SOURCE.resolve().as_uri())
        await page.emulate_media(media="print")
        await page.pdf(
            path=str(TARGET),
            width=f"{WIDTH}px",
            height=f"{HEIGHT}px",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        slides = await page.locator("section.slide").count()
        await browser.close()

    size = TARGET.stat().st_size / 1024
    print(f"PDF готов: {TARGET} ({slides} слайдов, {size:.0f} КБ)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(export()))