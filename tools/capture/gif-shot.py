"""Гифки веб-клиента для вики: настоящий браузер, настоящие действия.

Скрипт входит в приложение под нужной ролью и записывает короткие
последовательности кадров: нажатие кнопки, смену фильтра, загрузку карточек,
наведение на диаграмму. Один кадр — один screenshot страницы; сборка в GIF
идёт через Pillow, поэтому ничего не дорисовывается: в кадре ровно то, что
отрисовал React на живом API.

Запуск (API и dev-сервер должны быть подняты):
    python tools/capture/gif-shot.py                 # все сцены
    python tools/capture/gif-shot.py --only 37 38    # только страницы 37 и 38

Требуется playwright: python -m playwright install chromium (один раз).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import Browser, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "wiki" / "gifs"
BASE = "http://localhost:5173"
VIEWPORT = {"width": 1280, "height": 800}
GIF_WIDTH = 1200
FRAME_MS = 800
PAUSE_MS = 320
MAX_FRAMES = 16

CREDENTIALS = {
    "manager": ("manager", "Manager123!"),
    "admin": ("admin", "Admin123!"),
}


class Recorder:
    """Копит кадры текущей сцены и следит за их числом."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.frames: list[Image.Image] = []

    def shot(self) -> None:
        if len(self.frames) >= MAX_FRAMES:
            return
        png = self.page.screenshot()
        from io import BytesIO

        image = Image.open(BytesIO(png)).convert("RGB")
        if image.width != GIF_WIDTH:
            height = round(image.height * GIF_WIDTH / image.width)
            image = image.resize((GIF_WIDTH, height), Image.LANCZOS)
        self.frames.append(image)

    def wait(self, ms: int, every: int = PAUSE_MS) -> None:
        """Ждёт, снимая промежуточные кадры — так видно загрузку и анимацию."""
        left = ms
        while left > 0:
            step = min(every, left)
            self.page.wait_for_timeout(step)
            left -= step
            self.shot()

    def type(self, selector: str, text: str, per_frame: int = 3) -> None:
        """Печатает текст и снимает кадр каждые несколько символов."""
        self.page.fill(selector, "")
        typed = 0
        for char in text:
            self.page.type(selector, char, delay=40)
            typed += 1
            if typed % per_frame == 0:
                self.shot()


def login(page: Page, role: str) -> None:
    username, password = CREDENTIALS[role]
    page.goto(f"{BASE}/login", wait_until="domcontentloaded")
    page.wait_for_timeout(700)
    page.fill("#login-user", username)
    page.fill("#login-pass", password)
    page.click("form.login__card button[type=submit]")
    page.wait_for_url(f"{BASE}/", timeout=15_000)
    page.wait_for_timeout(2_500)


def card(page: Page, title: str):
    return page.locator(".card", has_text=title).first


def scene_36_router_run(rec: Recorder) -> None:
    """Переходы по меню: дашборд → заявки → аналитика → материалы."""
    page = rec.page
    page.goto(BASE, wait_until="domcontentloaded")
    rec.wait(1_500)
    for label in ("Заявки", "Аналитика", "Материалы и ЗИП"):
        page.get_by_role("link", name=label).first.click()
        rec.wait(1_400)


def scene_37_auth_signin(rec: Recorder) -> None:
    """Вход: набор логина и пароля, отправка формы."""
    page = rec.page
    page.goto(f"{BASE}/login", wait_until="domcontentloaded")
    rec.wait(900)
    rec.type("#login-user", "manager")
    rec.type("#login-pass", "Manager123!")
    page.click("form.login__card button[type=submit]")
    rec.wait(2_600, every=500)


def scene_37_guard_redirect(rec: Recorder) -> None:
    """Закрытый маршрут без сессии уводит на форму входа."""
    page = rec.page
    page.goto(f"{BASE}/analytics", wait_until="domcontentloaded")
    rec.wait(1_600, every=400)


