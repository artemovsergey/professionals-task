-- ============================================================================
--  ТОиР-Проф: триггеры базы данных
--
--  Выполнять ПОСЛЕ db/schema.sql и db/functions.sql:
--      psql -h 127.0.0.1 -U toirprof -d toirprof -f db/triggers.sql
--
--  Триггер нужен там, где правило зависит от истории изменений или
--  должно сработать при любом способе записи — из приложения, из
--  Postman, из psql. Ограничение CHECK такой силы не имеет.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
--  Триггер №1. Запрет изменения статуса выведенного из эксплуатации
--
--  Условие задания: оборудование, выведенное из эксплуатации, не
--  должно снова начать работать. Проверять это в приложении нельзя —
--  правило можно обойти любым другим путём записи.
--
--  BEFORE UPDATE: проверка должна сработать ДО записи, иначе строка
--  успешно обновится и только потом выбросит ошибку.
--
--  Меняться может что угодно, кроме самого статуса: завести заявку
--  или записать примечание к снятой единице нужно и можно.
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_equipment_status_guard()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status
       AND OLD.status = 'Выведено из эксплуатации' THEN
        RAISE EXCEPTION
            'Оборудование «%» (инвентарный номер %) выведено из эксплуатации: '
            'изменить статус нельзя',
            OLD.name, OLD.inventory_number
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_equipment_status_guard ON equipment;

CREATE TRIGGER trg_equipment_status_guard
    BEFORE UPDATE ON equipment
    FOR EACH ROW
    EXECUTE FUNCTION fn_equipment_status_guard();

-- ----------------------------------------------------------------------------
--  Триггер №2. Комплексная проверка дат заявки
--
--  Условие задания: проверить хронологию дат и рассчитать простой.
--  CHECK-ограничения проверяют каждую пару отдельно, а завязка на
--  таблицу делает возможным правило «нельзя завершить заявку, не
--  указав причину неисправности» — это уже не про даты, а про
--  содержание, и одним CHECK не выразить.
--
--  BEFORE INSERT OR UPDATE: и при создании заявки, и при её закрытии.
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_work_order_dates_check()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    -- 1. Плановые даты
    IF NEW.planned_start IS NOT NULL AND NEW.planned_end IS NOT NULL
       AND NEW.planned_end < NEW.planned_start THEN
        RAISE EXCEPTION
            'Плановая дата окончания (%) раньше даты начала (%)',
            NEW.planned_end, NEW.planned_start
            USING ERRCODE = 'check_violation';
    END IF;

    -- 2. Фактические даты
    IF NEW.actual_start IS NOT NULL AND NEW.actual_end IS NOT NULL
       AND NEW.actual_end < NEW.actual_start THEN
        RAISE EXCEPTION
            'Фактическая дата окончания (%) раньше даты начала (%)',
            NEW.actual_end, NEW.actual_start
            USING ERRCODE = 'check_violation';
    END IF;

    -- 3. Фактическое начало не раньше планового окончания:
    --    работы не могут начаться после того, как должны были закончиться.
    IF NEW.planned_end IS NOT NULL AND NEW.actual_start IS NOT NULL
       AND NEW.actual_start::date > NEW.planned_end THEN
        RAISE EXCEPTION
            'Фактическое начало (%) позже планового окончания (%)',
            NEW.actual_start::date, NEW.planned_end
            USING ERRCODE = 'check_violation';
    END IF;

    -- 4. Завершённая заявка обязана иметь фактические даты
    IF NEW.status = 'Завершена'
       AND (NEW.actual_start IS NULL OR NEW.actual_end IS NULL) THEN
        RAISE EXCEPTION
            'Заявка «%» помечена как завершённая, но не указаны даты начала и окончания работ',
            NEW.number
            USING ERRCODE = 'check_violation';
    END IF;

    -- 5. Завершённая заявка обязана иметь причину неисправности
    IF NEW.status = 'Завершена'
       AND (NEW.failure_reason IS NULL OR btrim(NEW.failure_reason) = '') THEN
        RAISE EXCEPTION
            'Заявка «%» помечена как завершённая, но не указана причина неисправности',
            NEW.number
            USING ERRCODE = 'check_violation';
    END IF;

    -- 6. Простой пересчитывается всегда, когда известны обе даты:
    --    он не вводится вручную, иначе отчёт будет расходиться.
    IF NEW.actual_start IS NOT NULL AND NEW.actual_end IS NOT NULL THEN
        NEW.downtime_hours := fn_calculate_downtime(NEW.actual_start, NEW.actual_end);
    ELSIF NEW.status IN ('Черновик', 'Назначена', 'Отменена') THEN
        NEW.downtime_hours := NULL;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_work_order_dates_check ON work_orders;

CREATE TRIGGER trg_work_order_dates_check
    BEFORE INSERT OR UPDATE ON work_orders
    FOR EACH ROW
    EXECUTE FUNCTION fn_work_order_dates_check();

-- ----------------------------------------------------------------------------
--  Триггер №3. Аудит изменений заявок
--
--  Условие задания: журнал операций. Писать аудит в приложении —
--  значит забыть его в одном из путей записи. Триггер пишет всегда.
--
--  AFTER INSERT OR UPDATE OR DELETE: смотрим на итоговое состояние строки,
--  само изменение к этому моменту уже произошло.
--
--  Кто именно работал, берём из настройки сессии current_setting('app.user_id').
--  Прямой INSERT из psql останется без автора — это нормально: журнал
--  покажет, что автор неизвестен.
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_write_audit()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_user_id uuid;
BEGIN
    BEGIN
        v_user_id := nullif(current_setting('app.user_id', true), '')::uuid;
    EXCEPTION
        WHEN invalid_text_representation THEN
            v_user_id := NULL;
    END;

    IF TG_OP = 'INSERT' THEN
        INSERT INTO operation_log (user_id, table_name, record_id, operation, old_values, new_values)
        VALUES (v_user_id, TG_TABLE_NAME, NEW.id, 'INSERT', NULL, to_jsonb(NEW));

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO operation_log (user_id, table_name, record_id, operation, old_values, new_values)
        VALUES (v_user_id, TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));

    ELSE
        INSERT INTO operation_log (user_id, table_name, record_id, operation, old_values, new_values)
        VALUES (v_user_id, TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD), NULL);
    END IF;

    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_audit_work_orders ON work_orders;

CREATE TRIGGER trg_audit_work_orders
    AFTER INSERT OR UPDATE OR DELETE ON work_orders
    FOR EACH ROW
    EXECUTE FUNCTION fn_write_audit();

-- ----------------------------------------------------------------------------
--  Аудит оборудования: тот же журнал, но отдельный триггер.
--  Смена статуса и снятие с учёта — события, о которых спрашивают
--  в первую очередь, поэтому они тоже попадают в журнал.
-- ----------------------------------------------------------------------------

DROP TRIGGER IF EXISTS trg_audit_equipment ON equipment;

CREATE TRIGGER trg_audit_equipment
    AFTER INSERT OR UPDATE OR DELETE ON equipment
    FOR EACH ROW
    EXECUTE FUNCTION fn_write_audit();

COMMIT;

-- ----------------------------------------------------------------------------
--  Проверка после выполнения:
--
--    SELECT tgname FROM pg_trigger
--     WHERE tgname LIKE 'trg_%' AND NOT tgisinternal ORDER BY tgname;
--
--  Ожидаемо четыре строки: trg_audit_equipment, trg_audit_work_orders,
--  trg_equipment_status_guard, trg_work_order_dates_check.
-- ----------------------------------------------------------------------------