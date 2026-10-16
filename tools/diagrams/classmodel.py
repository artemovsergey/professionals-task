"""Диаграмма классов системы ТОиР-Проф.

Классы повторяют таблицы из db/schema.sql один в один: то же набор атрибутов,
те же ключи и те же правила удаления. Это deliberate: диаграмма классов здесь
не «модель предметной области на бумаге», а контракт, по которому потом
написан код EF Core и сгенерирована база.

Каждый класс нарисован тремя секциями, как и требует лист задания:
имя класса, атрибуты с видимостью, операции с видимостью.
"""

from __future__ import annotations

from svgkit import ACCENT, BAD, INK, LINE, MUTED, OK, PAPER, WARN, Canvas, Drawio

TITLE = "Диаграмма классов — ТОиР-Проф"

WIDTH = 1700
HEIGHT = 1180

BOX_W = 230.0
COL_GAP = 70.0
ROW_GAP = 34.0
HEAD_H = 30.0
LINE_H = 17.0
ATTR_H = 26.0

# Ссылочные (справочные) сущности — заливка одного тона.
FILL_REF = "#eef4fa"
FILL_CORE = "#ffffff"
FILL_LINK = "#f4f1f9"
FILL_ENUM = "#fbf3e3"

# Ключ, имя, тон, атрибуты, операции
CLASSES = [
    (
        "Role",
        "Роль",
        FILL_REF,
        ["- id : UUID «PK»", "- code : string «UK»", "- name : string", "- description : string?"],
        [],
    ),
    (
        "User",
        "Пользователь",
        FILL_REF,
        [
            "- id : UUID «PK»",
            "- username : string «UK»",
            "- passwordHash : string",
            "- fullName : string",
            "- roleId : UUID «FK»",
            "- isActive : bool",
            "- createdAt : datetime",
            "- updatedAt : datetime",
        ],
        ["+ login()", "+ changePassword()"],
    ),
    (
        "Workshop",
        "Цех",
        FILL_REF,
        ["- id : UUID «PK»", "- code : string «UK»", "- name : string"],
        [],
    ),
    (
        "MaintenanceType",
        "Вид ТО",
        FILL_REF,
        [
            "- id : UUID «PK»",
            "- code : string «UK»",
            "- name : string",
            "- intervalDays : int",
            "- isActive : bool",
        ],
        [],
    ),
    (
        "Equipment",
        "Оборудование",
        FILL_CORE,
        [
            "- id : UUID «PK»",
            "- inventoryNumber : string «UK»",
            "- name : string",
            "- workshopId : UUID «FK»",
            "- commissionDate : date",
            "- decommissionDate : date?",
            "- status : EquipmentStatus",
            "- criticality : int",
        ],
        [
            "+ changeStatus(s : EquipmentStatus)",
            "+ isDecommissioned() : bool",
        ],
    ),
    (
        "MaintenanceSchedule",
        "График ТО",
        FILL_CORE,
        [
            "- id : UUID «PK»",
            "- equipmentId : UUID «FK»",
            "- maintenanceTypeId : UUID «FK»",
            "- plannedDate : date",
            "- completedDate : date?",
            "- nextPlannedDate : date?",
            "- status : string",
            "- actualCost : decimal?",
        ],
        ["+ complete(date : date, cost : decimal?)", "+ returnToPlan()"],
    ),
    (
        "Crew",
        "Бригада",
        FILL_REF,
        ["- id : UUID «PK»", "- code : string «UK»", "- name : string", "- specialty : string?", "- isActive : bool"],
        [],
    ),
    (
        "CrewMember",
        "Член бригады",
        FILL_LINK,
        ["- id : UUID «PK»", "- crewId : UUID «FK»", "- userId : UUID «FK»", "- joinedAt : date"],
        [],
    ),
    (
        "Material",
        "Материал",
        FILL_REF,
        [
            "- id : UUID «PK»",
            "- sku : string «UK»",
            "- name : string",
            "- unit : string",
            "- price : decimal",
            "- stock : decimal",
            "- minStock : decimal",
        ],
        ["+ isShortage() : bool", "+ receive(qty : decimal)"],
    ),
    (
        "WorkOrder",
        "Заявка",
        FILL_CORE,
        [
            "- id : UUID «PK»",
            "- number : string «UK»",
            "- equipmentId : UUID «FK»",
            "- maintenanceTypeId : UUID «FK?»",
            "- scheduleId : UUID «FK?»",
            "- crewId : UUID «FK?»",
            "- createdBy : UUID «FK»",
            "- assignedTo : UUID «FK?»",
            "- priority : WorkOrderPriority",
            "- status : WorkOrderStatus",
            "- plannedStart : date?",
            "- plannedEnd : date?",
            "- actualStart : datetime?",
            "- actualEnd : datetime?",
            "- downtimeHours : decimal?",
            "- failureReason : string?",
        ],
        [
            "+ assignCrew(crew : Crew)",
            "+ start(at : datetime)",
            "+ complete(at : datetime, reason : string)",
            "+ writeOff(material : Material, qty : decimal)",
            "+ canTransition(to : WorkOrderStatus) : bool",
        ],
    ),
    (
        "WorkOrderMaterial",
        "Списание",
        FILL_LINK,
        [
            "- id : UUID «PK»",
            "- workOrderId : UUID «FK»",
            "- materialId : UUID «FK»",
            "- quantity : decimal",
            "- unitPrice : decimal",
            "- cost : decimal «= q × p»",
        ],
        [],
    ),
    (
        "OperationLog",
        "Журнал операций",
        FILL_LINK,
        [
            "- id : UUID «PK»",
            "- userId : UUID «FK?»",
            "- tableName : string",
            "- recordId : UUID?",
            "- operation : string",
            "- oldValues : string?",
            "- newValues : string?",
            "- createdAt : datetime",
        ],
        [],
    ),
    (
        "WorkOrderCounter",
        "Счётчик номеров",
        FILL_LINK,
        ["- year : int «PK»", "- lastValue : int «≥ 0»"],
        ["+ next() : string «Z-YYYY-XXXX»"],
    ),
    (
        "EquipmentStatus",
        "Статус оборудования",
        FILL_ENUM,
        ["«enum» Работает", "«enum» В ремонте", "«enum» Выведено из эксплуатации"],
        [],
    ),
    (
        "WorkOrderStatus",
        "Статус заявки",
        FILL_ENUM,
        ["«enum» Черновик", "«enum» Назначена", "«enum» В работе", "«enum» Завершена", "«enum» Отменена"],
        [],
    ),
    (
        "WorkOrderPriority",
        "Приоритет заявки",
        FILL_ENUM,
        ["«enum» Низкий", "«enum» Средний", "«enum» Высокий", "«enum» Аварийный"],
        [],
    ),
]

