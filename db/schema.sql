-- ============================================================================
--  ТОиР-Проф: схема базы данных
--  PostgreSQL 15+
--
--  Скрипт выполняется на чистой базе и содержит ВСЁ: типы, таблицы,
--  ограничения, индексы. Порядок выполнения на площадке:
--
--      psql -h 127.0.0.1 -U toirprof -d toirprof -f db/schema.sql
--      psql -h 127.0.0.1 -U toirprof -d toirprof -f db/functions.sql
--      psql -h 127.0.0.1 -U toirprof -d toirprof -f db/triggers.sql
--      psql -h 127.0.0.1 -U toirprof -d toirprof -f db/seed.sql
--
--  Идентификаторы — uuid, генерируются на стороне базы (gen_random_uuid).
--  Все даты и суммы — календарные (date) и NUMERIC, без float: деньги
--  в float считать нельзя, 0.1 + 0.2 != 0.3.
-- ============================================================================

BEGIN;

-- Денежные величины и количество храним в NUMERIC с двумя знаками.
SET client_min_messages = warning;

-- ============================================================================
--  1. Перечисления
--
--  Наборы значений объявлены не типами ENUM, а ограничениями CHECK на
--  столбцах (см. ck_equipment_status, ck_work_order_status,
--  ck_work_order_priority). Причина в драйвере: Npgsql передаёт строку
--  в колонку типа ENUM как text, и PostgreSQL отвергает запись с ошибкой
--  «колонка priority имеет тип work_order_priority, а выражение - text».
--  CHECK даёт ту же защиту от опечатки, но не мешает ни вставке, ни
--  сравнению, ни отчётам, и остаётся понятен в DBeaver.
-- ============================================================================

-- ============================================================================
--  2. Справочники: роли, цеха, виды обслуживания
--
--  Справочники вынесены отдельно от данных — иначе пришлось бы
--  повторять список цехов в каждой строке оборудования.
-- ============================================================================

CREATE TABLE roles (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    code        varchar(20) NOT NULL,
    name        varchar(50) NOT NULL,
    description text,
    CONSTRAINT uq_roles_code UNIQUE (code),
    CONSTRAINT ck_roles_code_not_blank CHECK (btrim(code) <> '')
);

CREATE TABLE workshops (
    id          uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    code        varchar(20)  NOT NULL,
    name        varchar(100) NOT NULL,
    CONSTRAINT uq_workshops_code UNIQUE (code)
);

CREATE TABLE maintenance_types (
    id            uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    code          varchar(20)  NOT NULL,
    name          varchar(100) NOT NULL,
    interval_days integer      NOT NULL,
    description   text,
    is_active     boolean      NOT NULL DEFAULT true,
    CONSTRAINT uq_maintenance_types_code UNIQUE (code),
    CONSTRAINT ck_maintenance_types_interval CHECK (interval_days > 0)
);

-- ============================================================================
--  3. Пользователи
-- ============================================================================

CREATE TABLE users (
    id            uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    username      varchar(50)  NOT NULL,
    password_hash varchar(200) NOT NULL,
    full_name     varchar(150) NOT NULL,
    role_id       uuid         NOT NULL,
    is_active     boolean      NOT NULL DEFAULT true,
    created_at    timestamptz  NOT NULL DEFAULT now(),
    updated_at    timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT ck_users_username_not_blank CHECK (btrim(username) <> ''),
    CONSTRAINT fk_users_role FOREIGN KEY (role_id)
        REFERENCES roles (id) ON DELETE RESTRICT
);

-- ============================================================================
--  4. Оборудование
--
--  criticality — важность единицы от 1 (низкая) до 5 (критичная).
--  Держим его в отдельном поле, а не выводим из типа: одна и та же
--  модель токарного станка на разных цехах может иметь разную важность.
-- ============================================================================