def scene_37_menu_role(rec: Recorder) -> None:
    """Меню под ролью: переход в справочники и обратно."""
    page = rec.page
    page.goto(BASE, wait_until="domcontentloaded")
    rec.wait(1_200)
    page.get_by_role("link", name="Бригады").first.click()
    rec.wait(1_300)
    page.get_by_role("link", name="Заявки").first.click()
    rec.wait(1_300)


def scene_37_toast_error(rec: Recorder) -> None:
    """Ошибка входа: тост с сообщением от API."""
    page = rec.page
    page.goto(f"{BASE}/login", wait_until="domcontentloaded")
    rec.wait(800)
    page.fill("#login-user", "manager")
    rec.type("#login-pass", "Wrong123!")
    page.click("form.login__card button[type=submit]")
    rec.wait(2_000, every=400)


def scene_38_metrics_load(rec: Recorder) -> None:
    """Загрузка дашборда: полоса загрузки, затем карточки KPI."""
    page = rec.page
    page.goto(BASE, wait_until="domcontentloaded")
    rec.shot()
    rec.wait(2_800, every=380)


def scene_38_auto_refresh(rec: Recorder) -> None:
    """Дашборд живёт: событие приходит по SSE и обновляет цифры."""
    rec.page.goto(BASE, wait_until="domcontentloaded")
    rec.wait(1_500)
    rec.wait(9_000, every=1_400)


def scene_39_pie_hover(rec: Recorder) -> None:
    """Круговая диаграмма: обводим секторы курсором."""
    page = rec.page
    page.goto(BASE, wait_until="domcontentloaded")
    rec.wait(2_200)
    chart = card(page, "Статусы заявок")
    chart.scroll_into_view_if_needed()
    rec.wait(500)
    box = chart.bounding_box()
    if box is None:
        raise RuntimeError("не нашёл карточку круговой диаграммы")
    # Секторы лежат в левой половине карточки: ведём курсор по дуге.
    import math

    center_x = box["x"] + box["width"] * 0.32
    center_y = box["y"] + box["height"] * 0.55
    radius = min(box["width"] * 0.18, box["height"] * 0.3)
    for step in range(7):
        angle = -math.pi / 2 + step * math.pi / 4
        page.mouse.move(center_x + radius * math.cos(angle), center_y + radius * math.sin(angle))
        rec.wait(650)


def scene_39_top_hover(rec: Recorder) -> None:
    """Список «Топ-5 по простою»: наведение на строки."""
    page = rec.page
    page.goto(BASE, wait_until="domcontentloaded")
    rec.wait(2_000)
    block = card(page, "Топ-5 единиц по простою")
    block.scroll_into_view_if_needed()
    rows = block.locator("tbody tr, li, .top-row")
    count = min(rows.count(), 5)
    rec.wait(400)
    if count == 0:
        block.hover()
        rec.wait(700)
        return
    for index in range(count):
        rows.nth(index).hover()
        rec.wait(650)


def scene_39_orders_open(rec: Recorder) -> None:
    """Последние заявки: открытие заявки из дашборда."""
    page = rec.page
    page.goto(BASE, wait_until="domcontentloaded")
    rec.wait(2_000)
    block = card(page, "Последние заявки")
    block.scroll_into_view_if_needed()
    rec.wait(400)
    link = block.locator("a, tbody tr").first
    link.click()
    rec.wait(1_600)


def scene_40_filter_change(rec: Recorder) -> None:
    """Аналитика: смена периода в панели фильтров."""
    page = rec.page
    page.goto(f"{BASE}/analytics", wait_until="domcontentloaded")
    rec.wait(2_200)
    panel = card(page, "Панель фильтров")
    panel.scroll_into_view_if_needed()
    dates = panel.locator("input[type=date]")
    dates.nth(0).fill("2026-01-01")
    rec.wait(600)
    dates.nth(1).fill("2026-12-31")
    rec.wait(1_400)


