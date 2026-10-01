Сессия 4. Backend: CRUD задач · 0–55 мин

# 1. Валидатор входных данных (0–10 мин)

`src/api/TaskPlanner.Core/Validators/TaskValidators.cs`:

```csharp
using FluentValidation;
using TaskPlanner.Core.Dtos;

namespace TaskPlanner.Core.Validators;

public class TaskInputValidator : AbstractValidator<TaskInput>
{
    public TaskInputValidator()
    {
        RuleFor(x => x.Title)
            .NotEmpty().WithMessage("Название задачи обязательно")
            .MaximumLength(200).WithMessage("Название не длиннее 200 символов")
            .Must(title => !string.IsNullOrWhiteSpace(title))
            .WithMessage("Название не может состоять из пробелов");

        RuleFor(x => x.Description)
            .MaximumLength(5000).WithMessage("Описание не длиннее 5000 символов")
            .When(x => x.Description is not null);

        RuleFor(x => x.DueDate)
            .Must(dueDate => dueDate is null || dueDate.Value >= new DateOnly(2000, 1, 1))
            .WithMessage("Срок не может быть раньше 2000 года");
    }
}
```

> **Замечание:** ограничение длины `title` в 200 символов дублирует `VARCHAR(200)`
> в базе. Это нормально: код даёт понятное сообщение пользователю, база —
> гарантию. Проверка только в коде не считается ограничением, только в базе —
> не защищает от прямых вставок.

# 2. Изменение и удаление в сервисе (10–30 мин)

Добавьте в `src/api/TaskPlanner.Api/Services/ITaskService.cs` два метода:

```csharp
Task<TaskDto> UpdateAsync(long userId, long id, TaskInput input, CancellationToken cancellationToken);

Task DeleteAsync(long userId, long id, CancellationToken cancellationToken);
```

И в `TaskService` — `partial`-часть с методами изменения:

`src/api/TaskPlanner.Api/Services/TaskService.Update.cs`:

```csharp
using Microsoft.EntityFrameworkCore;
using TaskPlanner.Api.Data;
using TaskPlanner.Api.Mappers;
using TaskPlanner.Core.Dtos;
using TaskPlanner.Core.Entities;
using TaskPlanner.Core.Enums;
using TaskPlanner.Core.Exceptions;

namespace TaskPlanner.Api.Services;

public partial class TaskService
{
    public async Task<TaskDto> UpdateAsync(
        long userId,
        long id,
        TaskInput input,
        CancellationToken cancellationToken)
    {
        var task = await db.Tasks
            .FirstOrDefaultAsync(x => x.Id == id && x.UserId == userId, cancellationToken);

        if (task is null)
        {
            throw ApiException.NotFound("Задача не найдена");
        }

        var now = DateTimeOffset.UtcNow;

        task.Title = input.Title.Trim();
        task.Description = string.IsNullOrWhiteSpace(input.Description)
            ? null
            : input.Description.Trim();
        task.Priority = input.Priority;
        task.DueDate = input.DueDate;
        task.CategoryId = input.CategoryId;

        // completed_at и status меняем в одном объекте и сохраняем один раз.
        // CHECK ck_tasks_completed_at не допускает промежуточного состояния,
        // в котором статус и дата расходятся.
        if (input.Status != task.Status)
        {
            task.Status = input.Status;
            task.CompletedAt = input.Status == TaskStatus.Done ? now : null;
        }

        task.UpdatedAt = now;

        await db.SaveChangesAsync(cancellationToken);

        logger.LogInformation(
            "Пользователь {UserId} изменил задачу {TaskId}", userId, id);

        return task.ToDto();
    }

    public async Task DeleteAsync(
        long userId,
        long id,
        CancellationToken cancellationToken)
    {
        var task = await db.Tasks
            .FirstOrDefaultAsync(x => x.Id == id && x.UserId == userId, cancellationToken);

        if (task is null)
        {
            throw ApiException.NotFound("Задача не найдена");
        }

        db.Tasks.Remove(task);
        await db.SaveChangesAsync(cancellationToken);

        logger.LogInformation(
            "Пользователь {UserId} удалил задачу {TaskId}", userId, id);
    }
}
```

> **Замечание:** файл называется `TaskService.Update.cs`, а класс объявлен как
> `public partial class TaskService`. Такой приём дробит длинный класс на
> части по операциям. Если предпочитаете один файл — просто допишите методы
> в `TaskService.cs`, объявив класс как `partial` и в том, и в другом месте.

# 3. Контроллер: полный CRUD (30–45 мин)

Замените `src/api/TaskPlanner.Api/Controllers/TasksController.cs`:

