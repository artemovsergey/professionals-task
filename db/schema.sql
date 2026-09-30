-- =====================================================================
--  Планировщик личных задач — пример схемы базы данных
--  СУБД: PostgreSQL 15+  (для MySQL см. комментарии внизу файла)
--  Файл можно использовать как есть либо написать свою схему.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Пользователи
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id              BIGSERIAL     PRIMARY KEY,
    email           VARCHAR(255)  NOT NULL,
    password_hash   VARCHAR(255)  NOT NULL,
    full_name       VARCHAR(255)  NOT NULL,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT ck_users_email_format CHECK (email LIKE '%_@_%._%')
);

-- ---------------------------------------------------------------------
-- Задачи
-- ---------------------------------------------------------------------
CREATE TABLE tasks (
    id              BIGSERIAL     PRIMARY KEY,
    user_id         BIGINT        NOT NULL,
    title           VARCHAR(200)  NOT NULL,
    description     TEXT          NULL,
    status          VARCHAR(16)   NOT NULL DEFAULT 'new',
    priority        VARCHAR(16)   NOT NULL DEFAULT 'medium',
    due_date        DATE          NULL,
    completed_at    TIMESTAMPTZ   NULL,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_tasks_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,

    CONSTRAINT ck_tasks_title_not_empty CHECK (length(trim(title)) > 0),
    CONSTRAINT ck_tasks_status
        CHECK (status IN ('new', 'in_progress', 'done', 'cancelled')),
    CONSTRAINT ck_tasks_priority
        CHECK (priority IN ('low', 'medium', 'high')),

    -- Дата выполнения выставляется только у выполненной задачи
    CONSTRAINT ck_tasks_completed_at
        CHECK ((status = 'done' AND completed_at IS NOT NULL)
            OR (status <> 'done' AND completed_at IS NULL))
);

-- Категории — необязательная сущность, баллы за неё не начисляются
CREATE TABLE categories (
    id          BIGSERIAL     PRIMARY KEY,
    user_id     BIGINT        NOT NULL,
    name        VARCHAR(100)  NOT NULL,
    color       VARCHAR(7)    NULL,

    CONSTRAINT fk_categories_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT uq_categories_user_name UNIQUE (user_id, name)
);

ALTER TABLE tasks ADD COLUMN category_id BIGINT NULL;
ALTER TABLE tasks
    ADD CONSTRAINT fk_tasks_category
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL;

-- ---------------------------------------------------------------------
-- Индексы
-- ---------------------------------------------------------------------
CREATE INDEX ix_tasks_user_id      ON tasks (user_id);
CREATE INDEX ix_tasks_status       ON tasks (status);
CREATE INDEX ix_tasks_priority     ON tasks (priority);
CREATE INDEX ix_tasks_due_date     ON tasks (due_date);
CREATE INDEX ix_tasks_user_status  ON tasks (user_id, status);

-- ---------------------------------------------------------------------
-- Пример данных для проверки (не обязателен)
-- ---------------------------------------------------------------------
INSERT INTO users (email, password_hash, full_name) VALUES
    ('student@college.ru', '$2a$10$examplehashnotarealhash0000000000000000000000', 'Иван Петров'),
    ('teacher@college.ru', '$2a$10$examplehashnotarealhash0000000000000000000000', 'Мария Сидорова');

INSERT INTO categories (user_id, name, color) VALUES
    (1, 'Учёба',    '#4ECC0A'),
    (1, 'Личное',   '#0F9346'),
    (1, 'Работа',   '#FCEE73');

INSERT INTO tasks (user_id, category_id, title, description, status, priority, due_date) VALUES
    (1, 1, 'Сделать ER-диаграмму',  'Схема сущностей и связей',       'new',        'high',   CURRENT_DATE + 2),
    (1, 3, 'Сверстать главную',      'Список задач, адаптив',           'in_progress','medium', CURRENT_DATE + 5),
    (1, 2, 'Сходить в спортзал',     NULL,                             'done',       'low',    CURRENT_DATE - 1);

UPDATE tasks SET completed_at = NOW() WHERE id = 3;

-- ---------------------------------------------------------------------
-- Полезный запрос: сводка по задачам пользователя
-- ---------------------------------------------------------------------
-- SELECT
--     COUNT(*)                                                        AS total,
--     COUNT(*) FILTER (WHERE status = 'done')                         AS done,
--     COUNT(*) FILTER (WHERE status <> 'done')                        AS not_done,
--     COUNT(*) FILTER (WHERE status <> 'done'
--                        AND due_date IS NOT NULL
--                        AND due_date < CURRENT_DATE)                  AS overdue
-- FROM tasks
-- WHERE user_id = 1;


-- =====================================================================
--  Порядок создания для MySQL
--  ---------------------------------------------------------------------
--  1. BIGSERIAL       -> BIGINT UNSIGNED AUTO_INCREMENT
--  2. TIMESTAMPTZ     -> TIMESTAMP  (или DATETIME)
--  3. length(trim(x)) -> CHAR_LENGTH(TRIM(x))
--  4. ALTER TABLE ... ADD COLUMN без IF NOT EXISTS выполнять один раз
--  5. Последовательность: users -> categories -> tasks
-- =====================================================================
