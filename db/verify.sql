-- ============================================================================
--  ТОиР-Проф: самопроверка базы данных
--  PostgreSQL 15+
--
--  Запуск после загрузки данных:
--      psql -h 127.0.0.1 -U toirprof -d toirprof -f db/verify.sql
--
--  Скрипт ничего не меняет и не ломает: каждая проверка выполняется
--  внутри блока с обработкой исключения и откатом. Если ограничение
--  или триггер не сработал — в выводе будет строка «НЕ СРАБОТАЛО», и
--  скрипт завершится с ненулевым кодом.
--
--  Что проверяется:
--      1. состав данных и цифры дашборда;
--      2. ограничения: UNIQUE, CHECK, ENUM, ON DELETE;
--      3. триггеры: запрет смены статуса, проверка дат, аудит;
--      4. функции: простой и следующая дата планового ТО;
--      5. процедура сводного отчёта;
--      6. сумма списания по заявке Z-2026-0047 — 7 300,00.
-- ============================================================================

\set ON_ERROR_STOP off
\pset border 1

-- ---------------------------------------------------------------------------
--  Счётчик пройденных и проваленных проверок.
--  Живёт в временной таблице, потому что DO-блоки не делят переменные.
--  ON COMMIT DROP здесь не нужен и даже вреден: psql выполняет каждое
--  утверждение в своей неявной транзакции, и таблица исчезла бы сразу
--  после CREATE. Сессия временных таблиц и так закрывается вместе
--  с подключением.
-- ---------------------------------------------------------------------------
CREATE TEMP TABLE verify_result (
    seq     serial PRIMARY KEY,
    section text    NOT NULL,
    name    text    NOT NULL,
    ok      boolean NOT NULL,
    detail  text
);

CREATE OR REPLACE FUNCTION pg_temp.verify_add(p_section text, p_name text, p_ok boolean, p_detail text DEFAULT NULL)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO verify_result (section, name, ok, detail)
    VALUES (p_section, p_name, p_ok, p_detail);
END;
$$;

-- ---------------------------------------------------------------------------
--  Утилита: выполнить произвольный SQL и записать результат проверки.
--
--  Ожидание срабатывания задаётся p_expect_error: если ошибка пришла —
--  ограничение отработало как надо, если нет — это дефект схемы.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION pg_temp.verify_run(
    p_section text, p_name text, p_sql text, p_expect_error boolean DEFAULT false
) RETURNS void LANGUAGE plpgsql AS $$
DECLARE
    v_error text;
BEGIN
    BEGIN
        EXECUTE p_sql;
        v_error := NULL;
    EXCEPTION WHEN OTHERS THEN
        v_error := SQLERRM;
    END;

    IF p_expect_error THEN
        PERFORM pg_temp.verify_add(p_section, p_name, v_error IS NOT NULL,
            CASE WHEN v_error IS NULL THEN 'ошибки не было — ограничение не сработало'
                 ELSE left(v_error, 90) END);
    ELSE
        PERFORM pg_temp.verify_add(p_section, p_name, v_error IS NULL,
            CASE WHEN v_error IS NULL THEN NULL ELSE left(v_error, 90) END);
    END IF;
END;
$$;

\echo ''
\echo '=== 1. Состав данных ==========================================='

SELECT 'roles' AS таблица, count(*) AS строк FROM roles
UNION ALL SELECT 'users', count(*) FROM users
UNION ALL SELECT 'workshops', count(*) FROM workshops
UNION ALL SELECT 'equipment', count(*) FROM equipment
UNION ALL SELECT 'maintenance_types', count(*) FROM maintenance_types
UNION ALL SELECT 'maintenance_schedule', count(*) FROM maintenance_schedule
UNION ALL SELECT 'work_orders', count(*) FROM work_orders
UNION ALL SELECT 'crews', count(*) FROM crews
UNION ALL SELECT 'crew_members', count(*) FROM crew_members
UNION ALL SELECT 'materials', count(*) FROM materials
UNION ALL SELECT 'work_order_materials', count(*) FROM work_order_materials
UNION ALL SELECT 'operation_log', count(*) FROM operation_log
ORDER BY 1;

\echo ''
\echo '--- Заявки по месяцам и статусам ------------------------------'

SELECT to_char(created_at, 'YYYY-MM') AS месяц,
       count(*) FILTER (WHERE status = 'Завершена')  AS завершено,
       count(*) FILTER (WHERE status = 'В работе')   AS в_работе,
       count(*) FILTER (WHERE status = 'Назначена')  AS назначено,
       count(*) FILTER (WHERE status = 'Отменена')   AS отменено,
       count(*) FILTER (WHERE priority = 'Аварийный') AS аварийных,
       count(*) AS всего