# (откуда, куда, подпись на «дочернем» конце, вид линии, правило удаления)
RELATIONS = [
    ("Role", "User", "1 .. *", "solid", "—"),
    ("Workshop", "Equipment", "1 .. *", "solid", "RESTRICT"),
    ("MaintenanceType", "MaintenanceSchedule", "1 .. *", "solid", "RESTRICT"),
    ("Equipment", "MaintenanceSchedule", "1 .. *", "solid", "CASCADE"),
    ("Crew", "CrewMember", "1 .. *", "solid", "CASCADE"),
    ("User", "CrewMember", "1 .. *", "solid", "CASCADE"),
    ("User", "WorkOrder", "0 .. *", "solid", "RESTRICT"),
    ("User", "WorkOrder", "0 .. *", "solid", "SET NULL"),
    ("Equipment", "WorkOrder", "1 .. *", "solid", "RESTRICT"),
    ("MaintenanceType", "WorkOrder", "0 .. *", "solid", "RESTRICT"),
    ("MaintenanceSchedule", "WorkOrder", "0 .. 1", "solid", "SET NULL"),
    ("Crew", "WorkOrder", "0 .. *", "solid", "SET NULL"),
    ("WorkOrder", "WorkOrderMaterial", "1 .. *", "solid", "—"),
    ("Material", "WorkOrderMaterial", "1 .. *", "solid", "RESTRICT"),
    ("User", "OperationLog", "0 .. *", "solid", "SET NULL"),
    ("WorkOrderCounter", "WorkOrder", "1 .. 1", "dash", "—"),
]

GRID = {
    "Role": (0, 0),
    "User": (1, 0),
    "Workshop": (2, 0),
    "MaintenanceType": (3, 0),
    "Equipment": (0, 1),
    "MaintenanceSchedule": (1, 1),
    "Crew": (2, 1),
    "CrewMember": (3, 1),
    "Material": (0, 2),
    "WorkOrder": (1, 2),
    "WorkOrderMaterial": (2, 2),
    "OperationLog": (3, 2),
    "WorkOrderCounter": (0, 3),
    "EquipmentStatus": (2, 3),
    "WorkOrderStatus": (3, 3),
    "WorkOrderPriority": (2, 4),
}


def box_height(attributes: list[str], operations: list[str]) -> float:
    rows = len(attributes) + len(operations)
    return HEAD_H + (rows * LINE_H if rows else ATTR_H) + 10.0


def layout() -> tuple[dict[str, tuple[float, float]], float]:
    """Раскладывает классы по колонкам и считает общий размер холста."""
    heights = {key: box_height(attrs, ops) for key, _, _, attrs, ops in CLASSES}
    columns = 4
    top = 96.0
    boxes: dict[str, tuple[float, float]] = {}
    for key, (col, row) in GRID.items():
        x = 40.0 + col * (BOX_W + COL_GAP)
        y = top + sum(
            heights[k2] + ROW_GAP for k2, (c2, r2) in GRID.items() if c2 == col and r2 < row
        )
        boxes[key] = (x, y)

    max_bottom = max(boxes[key][1] + heights[key] for key, _, _, _, _ in CLASSES)
    width = 40 + columns * BOX_W + (columns - 1) * COL_GAP + 40
    return boxes, max_bottom


