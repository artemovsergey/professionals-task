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
/// График планового ТО. Ключевое действие экрана — отметить выполнение:
/// сервер считает следующую плановую дату функцией базы, клиент только
/// отправляет дату выполнения и фактическую стоимость.
/// </summary>
public sealed partial class ScheduleViewModel : PageViewModel
{
    public ScheduleViewModel(ApiClient api, ToastService toasts, FileLogger log)
        : base(api, toasts, log)
    {
        SortField = "plannedDate";
        SortOrder = "asc";

        // Период графика задан сразу, иначе пустые поля даты рисуют
        // английские подсказки вместо чисел.
        To = DateOnly.FromDateTime(DateTime.Today);
        From = To.Value.AddDays(-30);
    }

    public ObservableCollection<ScheduleRow> Rows { get; } = [];

    public IReadOnlyList<string> StatusOptions { get; } = ["Запланировано", "Выполнено", "Просрочено"];

    [ObservableProperty]
    private string? _statusFilter;

    [ObservableProperty]
    private DateOnly? _from;

    [ObservableProperty]
    private DateOnly? _to;

    /// <summary>
    /// Выбранная запись графика. Список и карточка выполнения —
    /// две разные вещи: мастер может отмечать выполнение, не
    /// переключаясь на другую запись.
    /// </summary>
    [ObservableProperty]
    private ScheduleRow? _selected;

    [ObservableProperty]
    private DateOnly? _completedDate;

    [ObservableProperty]
    private decimal? _actualCost;

    public override async Task RefreshAsync()
    {
        await RunLoadAsync("Загружаем график ТО…", async ct =>
        {
            var path =
                $"/api/maintenance-schedule?from={Fmt(From)}&to={Fmt(To)}" +
                $"&status={Uri.EscapeDataString(StatusFilter ?? string.Empty)}";

            var result = await Api!.GetAsync<List<ScheduleRow>>(path, ct);

            if (!result.Success || result.Data is null)
            {
                ErrorText = result.Message;
                OnPropertyChanged(nameof(ErrorText));
                Toasts!.Warn(result.Message);
                return;
            }

            Rows.Clear();
            foreach (var row in result.Data)
            {
                Rows.Add(row);
            }

            Total = result.Data.Count;
            OnPropertyChanged(nameof(TotalPages));
            OnPropertyChanged(nameof(PageCaption));
        });
    }

    [RelayCommand]
    private void Select(ScheduleRow? row)
    {
        Selected = row;
        if (row is not null)
        {
            // Дата выполнения по умолчанию — плановая: мастер чаще всего
            // отмечает ТО в срок, и лишний клик по календарю не нужен.
            CompletedDate = row.PlannedDate;
            ActualCost = row.ActualCost;
        }
    }

    /// <summary>
    /// Отметить выполнение. Сервер проверит, что дата не раньше ввода
    /// оборудования в эксплуатацию, и сам посчитает следующую дату.
    /// </summary>
    [RelayCommand]
    private async Task CompleteAsync()
    {
        if (Selected is null)
        {
            Toasts!.Warn("Сначала выберите запись графика.");
            return;
        }

        if (CompletedDate is null)
        {
            Toasts!.Warn("Укажите дату выполнения.");
            return;
        }

        await RunLoadAsync("Отмечаем выполнение…", async ct =>
        {
            var result = await Api!.PostAsync<ScheduleRow>(
                $"/api/maintenance-schedule/{Selected.Id}/complete",
                new
                {
                    completedDate = CompletedDate.Value.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
                    actualCost = ActualCost,
                },
                ct);

            if (!result.Success || result.Data is null)
            {
                Toasts!.Error(result.Message);
                return;
            }

            Toasts!.Success(
                $"ТО выполнено. Следующая дата: {result.Data.NextPlannedDate?.ToString("dd.MM.yyyy") ?? "не назначена"}");
            await RefreshAsync();
        });
    }

    /// <summary>Вернуть запись в план — снимает отметку о выполнении.</summary>
    [RelayCommand]
    private async Task ReturnToPlanAsync()
    {
        if (Selected is null)
        {
            return;
        }

        await RunLoadAsync("Возвращаем запись в план…", async ct =>
        {
            var result = await Api!.PostAsync<ScheduleRow>(
                $"/api/maintenance-schedule/{Selected.Id}/plan",
                new { },
                ct);

            if (!result.Success)
            {
                Toasts!.Error(result.Message);
                return;
            }

            Toasts!.Success("Запись возвращена в план.");
            await RefreshAsync();
        });
    }

    private static string Fmt(DateOnly? value) =>
        value is null ? string.Empty : value.Value.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
}