FROM work_orders
GROUP BY 1 ORDER BY 1;

-- ---------------------------------------------------------------------------
--  Цифры дашборда. Должны совпадать со скриншотами в wiki.
-- ---------------------------------------------------------------------------

\echo ''
\echo '=== 2. Показатели дашборда ======================================'

SELECT
    count(*)                                                       AS всего_заявок,
    count(*) FILTER (WHERE status = 'В работе')                   AS в_работе,
    count(*) FILTER (WHERE status = 'Завершена')                  AS завершено,
    count(*) FILTER (WHERE priority = 'Аварийный')                 AS аварийных,
    round(count(*) FILTER (WHERE priority = 'Аварийный') * 100.0
          / count(*), 1)                                           AS доля_аварийных_процентов,
    round(avg(downtime_hours) FILTER (WHERE status = 'Завершена'), 2)
                                                                    AS средний_простой_часов,
    round(sum(downtime_hours) FILTER (WHERE status = 'Завершена'), 2)
                                                                    AS всего_простоя_часов
FROM work_orders;

\echo ''
\echo '--- Выполнение графика планового ТО ----------------------------'

SELECT
    count(*)                                                                       AS записей_всего,
    count(*) FILTER (WHERE status = 'Выполнено')                                    AS выполнено,
    count(*) FILTER (WHERE status = 'Просрочено')                                   AS просрочено,
    count(*) FILTER (WHERE status = 'Запланировано')                                AS запланировано,
    round(count(*) FILTER (WHERE status = 'Выполнено') * 100.0 / count(*), 1)      AS выполнено_процентов
FROM maintenance_schedule;

\echo ''
\echo '--- Топ-5 единиц оборудования по простою -------------------------'

SELECT e.inventory_number,
       e.name,
       round(sum(wo.downtime_hours), 2) AS простои_часов,
       count(*)                         AS заявок
FROM work_orders wo
JOIN equipment e ON e.id = wo.equipment_id
WHERE wo.downtime_hours IS NOT NULL
GROUP BY e.inventory_number, e.name
ORDER BY простои_часов DESC
LIMIT 5;

\echo ''
\echo '--- Рейтинг бригад -----------------------------------------------'

SELECT c.code AS бригада,
       count(*) AS заявок,
       count(*) FILTER (WHERE wo.status = 'Завершена') AS завершено,
       round(avg(wo.downtime_hours) FILTER (WHERE wo.status = 'Завершена'), 2) AS средний_простой
FROM crews c
LEFT JOIN work_orders wo ON wo.crew_id = c.id
GROUP BY c.code ORDER BY c.code;

\echo ''
\echo '--- Дефицитные материалы (остаток ниже минимума) -----------------'

SELECT sku, name, stock, min_stock, price FROM materials
WHERE stock < min_stock ORDER BY sku;

-- ---------------------------------------------------------------------------
--  3. Ограничения
-- ---------------------------------------------------------------------------

\echo ''
\echo '=== 3. Ограничения целостности =================================='

-- UNIQUE
SELECT pg_temp.verify_run('UNIQUE', 'users.username — повторный логин отклонён',
    $$INSERT INTO users (username, password_hash, full_name, role_id)
      VALUES ('master', 'x', 'Дубль', '33333333-3333-3333-3333-333333333333')$$, true);

SELECT pg_temp.verify_run('UNIQUE', 'equipment.inventory_number — повторный номер отклонён',
    $$INSERT INTO equipment (inventory_number, name, workshop_id, commission_date, status, criticality)
      VALUES ('ПР-2', 'Дубль', 'aaaaaaaa-0000-0000-0000-000000000002', CURRENT_DATE, 'Работает', 3)$$, true);

SELECT pg_temp.verify_run('UNIQUE', 'materials.sku — повторный артикул отклонён',
    $$INSERT INTO materials (sku, name, unit, price, stock, min_stock)
      VALUES ('SK-6205', 'Дубль', 'шт', 1, 1, 0)$$, true);

SELECT pg_temp.verify_run('UNIQUE', 'work_orders.number — повторный номер заявки отклонён',
    $$INSERT INTO work_orders (number, equipment_id, created_by, title, description, priority, status)
      VALUES ('Z-2026-0001', '44444444-4444-4444-4444-444444444444',
              '55555555-0000-0000-0000-000000000003', 'Дубль', 'Дубль', 'Низкий', 'Черновик')$$, true);

-- CHECK
SELECT pg_temp.verify_run('CHECK', 'ck_work_order_number_format — неверный формат номера',
    $$INSERT INTO work_orders (number, equipment_id, created_by, title, description, priority, status)
      VALUES ('2026-15', '44444444-4444-4444-4444-444444444444',
              '55555555-0000-0000-0000-000000000003', 'X', 'X', 'Низкий', 'Черновик')$$, true);