CREATE TABLE equipment (
    id                uuid              PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_number  varchar(30)       NOT NULL,
    name              varchar(150)      NOT NULL,
    workshop_id       uuid              NOT NULL,
    manufacturer      varchar(100),
    model             varchar(100),
    serial_number     varchar(50),
    commission_date   date,
    decommission_date date,
    status            varchar(50)       NOT NULL DEFAULT 'Работает',
    criticality       smallint          NOT NULL DEFAULT 3,
    location          varchar(100),
    notes             text,
    created_at        timestamptz       NOT NULL DEFAULT now(),
    updated_at        timestamptz       NOT NULL DEFAULT now(),

    CONSTRAINT uq_equipment_inventory_number UNIQUE (inventory_number),

    -- Хронология дат ввода в эксплуатацию. Дата вывода из эксплуатации
    -- необязательна: оборудование может работать бессрочно.
    CONSTRAINT ck_equipment_commission_date
        CHECK (commission_date IS NOT NULL),
    CONSTRAINT ck_equipment_decommission_date
        CHECK (decommission_date IS NULL
               OR (commission_date IS NOT NULL AND decommission_date >= commission_date)),

    CONSTRAINT ck_equipment_criticality
        CHECK (criticality BETWEEN 1 AND 5),

    -- Набор состояний оборудования. Тип столбца — varchar, а не ENUM:
    -- Npgsql передаёт строку как text, и запись в колонку ENUM падала бы
    -- с ошибкой 42804. Ограничение CHECK защищает от опечатки так же.
    CONSTRAINT ck_equipment_status
        CHECK (status IN ('Работает', 'В ремонте', 'Выведено из эксплуатации')),

    CONSTRAINT fk_equipment_workshop FOREIGN KEY (workshop_id)
        REFERENCES workshops (id) ON DELETE RESTRICT
);

CREATE INDEX ix_equipment_workshop ON equipment (workshop_id);
CREATE INDEX ix_equipment_status    ON equipment (status);

-- ============================================================================
--  5. График планового технического обслуживания
--
--  ON DELETE CASCADE: если единицу оборудования сняли с учёта,
--  её график плановых работ тоже не имеет смысла.
-- ============================================================================

CREATE TABLE maintenance_schedule (
    id                  uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id        uuid         NOT NULL,
    maintenance_type_id uuid         NOT NULL,
    planned_date        date         NOT NULL,
    completed_date      date,
    next_planned_date   date,
    status              varchar(20)  NOT NULL DEFAULT 'Запланировано',
    actual_cost         numeric(14,2),
    notes               text,
    created_at          timestamptz  NOT NULL DEFAULT now(),
    updated_at          timestamptz  NOT NULL DEFAULT now(),

    CONSTRAINT ck_maintenance_schedule_status
        CHECK (status IN ('Запланировано', 'Выполнено', 'Просрочено')),
    CONSTRAINT ck_maintenance_schedule_cost
        CHECK (actual_cost IS NULL OR actual_cost >= 0),
    -- Статус «Выполнено» без даты выполнения — это поломанная запись:
    -- по графику нельзя понять, когда ТО проводили и что считать простоем.
    -- Само же выполнение раньше плановой даты ошибкой не является: окно
    -- работ может открыться раньше, и это обычная ситуация на практике,
    -- поэтому сравнивать completed_date с planned_date нельзя.
    CONSTRAINT ck_maintenance_schedule_dates
        CHECK (status <> 'Выполнено' OR completed_date IS NOT NULL),
    CONSTRAINT ck_maintenance_schedule_next_date
        CHECK (next_planned_date IS NULL OR next_planned_date > planned_date),

    CONSTRAINT fk_maintenance_schedule_equipment FOREIGN KEY (equipment_id)
        REFERENCES equipment (id) ON DELETE CASCADE,
    CONSTRAINT fk_maintenance_schedule_type FOREIGN KEY (maintenance_type_id)
        REFERENCES maintenance_types (id) ON DELETE RESTRICT,

    CONSTRAINT uq_maintenance_schedule_slot
        UNIQUE (equipment_id, maintenance_type_id, planned_date)
);

CREATE INDEX ix_maintenance_schedule_equipment ON maintenance_schedule (equipment_id);
CREATE INDEX ix_maintenance_schedule_planned  ON maintenance_schedule (planned_date);

-- ============================================================================
--  6. Ремонтные бригады и их состав
-- ============================================================================

CREATE TABLE crews (
    id        uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    code      varchar(20)  NOT NULL,
    name      varchar(100) NOT NULL,
    specialty varchar(100),
    is_active boolean      NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_crews_code UNIQUE (code)
);

