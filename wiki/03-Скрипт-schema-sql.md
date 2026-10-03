Сессия 1. База данных · 20–110 мин

# 1. Подготовка скрипта (20–25 мин)

Создайте файл `db/schema.sql`. Порядок выполнения важен:

```bash
createdb -h 127.0.0.1 -U taskplanner taskplanner
```

> **Замечание:** база уже создана на странице [00](00-Подготовка-окружения).
> Если удаляли базу между сессиями — создайте заново, таблиц в ней не будет.

Скрипт должен быть **повторяемым**: сначала сносятся таблицы в правильном
порядке, потом создаются заново. Иначе при втором запуске будет ошибка
`relation "tasks" already exists`.

# 2. Пользователи (25–40 мин)

```sql
-- =====================================================================
--  Планировщик личных задач — схема базы данных
--  СУБД: PostgreSQL 15+
--  Запуск:  psql -h 127.0.0.1 -U taskplanner -d taskplanner -f db/schema.sql
-- =====================================================================

-- Порядок сноса: сначала зависимые таблицы (tasks, categories),
-- потом users. CASCADE снимает зависимости между ними.
DROP TABLE IF EXISTS tasks     CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS users     CASCADE;

DROP TABLE IF EXISTS schema_version CASCADE;

CREATE TABLE schema_version (
    version     VARCHAR(32)  NOT NULL,
    applied_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO schema_version (version) VALUES ('1.0.0');

-- ---------------------------------------------------------------------
-- Пользователи
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id              BIGSERIAL     PRIMARY KEY,
    email           VARCHAR(255)  NOT NULL,
    password_hash   VARCHAR(255)  NOT NULL,
    full_name       VARCHAR(255)  NOT NULL,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    -- Email уникален: без этого можно зарегистрироваться дважды
    CONSTRAINT uq_users_email UNIQUE (email),

    -- Грубая проверка формата. Это НЕ полноценная валидация email —
    -- её делает сервер (валидация DTO), здесь ловим явный мусор.
    CONSTRAINT ck_users_email_format CHECK (email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),

    -- Имя не может состоять только из пробелов
    CONSTRAINT ck_users_full_name CHECK (length(btrim(full_name)) > 0)
);

COMMENT ON TABLE  users             IS 'Пользователи системы';
COMMENT ON COLUMN users.email       IS 'Логин и email, уникальный';
COMMENT ON COLUMN users.password_hash IS 'Хеш пароля (BCrypt). Открытый пароль в БД не хранится';
```

**Разбор ограничений:**

| Ограничение | Зачем |
|---|---|
| `NOT NULL` на `email`, `password_hash`, `full_name` | обязательные поля не могут оказаться пустыми |
| `UNIQUE (email)` | один человек — один аккаунт; ловит гонку двух одновременных регистраций |
| `CHECK (email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$')` | отсекает мусор на входе в БД |
| `CHECK (length(btrim(full_name)) > 0)` | строка из одних пробелов не считается именем |

> **Замечание:** `btrim` — обрезка пробелов с обоих концов. `trim` работает
> только со строковыми символами; для текста с пробелами и табуляцией
> используйте `btrim`.

# 3. Категории (необязательные) (40–48 мин)

```sql
-- ---------------------------------------------------------------------
-- Категории — необязательная сущность, баллы за неё не начисляются.
-- Делайте, если успеваете: она нужна полю categoryId в API.
-- ---------------------------------------------------------------------
CREATE TABLE categories (
    id          BIGSERIAL     PRIMARY KEY,
    user_id     BIGINT        NOT NULL,
    name        VARCHAR(100)  NOT NULL,
    color       VARCHAR(7)    NULL,

    CONSTRAINT fk_categories_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,

    -- Уникальность в пределах пользователя: у разных людей
    -- могут быть категории с одинаковым названием
    CONSTRAINT uq_categories_user_name UNIQUE (user_id, name),

    CONSTRAINT ck_categories_name
        CHECK (length(btrim(name)) > 0),

    -- Цвет либо отсутствует, либо в формате #RRGGBB
    CONSTRAINT ck_categories_color
        CHECK (color IS NULL OR color ~ '^#[0-9A-Fa-f]{6}$')
);
```

> **Замечание:** `ON DELETE CASCADE` у категорий означает, что при удалении
> пользователя его категории удаляются автоматически. Забыть про `ON DELETE`
> — значит получить ошибку при удалении пользователя.

# 4. Задачи (48–70 мин)

