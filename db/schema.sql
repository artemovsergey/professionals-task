-- =====================================================================
--  Планировщик личных задач — схема базы данных
--  PostgreSQL 15+
--
--  Скрипт повторяемый: сначала сносит таблицы, потом создаёт заново,
--  поэтому его можно запускать сколько угодно раз.
--  Порядок создания: schema_version -> users -> categories -> tasks.
--
--  Запуск:
--    psql -h 127.0.0.1 -U taskplanner -d taskplanner -f db/schema.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- Чистка: сначала, иначе будет "relation already exists"
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS tasks, categories, users, schema_version CASCADE;

-- ---------------------------------------------------------------------
-- Версия схемы: помогает понять, какая схема применена
-- ---------------------------------------------------------------------
CREATE TABLE schema_version (
    version     VARCHAR(32)   NOT NULL,
    applied_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

INSERT INTO schema_version (version) VALUES ('1.0.0');

-- ---------------------------------------------------------------------
-- Пользователи
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id              BIGSERIAL     PRIMARY KEY,
    email           VARCHAR(255)  NOT NULL,
    password_hash   VARCHAR(255)  NOT NULL,   -- только хеш BCrypt, не пароль
    full_name       VARCHAR(255)  NOT NULL,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_users_email UNIQUE (email),

    -- формат почты: regex, а не LIKE — LIKE '%_@_%._%' пропускает мусор
    CONSTRAINT ck_users_email_format
        CHECK (email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),

    -- btrim: строка из одних пробелов именем не считается
    CONSTRAINT ck_users_full_name
        CHECK (length(btrim(full_name)) > 0)
);

COMMENT ON COLUMN users.password_hash IS 'BCrypt-хеш пароля, открытый пароль не хранится';

-- ---------------------------------------------------------------------
-- Категории (необязательная сущность)
-- Принадлежат пользователю, поэтому уникальность на паре (user_id, name)
-- ---------------------------------------------------------------------
CREATE TABLE categories (
    id        BIGSERIAL     PRIMARY KEY,
    user_id   BIGINT        NOT NULL,
    name      VARCHAR(100)  NOT NULL,
    color     VARCHAR(7)    NULL,              -- #RRGGBB

    CONSTRAINT fk_categories_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    CONSTRAINT uq_categories_user_name UNIQUE (user_id, name),

    CONSTRAINT ck_categories_color
        CHECK (color IS NULL OR color ~ '^#[0-9A-Fa-f]{6}$')
);

-- ---------------------------------------------------------------------
-- Задачи
-- ---------------------------------------------------------------------
CREATE TABLE tasks (
    id            BIGSERIAL     PRIMARY KEY,
    user_id       BIGINT        NOT NULL,
    category_id   BIGINT        NULL,
    title         VARCHAR(200)  NOT NULL,
    description   TEXT          NULL,
    status        VARCHAR(16)   NOT NULL DEFAULT 'new',
    priority      VARCHAR(16)   NOT NULL DEFAULT 'medium',
    due_date      DATE          NULL,
    completed_at  TIMESTAMPTZ   NULL,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    -- задача без владельца невозможна
    CONSTRAINT fk_tasks_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- категорию удалили — задачи остались, категория стала NULL
    CONSTRAINT ck_tasks_title_not_empty
        CHECK (length(btrim(title)) > 0),

    CONSTRAINT ck_tasks_status
        CHECK (status IN ('new', 'in_progress', 'done', 'cancelled')),

    CONSTRAINT ck_tasks_priority
        CHECK (priority IN ('low', 'medium', 'high'))
);

-- Категория добавляется вторым ограничением: таблица categories создана позже
ALTER TABLE tasks
    ADD CONSTRAINT fk_tasks_category
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL;

-- Согласованность completed_at и статуса:
--   status = 'done'  -> completed_at заполнен
--   status <> 'done' -> completed_at пуст
ALTER TABLE tasks
    ADD CONSTRAINT ck_tasks_completed_at
        CHECK (
            (status = 'done'  AND completed_at IS NOT NULL)
            OR
            (status <> 'done' AND completed_at IS NULL)
        );

-- ---------------------------------------------------------------------
-- Индексы: под фильтры и сортировку из задания
-- ---------------------------------------------------------------------
CREATE INDEX ix_tasks_user_id ON tasks (user_id);
CREATE INDEX ix_tasks_status ON tasks (status);
CREATE INDEX ix_tasks_user_status_due ON tasks (user_id, status, due_date);
CREATE INDEX ix_tasks_created_at ON tasks (created_at);

COMMENT ON TABLE tasks IS 'Задачи пользователя; выборка всегда фильтруется по user_id';
COMMENT ON COLUMN tasks.status IS 'new | in_progress | done | cancelled';
COMMENT ON COLUMN tasks.priority IS 'low | medium | high';