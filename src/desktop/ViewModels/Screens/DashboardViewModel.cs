using CommunityToolkit.Mvvm.Input;
using System.Collections.Generic;
using System;
using System.Collections.ObjectModel;
using System.Globalization;
using System.Threading;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using ToirProf.Desktop.Models;
using ToirProf.Desktop.Services;

namespace ToirProf.Desktop.ViewModels.Screens;

/// <summary>
/// Дашборд мастера: шесть показателей за период и четыре среза.
///
/// Первый экран, который мастер видит после входа, поэтому он должен
/// собираться одним запросом и не требовать прокрутки: всё, что ниже
/// первого экрана, на демонстрации никто не увидит.
/// </summary>
public sealed partial class DashboardViewModel : PageViewModel
{
    public DashboardViewModel(ApiClient api, ToastService toasts, FileLogger log)
        : base(api, toasts, log)
    {
        // Период подставляем сразу: пустое поле выбора даты показывает
        // английские подсказки «day / month / year», и на снимке экрана
        // это выглядит как недоделанный фильтр. Те же границы, что
        // сервер берёт по умолчанию, — последние 30 дней.
        To = DateOnly.FromDateTime(DateTime.Today);
        From = To.Value.AddDays(-30);
    }

    /// <summary>Шесть карточек — по одной на показатель из задания.</summary>
    public ObservableCollection<MetricCard> Cards { get; } = [];

    public ObservableCollection<WorkshopSlice> ByWorkshop { get; } = [];

    public ObservableCollection<StatusSlice> ByStatus { get; } = [];

    public ObservableCollection<MonthSlice> ByMonth { get; } = [];

    [ObservableProperty]
    private DateOnly? _from;

    [ObservableProperty]
    private DateOnly? _to;

    [ObservableProperty]
    private string _periodCaption = "за последние 30 дней";

    public override async Task RefreshAsync()
    {
        await RunLoadAsync("Считаем показатели цеха…", async ct =>
        {
            var path = $"/api/dashboard/summary?from={Fmt(From)}&to={Fmt(To)}";
            var result = await Api!.GetAsync<DashboardSummary>(path, ct);

            if (!result.Success || result.Data is null)
            {
                ErrorText = result.Message;
                OnPropertyChanged(nameof(ErrorText));
                Toasts!.Warn(result.Message);
                return;
            }

            Fill(result.Data);
        });
    }

    private void Fill(DashboardSummary data)
    {
        Cards.Clear();
        Cards.Add(new MetricCard("Заявок за период", data.TotalOrders.ToString(CultureInfo.InvariantCulture), "все"));
        Cards.Add(new MetricCard("В работе", data.InProgress.ToString(CultureInfo.InvariantCulture), "требуют внимания"));
        Cards.Add(new MetricCard("Завершено", data.Completed.ToString(CultureInfo.InvariantCulture), "подтверждено"));
        Cards.Add(new MetricCard("Средний простой", $"{data.AverageDowntimeHours:0.0} ч", "на заявку"));
        Cards.Add(new MetricCard("Доля аварийных", $"{data.EmergencyShare:0.0}%", "от всех заявок"));
        Cards.Add(new MetricCard("План ТО выполнен", $"{data.MaintenancePlanShare:0.0}%", "по графику"));

        ByWorkshop.Clear();
        foreach (var row in data.ByWorkshop)
        {
            ByWorkshop.Add(row);
        }

        ByStatus.Clear();
        foreach (var row in data.ByStatus)
        {
            ByStatus.Add(row);
        }

        ByMonth.Clear();
        foreach (var row in data.ByMonth)
        {
            ByMonth.Add(row);
        }

        PeriodCaption = $"{data.PeriodFrom:dd.MM.yyyy} — {data.PeriodTo:dd.MM.yyyy}";
        Log?.Info($"Дашборд: заявок {data.TotalOrders}, аварийных {data.EmergencyShare:0.0}%, простой {data.AverageDowntimeHours:0.0} ч");
    }

    /// <summary>
    /// Дата в формате API. Пустая дата — пустая строка, а не «01.01.0001»:
    /// сервер подставит значение по умолчанию.
    /// </summary>
    private static string Fmt(DateOnly? value) =>
        value is null ? string.Empty : value.Value.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
}

/// <summary>Карточка показателя: подпись, значение и пояснение под ним.</summary>
public sealed record MetricCard(string Title, string Value, string Hint);
