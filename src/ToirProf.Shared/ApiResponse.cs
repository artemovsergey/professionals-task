namespace ToirProf.Shared;

/// <summary>
/// Единая обёртка ответа API. Все контроллеры возвращают только её:
/// так клиенту не нужно угадывать формат по HTTP-коду или по URL.
/// </summary>
/// <param name="Success">Успех ли запрос.</param>
/// <param name="Data">Полезная нагрузка. При ошибке всегда <c>null</c>.</param>
/// <param name="Message">Сообщение для человека: что произошло или что сделано.</param>
/// <param name="ErrorCode">Машиночитаемый код ошибки, см. <c>ErrorCodes</c>.</param>
public record ApiResponse<T>(
    bool Success,
    T? Data,
    string Message,
    string? ErrorCode)
{
    public static ApiResponse<T> Ok(T data, string message = "OK")
        => new(true, data, message, null);

    public static ApiResponse<T> Fail(string message, string errorCode, int statusCode = 400)
        => new(false, default, message, errorCode);
}

/// <summary>
/// Коды ошибок. Строки, а не числа: клиент сравнивает текст,
/// и при добавлении новой ошибки существующие значения не меняются.
/// </summary>
public static class ErrorCodes
{
    public const string ValidationError = "VALIDATION_ERROR";
    public const string NotFound = "NOT_FOUND";
    public const string Conflict = "CONFLICT";
    public const string InvalidToken = "INVALID_TOKEN";
    public const string Forbidden = "FORBIDDEN";
    public const string StatusLocked = "STATUS_LOCKED";
    public const string CrewBusy = "CREW_BUSY";
    public const string NotEnoughStock = "NOT_ENOUGH_STOCK";
    public const string TooManyRequests = "TOO_MANY_REQUESTS";
    public const string InternalError = "INTERNAL_ERROR";
}

/// <summary>Ответ без полезной нагрузки: 204, ошибки, health-check.</summary>
public record ApiResponse(bool Success, string Message, string? ErrorCode)
{
    public static ApiResponse Ok(string message = "OK") => new(true, message, null);

    public static ApiResponse Fail(string message, string errorCode)
        => new(false, message, errorCode);
}