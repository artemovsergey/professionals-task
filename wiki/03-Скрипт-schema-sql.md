Сессия 1. База данных · 20–110 мин

# Как читать эту страницу

Каждый шаг ниже — одна небольшая операция: сначала кусок кода, который надо
добавить в `db/schema.sql`, затем снимок того, как этот кусок выглядит в DBeaver
после выполнения. Скриншот снимайте сами — так вы увидите и свою ошибку.

Файлы для работы: `db/schema.sql` (схема) и `db/check_constraints.sql`
(проверка ограничений, страница [04](04-Тестовые-данные-и-проверка-ограничений)).

# 1. Подготовка базы (20–25 мин)

```bash
createdb -h 127.0.0.1 -U taskplanner taskplanner
```

> **Замечание:** база уже создана на странице [00](00-Подготовка-окружения).
> Если удаляли базу между сессиями — создайте заново, таблиц в ней не будет.

Скрипт должен быть **повторяемым**: сначала сносятся таблицы, потом создаются
заново. Иначе при втором запуске будет ошибка `relation "tasks" already exists`.

# 2. Шаг 1. Снос таблиц (25 мин)

```sql
DROP TABLE IF EXISTS tasks, categories, users, schema_version CASCADE;
```

Порядок не важен, потому что `CASCADE` снимает зависимости. Одна команда вместо
четырёх — так скрипт короче и его легче повторить.

![[images/db03-s1-drop.png]]
*Снос таблиц выполнен, CloudBeaver показывает `Status: Executed`*

# 3. Шаг 2. Версия схемы (30 мин)