```csharp
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Swashbuckle.AspNetCore.Annotations;
using TaskPlanner.Api.Infrastructure;
using TaskPlanner.Api.Services;
using TaskPlanner.Core.Common;
using TaskPlanner.Core.Dtos;

namespace TaskPlanner.Api.Controllers;

[ApiController]
[Route("api/tasks")]
[Authorize]
public class TasksController(ITaskService taskService, ICurrentUser currentUser) : ControllerBase
{
    /// <summary>Список задач текущего пользователя.</summary>
    [HttpGet]
    [ProducesResponseType(typeof(ApiResponse<IReadOnlyList<TaskDto>>), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetAll(CancellationToken cancellationToken)
    {
        var tasks = await taskService.GetAllAsync(currentUser.GetUserId(), cancellationToken);

        return Ok(ApiResponse<IReadOnlyList<TaskDto>>.Ok(tasks));
    }

    /// <summary>Получить задачу по идентификатору.</summary>
    [HttpGet("{id:long}")]
    [ProducesResponseType(typeof(ApiResponse<TaskDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ApiResponse<object?>), StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetById(long id, CancellationToken cancellationToken)
    {
        var task = await taskService.GetByIdAsync(currentUser.GetUserId(), id, cancellationToken);

        return Ok(ApiResponse<TaskDto>.Ok(task));
    }

    /// <summary>Создать задачу.</summary>
    [HttpPost]
    [ProducesResponseType(typeof(ApiResponse<TaskDto>), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ApiResponse<object?>), StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Create(
        [FromBody] TaskInput input,
        CancellationToken cancellationToken)
    {
        var task = await taskService.CreateAsync(
            currentUser.GetUserId(), input, cancellationToken);

        return Created($"/api/tasks/{task.Id}", ApiResponse<TaskDto>.Ok(task, "Задача создана"));
    }

    /// <summary>Изменить задачу.</summary>
    [HttpPut("{id:long}")]
    [ProducesResponseType(typeof(ApiResponse<TaskDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ApiResponse<object?>), StatusCodes.Status400BadRequest)]
    [ProducesResponseType(typeof(ApiResponse<object?>), StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Update(
        long id,
        [FromBody] TaskInput input,
        CancellationToken cancellationToken)
    {
        var task = await taskService.UpdateAsync(
            currentUser.GetUserId(), id, input, cancellationToken);

        return Ok(ApiResponse<TaskDto>.Ok(task, "Задача обновлена"));
    }

    /// <summary>Удалить задачу.</summary>
    [HttpDelete("{id:long}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(typeof(ApiResponse<object?>), StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Delete(long id, CancellationToken cancellationToken)
    {
        await taskService.DeleteAsync(currentUser.GetUserId(), id, cancellationToken);

        // 204 = No Content: тела ответа нет вообще.
        return NoContent();
    }
}
```

# 4. Статус ответа при удалении (45–50 мин)

По контракту `DELETE` возвращает **204 без тела**. Обёртка ответа при этом
не используется — отправлять `{"success":true,...}` вместе с `204` нельзя:
`204` по стандарту HTTP не допускает тела, клиенты и прокси его вырежут.

| Код | Когда | Тело |
|---|---|---|
| `204` | удаление прошло | нет |
| `404` | задачи нет или она чужая | обёртка с `error_code: NOT_FOUND` |
| `401` | нет токена | обёртка с `error_code: UNAUTHORIZED` |

# 5. Клиентский `fetch` (50–55 мин)

Пригодится всем клиентам. `src/web/src/api/client.ts` создайте позже, а пока
проверьте API так:

```bash
API=http://localhost:5000

TOKEN=$(curl -s -X POST $API/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"student@college.ru","password":"Passw0rd123"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['token'])")

# создать
NEW=$(curl -s -X POST $API/api/tasks -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Проверка CRUD","description":"из curl","priority":"high","dueDate":"2026-12-31"}')
echo "$NEW"
ID=$(echo "$NEW" | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])")
echo "id=$ID"

# прочитать
curl -s $API/api/tasks/$ID -H "Authorization: Bearer $TOKEN"

# изменить
curl -s -X PUT $API/api/tasks/$ID -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Проверка CRUD (изменено)","priority":"low"}'

# отметить выполненной
curl -s -X PATCH $API/api/tasks/$ID/complete -H "Authorization: Bearer $TOKEN"

# удалить
curl -s -i -X DELETE $API/api/tasks/$ID -H "Authorization: Bearer $TOKEN" | head -1
# HTTP/1.1 204 No Content
```

# Проверка

```bash
cd src && dotnet build
```

Полный CRUD через Swagger UI (`http://localhost:5000/swagger`):

| Шаг | Ожидание |
|---|---|
| `POST /api/tasks` без токена | `401`, `UNAUTHORIZED` |
| `POST /api/tasks` с `title: ""` | `400`, `VALIDATION_ERROR` |
| `POST /api/tasks` с `title: "Ок"` | `201`, в `data` — `id`, `createdAt`, `completedAt: null` |
| `PUT` с другим названием | `200`, `updatedAt` новее `createdAt` |
| `DELETE` | `204`, тела нет |
| `GET` удалённой задачи | `404`, `NOT_FOUND` |

Проверка изоляции: создайте задачу вторым пользователем и попробуйте
изменить её первым — тоже `404`, не `403`.

# Коммит

```bash
git add src
git commit -m "Backend: полный CRUD задач с проверкой владельца"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| `500` на `DELETE` | забыли `return NoContent();` или вернули `Ok(...)` вместе с `204` |
| `400 invalid_error про completed_at` | при `status=done` не выставлен `CompletedAt`, либо наоборот |
| `title` в БД обрезан молча | забыли `MaximumLength(200)` в валидаторе |
| `PUT` не меняет `status` | в методе условие `if (input.Status != task.Status)` — при одинаковом статусе дата не трогается, это правильно |
| Компилятор: `TaskService` уже определён | не объявили класс как `partial` в обоих файлах |
| `404` при `PUT` своей задачи | в предикате `x.UserId == userId` и `currentUser.GetUserId()` верный, проверьте токен |

---

Дальше: [10-Отметка-выполнения-и-сводка](10-Отметка-выполнения-и-сводка)
