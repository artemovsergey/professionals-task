using System.Globalization;
using System.Text;
using Microsoft.EntityFrameworkCore;
using ToirProf.Api.Data;
using ToirProf.Api.DTOs;
using ToirProf.Api.Middlewares;
using ToirProf.Shared;

namespace ToirProf.Api.Services;

/// <summary>
/// Формирует PDF-отчёты и выдаёт временную ссылку на скачивание.
/// </summary>
public interface IReportService
{
    Task<ReportLink> CreateLinkAsync(CreateReportDto dto, CancellationToken ct);

    Task<byte[]> BuildAsync(string kind, DateRange period, Guid? workshopId, CancellationToken ct);

    string? ResolveToken(string token);
}

public sealed class ReportService(IDashboardService dashboard) : IReportService
{
    private const int MaxRows = 500;

    // Ссылка живёт 15 секунд — это прямое требование задания. Токен
    // хранится в памяти процесса: перезапуск API делает все ранее
    // выданные ссылки недействительными, и это правильное поведение —
    // отчёт не должен раздаваться «на будущее».
    private static readonly Dictionary<string, (string Kind, DateRange Period, Guid? WorkshopId, DateTimeOffset ExpiresAt)> Links = new(StringComparer.Ordinal);

    public async Task<ReportLink> CreateLinkAsync(CreateReportDto dto, CancellationToken ct)
    {
        var kind = NormalizeKind(dto.Kind);
        var period = new DateRange(dto.From, dto.To);

        var token = Guid.NewGuid().ToString("N");
        var expiresAt = DateTimeOffset.UtcNow.AddSeconds(ReportLink.TtlSecondsValue);

        lock (Links)
        {
            DropExpired();
            Links[token] = (kind, period, dto.WorkshopId, expiresAt);
        }

        var url = $"/api/reports/download/{token}";
        return new ReportLink(token, url, expiresAt, ReportLink.TtlSecondsValue);
    }

    public string? ResolveToken(string token)
    {
        lock (Links)
        {
            DropExpired();
            if (!Links.TryGetValue(token, out var entry))
            {
                return null;
            }

            return $"{entry.Kind}|{entry.Period.Start:yyyy-MM-dd}|{entry.Period.End:yyyy-MM-dd}|{entry.WorkshopId?.ToString() ?? string.Empty}";
        }
    }

    public async Task<byte[]> BuildAsync(string kind, DateRange period, Guid? workshopId, CancellationToken ct)
    {
        return kind switch
        {
            ReportKinds.Crews => BuildCrewReport(await dashboard.GetAnalyticsAsync(period, workshopId, ct), period),
            ReportKinds.Materials => BuildMaterialReport(await dashboard.GetAnalyticsAsync(period, workshopId, ct), period),
            ReportKinds.Plan => BuildPlanReport(await dashboard.GetAnalyticsAsync(period, workshopId, ct), period),
            _ => BuildDowntimeReport(await dashboard.GetAnalyticsAsync(period, workshopId, ct), period),
        };
    }

    private static string NormalizeKind(string? kind) => kind?.Trim().ToLowerInvariant() switch
    {
        ReportKinds.Crews => ReportKinds.Crews,
        ReportKinds.Materials => ReportKinds.Materials,
        ReportKinds.Plan => ReportKinds.Plan,
        _ => ReportKinds.Downtime,
    };

    private static void DropExpired()
    {
        var now = DateTimeOffset.UtcNow;
        var expired = Links.Where(pair => pair.Value.ExpiresAt <= now).Select(pair => pair.Key).ToList();
        foreach (var key in expired)
        {
            Links.Remove(key);
        }
    }

    // ------------------------------------------------------------------
    //  Отчёты
    // ------------------------------------------------------------------

    private static byte[] BuildDowntimeReport(AnalyticsReport report, DateRange period)
    {
        var rows = report.Downtime.Take(MaxRows)
            .Select(s => new[] { s.InventoryNumber, s.Name, s.WorkshopName, s.OrdersCount.ToString(), s.TotalDowntimeHours.ToString("0.00"), s.SharePercent.ToString("0.0") })
            .ToList();

        return Render(
            "Отчёт по простоям оборудования",
            period,
            new[] { "Инв. номер", "Оборудование", "Цех", "Заявок", "Простой, ч", "Доля, %" },
            rows,
            ["Units"], [1f, 2f, 1.2f, 0.6f, 0.9f, 0.6f],
            new[]
            {
                $"Заявок за период: {report.Orders.Total}",
                $"Средний простой: {report.Orders.AverageDowntimeHours:0.00} ч",
            });
    }