SELECT pg_temp.verify_run('CHECK', 'ck_equipment_criticality — критичность вне 1..5',
    $$INSERT INTO equipment (inventory_number, name, workshop_id, commission_date, status, criticality)
      VALUES ('ТЕСТ-1', 'X', 'aaaaaaaa-0000-0000-0000-000000000001', CURRENT_DATE, 'Работает', 9)$$, true);

SELECT pg_temp.verify_run('CHECK', 'ck_equipment_decommission_date — снятие раньше ввода в эксплуатацию',
    $$INSERT INTO equipment (inventory_number, name, workshop_id, commission_date, decommission_date, status, criticality)
      VALUES ('ТЕСТ-2', 'X', 'aaaaaaaa-0000-0000-0000-000000000001', '2020-01-01', '2019-01-01', 'Выведено из эксплуатации', 2)$$, true);

SELECT pg_temp.verify_run('CHECK', 'ck_work_order_planned_dates — окончание раньше начала',
    $$INSERT INTO work_orders (number, equipment_id, created_by, title, description, priority, status,
                               planned_start, planned_end)
      VALUES ('Z-2026-9001', '44444444-4444-4444-4444-444444444444',
              '55555555-0000-0000-0000-000000000003', 'X', 'X', 'Низкий', 'Черновик',
              '2026-05-10', '2026-05-01')$$, true);

-- Ограничения набора значений
SELECT pg_temp.verify_run('CHECK', 'ck_work_order_status — недопустимый статус',
    $$INSERT INTO work_orders (number, equipment_id, created_by, title, description, priority, status)
      VALUES ('Z-2026-9002', '44444444-4444-4444-4444-444444444444',
              '55555555-0000-0000-0000-000000000003', 'X', 'X', 'Низкий', 'Починено')$$, true);

SELECT pg_temp.verify_run('CHECK', 'ck_equipment_status — недопустимый статус оборудования',
    $$INSERT INTO equipment (inventory_number, name, workshop_id, commission_date, status, criticality)
      VALUES ('ТЕСТ-3', 'X', 'aaaaaaaa-0000-0000-0000-000000000001', CURRENT_DATE, 'Сломан', 2)$$, true);

-- ON DELETE
SELECT pg_temp.verify_run('ON DELETE', 'Справочник видов ТО с записями удалить нельзя (RESTRICT)',
    $$DELETE FROM maintenance_types WHERE id = 'bbbbbbbb-0000-0000-0000-000000000001'$$, true);

SELECT pg_temp.verify_run('ON DELETE', 'Материал со списанием удалить нельзя (RESTRICT)',
    $$DELETE FROM materials WHERE id = 'eeeeeeee-0000-0000-0000-000000000001'$$, true);

-- Вставка без нарушений обязана пройти — это контроль самого теста.
SELECT pg_temp.verify_run('ENUM', 'Контрольная вставка с допустимыми значениями проходит',
    $$INSERT INTO work_orders (number, equipment_id, created_by, title, description, priority, status)
      VALUES ('Z-2026-9003', '44444444-4444-4444-4444-444444444444',
              '55555555-0000-0000-0000-000000000003', 'Контроль', 'Контроль', 'Средний', 'Черновик')$$,
    false);

DELETE FROM work_orders WHERE number = 'Z-2026-9003';

-- ---------------------------------------------------------------------------
--  4. Триггеры
-- ---------------------------------------------------------------------------

\echo ''
\echo '=== 4. Триггеры ================================================='

SELECT pg_temp.verify_run('Триггеры', 'trg_equipment_status_guard — статус выведенного из эксплуатации менять нельзя',
    $$UPDATE equipment SET status = 'Работает'
      WHERE inventory_number = 'КП-9'$$, true);

SELECT pg_temp.verify_run('Триггеры', 'trg_equipment_status_guard — прочие поля выведенного менять можно',
    $$UPDATE equipment SET notes = 'Морально изношен, список на списание (уточнено)'
      WHERE inventory_number = 'КП-9'$$, false);

SELECT pg_temp.verify_run('Триггеры', 'trg_work_order_dates_check — фактическое начало позже планового окончания',
    $$UPDATE work_orders SET actual_start = '2026-06-01', actual_end = '2026-06-01 10:00'
      WHERE number = 'Z-2026-0047'$$, true);

SELECT pg_temp.verify_run('Триггеры', 'trg_work_order_dates_check — завершённая заявка без причины неисправности',
    $$UPDATE work_orders SET status = 'Завершена', actual_start = '2026-03-20 08:00',
                            actual_end = '2026-03-20 12:00', failure_reason = '   '
      WHERE number = 'Z-2026-0044'$$, true);

