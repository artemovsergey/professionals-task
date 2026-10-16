# Инструкция по развёртыванию системы ТОиР-Проф

Документ описывает, как поднять систему на чистой машине под РедОС 8.0 и
как проверить, что всё поднялось. Рассчитан на 8–10 страниц при печати
в формате A4 с полями 20 мм.

---

## 1. Состав системы

Система состоит из четырёх частей:

| Часть | Технологии | Каталог | Порт |
|-------|-----------|---------|------|
| База данных | PostgreSQL 15 | `db/` | 5432 |
| REST API | .NET 10, ASP.NET Core, EF Core | `src/api/` | 5080 |
| Web-клиент руководителя | React 19, TypeScript, Vite | `src/web/` | 5173 |
| Desktop-клиент мастера | Avalonia 12 | `src/desktop/` | — |

Схему базы создают четыре SQL-файла из каталога `db/`. Миграций EF Core в
проекте нет намеренно: требования к базе заданы скриптами, и на площадке
их можно проверить и откатить без пересборки приложения.

```
db/schema.sql      таблицы, типы, ограничения, индексы
db/functions.sql   функции расчёта простоя и следующей даты, процедура отчёта
db/triggers.sql    триггеры: охрана статуса, проверка дат, журнал аудита
db/seed.sql        тестовые данные
db/verify.sql      самопроверка ограничений и функций
```

Порядок применения именно такой: функции нужны триггерам, триггеры —
сиду.

---

## 2. Требования к машине

| Компонент | Требование |
|-----------|-----------|
| ОС | РедОС 8.0 |
| CPU / память | 2 ядра, 4 ГБ |
| Место на диске | 8 ГБ |
| PostgreSQL | 15 или новее, установлен нативно через `dnf` |

Docker на площадке может быть недоступен, поэтому база ставится нативно.
Node.js и .NET SDK берутся из инфраструктурного листа площадки.

Проверить, что всё нужное уже есть:

```bash
dotnet --version
node --version
psql --version
```

Если какой-то из ответов пустой, инструмент не установлен — переходите к
разделу 3.

---

## 3. Установка инструментов

```bash
# PostgreSQL
sudo dnf install -y postgresql-server postgresql-contrib

# .NET SDK 10 и Node.js 22 ставится из инфраструктурного листа площадки
```

Инициализация кластера и запуск службы:

```bash
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
```

---

## 4. Подготовка базы данных

Создание роли и базы. Имя пользователя и пароль совпадают с именем базы:

```bash
sudo -u postgres psql -c "CREATE ROLE toirprof WITH LOGIN PASSWORD 'toirprof';"
sudo -u postgres psql -c "CREATE DATABASE toirprof OWNER toirprof ENCODING 'UTF8';"
```

Применение скриптов по порядку:

```bash
cd db
psql -h 127.0.0.1 -U toirprof -d toirprof -f schema.sql
psql -h 127.0.0.1 -U toirprof -d toirprof -f functions.sql
psql -h 127.0.0.1 -U toirprof -d toirprof -f triggers.sql
psql -h 127.0.0.1 -U toirprof -d toirprof -f seed.sql
```

Каждый скрипт начинается с `BEGIN` и заканчивается `COMMIT`, поэтому
частично применённая схема не остаётся. Признак успеха — сообщение
`CREATE TABLE`, `CREATE FUNCTION` и итоговые строки `INSERT 0 …`.

Проверка: скрипт самопроверки печатает сводку по всем ограничениям.

```bash
psql -h 127.0.0.1 -U toirprof -d toirprof -f verify.sql
```

В конце вывода должна быть строка `ИТОГО` со всеми проверками в статусе
«пройдено», а список непрошедших проверок — пустым. Скрипт ничего не
меняет: он делает `ROLLBACK` на каждую негативную проверку.

Ожидаемый состав данных: 3 роли, 3 цеха, 3 вида ТО, 7 пользователей,
10 единиц оборудования, 3 бригады, 8 материалов, 26 записей графика и
47 заявок.

---

## 5. Настройка API

Строка подключения лежит в `src/api/appsettings.json`:

```json
"ConnectionStrings": {
  "DefaultConnection": "Host=127.0.0.1;Port=5432;Database=toirprof;Username=toirprof;Password=toirprof"
}
```

Секрет для подписи токенов задаётся переменной окружения, а не файлом:

```bash
export ToirProf__Jwt__Key="замените-на-длинный-случайный-ключ-не-короче-32-символов"
```

Ключ должен быть одинаковым у всех экземпляров API: иначе один экземпляр
выпустит токен, который другой не примет.

Сборка и запуск:

