Сессия 2. Backend: CRUD задач · 150–210 мин

# Что делаем на этой странице

Четыре операции над задачей: создать, прочитать, изменить, удалить. Каждая
должна отдавать конверт со страницы [06](06-Единый-формат-ответа-и-ошибки) и
не давать доступа к чужой задаче — иначе это будет дыра в изоляции данных
(страница [08](08-Изоляция-данных)).

Все маршруты закрыты `RequireAuthorization()`: без токена они не видны вообще.

| Метод | Путь | Что делает | Успех |
|---|---|---|---|
| `POST` | `/api/tasks` | создать задачу | `201` |
| `GET` | `/api/tasks/{id}` | прочитать одну | `200` |
| `PUT` | `/api/tasks/{id}` | изменить | `200` |
| `DELETE` | `/api/tasks/{id}` | удалить | `200` с `data: null` |

# Шаг 1. Создание задачи

Сначала код обработчика `api/TaskPlanner.Api/Program.cs`:

```csharp
app.MapPost("/api/tasks", async (
    System.Security.Claims.ClaimsPrincipal user, Data.TaskPlannerContext db,
    Contracts.TaskInput input) =>
{
    var errors = Api.Validate(input);
    if (errors.Count > 0)
        return Api.Fail(400, "Проверьте поля: " + string.Join(", ", errors), "VALIDATION_ERROR");

    var task = new Models.TaskItem
    {
        UserId = Api.CurrentUserId(user),
        Title = input.Title!.Trim(),
        Status = input.Status ?? "new",
        Priority = input.Priority ?? "medium",
        DueDate = Api.ParseDate(input.DueDate),
        // DEFAULT NOW() из БД в сущность не попадает — проставляем сами
        CreatedAt = DateTimeOffset.UtcNow,
        UpdatedAt = DateTimeOffset.UtcNow,
    };
    db.Tasks.Add(task);
    await db.SaveChangesAsync();
    return Results.Json(Api.Envelope(task.ToDto()), statusCode: 201);
}).RequireAuthorization().WithName("CreateTask").WithTags("Tasks");
```

Три момента, на которых спотыкаются чаще всего:

- `UserId` берётся из токена, а не из тела запроса — иначе можно создать
  задачу «на чужого пользователя»;
- `CreatedAt` и `UpdatedAt` заполняются в коде: значение по умолчанию из БД
  в сущность не возвращается, и в ответе будет `0001-01-01`;
- `status = 'done'` требует заполнить `completedAt` — об этом на странице
  [03](03-Скрипт-schema-sql), ограничение `ck_tasks_completed_at` не даст
  сохранить половину.

Теперь проверьте живой запрос:

```bash
curl -s -X POST http://localhost:5000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Собрать дистрибутив клиента","description":"Инструкция из README","priority":"high","dueDate":"2026-12-01"}'
```

![[images/api09-s1-create-201.png]]
*`201`: задача создана, `id` присвоен базой, `completedAt: null`*

# Шаг 2. Чтение одной задачи

```csharp
app.MapGet("/api/tasks/{id:long}", async (
    System.Security.Claims.ClaimsPrincipal user, Data.TaskPlannerContext db, long id) =>
{
    var task = await db.Tasks.FirstOrDefaultAsync(t => t.Id == id);
    if (task is null) return Api.Fail(404, "Задача не найдена", "NOT_FOUND");
    if (task.UserId != Api.CurrentUserId(user))
        return Api.Fail(403, "Нет доступа к чужой задаче", "FORBIDDEN");
    return Api.Ok(task.ToDto());
}).RequireAuthorization().WithName("GetTask").WithTags("Tasks");
```

Проверка владельца стоит **после** проверки существования: так клиент получает
`404` для несуществующей задачи и `403` для чужой — два разных случая, которые
проверяющий различает.

```bash
curl -s http://localhost:5000/api/tasks/$ID -H "Authorization: Bearer $TOKEN"
```

![[images/api09-s8-code-read.png]]
*Обработчик чтения: две проверки подряд — сначала существование, потом владелец*

![[images/api09-s2-read-200.png]]
*`200`: та же задача, что создали на прошлом шаге*

# Шаг 3. Изменение задачи

```csharp
task.Title = input.Title!.Trim();
task.Description = input.Description;
task.Status = input.Status ?? task.Status;
task.Priority = input.Priority ?? task.Priority;
task.DueDate = Api.ParseDate(input.DueDate);
task.CompletedAt = task.Status == "done" ? task.CompletedAt ?? DateTimeOffset.UtcNow : null;
task.UpdatedAt = DateTimeOffset.UtcNow;
```

`?? task.Status` означает «если поле не прислали — оставь как было». Иначе
клиент, который отправляет только название, случайно сбросит статус.

Одна строка требует внимания: при переводе в `done` дата выполнения
проставляется только если её ещё нет, а при уходе из `done` — обнуляется.
Иначе ограничение базы отклонит запрос.

```bash
curl -s -X PUT http://localhost:5000/api/tasks/$ID \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Собрать дистрибутив клиента","priority":"low","status":"in_progress","dueDate":"2026-11-15"}'
```

![[images/api09-s9-code-update.png]]
*Обработчик изменения: те же проверки, затем присваивание полей*

![[images/api09-s3-update-200.png]]
*`200`: `priority` стала `low`, статус — `in_progress`, `dueDate` сдвинулся*

# Шаг 4. Что реально изменилось

Прочитайте задачу ещё раз и сравните с прошлым шагом:

```bash
curl -s http://localhost:5000/api/tasks/$ID -H "Authorization: Bearer $TOKEN"
```

![[images/api09-s4-read-after-update.png]]
*`updatedAt` новее `createdAt`, остальные поля соответствуют запросу*

# Шаг 5. Удаление

