using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using ToirProf.Shared;

namespace ToirProf.Desktop.Services;

/// <summary>
/// Результат запроса к серверу. Клиенту не нужен HttpResponseMessage:
/// он живёт доли секунды, а всё, что показывается на экране, — это
/// либо данные, либо текст ошибки из обёртки ответа.
/// </summary>
public sealed record ApiResult<T>(bool Success, T? Data, string Message, string? ErrorCode, int StatusCode)
{
    public bool IsOffline => StatusCode == 0;

    public static ApiResult<T> Fail(string message, string? errorCode = null, int statusCode = 0) =>
        new(false, default, message, errorCode, statusCode);

    public static ApiResult<T> Ok(T data, string message = "OK") =>
        new(true, data, message, null, 200);
}

/// <summary>
/// HTTP-клиент desktop-клиента. Намеренно не зависит ни от Avalonia,
/// ни от проекта API: DTO сервера клиенту не нужны, достаточно
/// разобрать обёртку {success, data, message, error_code}.
///
/// Что клиент делает сам, хотя по ТЗ не должен:
///  - хранит токен на диске, чтобы не вводить пароль после каждого запуска;
///  - кладёт операции в очередь, когда сервер недоступен;
///  - временно блокирует форму входа после серии неудачных попыток.
/// Это технические подпорки, а не бизнес-правила: подсчёт простоя,
/// проверку дат и стоимость материалов считает сервер.
/// </summary>
public sealed class ApiClient : IDisposable
{
    private const int MaxLoginAttempts = 3;

    /// <summary>Сколько секунд форма входа закрыта после серии неудач.</summary>
    public const int AutoBlockSeconds = 15;

    private static readonly JsonSerializerOptions Json = new(JsonSerializerDefaults.Web)
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    private readonly HttpClient _http;
    private readonly TokenStorage _tokens;
    private readonly OfflineQueue _queue;
    private readonly FileLogger _log;
    private readonly object _blockGate = new();

    private int _failedLogins;
    private DateTimeOffset _blockedUntil = DateTimeOffset.MinValue;

    public ApiClient(TokenStorage tokens, OfflineQueue queue, FileLogger log, string baseAddress = "http://localhost:5080")
    {
        _tokens = tokens;
        _queue = queue;
        _log = log;

        _http = new HttpClient
        {
            BaseAddress = new Uri(baseAddress),
            Timeout = TimeSpan.FromSeconds(20),
        };
        _http.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

        _tokens.Load();
        _queue.Load();
    }

    /// <summary>Сервер сейчас недоступен — клиент работает из очереди и кэша.</summary>
    public bool IsOffline { get; private set; }

    /// <summary>Секунд до разблокировки формы входа; 0, если блокировки нет.</summary>
    public int BlockSecondsRemaining
    {
        get
        {
            lock (_blockGate)
            {
                var left = (_blockedUntil - DateTimeOffset.UtcNow).TotalSeconds;
                return left <= 0 ? 0 : (int)Math.Ceiling(left);
            }
        }
    }

    public string? Username => _tokens.Username;

    public string? Role => _tokens.Role;

    public bool HasSession => _tokens.HasSession;

    /// <summary>Сколько операций ждут отправки — показывается в верхней панели.</summary>
    public int PendingQueueCount => _queue.PendingCount;

