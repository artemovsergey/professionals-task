Сессия 9. Документирование: README, OpenAPI, Postman · 0–90 мин

По критериям чемпионата документация — не формальность: без инструкции по
запуску проверить работу невозможно, и баллы за работоспособность снимаются.
На региональном этапе 2026 это отдельный раздел на 7,9 %.

# 1. README (0–40 мин)

`README.md` в корне репозитория:

````markdown
# Планировщик личных задач

Отборочное задание на чемпионат «Профессионалы», компетенция
«Программные решения для бизнеса».

Единая база данных и **один REST API** на четыре клиента: web, desktop,
mobile и (в перспективе) PWA.

## Стек

| Часть | Технология | Версия |
|---|---|---|
| База данных | PostgreSQL | 15+ |
| Backend | ASP.NET Core Web API + EF Core | .NET 9 |
| Web | React + TypeScript + Vite | React 19, Node 22 |
| Desktop | Avalonia (MVVM) | Avalonia 11 |
| Mobile | React Native (Expo) | 0.81+ |

## Что нужно установить

| Инструмент | Версия |
|---|---|
| Git | 2.40+ |
| .NET SDK | 9.0 |
| Node.js | 20 LTS+ |
| PostgreSQL | 15+ |
| DBeaver | 24+ |
| Postman | 10+ |

## Порядок запуска

Запускать в четырёх терминалах. База должна быть поднята первой.

### 1. База данных

```bash
createdb -h 127.0.0.1 -U taskplanner taskplanner
psql -h 127.0.0.1 -U taskplanner -d taskplanner -f db/schema.sql
psql -h 127.0.0.1 -U taskplanner -d taskplanner -f db/seed.sql
```

На РедОС 8.0, если сервера ещё нет:

```bash
sudo dnf install -y postgresql-server
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
sudo -u postgres psql -c "CREATE ROLE taskplanner LOGIN PASSWORD 'taskplanner' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE taskplanner OWNER taskplanner;"
```

### 2. Backend (порт 5000)

```bash
cd src/api/TaskPlanner.Api
dotnet restore
dotnet ef database update          # применить миграции вместо schema.sql
dotnet run
```

Swagger: <http://localhost:5000/swagger>
Проверка живости:

```bash
curl http://localhost:5000/health
```

### 3. Web-клиент (порт 5173)

```bash
cd src/web
npm install
npm run dev
```

Открыть <http://localhost:5173>. Прокси настроен в `vite.config.ts`:
запросы на `/api` пересылаются на `http://localhost:5000`.

### 4. Desktop-клиент

```bash
cd src/desktop/TaskPlanner.Desktop
dotnet run
```

Собранный исполняемый файл (если хотите приложение, а не `dotnet run`):

```bash
dotnet publish -c Release -r linux-x64 --self-contained false
./bin/Release/net9.0/linux-x64/publish/TaskPlanner.Desktop
```

### 5. Mobile-клиент

```bash
cd src/mobile
npm install
npx expo start
```

- **Android-эмулятор:** адрес API `http://10.0.2.2:5000` (в `.env`)
- **Реальный телефон:** укажите в `.env` IP компьютера в локальной сети:
  `EXPO_PUBLIC_API_URL=http://192.168.1.100:5000`

## Переменные окружения

Файл `.env` **не** в репозитории. Образец — `.env.example`:

| Переменная | Где используется | Пример |
|---|---|---|
| `ConnectionStrings__DefaultConnection` | `TaskPlanner.Api` | `Host=127.0.0.1;Port=5432;Database=taskplanner;Username=taskplanner;Password=taskplanner` |
| `Jwt__Key` | `TaskPlanner.Api` | 32+ символов, `openssl rand -base64 48` |
| `Jwt__Issuer` / `Jwt__Audience` | `TaskPlanner.Api` | `taskplanner-api` / `taskplanner-clients` |
| `Cors__AllowedOrigins` | `TaskPlanner.Api` | `http://localhost:5173` |
| `VITE_API_BASE_URL` | `src/web/.env.local` | `/api` |
| `EXPO_PUBLIC_API_URL` | `src/mobile/.env` | `http://10.0.2.2:5000` |

## Структура репозитория

```
.
├── api/openapi.yaml              спецификация API
├── db/
│   ├── schema.sql                DDL: таблицы, ограничения, индексы
│   ├── check_constraints.sql     проверка, что ограничения срабатывают
│   ├── seed.sql                  тестовые данные
│   └── erd/erd.md                ER-диаграмма (mermaid)
├── docs/
│   ├── testcases/testcases.md    10 тест-кейсов
│   ├── uml/                      use case, activity, IDEF0
│   └── screenshots/              скриншоты клиентов
├── postman/Professionals-Task.postman_collection.json
└── src/
    ├── TaskPlanner.sln
    ├── api/                      Core, Api, Tests
    ├── web/                      React
    ├── desktop/TaskPlanner.Desktop/   Avalonia
    └── mobile/                   React Native
```

