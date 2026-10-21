"""Снимки веб-клиента для вики: настоящий браузер, настоящие данные.

Скрипт входит в приложение под нужной ролью и снимает экраны и блоки,
которые перечислены в docs/capture-checklist.md. Ничего не дорисовывается:
каждый кадр — это то, что отрисовал React на живом API.

Запуск (API и dev-сервер должны быть подняты):
    python tools/capture/web-shot.py               # все сцены
    python tools/capture/web-shot.py --only 39 42  # только страницы 39 и 42

Требуется playwright: python -m playwright install chromium (один раз).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
from playwright.sync_api import Browser, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "wiki" / "images"
BASE = "http://localhost:5173"
MAX_WIDTH = 1200

CREDENTIALS = {
    "manager": ("manager", "Manager123!"),
    "admin": ("admin", "Admin123!"),
}


@dataclass
class Scene:
    """Один кадр: куда идти, что снимать, под какой ролью."""

    name: str
    route: str
    role: str = "manager"
    # "page" — вся страница, "clip" — селектор, "card" — карточка по заголовку,
    # "top" — верхняя полоса области содержимого (карточки KPI).
    kind: str = "page"
    target: str = ""
    # Действие перед снимком: текст кнопки, по которой нужно щёлкнуть.
    click: str = ""


SCENES: list[Scene] = [
    # 37. Оболочка: меню, верхняя панель, хлебные крошки, тосты.
    Scene("37-menu", "/", kind="clip", target=".sidebar"),
    Scene("37-crumbs", "/work-orders", kind="clip", target=".section-title"),
    Scene("43-connection-badge", "/", kind="clip", target=".topbar"),
    Scene("51-guide-web-dashboard", "/", kind="page"),
    # 38. Дашборд: карточки KPI, состояния, сетка.
    Scene("38-metrics", "/", kind="top"),
    Scene("38-responsive", "/", kind="page"),
    # 39. Диаграммы дашборда — каждая карточка отдельным кадром.
    Scene("39-pie", "/", kind="card", target="Статусы заявок"),
    Scene("39-bar", "/", kind="card", target="Заявки по цехам"),
    Scene("39-line", "/", kind="card", target="Динамика по месяцам"),
    Scene("39-top", "/", kind="card", target="Топ-5 единиц по простою"),
    Scene("39-orders", "/", kind="card", target="Последние заявки"),
    Scene("51-guide-web-schedule", "/", kind="card", target="Выполнение графика ТО"),
    # 40. Аналитика: панель фильтров, сводка, распределения.
    Scene("40-filter-panel", "/analytics", kind="page"),
    Scene("40-orders-summary", "/analytics", kind="card", target="Сводка по заявкам"),
    Scene("40-filters-applied", "/analytics", kind="card", target="Анализ простоев"),
    # 42. Экспорт: кнопки CSV / PNG / PDF в панели аналитики.
    Scene("42-export-menu", "/analytics", kind="page"),
    # 45. Реестры: глобальные экраны разделов.
    Scene("45-users-page", "/users", role="admin", kind="page"),
    Scene("45-error-states", "/work-orders", kind="page"),
    # 50. Руководство пользователя: экраны, на которые оно ссылается.
    # Форма входа снимается в чистом профиле: под залогиненной сессией
    # маршрут /login сразу уводит на дашборд, и кадр вышел бы не тем.
    Scene("50-guide-login", "/login", role="anonymous", kind="page"),
    Scene("50-guide-dashboard", "/", kind="page"),
    Scene("50-guide-workorder", "/work-orders", kind="page"),
    Scene("50-guide-offline", "/materials", kind="page"),
    # 51. Руководство: роли и доступные экраны (меню под администратором).
    Scene("51-guide-roles", "/users", role="admin", kind="clip", target=".sidebar"),
    # 54. Сквозная проверка перед защитой.
    Scene("54-check-e2e", "/", kind="card", target="Последние заявки"),
]


def login(page: Page, role: str) -> None:
    username, password = CREDENTIALS[role]
    page.goto(f"{BASE}/login", wait_until="domcontentloaded")
    page.fill("form.login__card input >> nth=0", username)
    page.fill("form.login__card input >> nth=1", password)
    page.click("form.login__card button[type=submit]")
    page.wait_for_url(f"{BASE}/", timeout=15_000)
    page.wait_for_timeout(2_500)


def shoot(page: Page, scene: Scene) -> str:
    page.goto(f"{BASE}{scene.route}", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2_000)

    if scene.click:
        page.get_by_role("button", name=scene.click).first.click()
        page.wait_for_timeout(700)

    target = OUT / f"{scene.name}.png"

    if scene.kind == "page":
        page.screenshot(path=str(target), full_page=True)
    elif scene.kind == "clip":
        page.locator(scene.target).first.screenshot(path=str(target))
    elif scene.kind == "card":
        page.locator(".card", has_text=scene.target).first.screenshot(path=str(target))
    elif scene.kind == "top":
        box = page.locator(".main").first.bounding_box()
        if box is None:
            raise RuntimeError("не нашёл область содержимого .main")
        page.screenshot(
            path=str(target),
            clip={"x": box["x"], "y": box["y"], "width": box["width"], "height": min(320, box["height"])},
        )
    else:
        raise RuntimeError(f"неизвестный вид кадра: {scene.kind}")

    return shrink(target)


def shrink(path: Path) -> str:
    image = Image.open(path).convert("RGB")
    if image.width > MAX_WIDTH:
        height = round(image.height * MAX_WIDTH / image.width)
        image = image.resize((MAX_WIDTH, height), Image.LANCZOS)
        image.save(path, "PNG", optimize=True)

    return f"OK   {path.name}  {image.width}x{image.height}  {path.stat().st_size // 1024} КБ"


def session_for(browser: Browser, role: str) -> Page:
    context = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)
    page = context.new_page()

    # Роль "anonymous" — это ещё не вошедший пользователь: нужна для
    # кадра с формой входа и подсказок руководства.
    if role != "anonymous":
        login(page, role)

    return page


def main() -> int:
    parser = argparse.ArgumentParser(description="Снимки веб-клиента для вики")
    parser.add_argument("--only", nargs="*", default=None, help="номера страниц, например 38 42")
    args = parser.parse_args()

    scenes = SCENES
    if args.only:
        allowed = tuple(args.only)
        scenes = [scene for scene in SCENES if scene.name.startswith(allowed)]

    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        pages: dict[str, Page] = {}
        failures = 0

        for scene in scenes:
            if scene.role not in pages:
                pages[scene.role] = session_for(browser, scene.role)

            try:
                print(shoot(pages[scene.role], scene))
            except Exception as error:  # noqa: BLE001 — снимаем остальные кадры даже после сбоя
                failures += 1
                print(f"FAIL {scene.name}: {error}")

        browser.close()

    print(f"Готово: {len(scenes) - failures} из {len(scenes)}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