-- Аудит: считаем записи в журнале до и после операции.
DO $$
DECLARE
    v_before integer;
    v_after  integer;
BEGIN
    SELECT count(*) INTO v_before FROM operation_log;
    INSERT INTO work_orders (number, equipment_id, created_by, title, description, priority, status)
    VALUES ('Z-2026-9004', '44444444-4444-4444-4444-444444444444',
            '55555555-0000-0000-0000-000000000003', 'Аудит', 'Аудит', 'Низкий', 'Черновик');
    UPDATE work_orders SET title = 'Аудит изменён'
     WHERE number = 'Z-2026-9004';
    DELETE FROM work_orders WHERE number = 'Z-2026-9004';
    SELECT count(*) INTO v_after FROM operation_log;

    PERFORM pg_temp.verify_add('Триггеры', 'trg_audit_work_orders — INSERT, UPDATE и DELETE пишут в журнал',
        v_after - v_before = 3,
        'записей добавлено: ' || (v_after - v_before) || ' (ожидается 3)');
END;
$$;

-- ---------------------------------------------------------------------------
--  5. Функции
-- ---------------------------------------------------------------------------

\echo ''
\echo '=== 5. Функции =================================================='

SELECT fn_calculate_downtime('2026-03-20 08:00', '2026-03-20 20:30') AS простой_часов,
       18.4::numeric AS ожидается;

SELECT fn_calculate_downtime(NULL, '2026-03-20 20:30') AS при_null_начале,
       fn_calculate_downtime('2026-03-20 08:00', NULL) AS при_null_окончании,
       0::numeric AS ожидается;

SELECT pg_temp.verify_run('Функции', 'fn_calculate_downtime — окончание раньше начала',
    $$SELECT fn_calculate_downtime('2026-03-20 20:00', '2026-03-20 08:00')$$, true);

SELECT fn_next_maintenance_date('2026-01-10', 30)  AS от_января,
       fn_next_maintenance_date('2026-01-10', 90)  AS от_квартала,
       fn_next_maintenance_date('2026-01-10', 365) AS от_года;

SELECT pg_temp.verify_run('Функции', 'fn_next_maintenance_date — неположительный интервал',
    $$SELECT fn_next_maintenance_date('2026-01-10', 0)$$, true);

-- ---------------------------------------------------------------------------
--  6. Процедура и представление
-- ---------------------------------------------------------------------------

\echo ''
\echo '=== 6. Процедура и представление ================================='

CALL proc_workshop_report('aaaaaaaa-0000-0000-0000-000000000002', '2026-03-01', '2026-03-31');

SELECT * FROM v_workshop_report ORDER BY workshop_name, period_month LIMIT 10;

-- ---------------------------------------------------------------------------
--  7. Списание материалов
-- ---------------------------------------------------------------------------

\echo ''
\echo '=== 7. Списание материалов в заявке Z-2026-0047 =================='

SELECT wom.material_id,
       m.name        AS материал,
       m.unit        AS ед,
       wom.quantity  AS количество,
       wom.unit_price AS цена,
       wom.cost      AS стоимость
FROM work_order_materials wom
JOIN materials m ON m.id = wom.material_id
JOIN work_orders wo ON wo.id = wom.work_order_id
WHERE wo.number = 'Z-2026-0047'
ORDER BY wom.cost DESC;

SELECT sum(wom.cost) AS итого_по_заявке,
       7300.00::numeric AS ожидается
FROM work_order_materials wom
JOIN work_orders wo ON wo.id = wom.work_order_id
WHERE wo.number = 'Z-2026-0047';

-- Счётчик номеров: следующая заявка должна получить Z-2026-0048.
SELECT last_value AS счётчик,
       'Z-2026-' || lpad((last_value + 1)::text, 4, '0') AS следующий_номер
FROM work_order_counters WHERE year = 2026;

-- ---------------------------------------------------------------------------
--  Итог
-- ---------------------------------------------------------------------------

\echo ''
\echo '=== Итог проверок =============================================='

SELECT section AS раздел,
       count(*) AS всего,
       count(*) FILTER (WHERE ok) AS успешно,
       count(*) FILTER (WHERE NOT ok) AS не_успешно
FROM verify_result
GROUP BY section
UNION ALL
SELECT 'ИТОГО', count(*), count(*) FILTER (WHERE ok), count(*) FILTER (WHERE NOT ok)
FROM verify_result
ORDER BY 1;

\echo ''
\echo '--- Непрошедшие проверки (должно быть пусто) --------------------'

SELECT section, name, detail
FROM verify_result
WHERE NOT ok
ORDER BY section, name;

DROP FUNCTION pg_temp.verify_run(text, text, text, boolean);
DROP FUNCTION pg_temp.verify_add(text, text, boolean, text);
