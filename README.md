# ТОиР-Проф — система управления техническим обслуживанием

**Компетенция:** Программные решения для бизнеса
**Чемпионат:** «Профессионалы» 2027

Система учёта технического обслуживания и ремонта промышленного оборудования:
график планового ТО, заявки на ремонт, ремонтные бригады, списание материалов
и ЗИП, аналитика простоев и эффективности бригад.

> **Полное описание задания — в [wiki](https://github.com/artemovsergey/professionals-task/wiki).**

---

## Что здесь лежит

Это репозиторий **организатора**: в нём разобрано задание, расписано
по спринтам и приложены инструменты для работы. Решение участника пишется
в этот же репозиторий поверх подготовленной базы.

| Каталог | Содержимое |
|---|---|
| `wiki/` | **54 страницы по 24 спринтам** — вся инструкция |
| `tools/wiki/` | генератор страниц вики |
| `tools/capture/` | захват скриншотов и гифок |
| `tools/publish-wiki.sh` | публикация вики в GitHub Wiki |
| `db/` | пример схемы базы данных |
| `api/` | спецификация OpenAPI |
| `postman/` | коллекция запросов |
| `docs/` | диаграммы, скриншоты, чек-лист захвата, план вики |
| `src/` | API, desktop-клиент, web-клиент, тесты |

---

## С чего начать

| Шаг | Что делать | Куда смотреть |
|---|---|---|
| 1 | Прочитать задание | wiki, страница Home |
| 2 | Проверить инструменты и поднять окружение | wiki, страница 01 |
| 3 | Создать структуру проекта и базу | wiki, страницы 02, 06–11 |
| 4 | Собрать API | wiki, страницы 12–25 |
| 5 | Собрать desktop-клиент | wiki, страницы 26–35 |
| 6 | Собрать web-клиент | wiki, страницы 36–45 |
| 7 | Написать тесты и документацию | wiki, страницы 46–53 |
| 8 | Пройти итоговую проверку | wiki, страница 54 |

**Общая карта спринтов** — на [wiki → Home](https://github.com/artemovsergey/professionals-task/wiki/Home).

---

## Стек

| Часть | Технология | Версия |
|---|---|---|
| База данных | PostgreSQL | 15+ |
| Backend / API | .NET (ASP.NET Core Web API) + Entity Framework Core | **.NET 10** |
| Desktop-клиент | C# / Avalonia (нативный UI, без WebView) | Avalonia 11 |
| Web-клиент | React + TypeScript + Vite | React 19 |
| Модульные тесты | xUnit + FluentAssertions | — |
| Инструменты | DBeaver, Postman, VS Code, Draw.io, Swagger UI | — |

---

## Как запустить

### База данных

```bash
# создать базу и пользователя (один раз)
sudo -u postgres psql -c "CREATE ROLE toirprof LOGIN PASSWORD 'toirprof';"
sudo -u postgres psql -c "CREATE DATABASE toirprof OWNER toirprof;"

# применить скрипты по порядку
psql -h 127.0.0.1 -U toirprof -d toirprof -f db/schema.sql
psql -h 127.0.0.1 -U toirprof -d toirprof -f db/triggers.sql
psql -h 127.0.0.1 -U toirprof -d toirprof -f db/functions.sql
psql -h 127.0.0.1 -U toirprof -d toirprof -f db/seed.sql
```

Строка подключения:

```
Host=127.0.0.1;Port=5432;Database=toirprof;Username=toirprof;Password=toirprof
```

### API

```bash
dotnet run --project src/api
```

Открывается на `http://localhost:5080`, Swagger — на
`http://localhost:5080/swagger` (только в режиме Development).

### Desktop-клиент

```bash
dotnet run --project src/desktop
```

### Web-клиент

```bash
cd src/web
npm install
npm run dev
```

Открывается на `http://localhost:5173`, запросы к API идут через прокси Vite
по пути `/api`.

### Тесты

```bash
dotnet test src/Tests
```

---

## Учётные записи для проверки

| Роль | Логин | Пароль |
|---|---|---|
| Администратор | `admin` | `Admin123!` |
| Руководитель | `manager` | `Manager123!` |
| Мастер | `master` | `Master123!` |

---

## Формат ответа API

Единая обёртка — везде одинаковая:

```json
{ "success": true,  "data": { }, "message": "OK",                   "error_code": null }
{ "success": false, "data": null,   "message": "Заявка не найдена",  "error_code": "NOT_FOUND" }
```

HTTP-коды: 200, 201, 400, 401, 403, 404, 409, 429, 500.

---

## Инструменты организатора

### Пересобрать вики

```bash
# измените tools/wiki/sprints.py, затем:
python3 tools/wiki/gen_pages.py

# проверить без записи
python3 tools/wiki/gen_pages.py --check
```

Генератор перезаписывает `wiki/*.md`, `wiki/Home.md`, `wiki/_Sidebar.md` и
`docs/capture-checklist.md`. Правьте `tools/wiki/sprints.py`, а не готовые
страницы.

### Снять скриншоты и гифки

```bash
# один кадр
python3 tools/capture/rec.py --name 07-schema-equipment --single

# запись экрана 8 секунд
python3 tools/capture/rec.py --name 07-schema-run --seconds 8

# выполнить команду шага и снять результат
./tools/capture/run-page.sh 07-schema-run psql -f db/schema.sql

# собрать гифку из готовых кадров
python3 tools/capture/make-gifs.py кадр1.png кадр2.png -o wiki/gifs/07-run.gif
```

Что и под каким именем снимать — в `docs/capture-checklist.md`.

### Опубликовать вики

```bash
bash tools/publish-wiki.sh              # запушить в GitHub Wiki
bash tools/publish-wiki.sh --dry-run    # только показать, что изменится
```

---

## Ограничения

- **Основная ОС на площадке — РедОС 8.0.** Код обязан собираться и
  запускаться на ней: никаких Windows-путей, `cmd` и PowerShell-команд.
- **PostgreSQL ставится нативно** через `dnf` — Docker на площадке может
  отсутствовать.
- **ИИ разрешён только для текстов** документации и презентации. Запрещено
  использовать ИИ для кода, SQL, триггеров, проектирования архитектуры БД
  и тестов.

---

## Брендбук и логотипы

- <https://pro.firpo.ru/>
- <https://disk.yandex.ru/d/tj4P7D5bgHsS1Q>
- <https://disk.yandex.ru/d/5inFXmJN7YBMJg>

## Полезные ссылки

- [docs/wiki-plan.md](docs/wiki-plan.md) — правила оформления страниц вики
- [docs/capture-checklist.md](docs/capture-checklist.md) — что снимать на скриншоты
- [Agents.md](Agents.md) — инструкции проекта