    /// <summary>
    /// Вход в систему. Три неудачи подряд закрывают форму на
    /// <see cref="AutoBlockSeconds"/> секунд: так демонстрация не
    /// превращается в перебор паролей перед экспертами.
    /// </summary>
    public async Task<ApiResult<string>> LoginAsync(string username, string password, CancellationToken ct = default)
    {
        var block = BlockSecondsRemaining;
        if (block > 0)
        {
            return ApiResult<string>.Fail(
                $"Слишком много попыток. Повторите вход через {block} с.",
                ErrorCodes.TooManyRequests,
                429);
        }

        var payload = new { username, password };
        var response = await PostAnonymousAsync<TokenEnvelope>("/api/auth/login", payload, ct);

        if (!response.Success || response.Data?.Token is null)
        {
            lock (_blockGate)
            {
                _failedLogins++;
                if (_failedLogins >= MaxLoginAttempts)
                {
                    _blockedUntil = DateTimeOffset.UtcNow.AddSeconds(AutoBlockSeconds);
                    _failedLogins = 0;
                    _log.Warn($"Вход заблокирован на {AutoBlockSeconds} с после {MaxLoginAttempts} неудачных попыток");
                }
            }

            return ApiResult<string>.Fail(response.Message, response.ErrorCode, response.StatusCode);
        }

        var envelope = response.Data;
        lock (_blockGate)
        {
            _failedLogins = 0;
            _blockedUntil = DateTimeOffset.MinValue;
        }

        _tokens.Save(envelope.Token, envelope.Username ?? username, envelope.Role ?? string.Empty);
        _log.Info($"Вход выполнен: {envelope.Username ?? username} ({envelope.Role})");
        StartQueuePump();
        return ApiResult<string>.Ok(envelope.Token, "Вход выполнен.");
    }

    public void Logout()
    {
        _tokens.Clear();
        _queue.Clear();
        _log.Info("Сеанс завершён");
    }

    public Task<ApiResult<T>> GetAsync<T>(string path, CancellationToken ct = default) =>
        SendAsync<T>(HttpMethod.Get, path, null, ct);

    public Task<ApiResult<T>> PostAsync<T>(string path, object body, CancellationToken ct = default) =>
        SendAsync<T>(HttpMethod.Post, path, body, ct);

    public Task<ApiResult<T>> PutAsync<T>(string path, object body, CancellationToken ct = default) =>
        SendAsync<T>(HttpMethod.Put, path, body, ct);

    public Task<ApiResult<T>> PatchAsync<T>(string path, object body, CancellationToken ct = default) =>
        SendAsync<T>(HttpMethod.Patch, path, body, ct);

    public Task<ApiResult<T>> DeleteAsync<T>(string path, CancellationToken ct = default) =>
        SendAsync<T>(HttpMethod.Delete, path, null, ct);

