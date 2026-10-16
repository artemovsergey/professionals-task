-- ============================================================================
--  ТОиР-Проф: функции базы данных
--
--  Выполнять ПОСЛЕ db/schema.sql и ДО db/triggers.sql:
--      psql -h 127.0.0.1 -U toirprof -d toirprof -f db/functions.sql
--
--  Функции помечены STABLE — они читают таблицы, но не меняют их.
--  Метка нужна планировщику: значение функции вычисляется один раз
--  в пределах одной SQL-команды.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
--  Функция №1. Расчёт простоя оборудования в часах
--
--  Простой — это разница между моментом окончания работ и моментом
--  начала. Возвращаем NUMERIC с двумя знаками: часы с сотыми нужны
--  для отчётов и суммирования, а FLOAT там даёт артефакты вида 7.29999.
--
--  Правила обработки граничных случаев:
--    * NULL на любом конце — простоя ещё не было, возвращаем 0;
--    * окончание раньше начала — это ошибка данных, а не ноль часов:
--      поднимаем исключение, чтобы ошибка всплыла, а не замаскировалась;
--    * окончание равно началу — простоя не было, возвращаем 0.
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_calculate_downtime(
    p_start timestamptz,
    p_end   timestamptz
)
RETURNS numeric
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_hours numeric;
BEGIN
    IF p_start IS NULL OR p_end IS NULL THEN
        RETURN 0;
    END IF;

    IF p_end < p_start THEN
        RAISE EXCEPTION
            'Недопустимый интервал: окончание (%) раньше начала (%)',
            p_end, p_start
            USING ERRCODE = 'check_violation';
    END IF;

    v_hours := round(EXTRACT(EPOCH FROM (p_end - p_start)) / 3600.0, 2);

    IF v_hours < 0 THEN
        v_hours := 0;
    END IF;

    RETURN v_hours;
END;
$$;

COMMENT ON FUNCTION fn_calculate_downtime(timestamptz, timestamptz) IS
    'Простой оборудования в часах. NULL на любом конце даёт 0, окончание раньше начала — исключение.';

-- ----------------------------------------------------------------------------
--  Функция №2. Следующая плановая дата технического обслуживания
--
--  Плановое ТО повторяется с периодом, заданным справочником
--  видов обслуживания. Возвращаем дату следующего планового обслуживания,
--  отсчитанную от даты выполнения.
--
--  Период приводим к календарному месяцу от интервала в днях
--  (30 дней ≈ месяц): точный месяц из целого числа дней получить нельзя,
--  а «каждые 30 дней» и «раз в месяц» в графике ТО — одно и то же.
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_next_maintenance_date(
    p_from          date,
    p_interval_days integer
)
RETURNS date
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_months integer;
BEGIN
    IF p_from IS NULL THEN
        RETURN NULL;
    END IF;

    IF p_interval_days IS NULL OR p_interval_days <= 0 THEN
        RAISE EXCEPTION
            'Интервал обслуживания должен быть положительным, получено %', p_interval_days
            USING ERRCODE = 'check_violation';
    END IF;

    -- 31 день и дольше — округляем вверх до месяца, иначе округляем к полумесяцу.
    v_months := GREATEST(1, round(p_interval_days / 30.0)::integer);

    -- Первый день месяца: график планового ТО привязан к началу периода,
    -- иначе записи одного вида обслуживания разъезжаются по дням.
    --
    -- Месяц приходится нормализовать вручную: make_date не берёт тринадцатый
    -- месяц и выдаёт ошибку «дата вне диапазона». При интервале в год (365
    -- дней) к месяцу прибавляется 12, и без этого сложения годовое ТО
    -- из января не сдвигается на следующий год. Схема та же, что и в
    -- календарной арифметике: (месяц + сдвиг - 1) делим на 12.
    RETURN make_date(
        EXTRACT(YEAR  FROM p_from)::integer
            + (EXTRACT(MONTH FROM p_from)::integer + v_months - 1) / 12,
        ((EXTRACT(MONTH FROM p_from)::integer + v_months - 1) % 12) + 1,
        1
    );
END;
$$;

COMMENT ON FUNCTION fn_next_maintenance_date(date, integer) IS
    'Дата следующего планового ТО: первый день месяца, отстоящего на интервал дней.';