def scene_40_filters_applied(rec: Recorder) -> None:
    """Аналитика: применение фильтра, обновление всех блоков."""
    page = rec.page
    page.goto(f"{BASE}/analytics", wait_until="domcontentloaded")
    rec.wait(2_200)
    page.get_by_role("button", name="Обновить").first.click()
    rec.wait(2_200, every=350)


def scene_40_orders_summary(rec: Recorder) -> None:
    """Аналитика: прокрутка до сводки по заявкам."""
    page = rec.page
    page.goto(f"{BASE}/analytics", wait_until="domcontentloaded")
    rec.wait(2_200)
    card(page, "Сводка по заявкам").scroll_into_view_if_needed()
    rec.wait(900)


def scene_42_export_csv(rec: Recorder) -> None:
    """Экспорт блока в CSV: нажатие кнопки."""
    page = rec.page
    page.goto(f"{BASE}/analytics", wait_until="domcontentloaded")
    rec.wait(2_200)
    block = card(page, "Сводка по заявкам")
    block.scroll_into_view_if_needed()
    rec.wait(500)
    with page.expect_download() as download:
        block.get_by_role("button", name="CSV").first.click()
    download.value.save_as(str(ROOT / "wiki" / "_export.csv"))
    rec.wait(1_200)


def scene_42_export_png(rec: Recorder) -> None:
    """Экспорт блока в PNG: состояние «Снимаю…» и готовый файл."""
    page = rec.page
    page.goto(f"{BASE}/analytics", wait_until="domcontentloaded")
    rec.wait(2_200)
    block = card(page, "Сводка по заявкам")
    block.scroll_into_view_if_needed()
    rec.wait(500)
    with page.expect_download() as download:
        block.get_by_role("button", name="PNG").first.click()
    download.value.save_as(str(ROOT / "wiki" / "_export.png"))
    rec.wait(1_000)


def scene_42_export_pdf(rec: Recorder) -> None:
    """Экспорт блока в PDF: нажатие и подготовка файла."""
    page = rec.page
    page.goto(f"{BASE}/analytics", wait_until="domcontentloaded")
    rec.wait(2_200)
    block = card(page, "Сводка по заявкам")
    block.scroll_into_view_if_needed()
    rec.wait(500)
    with page.expect_download() as download:
        block.get_by_role("button", name="PDF").first.click()
    download.value.save_as(str(ROOT / "wiki" / "_export.pdf"))
    rec.wait(1_000)


def scene_42_export_menu(rec: Recorder) -> None:
    """Кнопки экспорта у блока: наведение на каждую."""
    page = rec.page
    page.goto(f"{BASE}/analytics", wait_until="domcontentloaded")
    rec.wait(2_200)
    block = card(page, "Сводка по заявкам")
    block.scroll_into_view_if_needed()
    rec.wait(400)
    for name in ("CSV", "PNG", "PDF"):
        block.get_by_role("button", name=name).first.hover()
        rec.wait(700)


def scene_43_sse_stream(rec: Recorder) -> None:
    """Индикатор соединения и живое обновление дашборда."""
    page = rec.page
    page.goto(BASE, wait_until="domcontentloaded")
    rec.wait(2_000)
    page.locator(".topbar").first.hover()
    rec.wait(500)
    rec.wait(6_000, every=1_200)


def scene_45_users_page(rec: Recorder) -> None:
    """Пользователи: поиск сотрудника по логину."""
    page = rec.page
    page.goto(f"{BASE}/users", wait_until="domcontentloaded")
    rec.wait(2_000)
    field = page.get_by_placeholder("master, Иванов").first
    field.scroll_into_view_if_needed()
    rec.wait(400)
    rec.type("input[placeholder='master, Иванов']", "master")
    rec.wait(1_400)


def scene_50_guide_login(rec: Recorder) -> None:
    """Руководство: форма входа с подсказками."""
    page = rec.page
    page.goto(f"{BASE}/login", wait_until="domcontentloaded")
    rec.wait(900)
    page.locator("form.login__card").first.hover()
    rec.wait(700)
    rec.type("#login-user", "admin")
    rec.wait(700)


