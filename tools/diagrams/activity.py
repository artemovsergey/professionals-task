"""Диаграмма деятельности «Выполнение заявки на ремонт и ТО».

Требование листа задания: начало и конец, действия, ветвления, fork/join и
дорожки. Дорожки соответствуют участникам процесса, поэтому по диаграмме
видно, кто за что отвечает и где границы между человеком и системой.
"""

from __future__ import annotations

from svgkit import ACCENT, BAD, INK, LANE_A, LANE_B, LINE, MUTED, OK, PAPER, WARN, Canvas, Drawio

TITLE = "Диаграмма деятельности — выполнение заявки на ремонт и ТО"

WIDTH = 1320

# Дорожки: (название, ширина). Раскладка слева направо.
LANES = [
    ("Мастер", 300),
    ("Система", 300),
    ("Бригада", 300),
    ("Руководитель", 300),
]
LANE_X = 60.0
LANE_TOP = 120.0

BOX_W = 210.0
BOX_H = 44.0
ROW = 66.0
STEP_Y = 172.0

# Действия идут сверху вниз; в каждой строке указан участник.
# Вид: "start", "end", "action", "decision", "fork", "join".
STEPS = [
    ("start", "Мастер", 0, "", "start"),
    ("a1", "Мастер", 0, "Заполнить заявку:\nоборудование, описание, приоритет", "action"),
    ("d1", "Система", 1, "Оборудование\nв эксплуатации?", "decision"),
    ("e1", "Мастер", 0, "Отказ: создать\nзаявку на возврат в работу", "action"),
    ("a2", "Система", 1, "Сгенерировать номер\nZ-YYYY-XXXX", "action"),
    ("a3", "Система", 1, "Сохранить заявку,\nстатус «Черновик»", "action"),
    ("a4", "Руководитель", 3, "Назначить бригаду", "action"),
    ("d2", "Система", 1, "Бригада\nне занята?", "decision"),
    ("e2", "Руководитель", 3, "Выбрать другую\nбригаду", "action"),
    ("a5", "Система", 1, "Статус «Назначена»", "action"),
    ("fork", "Система", 1, "", "fork"),
    ("b1", "Бригада", 2, "Подготовить\nматериалы и ЗИП", "action"),
    ("b2", "Бригада", 2, "Прийти на объект,\nначать работу", "action"),
    ("a6", "Система", 1, "Зафиксировать факт\nначала, статус «В работе»", "action"),
    ("join", "Система", 1, "", "join"),
    ("b3", "Бригада", 2, "Выполнить ремонт\nили ТО", "action"),
    ("d3", "Бригада", 2, "Нужен\nматериал?", "decision"),
    ("b4", "Бригада", 2, "Списать материал\nиз ЗИП", "action"),
    ("d4", "Система", 1, "Остаток\nдостаточен?", "decision"),
    ("e3", "Мастер", 0, "Оформить приход\nили заявку поставщику", "action"),
    ("b5", "Бригада", 2, "Завершить работу,\nуказать причину", "action"),
    ("d5", "Система", 1, "Даты и причина\nзаполнены?", "decision"),
    ("a7", "Система", 1, "Рассчитать простой,\nстатус «Завершена»", "action"),
    ("a8", "Система", 1, "Записать в журнал,\nобновить аналитику", "action"),
    ("end", "Система", 1, "", "end"),
]