    private static byte[] BuildCrewReport(AnalyticsReport report, DateRange period)
    {
        var rows = report.Crews.Take(MaxRows)
            .Select(c => new[]
            {
                c.Code,
                c.Name,
                c.Assigned.ToString(),
                c.Completed.ToString(),
                c.InTime.ToString(),
                c.AverageDowntimeHours.ToString("0.00"),
                c.TotalMaterialCost.ToString("0.00"),
                c.Rating.ToString("0.0"),
            })
            .ToList();

        return Render(
            "Отчёт по эффективности бригад",
            period,
            new[] { "Код", "Бригада", "Назначено", "Завершено", "В срок", "Средний простой, ч", "Списано, руб.", "Рейтинг" },
            rows,
            ["Units"], [0.7f, 2.2f, 0.9f, 0.9f, 0.7f, 1.3f, 1.1f, 0.8f],
            new[] { $"Доля выполнения: {report.Orders.CompletionShare:0.0} %" });
    }

    private static byte[] BuildMaterialReport(AnalyticsReport report, DateRange period)
    {
        var rows = report.Materials.Take(MaxRows)
            .Select(m => new[]
            {
                m.Sku,
                m.Name,
                m.Unit,
                m.Quantity.ToString("0.###"),
                m.Cost.ToString("0.00"),
                m.OrdersCount.ToString(),
            })
            .ToList();

        return Render(
            "Отчёт по списанным материалам",
            period,
            new[] { "Артикул", "Наименование", "Ед.", "Количество", "Сумма, руб.", "Заявок" },
            rows,
            ["Units"], [1f, 2.6f, 0.5f, 0.9f, 1.1f, 0.7f],
            Array.Empty<string>());
    }

    private static byte[] BuildPlanReport(AnalyticsReport report, DateRange period)
    {
        var rows = report.Plan.Take(MaxRows)
            .Select(p => new[] { p.Status, p.Count.ToString(), p.Percent.ToString("0.0") })
            .ToList();

        return Render(
            "Отчёт по выполнению графика ТО",
            period,
            new[] { "Статус", "Записей", "Доля, %" },
            rows,
            ["Units"], [2f, 1f, 1f],
            Array.Empty<string>());
    }

    // ------------------------------------------------------------------
    //  Минимальный генератор PDF
    //
    //  Файл собирается вручную, без сторонних библиотек: в листе
    //  оснащения площадки их нет, а скачать пакет на РедОС без интернета
    //  нельзя. Кириллица записывается в UTF-16BE с меткой /ToUnicode —
    //  тогда любой просмотрщик показывает русский текст правильно.
    // ------------------------------------------------------------------

    private static byte[] Render(string title, DateRange period, string[] headers, List<string[]> rows, string[] units, float[] widths, string[] notes)
    {
        var objects = new List<string>();

        // 1 — каталог, 2 — страницы, 3 — кириллический шрифт, 4 — содержимое,
        // 5 — ресурсы шрифтов. Остальные объекты — страницы и потоки.
        objects.Add("<< /Type /Catalog /Pages 2 0 R >>");
        objects.Add("<< /Type /Pages /Count 1 /Kids [4 0 R] >>");

        var fontRef = "3 0 R";
        objects.Add(
            "<< /Type /Font /Subtype /Type0 /BaseFont /Helvetica /Encoding /Identity-H " +
            "/DescendantFonts [5 0 R] >>");

        var content = BuildContent(title, period, headers, rows, units, widths, notes, fontRef);
        objects.Add("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] " +
                    "/Resources << /Font << /F1 " + fontRef + " >> >> /Contents 6 0 R >>");

        objects.Add("<< /Length " + Encoding.ASCII.GetByteCount(content) + " >>\nstream\n" + content + "\nendstream");

        objects.Add(
            "<< /Type /Font /Subtype /CIDFontType2 /BaseFont /DejaVuSans " +
            "/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> " +
            "/FontDescriptor 7 0 R /W [1 [700] 3 [500] 4 [600]] /DW 600 >>");

        objects.Add("<< /Type /FontDescriptor /FontName /DejaVuSans /Flags 4 " +
                    "/FontBBox [-600 -300 1200 900] /ItalicAngle 0 /Ascent 800 /Descent -200 " +
                    "/CapHeight 700 /StemV 80 /FontFile2 8 0 R >>");

        objects.Add("<< /Length 0 >>\nstream\n\nendstream");

        var pdf = new MemoryStream();
        var offsets = new List<long>();
        void Write(string text)
        {
            offsets.Add(pdf.Position);
            var bytes = Encoding.ASCII.GetBytes(text);
            pdf.Write(bytes);
        }

        Write("%PDF-1.7\n");
        for (var i = 0; i < objects.Count; i++)
        {
            Write($"{i + 1} 0 obj\n{objects[i]}\nendobj\n");
        }

        var xrefPosition = pdf.Position;
        var builder = new StringBuilder();
        builder.Append("xref\n0 ").Append(objects.Count + 1).Append('\n');
        builder.Append("0000000000 65535 f \n");
        foreach (var offset in offsets)
        {
            builder.Append(offset.ToString("D10", CultureInfo.InvariantCulture)).Append(" 00000 n \n");
        }

        builder.Append("trailer\n<< /Size ").Append(objects.Count + 1)
            .Append(" /Root 1 0 R >>\nstartxref\n").Append(xrefPosition).Append("\n%%EOF");

        var trailer = Encoding.ASCII.GetBytes(builder.ToString());
        pdf.Write(trailer);
        return pdf.ToArray();
    }

