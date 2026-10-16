"""Проверка вёрстки слайдов: PNG-превью нескольких экранов.

Нужен, чтобы глазами убедиться, что таблицы и схемы не вылезают
за границы слайда. Файлы складываются во временный каталог.
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "slides.html"
WANTED = [1, 4, 8, 12]


async def shoot() -> int:
    out = Path(tempfile.gettempdir()) / "toirprof-slides"
    out.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page.goto(SOURCE.resolve().as_uri())

        total = await page.locator("section.slide").count()
        for index in WANTED:
            if index > total:
                continue
            target = out / f"slide-{index:02d}.png"
            await page.locator("section.slide").nth(index - 1).screenshot(path=str(target))
            print(target)

        await browser.close()

    print(f"Всего слайдов в колоде: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(shoot()))