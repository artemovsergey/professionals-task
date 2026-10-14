using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace ToirProf.Desktop.Services;

/// <summary>
/// Очередь операций, которые не удалось отправить без связи с сервером.
///
/// Сценарий из задания: мастер в цехе, где нет Wi-Fi, заполняет заявку
/// и нажимает «Сохранить». Заявка не должна пропасть — она попадает в
/// очередь на диске и уходит на сервер, как только связь появится.
/// Очередь намеренно на диске, а не в памяти: клиент может закрыть
/// и запустить заново, операции не потеряются.
/// </summary>
public sealed class OfflineQueue
{
    private readonly string _path;
    private readonly JsonSerializerOptions _json = new(JsonSerializerDefaults.Web);
    private readonly Lock _gate = new();
    private readonly List<QueuedOperation> _items = new();
    private CancellationTokenSource? _worker;

    public OfflineQueue()
        : this(Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "ToirProf",
            "queue.json"))
    {
    }

    public OfflineQueue(string path)
    {
        _path = path;
        Load();
    }

    /// <summary>Сколько операций ждёт отправки.</summary>
    public int PendingCount
    {
        get
        {
            lock (_gate)
            {
                return _items.Count;
            }
        }
    }

    /// <summary>Копия очереди для показа в интерфейсе.</summary>
    public IReadOnlyList<QueuedOperation> Snapshot
    {
        get
        {
            lock (_gate)
            {
                return _items.ToList();
            }
        }
    }

    /// <summary>
    /// Добавляет операцию в очередь. Повторное добавление той же операции
    /// ничего не делает — иначе два нажатия «Сохранить» подряд дадут
    /// две одинаковые заявки после восстановления связи.
    /// </summary>
    public bool Enqueue(QueuedOperation operation)
    {
        lock (_gate)
        {
            if (_items.Any(x => x.Id == operation.Id))
            {
                return false;
            }

            _items.Add(operation);
        }

        Save();
        return true;
    }

    public void Remove(Guid id)
    {
        lock (_gate)
        {
            _items.RemoveAll(x => x.Id == id);
        }

        Save();
    }

    public void Clear()
    {
        lock (_gate)
        {
            _items.Clear();
        }

        Save();
    }

    /// <summary>
    /// Запускает фоновую отправку. Каждая операция пытается уйти один раз;
    /// при неудаче она остаётся в очереди и ждёт следующего прохода.
    /// </summary>
    public void Start(Func<QueuedOperation, CancellationToken, Task<bool>> sender)
    {
        Stop();

        _worker = new CancellationTokenSource();

        var token = _worker.Token;
        _ = Task.Run(async () =>
        {
            while (!token.IsCancellationRequested)
            {
                foreach (var operation in Snapshot)
                {
                    if (token.IsCancellationRequested)
                    {
                        return;
                    }

                    if (await sender(operation, token))
                    {
                        Remove(operation.Id);
                    }
                    else
                    {
                        // Связи нет — дальше идти бессмысленно, ждём следующего прохода.
                        break;
                    }
                }

                await Task.Delay(TimeSpan.FromSeconds(15), token);
            }
        }, token);
    }

    public void Stop()
    {
        if (_worker is null)
        {
            return;
        }

        _worker.Cancel();
        _worker.Dispose();
        _worker = null;
    }

    /// <summary>
    /// Читает очередь с диска. Публичный метод: файл может остаться
    /// от прошлого запуска, и клиент обязан подхватить его сам —
    /// конструктору бездумно подменять состояние не стоит.
    /// </summary>
    public void Load()
    {
        if (!File.Exists(_path))
        {
            return;
        }

        try
        {
            var saved = JsonSerializer.Deserialize<List<QueuedOperation>>(
                File.ReadAllText(_path), _json);

            if (saved is not null)
            {
                lock (_gate)
                {
                    _items.AddRange(saved);
                }
            }
        }
        catch (JsonException)
        {
            // Повреждённый файл не должен ронять клиент: очищаем очередь.
            Clear();
        }
    }

    private void Save()
    {
        var directory = Path.GetDirectoryName(_path);
        if (!string.IsNullOrEmpty(directory))
        {
            Directory.CreateDirectory(directory);
        }

        File.WriteAllText(_path, JsonSerializer.Serialize(Snapshot, _json));
    }
}

/// <summary>
/// Отложенная операция: метод, путь и тело запроса. Хранится как есть,
/// чтобы при восстановлении связи отправить ровно тот запрос, который
/// клиент пытался сделать, а не «похожий».
/// </summary>
public sealed record QueuedOperation(
    Guid Id,
    string Method,
    string Path,
    string? Body,
    DateTimeOffset CreatedAt,
    string Description);