def draw(canvas: Canvas, art: Drawio) -> None:
    boxes, bottom = layout()

    canvas.text(24, 38, TITLE, size=20, weight="bold")
    canvas.text(
        24,
        60,
        "Классы повторяют таблицы db/schema.sql; секции: атрибуты, операции, видимость",
        size=12,
        fill=MUTED,
    )

    anchors: dict[str, int] = {}

    for key, title, fill, attributes, operations in CLASSES:
        x, y = boxes[key]
        h = box_height(attributes, operations)
        canvas.rect(x, y, BOX_W, h, fill=PAPER, stroke=ACCENT, rx=4, width=1.4)
        canvas.rect(x, y, BOX_W, HEAD_H, fill=fill, stroke=ACCENT, rx=4, width=1.4)
        canvas.text(x + 10, y + 20, f"«{title}»", size=13, weight="bold")

        row_y = y + HEAD_H + 4
        for attribute in attributes:
            is_key = "PK" in attribute
            is_fk = "FK" in attribute
            colour = BAD if is_key else (WARN if is_fk else MUTED)
            canvas.text(x + 10, row_y + 13, attribute, size=11, fill=colour)
            row_y += LINE_H

        if operations:
            canvas.line(x, row_y + 3, x + BOX_W, row_y + 3, stroke=LINE, width=1)
            row_y += 8
            for operation in operations:
                canvas.text(x + 10, row_y + 13, operation, size=11, fill=OK)
                row_y += LINE_H

        anchors[key] = art.shape(
            x,
            y,
            BOX_W,
            h,
            f"{title}\n{'  ' + chr(10).join(attributes)}\n  {chr(10).join(operations)}".strip(),
            style=(
                "swimlane;html=1;whiteSpace=wrap;startSize=30;fillColor=%s;strokeColor=#2f6fb0;"
                "fontStyle=1;align=center;" % fill
            ),
        )

    # ---- связи ------------------------------------------------------------
    for source, target, multiplicity, kind, rule in RELATIONS:
        sx, sy = boxes[source]
        tx, ty = boxes[target]
        dash = "8 5" if kind == "dash" else None
        start = (sx + BOX_W, sy + 30)
        end = (tx, ty + 30)
        if source == "WorkOrderCounter":
            start = (sx + BOX_W / 2, sy)
            end = (tx + BOX_W / 2, ty)
        canvas.polyline([start, end], stroke=LINE, width=1.3, dash=dash)
        canvas.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 - 6, multiplicity, size=10, fill=MUTED)
        if rule != "—":
            canvas.text(
                (start[0] + end[0]) / 2,
                (start[1] + end[1]) / 2 + 12,
                rule,
                size=9,
                fill=MUTED,
                italic=True,
            )
        art.connect(
            anchors[source],
            anchors[target],
            "endArrow=%s;html=1;strokeColor=#7d8891;dashed=%d;"
            % ("open" if kind == "dash" else "none", 1 if dash else 0),
        )

    # ---- легенда -----------------------------------------------------------
    canvas.rect(40, bottom + 28, 1620, 96, fill=PAPER, stroke=LINE, rx=6)
    canvas.text(60, bottom + 54, "Обозначения", size=13, weight="bold")
    canvas.text(60, bottom + 78, "- private / + public", size=11, fill=MUTED)
    canvas.text(300, bottom + 78, "«PK» первичный ключ", size=11, fill=BAD)
    canvas.text(500, bottom + 78, "«FK» внешний ключ", size=11, fill=WARN)
    canvas.text(680, bottom + 78, "«= q × p» вычисляемое поле", size=11, fill=MUTED)
    canvas.text(940, bottom + 78, "1 .. * одна ко многим", size=11, fill=MUTED)
    canvas.text(1200, bottom + 78, "0 .. * ноль или много", size=11, fill=MUTED)
    canvas.text(
        60,
        bottom + 102,
        "Подпись у связи — правило удаления: RESTRICT запрещает, CASCADE удаляет вместе, SET NULL обнуляет.",
        size=11,
        fill=MUTED,
    )


def _canvas_height() -> int:
    _, bottom = layout()
    return int(bottom + 140)


def to_svg() -> str:
    canvas = Canvas(WIDTH, _canvas_height())
    draw(canvas, Drawio(WIDTH, canvas.height))
    return canvas.to_svg(TITLE)


def to_drawio() -> str:
    canvas = Canvas(WIDTH, _canvas_height())
    art = Drawio(WIDTH, canvas.height)
    draw(canvas, art)
    return art.to_xml("class-model")


REQUIREMENTS = [
    "16 классов, каждый в трёх секциях: имя, атрибуты, операции.",
    "Видимость членов указана префиксами «-» (private) и «+» (public).",
    "16 ассоциаций с кратностями: 1 .. *, 0 .. *, 0 .. 1, 1 .. 1.",
    "У каждой ассоциации подписано правило удаления: RESTRICT, CASCADE или SET NULL.",
    "Три перечисления вынесены в отдельные классы: EquipmentStatus, WorkOrderStatus, WorkOrderPriority.",
    "Поле cost помечено как вычисляемое: в базе это GENERATED ALWAYS AS (quantity * unit_price) STORED.",
]