def scene_50_guide_dashboard(rec: Recorder) -> None:
    """Руководство: прокрутка дашборда от KPI до диаграмм."""
    page = rec.page
    page.goto(BASE, wait_until="domcontentloaded")
    rec.wait(2_200)
    for _ in range(5):
        page.mouse.wheel(0, 380)
        rec.wait(650)


def scene_50_guide_workorder(rec: Recorder) -> None:
    """Руководство: поиск заявки и открытие карточки."""
    page = rec.page
    page.goto(f"{BASE}/work-orders", wait_until="domcontentloaded")
    rec.wait(2_200)
    rec.type("input[placeholder='номер, название, оборудование']", "0047")
    rec.wait(1_600)
    page.locator("tbody tr").first.click()
    rec.wait(1_600)


def scene_50_guide_offline(rec: Recorder) -> None:
    """Руководство: справочник материалов и карточка прихода."""
    page = rec.page
    page.goto(f"{BASE}/materials", wait_until="domcontentloaded")
    rec.wait(2_200)
    page.locator("tbody tr").first.click()
    rec.wait(1_400)


def scene_51_guide_web_dashboard(rec: Recorder) -> None:
    """Руководство: карточки KPI и наведение на показатель."""
    page = rec.page
    page.goto(BASE, wait_until="domcontentloaded")
    rec.wait(2_000)
    for title in ("Заявок всего", "В работе", "Просрочено"):
        block = page.locator(".card", has_text=title).first
        if block.count():
            block.hover()
            rec.wait(700)


def scene_51_guide_analytics(rec: Recorder) -> None:
    """Руководство: аналитика — фильтры и диаграммы."""
    page = rec.page
    page.goto(f"{BASE}/analytics", wait_until="domcontentloaded")
    rec.wait(2_200)
    for _ in range(6):
        page.mouse.wheel(0, 400)
        rec.wait(600)


def scene_51_guide_admin(rec: Recorder) -> None:
    """Руководство: экран администратора — пользователи и роли."""
    page = rec.page
    page.goto(f"{BASE}/users", wait_until="domcontentloaded")
    rec.wait(2_000)
    for _ in range(5):
        page.mouse.wheel(0, 380)
        rec.wait(600)


def scene_54_check_e2e(rec: Recorder) -> None:
    """Сквозная проверка: фильтр заявок и карточка выбранной заявки."""
    page = rec.page
    page.goto(f"{BASE}/work-orders", wait_until="domcontentloaded")
    rec.wait(2_000)
    selects = page.locator("select")
    if selects.count():
        selects.nth(0).select_option(index=1)
        rec.wait(1_400)
    page.locator("tbody tr").first.click()
    rec.wait(1_400)


def open_page(rec: Recorder, path: str, pause: int = 2_000) -> None:
    """Открывает страницу приложения и даёт данным загрузиться."""
    rec.page.goto(BASE + path, wait_until="domcontentloaded")
    rec.wait(pause)


def scroll_to(rec: Recorder, text: str) -> None:
    """Прокручивает страницу к блоку с заголовком `text` и снимает кадры."""
    rec.page.get_by_text(text, exact=False).first.scroll_into_view_if_needed()
    rec.wait(1_200, every=400)


def scene_38_states_retry(rec: Recorder) -> None:
    """Состояние ошибки и повторная загрузка, когда API снова отвечает."""
    page = rec.page
    page.goto(BASE, wait_until="domcontentloaded")
    rec.wait(1_500)

    # Ломаем только запросы к API: страница остаётся живой, а карточки
    # получают настоящую сетевую ошибку и показывают состояние «ошибка».
    page.route("**/api/**", lambda route: route.abort())
    page.reload(wait_until="domcontentloaded")
    rec.wait(2_500, every=600)

    page.unroute("**/api/**")
    retry = page.get_by_role("button", name="Повторить")
    if retry.count():
        retry.first.click()
    else:
        page.reload(wait_until="domcontentloaded")
    rec.wait(2_500, every=600)