    /// <summary>
    /// Единая точка отправки. Здесь и только здесь решается, что делать
    /// с ошибкой сети: операцию изменения ставим в очередь, чтение —
    /// возвращаем как офлайн-ошибку, чтобы экран показал заглушку.
    /// </summary>
    private async Task<ApiResult<T>> SendAsync<T>(HttpMethod method, string path, object? body, CancellationToken ct)
    {
        try
        {
            using var request = new HttpRequestMessage(method, path);
            if (body is not null)
            {
                request.Content = JsonContent.Create(body, options: Json);
            }

            if (_tokens.Token is not null)
            {
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _tokens.Token);
            }

            using var response = await _http.SendAsync(request, ct);
            var text = await response.Content.ReadAsStringAsync(ct);
            return Parse<T>(response.StatusCode, text);
        }
        catch (HttpRequestException ex)
        {
            IsOffline = true;
            _log.Warn($"{method} {path}: сервер недоступен ({ex.Message})");

            if (method != HttpMethod.Get)
            {
                _queue.Enqueue(new QueuedOperation(
                    Guid.NewGuid(),
                    method.Method,
                    path,
                    body is null ? null : JsonSerializer.Serialize(body, Json),
                    DateTimeOffset.UtcNow,
                    $"{method} {path}"));
            }

            return ApiResult<T>.Fail("Сервер недоступен. Показаны последние сохранённые данные.", "OFFLINE");
        }
        catch (TaskCanceledException) when (!ct.IsCancellationRequested)
        {
            return ApiResult<T>.Fail("Сервер не ответил за 20 секунд.", "TIMEOUT");
        }
    }

    private async Task<ApiResult<T>> PostAnonymousAsync<T>(string path, object body, CancellationToken ct)
    {
        try
        {
            using var content = JsonContent.Create(body, options: Json);
            using var response = await _http.PostAsync(path, content, ct);
            var text = await response.Content.ReadAsStringAsync(ct);
            return Parse<T>(response.StatusCode, text);
        }
        catch (HttpRequestException ex)
        {
            IsOffline = true;
            _log.Warn($"POST {path}: сервер недоступен ({ex.Message})");
            return ApiResult<T>.Fail("Сервер недоступен. Проверьте, запущен ли API.", "OFFLINE");
        }
    }

    /// <summary>
    /// Разбор обёртки {success, data, message, error_code}.
    /// Ответ 401 с обёрткой и пустой ответ — разные вещи, поэтому
    /// спускаемся к тексту статуса только когда JSON разобрать не удалось.
    /// </summary>
    private static ApiResult<T> Parse<T>(HttpStatusCode status, string text)
    {
        var code = (int)status;

        if (string.IsNullOrWhiteSpace(text))
        {
            return code is >= 200 and < 300
                ? ApiResult<T>.Ok(default!)
                : ApiResult<T>.Fail($"Ошибка {code}.", null, code);
        }

        Envelope? envelope;
        try
        {
            envelope = JsonSerializer.Deserialize<Envelope>(text, Json);
        }
        catch (JsonException)
        {
            return ApiResult<T>.Fail($"Ошибка {code}: сервер вернул не JSON.", null, code);
        }

        if (envelope is null)
        {
            return ApiResult<T>.Fail($"Ошибка {code}.", null, code);
        }

        if (!envelope.Success)
        {
            return ApiResult<T>.Fail(
                string.IsNullOrWhiteSpace(envelope.Message) ? $"Ошибка {code}." : envelope.Message,
                envelope.ErrorCode,
                code);
        }

        T? data = default;
        if (envelope.Data.ValueKind is not JsonValueKind.Undefined and not JsonValueKind.Null)
        {
            try
            {
                data = envelope.Data.Deserialize<T>(Json);
            }
            catch (JsonException ex)
            {
                return ApiResult<T>.Fail($"Не удалось прочитать данные ответа: {ex.Message}", null, code);
            }
        }

        return new ApiResult<T>(true, data, envelope.Message ?? "OK", envelope.ErrorCode, code);
    }

    /// <summary>
    /// Фоновая отправка накопленных операций. Запускается после входа и
    /// живёт до выхода из приложения; интервал 15 секунд — из
    /// <see cref="OfflineQueue.Start"/>.
    /// </summary>
    private void StartQueuePump()
    {
        _queue.Start(ReplayAsync);
    }

    private async Task<bool> ReplayAsync(QueuedOperation operation, CancellationToken ct)
    {
        var result = await SendAsync<object>(
            new HttpMethod(operation.Method),
            operation.Path,
            operation.Body is null ? null : JsonSerializer.Deserialize<JsonElement>(operation.Body),
            ct);

        if (result.Success)
        {
            _log.Info($"Очередь: отправлена операция {operation.Description}");
            return true;
        }

        _log.Warn($"Очередь: операция {operation.Description} не прошла ({result.Message})");
        return false;
    }

    public void Dispose()
    {
        _queue.Stop();
        _http.Dispose();
    }

    /// <summary>Обёртка ответа сервера в том виде, в каком её присылает API.</summary>
    private sealed class Envelope
    {
        public bool Success { get; set; }

        /// <summary>
        /// Поле data необязательное, поэтому тип — JsonElement, а не JsonElement?:
        /// отсутствующее поле даёт Undefined, пустое — Null. Оба случая
        /// означают «данных нет» и проверяются одним условием.
        /// </summary>
        public JsonElement Data { get; set; }

        public string? Message { get; set; }

        public string? ErrorCode { get; set; }
    }

    /// <summary>Часть ответа /api/auth/login, нужная клиенту.</summary>
    private sealed class TokenEnvelope
    {
        public string? Token { get; set; }

        public string? Username { get; set; }

        public string? Role { get; set; }
    }
}
