using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.OpenApi;
using Swashbuckle.AspNetCore.SwaggerGen;

namespace ToirProf.Api.Swagger;

/// <summary>
/// Добавляет к каждой операции набор стандартных ответов, который требует
/// лист задания: 400, 401, 403, 404, 409, 429 и 500.
///
/// Почему фильтр, а не атрибуты на каждом методе: правило одно и то же для
/// всех 70 операций, а атрибут пришлось бы повторить столько же раз и
/// забыть где-нибудь. Здесь правило описано один раз, а Swagger получает
/// одинаковые коды у всех операций без ручного труда.
///
/// Что добавляется:
/// <list type="bullet">
///   <item>400 — тело запроса не прошло проверку; код из <c>error_code</c> — <c>VALIDATION_ERROR</c>;</item>
///   <item>401 — нет или просрочен токен; <c>INVALID_TOKEN</c>;</item>
///   <item>403 — роль не даёт права на операцию; <c>FORBIDDEN</c>;</item>
///   <item>404 — записи с таким идентификатором нет; <c>NOT_FOUND</c>;</item>
///   <item>409 — нарушено ограничение: дубль ключа, занятая бригада,
///         нехватка материала, запрещённый переход статуса;</item>
///   <item>429 — превышен предел частоты запросов; <c>TOO_MANY_REQUESTS</c>;</item>
///   <item>500 — непредвиденная ошибка сервера; <c>INTERNAL_ERROR</c>.</item>
/// </list>
/// У анонимных операций (health-check, регистрация, вход) коды 401, 403 и
/// 404 не добавляются: токен там не требуется, и упоминать про него в
/// документации незачем.
/// </summary>
public sealed class StandardResponsesOperationFilter : IOperationFilter
{
    private const string ErrorPayload =
        "Тело ответа: { success: false, data: null, message: «…», error_code: «…» }.";

    public void Apply(OpenApiOperation operation, OperationFilterContext context)
    {
        var method = context.ApiDescription.HttpMethod ?? "GET";
        var anonymous = context.ApiDescription.ActionDescriptor.EndpointMetadata
            .Any(item => item is IAllowAnonymous);

        Add(operation, "400", "Некорректные данные запроса. " + ErrorPayload);
        Add(operation, "401", "Токен не передан или просрочен. " + ErrorPayload);
        Add(operation, "403", "Недостаточно прав для этой операции. " + ErrorPayload);
        Add(operation, "404", "Запись с таким идентификатором не найдена. " + ErrorPayload);

        if (method is "POST" or "PUT" or "PATCH" or "DELETE")
        {
            Add(operation, "409", "Нарушено ограничение целостности или переход статуса недопустим. " + ErrorPayload);
        }

        Add(operation, "429", "Превышен предел частоты запросов. Повторите позже. " + ErrorPayload);
        Add(operation, "500", "Внутренняя ошибка сервера. " + ErrorPayload);

        if (anonymous)
        {
            Remove(operation, "401");
            Remove(operation, "403");
            Remove(operation, "404");
        }
    }

    private static void Add(OpenApiOperation operation, string code, string description)
    {
        // В Microsoft.OpenApi 2.x свойство объявлено nullable: у операции без
        // явно заданных ответов коллекции может не быть. Создаём её сами,
        // иначе фильтр упал бы ровно там, где нужен.
        var responses = operation.Responses;
        if (responses == null)
        {
            responses = new OpenApiResponses();
            operation.Responses = responses;
        }

        // Ответ, объявленный атрибутом ProducesResponseType на самом методе,
        // приоритетнее: так описание можно уточнить точечно.
        if (responses.ContainsKey(code))
        {
            return;
        }

        responses[code] = new OpenApiResponse { Description = description };
    }

    private static void Remove(OpenApiOperation operation, string code)
    {
        operation.Responses?.Remove(code);
    }
}