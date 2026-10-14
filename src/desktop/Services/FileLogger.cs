using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace ToirProf.Desktop.Services;

/// <summary>
/// Локальный журнал клиента. Требование задания: клиент пишет, что делает,
/// даже если сервер недоступен, — по журналу эксперт может понять, что
/// происходило в офлайне.
///
/// Файл один и растёт до полумегабайта, дальше начинается новая копия:
/// иначе за несколько недель эксплуатации журнал станет нечитаемым.
/// </summary>
public sealed class FileLogger
{
    private const long MaxFileSize = 512 * 1024;
    private const int MaxFiles = 5;

    private readonly string _directory;
    private readonly object _gate = new();

    public FileLogger()
        : this(Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "ToirProf",
            "logs"))
    {
    }

    public FileLogger(string directory) => _directory = directory;

    /// <summary>Путь к текущему файлу журнала — показывается в окне отчётов.</summary>
    public string CurrentFile => Path.Combine(_directory, "client.log");

    public void Info(string message) => Write("INFO ", message);

    public void Warn(string message) => Write("WARN ", message);

    public void Error(string message, Exception? error = null)
    {
        var text = error is null ? message : $"{message} | {error.GetType().Name}: {error.Message}";
        Write("ERROR", text);
    }

    /// <summary>
    /// Последние строки журнала снизу вверх — так их удобнее читать
    /// в окне «Отчёты», не открывая файл.
    /// </summary>
    public IReadOnlyList<string> Tail(int lines = 200)
    {
        lock (_gate)
        {
            if (!File.Exists(CurrentFile))
            {
                return Array.Empty<string>();
            }

            var all = File.ReadAllLines(CurrentFile, Encoding.UTF8);
            var take = Math.Min(lines, all.Length);

            var result = new List<string>(take);
            for (var i = all.Length - 1; i >= all.Length - take; i--)
            {
                result.Add(all[i]);
            }

            result.Reverse();
            return result;
        }
    }

    private void Write(string level, string message)
    {
        var line = $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} {level} {message}";

        lock (_gate)
        {
            try
            {
                Directory.CreateDirectory(_directory);
                RollIfNeeded();
                File.AppendAllText(CurrentFile, line + Environment.NewLine, Encoding.UTF8);
            }
            catch (IOException)
            {
                // Журнал не записался — это не повод ронять рабочее место
                // мастера из-за прав доступа к папке профиля.
            }
        }
    }

    private void RollIfNeeded()
    {
        var info = new FileInfo(CurrentFile);
        if (!info.Exists || info.Length < MaxFileSize)
        {
            return;
        }

        // client.log -> client.1.log -> client.2.log и так далее
        for (var index = MaxFiles - 1; index >= 1; index--)
        {
            var older = Path.Combine(_directory, $"client.{index}.log");
            if (!File.Exists(older))
            {
                continue;
            }

            var newer = Path.Combine(_directory, $"client.{index + 1}.log");
            if (index == MaxFiles - 1)
            {
                File.Delete(older);
            }
            else
            {
                File.Move(older, newer, overwrite: true);
            }
        }

        File.Move(CurrentFile, Path.Combine(_directory, "client.1.log"), overwrite: true);
    }
}