# Переходы: (из шага, в шаг, подпись на ребре)
EDGES = [
    ("start", "a1", ""),
    ("a1", "d1", ""),
    ("d1", "a2", "да"),
    ("d1", "e1", "нет"),
    ("e1", "end", ""),
    ("a2", "a3", ""),
    ("a3", "a4", ""),
    ("a4", "d2", ""),
    ("d2", "a5", "да"),
    ("d2", "e2", "нет"),
    ("e2", "a4", ""),
    ("a5", "fork", ""),
    ("fork", "b1", ""),
    ("fork", "b2", ""),
    ("b1", "join", ""),
    ("b2", "join", ""),
    ("join", "b3", ""),
    ("b3", "d3", ""),
    ("d3", "b4", "да"),
    ("d3", "b5", "нет"),
    ("b4", "d4", ""),
    ("d4", "b5", "да"),
    ("d4", "e3", "нет"),
    ("e3", "b4", "после прихода"),
    ("b5", "d5", ""),
    ("d5", "a7", "да"),
    ("d5", "b5", "нет, уточнить"),
    ("a7", "a8", ""),
    ("a8", "end", ""),
]

HEIGHT = int(STEP_Y + ROW * len(STEPS) + 220)

# Дорожка заканчивается вместе с последним шагом плюс запас под легенду.
LANE_H = float(HEIGHT) - LANE_TOP - 130.0


def lane_x(index: int) -> float:
    return LANE_X + sum(width for _, width in LANES[:index]) + 10.0


def step_y(index: int) -> float:
    return STEP_Y + ROW * index


def positions() -> dict[str, tuple[float, float]]:
    """Возвращает центр каждого шага."""
    result: dict[str, tuple[float, float]] = {}
    for index, (key, _lane, col, _label, _kind) in enumerate(STEPS):
        result[key] = (lane_x(col) + LANES[col][1] / 2, step_y(index))
    return result


def _terminal(canvas: Canvas, cx: float, cy: float, filled: bool) -> None:
    canvas.ellipse(cx, cy, 15, 15, fill=INK if filled else PAPER, stroke=INK, width=1.6)


def _action(canvas: Canvas, cx: float, cy: float, lines: list[str]) -> None:
    canvas.rect(cx - BOX_W / 2, cy - BOX_H / 2, BOX_W, BOX_H, fill=LANE_B, stroke=INK, width=1.3, rx=3)
    for index, line in enumerate(lines):
        offset = (index - (len(lines) - 1) / 2) * 14
        canvas.text(cx, cy + 5 + offset, line, size=11, anchor="middle")


def _decision(canvas: Canvas, cx: float, cy: float, lines: list[str]) -> None:
    w = 76.0
    h = 40.0
    canvas.path(
        f"M{cx:g},{cy - h:g} L{cx + w:g},{cy:g} L{cx:g},{cy + h:g} L{cx - w:g},{cy:g} Z",
        stroke=WARN,
        width=1.5,
    )
    canvas.rect(cx - 86, cy - 14, 172, 30, fill=PAPER, stroke="none", rx=4)
    for index, line in enumerate(lines):
        offset = (index - (len(lines) - 1) / 2) * 13
        canvas.text(cx, cy + 4 + offset, line, size=10, anchor="middle")


def _bar(canvas: Canvas, cx: float, cy: float, horizontal: bool) -> None:
    if horizontal:
        canvas.rect(cx - 52, cy - 3, 104, 6, fill=INK, stroke=INK)
    else:
        canvas.rect(cx - 3, cy - 24, 6, 48, fill=INK, stroke=INK)