```bash
cd src
dotnet restore
dotnet build ToirProf.slnx -c Release --no-incremental
dotnet run --project api --urls http://localhost:5080
```

Swagger доступен по адресу `http://localhost:5080/swagger` только в
режиме Development. В рабочем режиме интерфейс документации
выключается намеренно.

---

## 6. Настройка web-клиента

```bash
cd src/web
npm install
npm run build          # проверка типов и сборка в dist
npm run preview        # раздача собранного клиента на порту 4173
```

Для разработки: `npm run dev` — сервер на 5173 проксирует `/api` на
`http://localhost:5080`. Адрес API можно переопределить переменной
`VITE_API_TARGET`.

Для рабочего режима статику `dist/` отдаёт Nginx:

```nginx
server {
    listen 80;
    server_name toirprof.local;

    root /opt/toirprof/web;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Поток событий дашборда нельзя буферизовать: иначе обновления
        # приходят пачками вместо событий по мере изменений.
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600s;
    }
}
```

Заголовок `X-Accel-Buffering: no` выставляет и сам API, поэтому
достаточно `proxy_buffering off`.

---

## 7. Настройка desktop-клиента

```bash
cd src/desktop
dotnet build ToirProf.Desktop.csproj -c Release --no-incremental
```

Запуск из РедОС возможен, если на машине есть графическая оболочка:

```bash
dotnet run --project src/desktop
```

Адрес API задаётся переменной окружения `TOIRPROF_API`, по умолчанию —
`http://localhost:5080`. Токен, локальный журнал и очередь офлайн-операций
клиент хранит в `%LOCALAPPDATA%/ToirProf` (в РедОС — `~/.local/share/ToirProf`).

---

## 8. Учётные записи для проверки

| Логин | Пароль | Роль | Что может |
|-------|--------|------|-----------|
| `admin` | `Admin123!` | Администратор | всё, включая справочники и пользователей |
| `manager` | `Manager123!` | Руководитель | сводка, аналитика, реестры, приход на склад |
| `master` | `Master123!` | Мастер | дашборд и работа с заявками |

---

## 9. Проверка после развёртывания

```bash
# 1. База отвечает
psql -h 127.0.0.1 -U toirprof -d toirprof -c "SELECT count(*) FROM work_orders;"

# 2. API отвечает без токена
curl -s http://localhost:5080/api/health

# 3. Вход работает и выдаёт токен
curl -s -X POST http://localhost:5080/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"master","password":"Master123!"}'

# 4. Авторизованный запрос проходит
curl -s http://localhost:5080/api/dashboard/summary -H 'Authorization: Bearer <токен>'

# 5. Поток событий отдаёт обновления
curl -N http://localhost:5080/api/dashboard/events?access_token=<токен>
```

Чек-лист готовности:

- [ ] `verify.sql` не выдал непрошедших проверок;
- [ ] `/api/health` отвечает `success: true`;
- [ ] вход мастером возвращает токен;
- [ ] дашборд открывается в браузере и показывает цифры;
- [ ] поток событий печатает `event: dashboard.updated` не реже раза в полминуты;
- [ ] списание материалов уменьшает остаток в справочнике;
- [ ] отчёт PDF скачивается по временной ссылке в пределах 15 секунд.

---

## 10. Обслуживание

**Резервная копия.** Обязательна перед каждой демонстрацией:

```bash
pg_dump -h 127.0.0.1 -U toirprof -d toirprof -Fc -f /backup/toirprof-$(date +%F).dump
```

Восстановление из копии:

```bash
sudo -u postgres dropdb toirprof
sudo -u postgres createdb toirprof -O toirprof
pg_restore -h 127.0.0.1 -U toirprof -d toirprof /backup/toirprof-2026-10-16.dump
```

**Журнал аудита.** Каждое изменение заявок и оборудования пишется в
таблицу `operation_log`. Очищать её не нужно: на демонстрации журнал
показывает, что система действительно следит за изменениями.

```bash
psql -h 127.0.0.1 -U toirprof -d toirprof \
  -c "SELECT table_name, operation, created_at FROM operation_log ORDER BY created_at DESC LIMIT 20;"
```

**Обновление приложения.** Схема базы при обновлении не меняется, поэтому
порядок такой: остановить API, обновить бинарники, запустить заново.

```bash
sudo systemctl stop toirprof-api
sudo cp -r build/toirprof-api/* /opt/toirprof/api/
sudo systemctl start toirprof-api
```

**Сброс демонстрационных данных.** Скрипт `db/seed.sql` идемпотентен по
сути: он очищает заполненные таблицы и заливает тестовый набор заново.
Запускать его на боевой базе нельзя.