```sql
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

    CONSTRAINT ck_tasks_title_not_empty
        CHECK (length(btrim(title)) > 0),

    CONSTRAINT ck_tasks_status
        CHECK (status IN ('new', 'in_progress', 'done', 'cancelled')),

    CONSTRAINT ck_tasks_priority
        CHECK (priority IN ('low', 'medium', 'high')),

    -- Дата выполнения выставляется ТОЛЬКО у выполненной задачи.
    -- Согласованность двух полей средствами БД, а не только в коде.
    CONSTRAINT ck_tasks_completed_at
        CHECK ((status = 'done'  AND completed_at IS NOT NULL)
            OR (status <> 'done' AND completed_at IS NULL))
);

COMMENT ON TABLE  tasks                   IS 'Задачи пользователей';
COMMENT ON COLUMN tasks.user_id           IS 'Владелец задачи. Все выборки фильтруются по нему';
COMMENT ON COLUMN tasks.completed_at      IS 'Дата и время выполнения. Не NULL только при status = done';
COMMENT ON COLUMN tasks.due_date          IS 'Срок. NULL — срока нет';

-- Категория добавляется отдельным ALTER: так порядок создания таблиц
-- остаётся users -> categories -> tasks без циклических зависимостей.
ALTER TABLE tasks
    ADD COLUMN category_id BIGINT NULL;

ALTER TABLE tasks
    ADD CONSTRAINT fk_tasks_category
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL;
```

**Почему `ON DELETE SET NULL` у категории, а не `CASCADE`:**

- удалили категорию «Учёба» — задачи, которые к ней относились, должны
  **остаться** у пользователя;
- `SET NULL` оставляет задачу живой, но без категории;
- `CASCADE` здесь удалил бы задачи вместе с категорией, что неверно.

**Ограничение `ck_tasks_completed_at` — самое важное и самое коварное:**

Оно требует **строгой согласованности**:

| `status` | `completed_at` | Результат |
|---|---|---|
| `done` | задан | ✅ |
| `done` | `NULL` | ❌ нарушение CHECK |
| не `done` | задан | ❌ нарушение CHECK |
| не `done` | `NULL` | ✅ |

Практическое следствие: **нельзя** выполнить `UPDATE tasks SET status='done'`
отдельно от `UPDATE tasks SET completed_at=NOW()` — первый запрос упадёт.
Оба значения меняются в одной транзакции, а приложение должно выставлять их
согласованно. Это обсуждается на странице [09-CRUD-задач](09-CRUD-задач).

# 5. Индексы (70–85 мин)

```sql
-- ---------------------------------------------------------------------
-- Индексы
-- ---------------------------------------------------------------------
-- Узкий индекс по владельцу: самый частый запрос — «задачи пользователя»
CREATE INDEX ix_tasks_user_id   ON tasks (user_id);

-- Фильтры по статусу и сроку
CREATE INDEX ix_tasks_status    ON tasks (status);
CREATE INDEX ix_tasks_due_date  ON tasks (due_date);

-- Составной: запрос «задачи пользователя со статусом X с сортировкой по сроку»
-- обслуживается одним индексом вместо двух
CREATE INDEX ix_tasks_user_status_due ON tasks (user_id, status, due_date);

-- Поиск по названию: LIKE '%текст%' индексом не ускоряется,
-- поэтому ограничиваемся префиксным поиском по title
CREATE INDEX ix_tasks_title_lower ON tasks (lower(title));

-- Сводка считает условия по датам — помогает диапазонный доступ
CREATE INDEX ix_tasks_created_at ON tasks (created_at);
```

Проверьте, что индексы действительно созданы:

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'tasks'
ORDER BY indexname;
```

> **Замечание:** составной индекс `(user_id, status, due_date)` покрывает и
> запросы без `status` — PostgreSQL использует его префикс. Не плодите
> индексы на каждый столбец: лишние индексы замедляют вставку.

# 6. Проверка ограничений на уровне БД (85–110 мин)

Создайте `db/check_constraints.sql` — скрипт, который **должен упасть** на
каждом нарушении. Запустите его и убедитесь, что он останавливает каждую
попытку:

```sql
-- Каждый блок ниже ДОЛЖЕН завершиться ошибкой. Это проверка того,
-- что ограничения работают на уровне базы данных.
-- psql по умолчанию прерывается на первой ошибке, поэтому запускайте
-- каждый блок отдельно:  psql -v ON_ERROR_STOP=1 -c "<запрос>"

-- Подготовка: временный пользователь, на котором проверяем ограничения.
-- Он получает id = 1, и на него ссылаются все INSERT в tasks.
INSERT INTO users (email, password_hash, full_name)
VALUES ('check@college.ru', 'notarealhash', 'Проверка ограничений');

-- 1. Дубликат email                    -> ERROR: duplicate key value violates unique constraint "uq_users_email"
INSERT INTO users (email, password_hash, full_name)
VALUES ('check@college.ru', 'x', 'Дубль');

-- 2. Пустое имя из пробелов            -> ERROR: new row violates check constraint "ck_users_full_name"
INSERT INTO users (email, password_hash, full_name)
VALUES ('spaces@college.ru', 'x', '     ');

-- 3. Кривой email                      -> ERROR: violates check constraint "ck_users_email_format"
INSERT INTO users (email, password_hash, full_name)
VALUES ('не-почта', 'x', 'Иван');

-- 4. Неизвестный статус                -> ERROR: violates check constraint "ck_tasks_status"
INSERT INTO tasks (user_id, title, status)
VALUES (1, 'Задача', 'сделано');