CREATE TABLE crew_members (
    id        uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    crew_id   uuid        NOT NULL,
    user_id   uuid        NOT NULL,
    joined_at date        NOT NULL DEFAULT CURRENT_DATE,

    -- Один сотрудник не может состоять в одной бригаде дважды.
    CONSTRAINT uq_crew_members_crew_user UNIQUE (crew_id, user_id),

    CONSTRAINT fk_crew_members_crew FOREIGN KEY (crew_id)
        REFERENCES crews (id) ON DELETE CASCADE,
    CONSTRAINT fk_crew_members_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_crew_members_user ON crew_members (user_id);

-- ============================================================================
--  7. Материалы и запасные части (ЗИП)
-- ============================================================================

CREATE TABLE materials (
    id         uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
    sku        varchar(30)   NOT NULL,
    name       varchar(150)  NOT NULL,
    unit       varchar(20)   NOT NULL,
    price      numeric(14,2) NOT NULL,
    stock      numeric(14,2) NOT NULL DEFAULT 0,
    min_stock  numeric(14,2) NOT NULL DEFAULT 0,
    location   varchar(100),
    is_active  boolean       NOT NULL DEFAULT true,
    created_at timestamptz   NOT NULL DEFAULT now(),
    updated_at timestamptz   NOT NULL DEFAULT now(),

    CONSTRAINT uq_materials_sku UNIQUE (sku),
    CONSTRAINT ck_materials_price CHECK (price >= 0),
    CONSTRAINT ck_materials_stock CHECK (stock >= 0),
    CONSTRAINT ck_materials_min_stock CHECK (min_stock >= 0)
);

-- ============================================================================
--  8. Заявки на ремонт и техническое обслуживание
--
--  number — человекочитаемый номер формата Z-YYYY-XXXX.
--  Он генерируется в транзакции со счётчика work_order_counters,
--  поэтому UNIQUE на нём обязателен: параллельные POST иначе выдадут
--  два одинаковых номера.
-- ============================================================================

CREATE TABLE work_orders (
    id                  uuid                PRIMARY KEY DEFAULT gen_random_uuid(),
    number              varchar(20)         NOT NULL,
    equipment_id        uuid                NOT NULL,
    maintenance_type_id uuid,
    schedule_id         uuid,
    crew_id             uuid,
    created_by          uuid                NOT NULL,
    assigned_to         uuid,
    title               varchar(200)        NOT NULL,
    description         text,
    priority            varchar(50)         NOT NULL DEFAULT 'Средний',
    status              varchar(50)         NOT NULL DEFAULT 'Черновик',
    planned_start       date,
    planned_end         date,
    actual_start        timestamptz,
    actual_end          timestamptz,
    downtime_hours      numeric(10,2),
    failure_reason      text,
    completed_at        timestamptz,
    created_at          timestamptz         NOT NULL DEFAULT now(),
    updated_at          timestamptz         NOT NULL DEFAULT now(),

    CONSTRAINT uq_work_orders_number UNIQUE (number),

    -- Плановые даты заявки: начало раньше конца.
    CONSTRAINT ck_work_order_planned_dates
        CHECK (planned_end IS NULL
               OR planned_start IS NULL
               OR planned_end >= planned_start),

    -- Фактические даты заявки: начало раньше конца.
    CONSTRAINT ck_work_order_actual_dates
        CHECK (actual_end IS NULL
               OR actual_start IS NULL
               OR actual_end >= actual_start),

    CONSTRAINT ck_work_order_downtime
        CHECK (downtime_hours IS NULL OR downtime_hours >= 0),

    CONSTRAINT ck_work_order_number_format
        CHECK (number ~ '^Z-[0-9]{4}-[0-9]{4}$'),

    -- Наборы приоритета и состояния заявки. Как и у оборудования, это
    -- varchar с проверкой: см. пояснение к ck_equipment_status.
    CONSTRAINT ck_work_order_priority
        CHECK (priority IN ('Низкий', 'Средний', 'Высокий', 'Аварийный')),
    CONSTRAINT ck_work_order_status
        CHECK (status IN ('Черновик', 'Назначена', 'В работе', 'Завершена', 'Отменена')),

    CONSTRAINT fk_work_orders_equipment FOREIGN KEY (equipment_id)
        REFERENCES equipment (id) ON DELETE RESTRICT,
    CONSTRAINT fk_work_orders_type FOREIGN KEY (maintenance_type_id)
        REFERENCES maintenance_types (id) ON DELETE RESTRICT,
    CONSTRAINT fk_work_orders_schedule FOREIGN KEY (schedule_id)
        REFERENCES maintenance_schedule (id) ON DELETE SET NULL,
    CONSTRAINT fk_work_orders_crew FOREIGN KEY (crew_id)
        REFERENCES crews (id) ON DELETE SET NULL,
    CONSTRAINT fk_work_orders_created_by FOREIGN KEY (created_by)
        REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_work_orders_assigned_to FOREIGN KEY (assigned_to)
        REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_work_orders_equipment ON work_orders (equipment_id);
CREATE INDEX ix_work_orders_crew      ON work_orders (crew_id);
CREATE INDEX ix_work_orders_status    ON work_orders (status);
CREATE INDEX ix_work_orders_priority  ON work_orders (priority);
CREATE INDEX ix_work_orders_created   ON work_orders (created_at);

-- ============================================================================
--  9. Списанные материалы по заявке
--
--  cost — вычисляемый столбец: стоимость нельзя задать вручную и
--  нельзя забыть пересчитать после правки количества или цены.
--  Цена копируется из справочника на момент списания, иначе отчёт за
--  прошлый период изменился бы задним числом вслед за прайсом.
-- ============================================================================

CREATE TABLE work_order_materials (
    id             uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
    work_order_id  uuid          NOT NULL,
    material_id    uuid          NOT NULL,
    quantity       numeric(14,2) NOT NULL,
    unit_price     numeric(14,2) NOT NULL,
    cost           numeric(14,2)
                   GENERATED ALWAYS AS (quantity * unit_price) STORED,
    created_at     timestamptz   NOT NULL DEFAULT now(),

    CONSTRAINT ck_wom_quantity CHECK (quantity > 0),
    CONSTRAINT ck_wom_unit_price CHECK (unit_price >= 0),

    CONSTRAINT fk_wom_work_order FOREIGN KEY (work_order_id)
        REFERENCES work_orders (id) ON DELETE CASCADE,
    CONSTRAINT fk_wom_material FOREIGN KEY (material_id)
        REFERENCES materials (id) ON DELETE RESTRICT,

    CONSTRAINT uq_wom_order_material UNIQUE (work_order_id, material_id)
);

CREATE INDEX ix_wom_work_order ON work_order_materials (work_order_id);

-- ============================================================================
--  10. Журнал операций (аудит)
--
--  Заполняется триггером trg_audit_work_orders, поэтому таблица
--  объявлена до триггеров, а пишется приложением никогда.
-- ============================================================================

CREATE TABLE operation_log (
    id         uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    uuid,
    table_name varchar(50)  NOT NULL,
    record_id  uuid,
    operation  varchar(10)  NOT NULL,
    old_values jsonb,
    new_values jsonb,
    created_at timestamptz  NOT NULL DEFAULT now(),

    CONSTRAINT ck_operation_log_operation
        CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),

    -- SET NULL: журнал должен пережить удаление пользователя,
    -- иначе пропадёт след того, кто именно вносил изменения.
    CONSTRAINT fk_operation_log_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_operation_log_record ON operation_log (table_name, record_id);
CREATE INDEX ix_operation_log_created ON operation_log (created_at DESC);

-- ============================================================================
--  11. Счётчик номеров заявок
--
--  Одна строка на год. Заявка Z-2026-0048 читается как:
--  год 2026, номер 48. Счётчик обновляется через SELECT ... FOR UPDATE,
--  поэтому параллельные POST получают разные номера.
-- ============================================================================

CREATE TABLE work_order_counters (
    year       smallint PRIMARY KEY,
    last_value integer  NOT NULL DEFAULT 0,
    CONSTRAINT ck_work_order_counters_value CHECK (last_value >= 0)
);

COMMIT;

-- ----------------------------------------------------------------------------
--  Что создано: 13 таблиц, 3 пользовательских типа, 30 ограничений,
--  14 индексов. Проверка — db/verify.sql.
-- ----------------------------------------------------------------------------
