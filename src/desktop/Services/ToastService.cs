using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Threading;
using System.Threading.Tasks;

namespace ToirProf.Desktop.Services;

public enum ToastKind
{
    Info,
    Success,
    Warning,
    Error,
}

/// <summary>
/// Всплывающее уведомление. Одна запись живёт <see cref="DefaultLifetime"/>
/// секунд и исчезает сама — пользователю не нужно ничего закрывать.
/// </summary>
public sealed class Toast(Guid id, string message, ToastKind kind, DateTimeOffset createdAt)
{
    public Guid Id { get; } = id;

    public string Message { get; } = message;

    public ToastKind Kind { get; } = kind;

    public DateTimeOffset CreatedAt { get; } = createdAt;

    /// <summary>Заголовок для окна: один символ заменяет иконку из ресурсов.</summary>
    public string Glyph => Kind switch
    {
        ToastKind.Success => "OK",
        ToastKind.Warning => "!",
        ToastKind.Error => "X",
        _ => "i",
    };
}

/// <summary>
/// Всплывающие сообщения для всех экранов. Экран не знает, где именно
/// будет показано уведомление: он просто вызывает Info или Error, а
/// оболочка подписана на <see cref="Items"/> и рисует список поверх окна.
///
/// Класс не зависит от Avalonia — в нём только коллекция и таймеры,
/// поэтому его можно использовать и в тестах.
/// </summary>
public sealed class ToastService : IDisposable
{
    public const int DefaultLifetime = 4;

    /// <summary>Больше пяти сообщений на экране превращаются в стену текста.</summary>
    public const int MaxVisible = 5;

    private readonly ObservableCollection<Toast> _items = new();

    private CancellationTokenSource? _lifetime;

    public ReadOnlyObservableCollection<Toast> Items { get; }

    public ToastService()
    {
        Items = new ReadOnlyObservableCollection<Toast>(_items);
    }

    public void Info(string message) => Show(message, ToastKind.Info);

    public void Success(string message) => Show(message, ToastKind.Success);

    public void Warn(string message) => Show(message, ToastKind.Warning);

    public void Error(string message) => Show(message, ToastKind.Error);

    public void Show(string message, ToastKind kind = ToastKind.Info, int lifetimeSeconds = DefaultLifetime)
    {
        _items.Insert(0, new Toast(Guid.NewGuid(), message, kind, DateTimeOffset.UtcNow));

        while (_items.Count > MaxVisible)
        {
            _items.RemoveAt(_items.Count - 1);
        }

        DismissLater(_items[0], lifetimeSeconds);
    }

    /// <summary>Показать сразу несколько сообщений — так удобно после загрузки экрана.</summary>
    public void ShowMany(IEnumerable<(string Message, ToastKind Kind)> messages)
    {
        foreach (var (message, kind) in messages)
        {
            Show(message, kind);
        }
    }

    public void Dismiss(Guid id)
    {
        for (var i = 0; i < _items.Count; i++)
        {
            if (_items[i].Id == id)
            {
                _items.RemoveAt(i);
                return;
            }
        }
    }

    public void Clear() => _items.Clear();

    private void DismissLater(Toast toast, int lifetimeSeconds)
    {
        _lifetime?.Cancel();
        _lifetime = new CancellationTokenSource();

        var token = _lifetime.Token;
        _ = Task.Delay(TimeSpan.FromSeconds(Math.Max(1, lifetimeSeconds)), token)
            .ContinueWith(
                _ => Dismiss(toast.Id),
                CancellationToken.None,
                TaskContinuationOptions.OnlyOnRanToCompletion,
                TaskScheduler.Default);
    }

    public void Dispose()
    {
        _lifetime?.Cancel();
        _lifetime?.Dispose();
        Clear();
    }
}