```sql
CREATE TABLE schema_version (
    version    VARCHAR(32) NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Таблица не влияет на работу приложения. Она нужна, чтобы на реальном проекте
было видно, какая версия схемы применена к этой базе.

![[images/db03-s2-version-table.png]]
*Таблица `schema_version` создана*

# 4. Шаг 3. Запись версии (32 мин)

```sql
INSERT INTO schema_version (version) VALUES ('1.0.0');
SELECT * FROM schema_version;
```

![[images/db03-s3-version-row.png]]
*Версия `1.0.0` записана вместе со временем применения*

# 5. Шаг 4. Таблица пользователей (35–45 мин)

```sql
CREATE TABLE users (
    id            BIGSERIAL    PRIMARY KEY,
    email         VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(255) NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT ck_users_email_format
        CHECK (email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
    CONSTRAINT ck_users_full_name CHECK (length(btrim(full_name)) > 0)
);
```

Три ограничения вместо одной проверки в коде:

| Ограничение | Что ловит |
|---|---|
| `UNIQUE (email)` | второй аккаунт на тот же адрес, включая гонку двух одновременных регистраций |
| `CHECK (email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$')` | явный мусор в адресе на входе в БД |
| `CHECK (length(btrim(full_name)) > 0)` | строку из одних пробелов как «имя» |

> **Замечание:** `btrim` обрезает пробелы с обоих концов. `trim` работает только
> со строковыми символами; для текста с пробелами используйте `btrim`.
> Регулярное выражение пишется без кавычек-экранирований: `\s` в SQL-литерале
> пишется как есть.

![[images/db03-s4-users.png]]
*Таблица `users` с тремя ограничениями*

# 6. Шаг 5. Первая запись (45 мин)

```sql
INSERT INTO users (email, password_hash, full_name)
VALUES ('teacher@college.ru', '$2b$10$hashed', 'Иван Петров');
SELECT id, email, full_name FROM users;
```

Пароль в базе не хранится: в `password_hash` лежит хеш BCrypt.

![[images/db03-s5-users-row.png]]
*Пользователь создан, `id` присвоен последовательностью*

# 7. Шаг 6. Дубль email (46 мин)

```sql
INSERT INTO users (email, password_hash, full_name)
VALUES ('teacher@college.ru', '$2b$10$hashed', 'Второй Иван');
```

![[images/db03-s6-users-email-error.png]]
*Отказ: `new row for relation "users" violates unique constraint "uq_users_email"`*

# 8. Шаг 7. Имя из пробелов (47 мин)

```sql
INSERT INTO users (email, password_hash, full_name)
VALUES ('spaces@college.ru', '$2b$10$hashed', '   ');
```

![[images/db03-s7-users-name-error.png]]
*Отказ: `violates check constraint "ck_users_full_name"`*

# 9. Шаг 8. Таблица категорий (48–52 мин)

```sql
CREATE TABLE categories (
    id      BIGSERIAL    PRIMARY KEY,
    user_id BIGINT       NOT NULL,
    name    VARCHAR(100) NOT NULL,
    color   VARCHAR(7)   NULL,
    CONSTRAINT fk_categories_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT uq_categories_user_name UNIQUE (user_id, name)
);
```

Категории — необязательная сущность, баллы за неё не начисляются. Без неё
поле `categoryId` в API тоже можно убрать.

`ON DELETE CASCADE` у категорий означает: при удалении пользователя его
категории удаляются автоматически. Забыть `ON DELETE` — значит получить ошибку
при удалении пользователя.

![[images/db03-s8-categories.png]]
*Категории привязаны к пользователю каскадом, имя уникально внутри пользователя*

# 10. Шаг 9. Таблица задач (52–62 мин)

```sql
CREATE TABLE tasks (
    id           BIGSERIAL    PRIMARY KEY,
    user_id      BIGINT       NOT NULL,
    title        VARCHAR(200) NOT NULL,
    description  TEXT         NULL,
    status       VARCHAR(16)  NOT NULL DEFAULT 'new',
    priority     VARCHAR(16)  NOT NULL DEFAULT 'medium',
    due_date     DATE         NULL,
    completed_at TIMESTAMPTZ  NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_tasks_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT ck_tasks_title_not_empty
        CHECK (length(btrim(title)) > 0),
    CONSTRAINT ck_tasks_status
        CHECK (status IN ('new', 'in_progress', 'done', 'cancelled')),
    CONSTRAINT ck_tasks_priority
        CHECK (priority IN ('low', 'medium', 'high'))
);
```

Списки допустимых значений заданы в БД, поэтому приложение не сможет записать
`status = 'сделано'` даже при ошибке в коде.

![[images/db03-s9-tasks.png]]
*Задачи: статусы и приоритеты ограничены списками значений*

# 11. Шаг 10. Согласованность status и completed_at (62–66 мин)

```sql
ALTER TABLE tasks
    ADD CONSTRAINT ck_tasks_completed_at
    CHECK ((status = 'done'  AND completed_at IS NOT NULL)
        OR (status <> 'done' AND completed_at IS NULL));
```

Ограничение требует строгой согласованности двух полей:

| `status` | `completed_at` | Результат |
|---|---|---|
| `done` | задан | проходит |
| `done` | `NULL` | нарушение CHECK |
| не `done` | задан | нарушение CHECK |
| не `done` | `NULL` | проходит |

Следствие: нельзя выполнить `UPDATE tasks SET status='done'` отдельно от
`UPDATE tasks SET completed_at=NOW()` — первый запрос упадёт. Оба значения
меняются в одной транзакции. Подробнее — на странице
[09-CRUD-задач](09-CRUD-задач).

![[images/db03-s10-completed-check.png]]
*Ограничение добавлено отдельным `ALTER TABLE`*

# 12. Шаг 11. Попытка выполнить задачу без даты (66 мин)

```sql
INSERT INTO tasks (user_id, title, status)
SELECT id, 'Сдать лабораторную', 'done'
FROM users WHERE email = 'teacher@college.ru';
```

![[images/db03-s11-completed-error.png]]
*Отказ: `violates check constraint "ck_tasks_completed_at"`*

# 13. Шаг 12. Корректная выполненная задача (67 мин)

```sql
INSERT INTO tasks (user_id, title, status, completed_at)
SELECT id, 'Сдать лабораторную', 'done', NOW()
FROM users WHERE email = 'teacher@college.ru';
SELECT id, title, status, completed_at FROM tasks;
```

![[images/db03-s12-tasks-row.png]]
*Задача со статусом `done` сохранилась вместе с датой выполнения*

# 14. Шаг 13. Категория задачи (68–70 мин)

```sql
ALTER TABLE tasks ADD COLUMN category_id BIGINT NULL;
```

Колонка добавляется отдельным `ALTER`: так порядок создания таблиц остаётся
`users -> categories -> tasks` без циклических зависимостей.

![[images/db03-s13-category-column.png]]
*Колонка `category_id` появилась в `tasks`*

# 15. Шаг 14. Связь с категорией (70–72 мин)

```sql
ALTER TABLE tasks
    ADD CONSTRAINT fk_tasks_category
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL;
```

Здесь `SET NULL`, а не `CASCADE`:

- удалили категорию «Учёба» — задачи, которые к ней относились, должны
  **остаться** у пользователя;
- `SET NULL` оставляет задачу живой, но без категории;
- `CASCADE` удалил бы задачи вместе с категорией, что неверно.

![[images/db03-s14-category-fk.png]]
*Внешний ключ на `category_id` с мягким удалением*

# 16. Шаг 15. Индексы (72–78 мин)

```sql
CREATE INDEX ix_tasks_user_id ON tasks (user_id);
CREATE INDEX ix_tasks_status ON tasks (status);
CREATE INDEX ix_tasks_user_status_due ON tasks (user_id, status, due_date);
CREATE INDEX ix_tasks_created_at ON tasks (created_at);
```

Составной индекс `(user_id, status, due_date)` обслуживает запрос «задачи
пользователя со статусом X с сортировкой по сроку» одним индексом вместо
двух. Лишние индексы не бесплатны: они замедляют вставку.

![[images/db03-s15-indexes.png]]
*Четыре индекса созданы*

# 17. Шаг 16. Проверка, что индексы действительно есть (78 мин)

```sql
SELECT indexname, indexdef FROM pg_indexes
WHERE tablename = 'tasks' ORDER BY indexname;
```

![[images/db03-s16-indexes-list.png]]
*Системный каталог показывает четыре индекса и индекс первичного ключа*

# 18. Шаг 17. Данные перед каскадным удалением (79–82 мин)

```sql
INSERT INTO categories (user_id, name)
SELECT id, 'Учёба' FROM users WHERE email = 'teacher@college.ru';
SELECT (SELECT count(*) FROM tasks)      AS tasks,
       (SELECT count(*) FROM categories) AS categories;
```

Ссылаемся на пользователя по `email`, а не по `id`: `id` зависит от того,
что уже вставлено в базу, и ломается при повторном запуске скрипта.

![[images/db03-s17-cascade-before.png]]
*Перед удалением: одна задача и одна категория*

# 19. Шаг 18. Каскадное удаление (82–84 мин)

```sql
DELETE FROM users WHERE email = 'teacher@college.ru';
SELECT (SELECT count(*) FROM tasks)      AS tasks,
       (SELECT count(*) FROM categories) AS categories;
```

![[images/db03-s18-cascade-after.png]]
*После удаления пользователя обе таблицы пусты — сработал `CASCADE`*

# 20. Шаг 19. Задача с категорией (85–87 мин)

```sql
INSERT INTO users (email, password_hash, full_name)
VALUES ('setnull@college.ru', '$2b$10$hashed', 'Мария Соколова');
INSERT INTO categories (user_id, name)
SELECT id, 'Учёба' FROM users WHERE email = 'setnull@college.ru';
INSERT INTO tasks (user_id, title, category_id)
SELECT u.id, 'Задача с категорией', c.id
FROM users u, categories c
WHERE u.email = 'setnull@college.ru' AND c.name = 'Учёба';
SELECT id, title, category_id FROM tasks;
```

![[images/db03-s19-setnull-before.png]]
*Задача привязана к категории «Учёба»*

# 21. Шаг 20. Удаление категории (87–88 мин)

```sql
DELETE FROM categories
WHERE name = 'Учёба'
  AND user_id = (SELECT id FROM users WHERE email = 'setnull@college.ru');
SELECT id, title, category_id FROM tasks;
```

![[images/db03-s20-setnull-after.png]]
*Задача осталась, `category_id` стал `NULL` — это и есть `SET NULL`*

# 22. Шаг 21. Уборка (88 мин)

```sql
DELETE FROM users WHERE email = 'setnull@college.ru';
```

![[images/db03-s21-cleanup.png]]
*Данные для проверки удалены, в базе снова чисто*

# Проверка

Соберите весь скрипт в `db/schema.sql` и выполните его от начала до конца:

```bash
psql -h 127.0.0.1 -U taskplanner -d taskplanner -f db/schema.sql
```

Ожидаемый результат: серии `CREATE TABLE`, `CREATE INDEX`, `COMMENT`, без
ошибок. Затем:

```sql
\d users
\d tasks
SELECT version FROM schema_version;
```

`\d tasks` покажет колонки, индексы и все ограничения, включая
`ck_tasks_completed_at`.

Отдельным скриптом `db/check_constraints.sql` докажите, что каждое
ограничение срабатывает — это разобрано на странице
[04](04-Тестовые-данные-и-проверка-ограничений).

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
| Регулярка не срабатывает на мусоре | `\s` в SQL-литерале пишется как `\s`; если пишете скрипт на JS/TS, экранируйте как `\\s` |
| Не понимаете, зачем `schema_version` | на отборе не обязательно, но на реальном проекте это удобно: видно, какая версия схемы применена |
| Ограничения проверяются только в коде приложения | это снимает баллы: ограничения должны быть в БД — см. раздел 1 `criteria.md` |

---

Дальше: [04-Тестовые-данные-и-проверка-ограничений](04-Тестовые-данные-и-проверка-ограничений)