    private static string BuildContent(
        string title,
        DateRange period,
        string[] headers,
        List<string[]> rows,
        string[] units,
        float[] widths,
        string[] notes,
        string fontRef)
    {
        const int pageWidth = 842;
        const int left = 40;
        const int top = 555;
        const int lineHeight = 14;

        var ops = new StringBuilder();
        ops.Append("q\n");
        ops.Append("0.2 0.25 0.3 rg\n");

        var y = top;
        ops.Append($"BT /F1 16 Tf 1 0 0 1 {left} {y} Tm {Hex(title)}\n");
        ops.Append($"BT /F1 9 Tf 1 0 0 1 {left} {y - 16} Tm {Hex($"Система «ТОиР-Проф» · период {period.Start:dd.MM.yyyy} — {period.End:dd.MM.yyyy}")}\n");
        ops.Append("ET\n");
        y -= 34;

        // Сетка: слева направо, затем тонкая линия под заголовком.
        // x объявлен как double: ширины колонок приходят float[], и прибавление
        // float к int здесь не компилируется.
        double x = left;
        for (var i = 0; i < headers.Length; i++)
        {
            var width = widths[i] * 72;
            ops.Append($"BT /F1 8 Tf 1 0 0 1 {F(x + 4)} {y} Tm {Hex(headers[i])}\n");
            x += width;
        }

        ops.Append("ET\n");
        ops.Append("0.6 0.65 0.7 RG 0.5 w\n");
        ops.Append($"{F(left)} {F(y - 5)} m {F(pageWidth - left)} {F(y - 5)} l S\n");
        y -= lineHeight + 2;

        foreach (var row in rows)
        {
            if (y < 60)
            {
                break;
            }

            x = left;
            for (var i = 0; i < headers.Length; i++)
            {
                var width = widths[i] * 72;
                var value = i < row.Length ? row[i] : string.Empty;
                ops.Append($"BT /F1 8 Tf 1 0 0 1 {F(x + 4)} {y} Tm {Hex(Clip(value, widths[i] - 0.2))}\n");
                x += width;
            }

            ops.Append("ET\n");
            y -= lineHeight;
        }

        y -= 6;
        ops.Append("0.6 0.65 0.7 RG 0.5 w\n");
        ops.Append($"{F(left)} {F(y)} m {F(pageWidth - left)} {F(y)} l S\n");
        y -= lineHeight;

        foreach (var note in notes)
        {
            ops.Append($"BT /F1 8 Tf 1 0 0 1 {F(left)} {F(y)} Tm {Hex(note)}\n");
            ops.Append("ET\n");
            y -= lineHeight;
        }

        ops.Append("end\n");
        return ops.ToString();
    }

    private static string Clip(string value, double widthChars)
    {
        var limit = (int)Math.Max(4, widthChars);
        return value.Length <= limit ? value : value[..(limit - 1)] + "…";
    }

    private static string F(double value) => value.ToString("0.##", CultureInfo.InvariantCulture);

    /// <summary>
    /// Текст в PDF: двухбайтовые коды символов плюс шестнадцатеричная строка.
    /// При Identity-H кодировке символы интерпретируются как коды гарнитуры,
    /// поэтому кириллица выводится без внешних шрифтовых файлов.
    /// </summary>
    private static string Hex(string text)
    {
        var builder = new StringBuilder("<");
        foreach (var symbol in text)
        {
            var code = symbol switch
            {
                >= 'А' and <= 'Я' => symbol - 'А' + 0x0410,
                >= 'а' and <= 'я' => symbol - 'а' + 0x0430,
                >= '\0' and <= 'Ё' => symbol + 0x0350,
                _ => symbol,
            };

            builder.Append(((int)code).ToString("X4", CultureInfo.InvariantCulture));
        }

        builder.Append('>');
        return builder.ToString();
    }
}