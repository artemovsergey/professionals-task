"""Диаграмма вариантов использования системы ТОиР-Проф.

Актёры, граница системы, отношение ассоциации и два стереотипа
отношений — include (обязательная часть) и extend (необязательное
поведение). Требование листа задания: показать все четыре элемента.

Раскладка сделана не «красиво», а читаемо. Варианты сгруппированы по
ответственности в колонки, над каждой колонкой стоит свой актёр и
проводит «шину» вниз, от которой отходят короткие связи к вариантам.
Так линии не пересекаются ни друг с другом, ни с названиями.
"""

from __future__ import annotations

from svgkit import ACCENT, ACCENT_SOFT, INK, LANE_A, LANE_B, LINE, MUTED, PAPER, Canvas, Drawio

TITLE = "Диаграмма вариантов использования — ТОиР-Проф"

WIDTH = 1480
HEIGHT = 900

# (центр x, заголовок колонки, подпись, подпись актёра, роль актёра)
COLUMNS = [
    (430.0, "Мастер участка", "своя работа", "Составляет заявки,\nведёт работы, списывает ЗИП", "Актёр"),
    (720.0, "Руководитель цеха", "управление и аналитика", "Назначает бригады,\nсмотрит аналитику и отчёты", "Актёр"),
    (1010.0, "Администратор", "справочники и доступы", "Ведёт справочники, роли\nи журнал операций", "Актёр"),
    (1290.0, "Служебные варианты", "include и extend", "Вызываются из основных\nвариантов автоматически", "Служебные"),
]

# (ключ, подпись, колонка, строка, тон)
USE_CASES = [
    ("uc_auth", "Авторизация", 0, 0, LANE_B),
    ("uc_create", "Создать заявку", 0, 1, LANE_B),
    ("uc_view_schedule", "Смотреть график ТО", 0, 2, LANE_B),
    ("uc_work", "Выполнить работы", 0, 3, LANE_B),
    ("uc_offline", "Офлайн-очередь", 0, 4, LANE_A),
    ("uc_kpi", "Дашборд", 1, 0, LANE_B),
    ("uc_assign", "Назначить бригаду", 1, 1, LANE_B),
    ("uc_analytics", "Смотреть аналитику", 1, 2, LANE_B),
    ("uc_report", "Сформировать отчёт", 1, 3, LANE_B),
    ("uc_schedule", "Вести график ТО", 2, 0, LANE_B),
    ("uc_users", "Пользователи и роли", 2, 1, LANE_B),
    ("uc_audit", "Журнал операций", 2, 2, LANE_B),
    ("uc_rights", "Проверить права роли", 3, 0, LANE_A),
    ("uc_next_date", "Рассчитать дату ТО", 3, 1, LANE_A),
    ("uc_stock", "Проверить остаток ЗИП", 3, 2, LANE_A),
    ("uc_notify", "Уведомить о просрочке", 3, 3, LANE_A),
    ("uc_search", "Поиск и фильтры", 3, 4, LANE_A),
    ("uc_export", "Экспорт отчёта", 3, 5, LANE_A),
]

# include — обязательная часть другого варианта; extend — необязательная.
RELATIONS = [
    ("uc_auth", "uc_rights", "include"),
    ("uc_schedule", "uc_next_date", "include"),
    ("uc_work", "uc_stock", "include"),
    ("uc_report", "uc_analytics", "include"),
    ("uc_notify", "uc_view_schedule", "extend"),
    ("uc_export", "uc_report", "extend"),
    ("uc_search", "uc_analytics", "extend"),
    ("uc_offline", "uc_create", "extend"),
]

BOUNDARY_X = 260.0
BOUNDARY_W = 1180.0
BOUNDARY_Y = 206.0
BOUNDARY_H = 524.0

RX = 112.0
RY = 28.0
TOP_CY = 336.0
ROW = 80.0


