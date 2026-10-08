Сессия 9. Документирование: README, OpenAPI, Postman · 0–90 мин

# Что делаем на этой странице

Три вещи, без которых проект нельзя проверить: инструкция по запуску,
спецификация API и готовая коллекция запросов. На региональном этапе 2026
документация — отдельный раздел на 7,9 %.

# Шаг 1. README: что это

`README.md` в корне репозитория читает первым — часто раньше, чем код.
В нём шесть обязательных разделов:

```markdown
# Планировщик личных задач

Единая база данных и **один REST API** на четыре клиента: web, desktop,
mobile и PWA.

## Стек
## Что нужно установить
## Порядок запуска
## Переменные окружения
## Структура репозитория
## Автотесты
```

Первый абзац отвечает на вопрос «что это» за пять секунд. Остальное —
на что эксперт будет смотреть дальше.

![[images/test24-readme.png]]
*README открыт в VS Code — это первое, что увидит проверяющий*

# Шаг 2. Стек и требования

```markdown
## Стек

| Часть | Технология | Версия |
|---|---|---|
| База данных | PostgreSQL | 15+ |
| Backend | ASP.NET Core Web API + EF Core | .NET 9 |
| Web | React + Vite | Node 20+ |
| Desktop | Avalonia (MVVM) | Avalonia 11 |
| Mobile | React Native (react-native-web) | 0.81+ |
```

Таблица, а не список. По ней сразу видно, соответствует ли стек заданию и
совпадают ли версии с инфраструктурным листом.

# Шаг 3. Порядок запуска

Запускать в четырёх терминалах, база — первой:

```markdown
### 1. База данных
psql -h 127.0.0.1 -U taskplanner -d taskplanner -f db/schema.sql
psql -h 127.0.0.1 -U taskplanner -d taskplanner -f db/seed.sql

### 2. Backend (порт 5080)
cd src/api && dotnet run --urls http://localhost:5080

### 3. Web-клиент (порт 5173)
cd src/web && npm install && npm run dev

### 4. Desktop-клиент
cd src/desktop/TaskPlanner.Desktop && dotnet run
```

Порядок неочевиден, поэтому он и написан: без базы API стартует, но первый
же запрос вернёт ошибку подключения.

# Шаг 4. Переменные окружения

Файл `.env` не в репозитории — образец `.env.example`:

```markdown
| Переменная | Где используется | Пример |
|---|---|---|
| `ConnectionStrings__Default` | `TaskPlanner.Api` | `Host=127.0.0.1;Port=5432;Database=taskplanner;…` |
| `Jwt__Key` | `TaskPlanner.Api` | 32+ символов: `openssl rand -base64 48` |
| `VITE_API_BASE_URL` | `src/web/.env.local` | `/api` |
```

Ключ JWT генерируется, а не пишется руками: захардкоженный ключ из
примера попадёт в репозиторий и в скриншоты.

# Шаг 5. Коллекция Postman

`postman/Professionals-Task.postman_collection.json` — файл коллекции,
импортируется через **Import → File**. Внутри три группы:

![[images/test24-s1-postman.png]]
*Коллекция: Auth, Tasks и Negative — 16 запросов, каждый с ожидаемым кодом*

Группа `Negative` — самая ценная. Четыре запроса проверяют отказы: `400`
без названия, `401` без токена, `404` для несуществующей задачи и `400` при
неверном приоритете. Именно их чаще всего не делают.

# Шаг 6. Токен и id подставляются сами

В коллекции три переменные: `baseUrl`, `token` и `taskId`. Токен пишет
скрипт запроса Login, а id задачи — скрипт Create task:

```javascript
// у запроса Login
const body = pm.response.json();
pm.test('Токен получен', () => pm.expect(body.data.token).to.be.a('string'));
pm.collectionVariables.set('token', body.data.token);

// у запроса Create task
pm.test('Создана 201', function () { pm.response.to.have.status(201); });
const body = pm.response.json();
pm.test('Идентификатор задан', function () {
    pm.expect(body.data.id).to.not.be.undefined;
});
pm.collectionVariables.set('taskId', body.data.id);
```

![[images/test24-s2-postman-test.png]]
*Запрос Create task хранит id в taskId — следующие запросы не нужно править руками*

Порядок выполнения: **Auth / Register → Auth / Login → Tasks → Negative**.
Первые два запроса дают токен, третий — id.

# Шаг 7. OpenAPI

Контракт лежит в `api/openapi.yaml` и используется дважды: как спецификация
для эксперта и как источник ожидаемых ответов при проверке. Если он
расходится с реальным API, это уже дефект — сверяйтесь с
[12-Логирование-и-Swagger](12-Логирование-и-Swagger).

# Проверка

```bash
# README открывается на GitHub и в нём есть порядок запуска
# коллекция импортируется без ошибок
# после Register и Login остальные запросы уходят с токеном
```

# Коммит

```bash
git add README.md postman .env.example
git commit -m "Документирование: README, коллекция Postman и образец .env"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| Коллекция не импортируется | проверьте JSON: проще всего открыть файл в редакторе JSON и убедиться, что он валиден |
| Запросы уходят без токена | не выполнен `Auth / Login` — токен пишет именно он |
| `taskId` пустой | не выполнен `Tasks / Create task` |
| В README старые порты | сверьтесь с фактическим `dotnet run --urls` и `npm run dev` |
| Эксперт не смог запустить проект | чаще всего забыт шаг с `db/seed.sql` — списка без данных недостаточно для проверки фильтров |