-- ----------------------------------------------------------------------------
--  Процедура №3. Сводный отчёт по цеху за период
--
--  Процедура, а не функция: результат не возвращается, а выводится
--  через RAISE NOTICE. Так она вызывается из psql и из DBeaver
--  одним и тем же способом.
--
--  Принимает цех и период, печатает:
--    1. количество единиц оборудования в цеху и их статусы;
--    2. сводку по заявкам: сколько, сколько закрыто, суммарный простой;
--    3. пять единиц оборудования с наибольшим простоем.
-- ----------------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE proc_workshop_report(
    p_workshop_id uuid,
    p_from        date,
    p_to          date
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_name      text;
    v_total     integer;
    v_working   integer;
    v_repair    integer;
    v_retired   integer;
    v_orders    integer;
    v_completed integer;
    v_downtime  numeric;
    v_row       record;
BEGIN
    SELECT name INTO v_name
    FROM workshops
    WHERE id = p_workshop_id;

    IF v_name IS NULL THEN
        RAISE NOTICE 'Цех с идентификатором % не найден', p_workshop_id;
        RETURN;
    END IF;

    IF p_from IS NULL OR p_to IS NULL OR p_to < p_from THEN
        RAISE NOTICE 'Некорректный период: с % по %', p_from, p_to;
        RETURN;
    END IF;

    RAISE NOTICE '================================================================';
    RAISE NOTICE 'СВОДНЫЙ ОТЧЁТ ПО ЦЕХУ «%»', upper(v_name);
    RAISE NOTICE 'Период: с % по %', p_from, p_to;
    RAISE NOTICE '================================================================';

    -- 1. Оборудование цеха
    SELECT count(*),
           count(*) FILTER (WHERE status = 'Работает'),
           count(*) FILTER (WHERE status = 'В ремонте'),
           count(*) FILTER (WHERE status = 'Выведено из эксплуатации')
      INTO v_total, v_working, v_repair, v_retired
      FROM equipment
     WHERE workshop_id = p_workshop_id;

    RAISE NOTICE '';
    RAISE NOTICE 'ОБОРУДОВАНИЕ: всего %, работает %, в ремонте %, выведено из эксплуатации %',
                 v_total, v_working, v_repair, v_retired;

    -- 2. Сводка по заявкам за период
    SELECT count(*),
           count(*) FILTER (WHERE wo.status = 'Завершена'),
           COALESCE(sum(wo.downtime_hours), 0)
      INTO v_orders, v_completed, v_downtime
      FROM work_orders wo
      JOIN equipment e ON e.id = wo.equipment_id
     WHERE e.workshop_id = p_workshop_id
       AND wo.created_at >= p_from::timestamptz
       AND wo.created_at <  (p_to::timestamptz + INTERVAL '1 day');

    RAISE NOTICE '';
    RAISE NOTICE 'ЗАЯВКИ ЗА ПЕРИОД: всего %, завершено %', v_orders, v_completed;
    RAISE NOTICE 'СУММАРНЫЙ ПРОСТОЙ: % ч', v_downtime;

    -- 3. Топ-5 единиц оборудования по простою
    RAISE NOTICE '';
    RAISE NOTICE 'ТОП-5 ОБОРУДОВАНИЯ ПО ПРОСТОЮ:';
    RAISE NOTICE '%', rpad('Инвентарный номер', 20) || rpad('Наименование', 34) || rpad('Заявок', 9) || 'Простой, ч';

    FOR v_row IN
        SELECT e.inventory_number,
               e.name,
               count(*)                        AS order_count,
               COALESCE(sum(wo.downtime_hours), 0) AS total_downtime
          FROM work_orders wo
          JOIN equipment e ON e.id = wo.equipment_id
         WHERE e.workshop_id = p_workshop_id
           AND wo.created_at >= p_from::timestamptz
           AND wo.created_at <  (p_to::timestamptz + INTERVAL '1 day')
         GROUP BY e.inventory_number, e.name
         ORDER BY total_downtime DESC
         LIMIT 5
    LOOP
        RAISE NOTICE '%',
            rpad(v_row.inventory_number, 20)
            || rpad(v_row.name, 34)
            || rpad(v_row.order_count::text, 9)
            || v_row.total_downtime;
    END LOOP;

    RAISE NOTICE '================================================================';
END;
$$;

-- ----------------------------------------------------------------------------
--  Обёртка для API.
--
--  Процедуру из C# вызвать нельзя, а функции — можно. Поэтому та же
--  логика отчёта доступна и как представление: приложение читает
--  сводку обычным SELECT, а процедура остаётся для демонстрации
--  в DBeaver и psql, как того требует задание.
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW v_workshop_report AS
SELECT
    e.workshop_id,
    w.name                                                        AS workshop_name,
    date_trunc('month', wo.created_at)::date                     AS period_month,
    wo.status,
    wo.priority,
    count(*)                                                      AS orders_count,
    COALESCE(sum(wo.downtime_hours), 0)                           AS downtime_hours,
    COALESCE(sum(wom.cost), 0)                                    AS material_cost
FROM work_orders wo
JOIN equipment e                ON e.id = wo.equipment_id
JOIN workshops w                ON w.id = e.workshop_id
LEFT JOIN work_order_materials wom ON wom.work_order_id = wo.id
GROUP BY e.workshop_id, w.name, date_trunc('month', wo.created_at)::date,
         wo.status, wo.priority;

COMMENT ON VIEW v_workshop_report IS
    'Сводный отчёт по цехам, месяцам, статусам и приоритетам — источник для дашборда и аналитики.';

-- Счётчик номеров: с 2026 года нумерация заявок идёт по этому году.
INSERT INTO work_order_counters (year, last_value)
VALUES (2026, 0)
ON CONFLICT (year) DO NOTHING;

COMMIT;