-- 5. Неизвестный приоритет             -> ERROR: violates check constraint "ck_tasks_priority"
INSERT INTO tasks (user_id, title, priority)
VALUES (1, 'Задача', 'очень-важно');

-- 6. Пустое название                   -> ERROR: violates check constraint "ck_tasks_title_not_empty"
INSERT INTO tasks (user_id, title)
VALUES (1, '   ');

-- 7. Выполнена без completed_at        -> ERROR: violates check constraint "ck_tasks_completed_at"
INSERT INTO tasks (user_id, title, status)
VALUES (1, 'Задача', 'done');

-- 8. Не выполнена, но completed_at     -> ERROR: violates check constraint "ck_tasks_completed_at"
INSERT INTO tasks (user_id, title, status, completed_at)
VALUES (1, 'Задача', 'in_progress', NOW());

-- 9. Несуществующий пользователь       -> ERROR: insert or update on table "tasks" violates foreign key constraint "fk_tasks_user"
INSERT INTO tasks (user_id, title)
VALUES (999999, 'Задача');

-- 10. Название длиннее 200 символов    -> ERROR: value too long for type character varying(200)
INSERT INTO tasks (user_id, title)
VALUES (1, repeat('я', 201));
```

Блоки 1–10 запускайте **по одному**. Все должны упасть. Это и есть
доказательство, что ограничения сделаны средствами SQL, а не только в коде.

Обратите внимание на порядок проверки PostgreSQL: сначала `NOT NULL`, затем
`CHECK` и длина значения, и только потом срабатывает внешний ключ. Поэтому в
блоке 10 вы увидите ошибку длины, а не ошибку внешнего ключа — ограничения
срабатывают раньше, чем FK-триггер.

Затем проверьте, что целостность данных поддерживается:

```sql
-- Связность: задачи и категории создаются от временного пользователя
INSERT INTO categories (user_id, name, color) VALUES (1, 'Учёба', '#4ECC0A');
INSERT INTO tasks (user_id, title) VALUES (1, 'Задача к удалению');

SELECT count(*) FROM tasks      WHERE user_id = 1;   -- 1
SELECT count(*) FROM categories WHERE user_id = 1;   -- 1

-- Каскадное удаление: задачи и категории исчезнут вместе с пользователем
DELETE FROM users WHERE id = 1;

SELECT count(*) FROM tasks      WHERE user_id = 1;   -- 0
SELECT count(*) FROM categories WHERE user_id = 1;   -- 0
```

Заодно убедитесь, что `SET NULL` работает мягче, чем каскад:

```sql
INSERT INTO users (email, password_hash, full_name)
VALUES ('cascade-check@college.ru', 'x', 'Проверка категории');

INSERT INTO categories (user_id, name) VALUES (2, 'Учёба');
INSERT INTO tasks (user_id, title, category_id, status, completed_at)
VALUES (2, 'Задача с категорией', 2, 'done', NOW());

DELETE FROM categories WHERE id = 2;

SELECT title, category_id FROM tasks WHERE user_id = 2;
-- Задача осталась, category_id стал NULL

DELETE FROM users WHERE email = 'cascade-check@college.ru';
```

# Проверка

Выполните в DBeaver (правый клик по скрипту → «Выполнить SQL») и в терминале:

```bash
psql -h 127.0.0.1 -U taskplanner -d taskplanner -f db/schema.sql
```

Ожидаемый результат: серии `CREATE TABLE`, `CREATE INDEX`, `COMMENT`, без
ошибок. Затем:

```sql
\d users
\d tasks
SELECT version FROM schema_version;   -- 1.0.0
```

`\d tasks` покажет колонки, индексы и все ограничения, включая
`ck_tasks_completed_at`.

# Коммит

```bash
git add db/schema.sql db/check_constraints.sql
git commit -m "База данных: схема PostgreSQL, ограничения целостности, индексы"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| `permission denied for database taskplanner` | вы вошли не под `taskplanner`; в `pg_hba.conf` должен быть `scram-sha-256`, а не только `peer` |
| `relation "tasks" already exists` | не добавили `DROP TABLE IF EXISTS ... CASCADE` в начало скрипта |
| `syntax error at or near "btrim"` | `btrim` есть в PostgreSQL 9.1+; на очень старой версии используйте `trim(both from ...)` |
| `operator does not exist: character varying ~ unknown` | оператор `~` требует тип `text`: напишите `email::text ~ '...'` |
| Не понимаете, зачем `schema_version` | на отборе не обязательно, но на реальном проекте это удобно: видно, какая версия схемы применена |
| Ограничения проверяются только в коде приложения | это снимает баллы: ограничения должны быть в БД — см. раздел 1 `criteria.md` |

## Иллюстрации

![[images/db03-tree.png]]
*Схема `public` с таблицами после выполнения `db/schema.sql` в DBeaver*

![[images/db03-tasks-columns.png]]
*Колонки `tasks`: имена, типы и обязательность*

![[images/db03-tasks-constraints.png]]
*Семь ограничений таблицы `tasks` — из системного каталога*

![[images/db03-tasks-indexes.png]]
*Индексы `tasks`, которые создаёт скрипт*