def draw(canvas: Canvas, art: Drawio) -> None:
    pos = positions()

    canvas.text(24, 38, TITLE, size=20, weight="bold")
    canvas.text(
        24,
        60,
        "Дорожки по участникам процесса, ветвления — ромбы, параллельные действия — fork и join",
        size=12,
        fill=MUTED,
    )

    # ---- дорожки -----------------------------------------------------------
    for index, (name, width) in enumerate(LANES):
        x = lane_x(index) - 10.0
        canvas.rect(x, LANE_TOP, width - 0.0, LANE_H, fill=LANE_A if index % 2 == 0 else LANE_B, stroke=LINE)
        canvas.rect(x, LANE_TOP, width, 34, fill=ACCENT, stroke=ACCENT)
        canvas.text(x + width / 2, LANE_TOP + 23, name, size=13, weight="bold", anchor="middle", fill=PAPER)

    # ---- переходы (рисуем первыми, чтобы узлы лежали поверх) --------------
    label_slots: list[tuple[float, float, str]] = []
    for source, target, label in EDGES:
        sx, sy = pos[source]
        tx, ty = pos[target]
        if abs(sx - tx) < 1:
            canvas.polyline([(sx, sy), (tx, ty)], stroke=INK, width=1.3, arrow=True)
            if label:
                label_slots.append(((sx + tx) / 2, (sy + ty) / 2, label))
        else:
            mid = (sy + ty) / 2
            canvas.polyline([(sx, sy), (sx, mid), (tx, mid), (tx, ty)], stroke=INK, width=1.3, arrow=True)
            if label:
                label_slots.append((tx + 8, mid, label))

    for x, y, label in label_slots:
        canvas.rect(x - 6, y - 9, len(label) * 6.4 + 12, 18, fill=PAPER, stroke="none", rx=4)
        canvas.text(x, y + 4, label, size=10, fill=MUTED)

    # ---- узлы ---------------------------------------------------------------
    for index, (key, _lane, col, label, kind) in enumerate(STEPS):
        cx, cy = pos[key]
        if kind == "start":
            _terminal(canvas, cx, cy, filled=True)
        elif kind == "end":
            _terminal(canvas, cx, cy, filled=False)
            canvas.ellipse(cx, cy, 10, 10, fill=PAPER, stroke=INK, width=1.6)
        elif kind == "action":
            _action(canvas, cx, cy, label.split("\n"))
        elif kind == "decision":
            _decision(canvas, cx, cy, label.split("\n"))
        elif kind in {"fork", "join"}:
            _bar(canvas, cx, cy, horizontal=False)

    # ---- легенда ------------------------------------------------------------
    legend_y = LANE_TOP + LANE_H + 26
    canvas.rect(24, legend_y, 1272, 92, fill=PAPER, stroke=LINE, rx=6)
    canvas.text(44, legend_y + 26, "Обозначения", size=13, weight="bold")
    canvas.path("M150,79 L188,66 L226,79 L188,92 Z", stroke=WARN, width=1.4)
    canvas.text(238, legend_y + 26, "ветвление (решение)", size=11, fill=MUTED)
    canvas.rect(420, legend_y + 14, 34, 6, fill=INK)
    canvas.text(466, legend_y + 26, "fork / join — параллельные действия", size=11, fill=MUTED)
    canvas.rect(760, legend_y + 12, 34, 22, fill=LANE_B, stroke=INK)
    canvas.text(806, legend_y + 26, "действие участника", size=11, fill=MUTED)
    canvas.text(44, legend_y + 52, "Правила, которые проверяет система: триггер dates_check — даты и причина неисправности;", size=11, fill=MUTED)
    canvas.text(44, legend_y + 72, "ограничение остатка — нехватка ЗИП останавливает списание; ошибки приходят как 400 или 409.", size=11, fill=MUTED)


def to_svg() -> str:
    canvas = Canvas(WIDTH, HEIGHT)
    draw(canvas, Drawio(WIDTH, HEIGHT))
    return canvas.to_svg(TITLE)


def to_drawio() -> str:
    art = Drawio(WIDTH, HEIGHT)
    draw(Canvas(WIDTH, HEIGHT), art)
    return art.to_xml("activity")


REQUIREMENTS = [
    "Начало и конец показаны отдельными терминалами.",
    "23 узла процесса, из них 5 ветвлений с подписанными ветвями «да» / «нет».",
    "Параллельные действия показаны через fork и join: подготовка материалов идёт одновременно с выездом бригады.",
    "Четыре дорожки: мастер, система, бригада, руководитель.",
    "Отдельные ветви отказов: отказ по выведенному из эксплуатации оборудованию, занятая бригада, нехватка материала, неполные данные при завершении.",
    "Каждое действие подписано правилом, которое проверяет система: генерация номера, расчёт простоя, запись в журнал.",
]