def scene_41_downtime_block(rec: Recorder) -> None:
    """Аналитика: блок «Анализ простоев» с разрезом по цехам."""
    open_page(rec, "/analytics", 2_500)
    scroll_to(rec, "Блок 2. Анализ простоев")


def scene_41_materials_block(rec: Recorder) -> None:
    """Аналитика: блок «Расход материалов» и стоимость ЗИП."""
    open_page(rec, "/analytics", 2_500)
    scroll_to(rec, "Блок 3. Расход материалов")


def scene_41_schedule_block(rec: Recorder) -> None:
    """Аналитика: блок «Выполнение графика ТО»."""
    open_page(rec, "/analytics", 2_500)
    scroll_to(rec, "Блок 4. Выполнение графика ТО")


def scene_41_crew_rating(rec: Recorder) -> None:
    """Аналитика: рейтинг бригад — блок 5."""
    open_page(rec, "/analytics", 2_500)
    scroll_to(rec, "Блок 5. Эффективность бригад")


def scene_41_analytics_page(rec: Recorder) -> None:
    """Вся страница аналитики: фильтры, сводка и пять блоков подряд."""
    page = rec.page
    open_page(rec, "/analytics", 2_500)
    for _ in range(7):
        page.mouse.wheel(0, 620)
        rec.wait(420, every=420)


def scene_44_data_table_page(rec: Recorder) -> None:
    """Реестр оборудования: страницы таблицы и размер страницы."""
    page = rec.page
    open_page(rec, "/equipment", 2_500)
    forward = page.get_by_role("button", name="Вперёд").first
    if forward.count() and forward.is_enabled():
        forward.click()
        rec.wait(1_600)
        forward = page.get_by_role("button", name="Вперёд").first
        if forward.is_enabled():
            forward.click()
            rec.wait(1_400)
        back = page.get_by_role("button", name="Назад").first
        if back.is_enabled():
            back.click()
            rec.wait(1_200)
    else:
        # Строк меньше страницы — листание выключено, зато виден выбор
        # «на странице»: меняем его и прокручиваем таблицу.
        pager = page.locator(".pager select")
        if pager.count():
            pager.first.select_option(index=1)
            rec.wait(1_800)
        page.mouse.wheel(0, 500)
        rec.wait(1_200, every=400)


def scene_44_equipment_filter(rec: Recorder) -> None:
    """Реестр оборудования: поиск «ПР» и фильтр по цеху."""
    page = rec.page
    open_page(rec, "/equipment", 2_500)
    selects = page.locator("select")
    if selects.count():
        selects.nth(0).select_option(index=1)
        rec.wait(1_200)
    field = page.locator("input[placeholder='ПР-2 или пресс']")
    rec.type("input[placeholder='ПР-2 или пресс']", "ПР", per_frame=1) if field.count() else None
    page.get_by_role("button", name="Найти").first.click()
    rec.wait(2_000)


def scene_44_orders_registry(rec: Recorder) -> None:
    """Реестр заявок: поиск по номеру и открытие карточки."""
    page = rec.page
    open_page(rec, "/work-orders", 2_500)
    page.fill("input[placeholder='номер, название, оборудование']", "0047")
    rec.wait(600, every=300)
    page.get_by_role("button", name="Найти").first.click()
    rec.wait(2_000)
    rows = page.locator("tbody tr")
    if rows.count():
        rows.first.click()
        rec.wait(1_600)


def scene_44_schedule_month(rec: Recorder) -> None:
    """График ТО: записи месяца и фильтр по статусу."""
    page = rec.page
    open_page(rec, "/schedule", 2_500)
    selects = page.locator("select")
    if selects.count() > 1:
        selects.nth(1).select_option(index=1)
        rec.wait(1_800)
    page.mouse.wheel(0, 400)
    rec.wait(1_200, every=400)


def scene_42_print_preview(rec: Recorder) -> None:
    """Печатная версия аналитики: панель фильтров скрыта, блоки на листе."""
    page = rec.page
    open_page(rec, "/analytics", 2_500)
    page.emulate_media(media="print")
    rec.wait(2_000, every=500)
    page.mouse.wheel(0, 900)
    rec.wait(1_500, every=500)
    page.emulate_media(media="screen")


