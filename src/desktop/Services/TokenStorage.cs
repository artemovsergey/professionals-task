using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

namespace ToirProf.Desktop.Services;

/// <summary>
/// Хранилище токена и учётной записи текущего пользователя.
///
/// Токен лежит в файле рядом с программой, а не в памяти: мастер закрывает
/// клиент на обеденный перерыв и возвращается к тому же рабочему месту.
/// Файл сознательно простой — расшифровка токена секретом не является,
/// защищать его от локального чтения нечем.
/// </summary>
public sealed class TokenStorage
{
    private readonly string _path;
    private readonly JsonSerializerOptions _json = new(JsonSerializerDefaults.Web);

    public TokenStorage()
        : this(Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "ToirProf",
            "session.json"))
    {
    }

    public TokenStorage(string path) => _path = path;

    /// <summary>Токен в формате JWT либо null, если пользователь не входил.</summary>
    public string? Token { get; private set; }

    /// <summary>Логин текущего пользователя — показывается в верхней панели.</summary>
    public string? Username { get; private set; }

    /// <summary>Роль текущего пользователя: ADMIN, MANAGER или MASTER.</summary>
    public string? Role { get; private set; }

    /// <summary>true, если в системе есть сохранённая сессия.</summary>
    public bool HasSession => !string.IsNullOrEmpty(Token);

    public void Save(string token, string username, string role)
    {
        Token = token;
        Username = username;
        Role = role;

        var directory = Path.GetDirectoryName(_path);
        if (!string.IsNullOrEmpty(directory))
        {
            Directory.CreateDirectory(directory);
        }

        var state = new SessionState(token, username, role);
        File.WriteAllText(_path, JsonSerializer.Serialize(state, _json));
    }

    public void Load()
    {
        if (!File.Exists(_path))
        {
            return;
        }

        try
        {
            var state = JsonSerializer.Deserialize<SessionState>(File.ReadAllText(_path), _json);
            if (state is null || string.IsNullOrEmpty(state.Token))
            {
                return;
            }

            Token = state.Token;
            Username = state.Username;
            Role = state.Role;
        }
        catch (JsonException)
        {
            // Файл повреждён — считаем, что сессии нет, и просим войти заново.
            Clear();
        }
    }

    public void Clear()
    {
        Token = null;
        Username = null;
        Role = null;

        if (File.Exists(_path))
        {
            File.Delete(_path);
        }
    }

    /// <summary>
    /// Заголовок Authorization. Возвращает null, когда токена нет:
    /// вызывающий код сам решает, отправить ли запрос вообще.
    /// </summary>
    public string? AuthorizationHeader =>
        Token is null ? null : $"Bearer {Token}";

    private sealed record SessionState(string Token, string? Username, string? Role);
}