## Тесты

```bash
cd src
dotnet test                       # юнит- и интеграционные тесты API
```

## API

Спецификация: [`api/openapi.yaml`](api/openapi.yaml) — импортируется в Swagger UI
и Postman.

Коллекция Postman: [`postman/Professionals-Task.postman_collection.json`](postman/Professionals-Task.postman_collection.json).
Импортируйте через Postman → Import → выберите файл. Переменные коллекции:
`baseUrl`, `email`, `password`, `token`, `taskId`.

Быстрая проверка вручную:

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"student@college.ru","password":"Passw0rd123"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['token'])")

curl -s http://localhost:5000/api/tasks -H "Authorization: Bearer $TOKEN"
```

## Формат ответа

```json
{ "success": true, "data": { }, "message": "OK", "error_code": null }
```

Коды ошибок: `VALIDATION_ERROR`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`,
`EMAIL_TAKEN`, `INTERNAL_ERROR`.

## Скриншоты

| Клиент | Экраны |
|---|---|
| Web | [вход](docs/screenshots/web-login.png), [список](docs/screenshots/web-tasks.png), [сводка](docs/screenshots/web-summary.png) |
| Desktop | [список](docs/screenshots/desktop-tasks.png), [сводка](docs/screenshots/desktop-summary.png) |
| Mobile | [вход](docs/screenshots/mobile-login.png), [список](docs/screenshots/mobile-tasks.png), [форма](docs/screenshots/mobile-task-form.png) |
````

> **Замечание:** в README пишите команды, которые **реально выполнили**. Если
> на РедОС `dotnet ef database update` не работает, а помогает `psql -f
> db/schema.sql` — так и напишите. Проверяющий повторит инструкцию буквально,
> и расхождение смутит сильнее, чем честная пометка об альтернативе.

Проверка ссылки на команды: скопируйте каждую команду из README в
терминал на чистой машине и убедитесь, что она отрабатывает.

# 2. Приведение `api/openapi.yaml` в порядок (40–55 мин)

Спецификация из исходного репозитория уже описывает все 9 методов. Проверьте,
что реализация совпадает с ней:

| Метод | Путь | Коды |
|---|---|---|
| POST | `/api/auth/register` | 201, 400, 409, 500 |
| POST | `/api/auth/login` | 200, 400, 401, 500 |
| GET | `/api/tasks` | 200, 400, 401, 500 |
| POST | `/api/tasks` | 201, 400, 401, 500 |
| GET | `/api/tasks/{id}` | 200, 401, 403, 404, 500 |
| PUT | `/api/tasks/{id}` | 200, 400, 401, 403, 404, 500 |
| DELETE | `/api/tasks/{id}` | 204, 401, 403, 404, 500 |
| PATCH | `/api/tasks/{id}/complete` | 200, 401, 403, 404, 500 |
| GET | `/api/tasks/summary` | 200, 401, 500 |

Если ваша реализация отличается (например, `DELETE` возвращает `200` с
обёрткой вместо `204`) — приведите **реализацию** к спецификации, а не
наоборот. Расхождение контракта с кодом — это дефект.

Скопируйте спецификацию в `docs/api/`:

```bash
mkdir -p docs/api
cp api/openapi.yaml docs/api/openapi.yaml
```

Добавьте примеры ответов, которых не хватает. Для `GET /api/tasks` в
`components/schemas` должен быть `PagedTasks`:

```yaml
    PagedTasks:
      type: object
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Task'
        total:
          type: integer
          example: 50
        page:
          type: integer
          example: 1
        pageSize:
          type: integer
          example: 20
        totalPages:
          type: integer
          example: 3
```

Проверка спецификации:

```bash
# спецификация должна быть валидным YAML и OpenAPI 3.0
python3 -c "
import yaml, sys
spec = yaml.safe_load(open('api/openapi.yaml', encoding='utf-8'))
print('openapi:', spec['openapi'])
print('путей:', len(spec['paths']))
print('схем:', len(spec['components']['schemas']))
"
```

> **Замечание:** `totalPages` нет в контракте из исходного репозитория, но его
> возвращает ваш `PagedResult<T>`. Добавьте его в спецификацию — документация
> должна описывать фактический ответ, иначе она врёт.

# 3. Коллекция Postman (55–90 мин)

Коллекция из исходного репозитория уже есть в
`postman/Professionals-Task.postman_collection.json`. Доработайте её:

**Переменные коллекции** (Postman → Environments → создать `TaskPlanner local`):

| Переменная | Значение |
|---|---|
| `baseUrl` | `http://localhost:5000` |
| `email` | `student@college.ru` |
| `password` | `Passw0rd123` |
| `token` | пусто, заполняется скриптом входа |
| `taskId` | пусто, заполняется скриптом создания |

**Структура папок** — как в критериях регионального этапа («запросы
сгруппированы по папкам, понятные имена, у каждого запроса есть описание»):