def scene_43_sse_reconnect(rec: Recorder) -> None:
    """SSE: разрыв связи, статус «нет соединения», восстановление потока."""
    page = rec.page
    page.goto(BASE, wait_until="domcontentloaded")
    rec.wait(2_000)
    page.context.set_offline(True)
    rec.wait(4_500, every=700)
    page.context.set_offline(False)
    rec.wait(5_000, every=700)


def scene_43_polling_ticks(rec: Recorder) -> None:
    """Резервный опрос: дашборд обновляется по таймеру."""
    rec.page.goto(BASE, wait_until="domcontentloaded")
    rec.wait(8_000, every=800)


def scene_43_connection_states(rec: Recorder) -> None:
    """Бейдж соединения: в сети → офлайн → снова в сети."""
    page = rec.page
    page.goto(BASE, wait_until="domcontentloaded")
    rec.wait(1_500)
    page.context.set_offline(True)
    rec.wait(3_500, every=600)
    page.context.set_offline(False)
    rec.wait(3_500, every=600)


def scene_43_dashboard_source(rec: Recorder) -> None:
    """Источник данных дашборда: последние заявки приходят из SSE-потока."""
    page = rec.page
    open_page(rec, "/", 2_500)
    scroll_to(rec, "Последние заявки")
    rows = page.locator("tbody tr")
    if rows.count():
        rows.first.hover()
        rec.wait(1_400, every=400)


def scene_48_swagger_ui(rec: Recorder) -> None:
    """Swagger UI: список контроллеров и свёрнутые операции."""
    page = rec.page
    page.goto("http://localhost:5080/swagger/index.html", wait_until="domcontentloaded")
    rec.wait(3_000, every=600)
    page.mouse.wheel(0, 700)
    rec.wait(1_500, every=500)


def scene_48_swagger_example(rec: Recorder) -> None:
    """Swagger UI: раскрытая операция входа с примером ответа."""
    page = rec.page
    page.goto("http://localhost:5080/swagger/index.html", wait_until="domcontentloaded")
    # Swagger рисует операции после загрузки спецификации: при DPR 1.5
    # это заметно дольше, чем раньше, поэтому ждём появления блока.
    page.wait_for_selector(".opblock-summary", timeout=25_000)
    rec.wait(1_000)
    login = page.locator(".opblock-summary").filter(has_text="login").first
    if login.count():
        login.click()
    else:
        page.locator(".opblock-summary").first.click()
    rec.wait(1_500)
    try_it = page.get_by_role("button", name="Try it out")
    if try_it.count():
        try_it.first.click()
        rec.wait(1_200)
    execute = page.get_by_role("button", name="Execute")
    if execute.count():
        execute.first.click()
        rec.wait(2_500)


def scene_48_openapi_export(rec: Recorder) -> None:
    """Экспорт спецификации: живой openapi.json из запущенного API."""
    page = rec.page
    page.goto("http://localhost:5080/swagger/v1/swagger.json", wait_until="domcontentloaded")
    rec.wait(1_500, every=500)
    page.mouse.wheel(0, 600)
    rec.wait(1_500, every=500)


def scene_45_error_403(rec: Recorder) -> None:
    """Доступ запрещён: руководитель открывает раздел «Пользователи»."""
    page = rec.page
    page.goto(BASE + "/users", wait_until="domcontentloaded")
    rec.wait(2_500, every=600)
    # Если приложение просто вернуло на дашборд — вернёмся в раздел, чтобы
    # кадр показал именно реакцию на прямой переход по адресу.
    if "/users" not in page.url:
        page.goto(BASE + "/users", wait_until="domcontentloaded")
        rec.wait(2_000, every=500)


