using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;
using Npgsql;
using ToirProf.Shared;

namespace ToirProf.Api.Middlewares;

/// <summary>
/// Единая точка, где превращаются исключения в ответы API.
///
/// Зачем он нужен: без него любое исключение возвращает клиенту
/// пустую страницу 500 без понятного текста. С middleware клиент всегда
/// получает одну и ту же структуру {success, data, message, error_code}
/// и осмысленный код ошибки, а в консоль попадает полный стек-трейс.
///
/// В контроллерах и сервисах try-catch не пишется — это нарушение,
/// которое ловит и проверяющий в коде, и эксперт на демонстрации.
/// </summary>
public sealed class ExceptionMiddleware(
    RequestDelegate next,
    ILogger<ExceptionMiddleware> logger)
{
    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await next(context);
        }
        catch (ApiException ex)
        {
            await WriteAsync(context, ex.StatusCode, ex.Message, ex.ErrorCode);
        }
        catch (DbUpdateConcurrencyException ex)
        {
            // Конфликт версий: строку изменили, пока её правили.
            logger.LogWarning(ex, "Конфликт при сохранении {Path}", context.Request.Path);
            await WriteAsync(context, StatusCodes.Status409Conflict,
                "Запись уже изменена другим пользователем. Обновите страницу и повторите.",
                ErrorCodes.Conflict);
        }
        catch (DbUpdateException ex) when (ex.InnerException is PostgresException { SqlState: PostgresErrorCodes.UniqueViolation })
        {
            // UNIQUE из db/schema.sql сработал — сообщение пользователю,
            // а не в лог: «такой номер уже есть» это штатная ситуация,
            // а не поломка.
            logger.LogInformation(ex, "Нарушение UNIQUE на {Path}", context.Request.Path);
            await WriteAsync(context, StatusCodes.Status409Conflict,
                "Запись с таким уникальным значением уже существует.",
                ErrorCodes.Conflict);
        }
        catch (DbUpdateException ex) when (ex.InnerException is PostgresException { SqlState: PostgresErrorCodes.ForeignKeyViolation })
        {
            logger.LogInformation(ex, "Нарушение внешнего ключа на {Path}", context.Request.Path);
            await WriteAsync(context, StatusCodes.Status409Conflict,
                "Запись используется в других документах и не может быть изменена или удалена.",
                ErrorCodes.Conflict);
        }
        catch (DbUpdateException ex) when (ex.InnerException is PostgresException { SqlState: PostgresErrorCodes.CheckViolation })
        {
            // Сработал CHECK или один из триггеров: сюда попадает в том числе
            // запрет менять статус выведенного из эксплуатации оборудования.
            logger.LogInformation(ex, "Нарушение CHECK/триггера на {Path}", context.Request.Path);
            await WriteAsync(context, StatusCodes.Status400BadRequest,
                "Данные не проходят проверку в базе: проверьте даты, статусы и числовые значения.",
                ErrorCodes.ValidationError);
        }
        catch (DbUpdateException ex)
        {
            logger.LogError(ex, "Ошибка сохранения на {Path}", context.Request.Path);
            await WriteAsync(context, StatusCodes.Status500InternalServerError,
                "Не удалось сохранить данные. Повторите попытку или обратитесь к администратору.",
                ErrorCodes.InternalError);
        }
        catch (OperationCanceledException) when (context.RequestAborted.IsCancellationRequested)
        {
            // Клиент закрыл соединение — отвечать уже некому, но и 500 не нужно.
            logger.LogDebug("Запрос {Path} отменён клиентом", context.Request.Path);
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Необработанная ошибка на {Path}", context.Request.Path);
            await WriteAsync(context, StatusCodes.Status500InternalServerError,
                "Внутренняя ошибка сервера. Повторите попытку позже.",
                ErrorCodes.InternalError);
        }
    }

    private static async Task WriteAsync(HttpContext context, int statusCode, string message, string errorCode)
    {
        if (context.Response.HasStarted)
        {
            // Заголовки уже ушли: тело дописать нельзя, рвём соединение.
            return;
        }

        context.Response.Clear();
        context.Response.StatusCode = statusCode;
        context.Response.ContentType = "application/json; charset=utf-8";

        var payload = ApiResponse<object>.Fail(message, errorCode);
        await context.Response.WriteAsync(
            JsonSerializer.Serialize(payload, JsonOptions),
            context.RequestAborted);
    }

    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };
}

/// <summary>
/// Исключение, которым сервис сообщает контроллеру ожидаемую ошибку.
/// Код возврата и текст подставляются один раз, в одном месте.
/// </summary>
public sealed class ApiException(
    int statusCode,
    string message,
    string errorCode) : Exception(message)
{
    public int StatusCode { get; } = statusCode;

    public string ErrorCode { get; } = errorCode;

    public static ApiException NotFound(string message)
        => new(StatusCodes.Status404NotFound, message, ErrorCodes.NotFound);

    public static ApiException Conflict(string message, string errorCode = ErrorCodes.Conflict)
        => new(StatusCodes.Status409Conflict, message, errorCode);

    public static ApiException Forbidden(string message)
        => new(StatusCodes.Status403Forbidden, message, ErrorCodes.Forbidden);

    public static ApiException BadRequest(string message, string errorCode = ErrorCodes.ValidationError)
        => new(StatusCodes.Status400BadRequest, message, errorCode);

    public static ApiException TooManyRequests(string message)
        => new(StatusCodes.Status429TooManyRequests, message, ErrorCodes.TooManyRequests);
}