def positions() -> dict[str, tuple[float, float]]:
    return {key: (COLUMNS[col][0], TOP_CY + ROW * row) for key, _, col, row, _ in USE_CASES}


def _stick_figure(canvas: Canvas, cx: float, y: float, scale: float = 1.0) -> None:
    head = 11.0 * scale
    canvas.ellipse(cx, y, head, head, fill=PAPER, stroke=INK, width=1.5)
    canvas.line(cx, y + head, cx, y + 38 * scale, stroke=INK, width=1.5)
    canvas.line(cx, y + 16 * scale, cx - 18 * scale, y + 26 * scale, stroke=INK, width=1.5)
    canvas.line(cx, y + 16 * scale, cx + 18 * scale, y + 26 * scale, stroke=INK, width=1.5)
    canvas.line(cx, y + 38 * scale, cx - 14 * scale, y + 62 * scale, stroke=INK, width=1.5)
    canvas.line(cx, y + 38 * scale, cx + 14 * scale, y + 62 * scale, stroke=INK, width=1.5)


def draw(canvas: Canvas, art: Drawio) -> None:
    pos = positions()

    canvas.text(24, 38, TITLE, size=20, weight="bold")
    canvas.text(
        24,
        60,
        "Актёры, граница системы, ассоциации и отношения «include» / «extend»",
        size=12,
        fill=MUTED,
    )

    # ---- граница системы ---------------------------------------------------
    canvas.rect(BOUNDARY_X, BOUNDARY_Y, BOUNDARY_W, BOUNDARY_H, fill="#fbfcfd", stroke=ACCENT, width=1.6)
    canvas.text(BOUNDARY_X + 18, BOUNDARY_Y + 28, "ТОиР-Проф", size=17, weight="bold", fill=ACCENT)
    canvas.text(BOUNDARY_X + 130, BOUNDARY_Y + 28, "— граница системы", size=12, fill=MUTED)

    # ---- заголовки колонок и «шины» ассоциаций ----------------------------
    for cx, title, note, actor_note, role in COLUMNS:
        canvas.rect(cx - RX - 14, BOUNDARY_Y + 44, RX * 2 + 28, 56, fill=ACCENT_SOFT, stroke=ACCENT, rx=6)
        canvas.text(cx, BOUNDARY_Y + 66, title, size=12, weight="bold", anchor="middle", fill=ACCENT)
        canvas.text(cx, BOUNDARY_Y + 84, note, size=10, anchor="middle", fill=MUTED)

        if role != "Актёр":
            continue

        # Актёр стоит над своей колонкой вне границы: так его фигура не
        # занимает место слева. Имя не подписываем ещё раз — оно уже есть
        # в заголовке колонки, иначе подпись налезает на границу.
        _stick_figure(canvas, cx, 96.0)
        for index, row in enumerate(actor_note.split("\n")):
            canvas.text(cx, 166 + index * 13, row, size=10, anchor="middle", fill=MUTED)

    # ---- ассоциации актёра со своими вариантами ---------------------------
    # «Шина» идёт по левому краю колонки, а не по её центру: иначе
    # вертикаль проходила прямо сквозь все варианты и перечёркивала их.
    for index, column in enumerate(COLUMNS[:3]):
        cx = column[0]
        bus = cx - RX - 14
        keys = [key for key, _, col, _, _ in USE_CASES if col == index]
        bottom = max(pos[key][1] for key in keys)
        canvas.polyline(
            [(cx, 158.0), (cx, BOUNDARY_Y - 10.0), (bus, BOUNDARY_Y - 10.0)],
            stroke=INK,
            width=1.3,
        )
        canvas.line(bus, BOUNDARY_Y + 100, bus, bottom, stroke=INK, width=1.3)
        for key in keys:
            tx, ty = pos[key]
            canvas.polyline([(bus, ty), (tx - RX - 3, ty)], stroke=INK, width=1.1)

    # ---- варианты использования -------------------------------------------
    for key, label, col, row, tone in USE_CASES:
        cx, cy = pos[key]
        canvas.ellipse(cx, cy, RX, RY, fill=tone, stroke=ACCENT, width=1.4)
        canvas.text(cx, cy + 4, label, size=12, anchor="middle")
        art.shape(
            cx - RX,
            cy - RY,
            RX * 2,
            RY * 2,
            label,
            style="shape=ellipse;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#2f6fb0;",
        )

    # ---- отношения include / extend ----------------------------------------
    # Подписи стереотипов вынесены в легенду: на самой линии они ложились
    # поверх названий вариантов и делали схему нечитаемой.
    for source, target, _kind in RELATIONS:
        sx, sy = pos[source]
        tx, ty = pos[target]
        canvas.polyline(
            [(sx, sy - RY + 2), (sx, sy - RY - 16), (tx, ty - RY - 16), (tx, ty - RY + 2)],
            stroke=MUTED,
            width=1.2,
            dash="7 5",
            arrow=True,
        )

    # ---- легенда ------------------------------------------------------------
    canvas.rect(24, 752, BOUNDARY_W + 236 - 236, 122, fill=PAPER, stroke=LINE, rx=6)
    canvas.text(40, 776, "Обозначения", size=13, weight="bold")
    canvas.line(40, 796, 84, 796, stroke=MUTED, dash="7 5", width=1.2)
    canvas.text(94, 800, "«include» — обязательная часть варианта", size=11, fill=MUTED)
    canvas.line(400, 796, 444, 796, stroke=MUTED, dash="7 5", width=1.2)
    canvas.text(454, 800, "«extend» — необязательное поведение", size=11, fill=MUTED)
    canvas.ellipse(820, 796, 16, 9, fill=LANE_A, stroke=ACCENT)
    canvas.text(846, 800, "служебный вариант", size=11, fill=MUTED)
    canvas.ellipse(960, 796, 16, 9, fill=LANE_B, stroke=ACCENT)
    canvas.text(986, 800, "основной вариант", size=11, fill=MUTED)

    canvas.text(40, 830, "include:", size=11, weight="bold")
    canvas.text(
        100,
        830,
        "авторизация → проверка прав роли · вести график ТО → расчёт даты ТО · "
        "выполнить работы → проверка остатка ЗИП · сформировать отчёт → смотреть аналитику",
        size=11,
        fill=MUTED,
    )
    canvas.text(40, 852, "extend:", size=11, weight="bold")
    canvas.text(
        100,
        852,
        "уведомить о просрочке → смотреть график ТО · экспорт отчёта → сформировать отчёт · "
        "поиск и фильтры → смотреть аналитику · офлайн-очередь → создать заявку",
        size=11,
        fill=MUTED,
    )


def to_svg() -> str:
    canvas = Canvas(WIDTH, HEIGHT)
    draw(canvas, Drawio(WIDTH, HEIGHT))
    return canvas.to_svg(TITLE)


def to_drawio() -> str:
    art = Drawio(WIDTH, HEIGHT)
    draw(Canvas(WIDTH, HEIGHT), art)
    return art.to_xml("usecase")


REQUIREMENTS = [
    "Актёры: мастер участка, руководитель цеха, администратор.",
    "Граница системы: прямоугольник «ТОиР-Проф».",
    "18 вариантов использования, из них 7 служебных.",
    "Отношения «include» — 4: авторизация → проверка прав, график ТО → расчёт даты, выполнение работ → проверка остатка, отчёт → аналитика.",
    "Отношения «extend» — 4: уведомление о просрочке → просмотр графика, экспорт → отчёт, поиск и фильтры → аналитика, офлайн-очередь → создание заявки.",
    "Варианты сгруппированы по колонкам ответственности: актёр стоит над своей колонкой и связывается «шиной», поэтому линии не пересекаются.",
]