# Сцены: имя гифки → роль → функция.
SCENES = [    ("36-router-run", "manager", scene_36_router_run),
    ("37-auth-signin", "anonymous", scene_37_auth_signin),
    ("37-guard-redirect", "anonymous", scene_37_guard_redirect),
    ("37-menu-role", "manager", scene_37_menu_role),
    ("37-toast-error", "anonymous", scene_37_toast_error),
    ("38-metrics-load", "manager", scene_38_metrics_load),
    ("38-auto-refresh", "manager", scene_38_auto_refresh),
    ("39-pie-hover", "manager", scene_39_pie_hover),
    ("39-top-hover", "manager", scene_39_top_hover),
    ("39-orders-open", "manager", scene_39_orders_open),
    ("40-filter-change", "manager", scene_40_filter_change),
    ("40-filters-applied", "manager", scene_40_filters_applied),
    ("40-orders-summary", "manager", scene_40_orders_summary),
    ("42-export-csv", "manager", scene_42_export_csv),
    ("42-export-png", "manager", scene_42_export_png),
    ("42-export-pdf", "manager", scene_42_export_pdf),
    ("42-export-menu", "manager", scene_42_export_menu),
    ("43-sse-stream", "manager", scene_43_sse_stream),
    ("45-users-page", "admin", scene_45_users_page),
    ("50-guide-login", "anonymous", scene_50_guide_login),
    ("50-guide-dashboard", "manager", scene_50_guide_dashboard),
    ("50-guide-workorder", "manager", scene_50_guide_workorder),
    ("50-guide-offline", "manager", scene_50_guide_offline),
    ("51-guide-web-dashboard", "manager", scene_51_guide_web_dashboard),
    ("51-guide-analytics", "manager", scene_51_guide_analytics),
    ("51-guide-admin", "admin", scene_51_guide_admin),
    ("54-check-e2e", "manager", scene_54_check_e2e),
    ("38-states-retry", "manager", scene_38_states_retry),
    ("41-downtime-block", "manager", scene_41_downtime_block),
    ("41-materials-block", "manager", scene_41_materials_block),
    ("41-schedule-block", "manager", scene_41_schedule_block),
    ("41-crew-rating", "manager", scene_41_crew_rating),
    ("41-analytics-page", "manager", scene_41_analytics_page),
    ("42-print-preview", "manager", scene_42_print_preview),
    ("43-sse-reconnect", "manager", scene_43_sse_reconnect),
    ("43-polling-ticks", "manager", scene_43_polling_ticks),
    ("43-connection-states", "manager", scene_43_connection_states),
    ("43-dashboard-source", "manager", scene_43_dashboard_source),
    ("44-data-table-page", "manager", scene_44_data_table_page),
    ("44-equipment-filter", "manager", scene_44_equipment_filter),
    ("44-orders-registry", "manager", scene_44_orders_registry),
    ("44-schedule-month", "manager", scene_44_schedule_month),
    ("45-error-403", "manager", scene_45_error_403),
    ("48-swagger-ui", "anonymous", scene_48_swagger_ui),
    ("48-swagger-example", "anonymous", scene_48_swagger_example),
    ("48-openapi-export", "anonymous", scene_48_openapi_export),
]

# Последний кадр сцены сохраняем ещё и как PNG для страницы: на странице
# картинка нужна как «состояние экрана», а гифка — как движение к нему.
# Имя PNG совпадает с объявленным в sprints.py.
PNG_FOR = {
    "38-states-retry": "38-states",
    "41-downtime-block": "41-downtime-block",
    "41-materials-block": "41-materials-block",
    "41-schedule-block": "41-schedule-block",
    "41-crew-rating": "41-crew-rating",
    "41-analytics-page": "41-analytics-page",
    "42-print-preview": "42-print-preview",
    "43-connection-states": "43-connection-states",
    "44-data-table-page": "44-data-table-page",
    "44-equipment-filter": "44-equipment-filter",
    "44-orders-registry": "44-orders-registry",
    "44-schedule-month": "44-schedule-month",
    "48-swagger-ui": "48-swagger-ui",
}

IMAGES = ROOT / "wiki" / "images"