```csharp
app.MapDelete("/api/tasks/{id:long}", async (
    System.Security.Claims.ClaimsPrincipal user, Data.TaskPlannerContext db, long id) =>
{
    var task = await db.Tasks.FirstOrDefaultAsync(t => t.Id == id);
    if (task is null) return Api.Fail(404, "Задача не найдена", "NOT_FOUND");
    if (task.UserId != Api.CurrentUserId(user))
        return Api.Fail(403, "Нет доступа к чужой задаче", "FORBIDDEN");

    db.Tasks.Remove(task);
    await db.SaveChangesAsync();
    return Api.Ok<object?>(null);
}).RequireAuthorization().WithName("DeleteTask").WithTags("Tasks");
```

Успех отдаётся как `200` с `data: null`, а не `204 No Content`. Причина
практическая: клиенту нужен разобранный JSON. Если отдавать `204`, придётся
оборачивать вызов в проверку статуса в каждом из трёх клиентов.

```bash
curl -s -X DELETE http://localhost:5000/api/tasks/$ID \
  -H "Authorization: Bearer $TOKEN"
```

![[images/api09-s10-code-delete.png]]
*Обработчик удаления заканчивается `Ok<object?>(null)` — конверт остаётся единым*

![[images/api09-s5-delete.png]]
*`200` с `data: null` — тот же конверт, что и у остальных методов*

# Шаг 6. Удалённой задачи больше нет

```bash
curl -s http://localhost:5000/api/tasks/$ID -H "Authorization: Bearer $TOKEN"
```

![[images/api09-s6-read-deleted-404.png]]
*`404` и `NOT_FOUND`: удаление завершилось, строка исчезла из базы*

# Шаг 7. Один обработчик — один результат

Сравните четыре обработчика: в каждом одинаковые строки проверки. Это не
копипаст ради копипаста: если забыть проверку владения в одном методе, дыра
появится именно там.

```csharp
var task = await db.Tasks.FirstOrDefaultAsync(t => t.Id == id);
if (task is null) return Api.Fail(404, "Задача не найдена", "NOT_FOUND");
if (task.UserId != Api.CurrentUserId(user))
    return Api.Fail(403, "Нет доступа к чужой задаче", "FORBIDDEN");
```

![[images/api09-s7-code-create.png]]
*Создание: `Validate`, заполнение полей из токена и входа, `201`*

# Шаг 8. Клиентский слой

Все вызовы идут через одну функцию — она разбирает конверт и превращает
ошибку в исключение с кодом:

```javascript
async function request(method, path, body) {
  const token = getToken();
  let response;
  try {
    response = await fetch(path, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    // Офлайн или API не поднят: сообщение пользователю, а не браузерное
    throw new Error('Нет связи с сервером. Проверьте подключение.');
  }
  // ...
  if (!response.ok || !payload?.success) {
    const error = new Error(payload?.message ?? `Ошибка ${response.status}`);
    error.code = payload?.error_code ?? String(response.status);
    throw error;
  }
  return payload.data;
}
```

![[images/api09-s11-client-request.png]]
*Одна функция на все методы: токен, конверт, код ошибки*

# Шаг 9. Четыре метода клиента

```javascript
createTask: (body) => request('POST', '/api/tasks', body),
updateTask: (id, body) => request('PUT', `/api/tasks/${id}`, body),
deleteTask: (id) => request('DELETE', `/api/tasks/${id}`),
toggleDone: (id, done) => request('PATCH', `/api/tasks/${id}/complete`, { done }),
```

![[images/api09-s12-client-crud.png]]
*Объект `api` — весь контракт клиента в одном месте*

# Проверка

Пройдите таблицу ещё раз, теперь со своими данными:

| Проверка | Ожидание |
|---|---|
| `POST /api/tasks` без токена | `401`, `UNAUTHORIZED` |
| `POST` с `title: ""` | `400`, `VALIDATION_ERROR` |
| `POST` с `title: "Ок"` | `201`, в `data` — `id` и `createdAt` |
| `PUT` с другим названием | `200`, `updatedAt` новее `createdAt` |
| `PUT` чужой задачи | `403`, `FORBIDDEN` |
| `DELETE` | `200`, `data: null` |
| `GET` удалённой задачи | `404`, `NOT_FOUND` |

# Коммит

```bash
git add src
git commit -m "Backend: CRUD задач с проверкой владельца на каждом маршруте"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| `500` на `DELETE` | забыли `SaveChangesAsync()` или возвращаете объект, который EF не смог сохранить |
| `400` при создании выполненной задачи | при `status = "done"` не проставлен `completedAt` либо наоборот |
| `title` в базе обрезан молча | в схеме `VARCHAR(200)`, а проверка длины живёт в `Validate` |
| `PUT` сбрасывает статус | в коде `input.Status ?? task.Status`, а не `input.Status` |
| `updatedAt` не меняется | забыли присвоить `UpdatedAt = DateTimeOffset.UtcNow` перед `SaveChangesAsync` |
| `404` вместо `403` на чужой задаче | вы сравниваете владельца только через `FirstOrDefaultAsync(t => t.Id == id && t.UserId == userId)` — тогда клиент не может отличить «нет» от «нельзя» |
| Клиент показывает `[object Object]` | наружу отдавайте `payload.data`, а не весь конверт |

# Что должно быть в репозитории к концу сессии 2

- [ ] `POST /api/tasks` с `201` и проверкой полей
- [ ] `GET`, `PUT`, `DELETE /api/tasks/{id}` с проверкой владельца
- [ ] `DELETE` отдаёт `200` с `data: null`
- [ ] Общая функция запроса в клиенте, разбирающая конверт

---

Дальше: [10-Отметка-выполнения-и-сводка](10-Отметка-выполнения-и-сводка)