```
Планировщик задач
├── Auth
│   ├── Регистрация
│   └── Вход
├── Tasks
│   ├── Список задач (с фильтрами)
│   ├── Создать задачу
│   ├── Получить задачу
│   ├── Изменить задачу
│   ├── Удалить задачу
│   └── Отметить выполненной
└── Summary
    └── Сводка
```

**Скрипт входа** — вкладка `Scripts` → `Post-response` у запроса «Вход»:

```javascript
// Токен и id задачи достаются из ответа и подставляются в следующие запросы
const json = pm.response.json();

pm.test('Вход успешен', function () {
  pm.response.to.have.status(200);
  pm.expect(json.success).to.be.true;
  pm.expect(json.data.token).to.be.a('string').and.not.empty;
  pm.expect(json.data.user.email).to.eql(pm.environment.get('email'));
});

pm.environment.set('token', json.data.token);
```

**Скрипт создания задачи** — `Post-response`:

```javascript
const json = pm.response.json();

pm.test('Задача создана', function () {
  pm.response.to.have.status(201);
  pm.expect(json.success).to.be.true;
  pm.expect(json.data.id).to.be.a('number');
  pm.expect(json.data.title).to.be.a('string');
  pm.expect(json.data.userId).to.be.a('number');
});

pm.environment.set('taskId', json.data.id);
```

**Тесты на списке задач** — `Post-response`:

```javascript
const json = pm.response.json();

pm.test('Список задач вернул структуру', function () {
  pm.response.to.have.status(200);
  pm.expect(json.success).to.be.true;

  pm.expect(json.data.items).to.be.an('array');
  pm.expect(json.data.total).to.be.a('number');
  pm.expect(json.data.page).to.be.a('number');
  pm.expect(json.data.pageSize).to.be.a('number');
});

pm.test('Задачи принадлежат текущему пользователю', function () {
  json.data.items.forEach((task) => {
    pm.expect(task.userId).to.eql(1);
  });
});

pm.test('total не меньше числа выданных записей', function () {
  pm.expect(json.data.total).to.be.at.least(json.data.items.length);
});
```

**Тест на изоляцию данных** — отдельный запрос, проверяющий `404` на чужую
задачу:

```javascript
pm.test('Чужая задача недоступна', function () {
  pm.response.to.have.status(404);
  pm.expect(pm.response.json().error_code).to.eql('NOT_FOUND');
});
```

**Тест на изоляцию по токену** — запрос без заголовка `Authorization`:

```javascript
pm.test('Без токена возвращается 401', function () {
  pm.response.to.have.status(401);
  pm.expect(pm.response.json().error_code).to.eql('UNAUTHORIZED');
});
```

Добавьте `Authorization` **уровнем коллекции** (вкладка `Authorization` →
`Type: Bearer` → `{{token}}`), чтобы не вписывать заголовок в каждый запрос.
Отключите его для `register` и `login`.

Экспортируйте коллекцию: Postman → … → `Export` → v2.1 → сохраните в
`postman/Professionals-Task.postman_collection.json`.

**Прогон коллекции.** Postman → `Runner` → выберите коллекцию и окружение →
`Run`. Все тесты должны стать зелёными. Скриншот прогона с количеством
пройденных тестов приложите в `docs/screenshots/postman-run.png`.

# Проверка

1. Откройте `README.md` на GitHub — все ссылки на файлы не битые
   (GitHub подсвечивает несуществующие пути).
2. С нуля пройдите раздел «Порядок запуска»: база → API → web → desktop → mobile.
3. `python3` проверка `api/openapi.yaml` отрабатывает и печатает число путей
   (должно быть 9).
4. Импортируйте коллекцию в Postman, запустите `Runner` — все тесты зелёные.
5. Проверьте, что в коллекции нет захардкоженного токена: значение `token`
   хранится в окружении, а не в самой коллекции.
6. `git grep -n "eyJhbGciOi" -- . ':!*.json'` — пусто, токенов в репозитории нет.

# Коммит

```bash
git add README.md .env.example api docs postman docs/screenshots
git commit -m "Документирование: README, OpenAPI, коллекция Postman с тестами"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| Postman отдаёт `401` на все запросы | не настроен `Authorization` уровнем коллекции или не заполнена переменная `token` |
| `pm.expect` не сработал | скрипт в вкладке `Tests`, а не `Pre-request` |
| Переменная `token` не сохраняется | используйте `pm.environment.set`, не `pm.globals.set` |
| YAML не парсится | проверьте отступы; в OpenAPI критичны пробелы |
| Спецификация не подхватывается Swagger UI | в `AddSwaggerGen` проверьте `IncludeXmlComments`; сама YAML-файл читается автоматически |
| README-команды не работают на РедОС | перепишите инструкцию под фактический сценарий, а не под желаемый |
| Секреты попали в историю git | отфильтруйте: `git filter-repo --path .env --invert-paths` |

## Иллюстрации

![[images/test24-readme.png]]
*README проекта в VS Code — его и читает преподаватель*