def save_gif(frames: list[Image.Image], target: Path) -> str:
    """Собирает GIF и ужимает его, если файл вышел тяжёлым.

    Кадры — тёмный интерфейс с градиентами, поэтому «как есть» гифка на
    десять кадров весит около мегабайта. Для вики это много: страница с
    тремя такими гифками грузится секунды. Поэтому пробуем по убыванию
    качества и останавливаемся, когда файл укладывается в бюджет.
    """
    if len(frames) < 2:
        frames = frames * 2

    # Тёмный интерфейс с мелким текстом плохо сжимается: сначала пробуем
    # 256 цветов без потери ширины и только потом ужимаем кадр.
    budget_kb = 2600
    attempts = [(1200, 256), (1200, 192)]

    saved = None
    for width, colors in attempts:
        prepared = []
        for frame in frames:
            image = frame
            if image.width != width:
                height = round(image.height * width / image.width)
                image = image.resize((width, height), Image.LANCZOS)
            prepared.append(image.quantize(colors=colors, method=Image.MEDIANCUT))
        prepared[0].save(
            target,
            save_all=True,
            append_images=prepared[1:],
            duration=FRAME_MS,
            loop=0,
            optimize=True,
            disposal=2,
        )
        saved = (width, colors)
        if target.stat().st_size <= budget_kb * 1024:
            break

    return (
        f"OK   {target.name}  кадров={len(frames)}  {saved[0]}px/{saved[1]}цв"
        f"  {target.stat().st_size // 1024} КБ"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Гифки веб-клиента для вики")
    parser.add_argument("--only", nargs="*", default=None, help="номера страниц, например 37 42")
    args = parser.parse_args()

    scenes = SCENES
    if args.only:
        allowed = tuple(args.only)
        scenes = [scene for scene in SCENES if scene[0].startswith(allowed)]

    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser: Browser = playwright.chromium.launch()
        contexts: dict[str, Page] = {}
        failures = 0

        for name, role, action in scenes:
            # Анонимные сцены идут каждая в своём профиле: сцена входа
            # заканчивается авторизацией, и следующий кадр «не вошедшего»
            # пользователя в том же профиле уже не снять.
            if role == "anonymous":
                context = browser.new_context(viewport=VIEWPORT, device_scale_factor=1.5)
                page = context.new_page()
            else:
                if role not in contexts:
                    context = browser.new_context(viewport=VIEWPORT, device_scale_factor=1.5)
                    page = context.new_page()
                    login(page, role)
                    contexts[role] = page
                page = contexts[role]

            page.set_default_timeout(8_000)

            recorder = Recorder(page)
            try:
                action(recorder)
                print(save_gif(recorder.frames, OUT / f"{name}.gif"))

                png_name = PNG_FOR.get(name)
                if png_name and recorder.frames:
                    target = IMAGES / f"{png_name}.png"
                    # Сохраняем всегда: при повторной съёмке кадр должен
                    # обновиться до текущего разрешения (раньше старый файл
                    # оставался на диске и вики показывала 960 px).
                    recorder.frames[-1].save(target)
                    print(f"PNG  {target.name}  {target.stat().st_size // 1024} КБ")
            except Exception as error:  # noqa: BLE001 — снимаем остальные сцены даже после сбоя
                failures += 1
                # Сообщение Playwright может содержать символы вне cp866,
                # а консоль на этой машине именно её и ждёт.
                text = str(error).encode("ascii", "replace").decode("ascii")
                print(f"FAIL {name}: {text}")
            finally:
                # Сцены со сетевыми сбоями выключают сеть контекста. Если
                # сцена упала посередине, контекст остался бы офлайн и
                # следующие сцены не смогли бы даже открыть страницу.
                try:
                    page.context.set_offline(False)
                except Exception:  # noqa: BLE001 — контекст мог уже закрыться
                    pass
                if role == "anonymous":
                    context.close()

        browser.close()

    print(f"\nГотово: {len(scenes) - failures} из {len(scenes)}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
