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
/// Материалы и ЗИП: остаток, приход и дефицит. Отдельный фильтр
/// «только дефицитные» — на демонстрации его включают первым, потому
/// что именно дефицит объясняет, почему ремонт встал.
/// </summary>
public sealed partial class MaterialsViewModel : PageViewModel
{
    public MaterialsViewModel(ApiClient api, ToastService toasts, FileLogger log)
        : base(api, toasts, log)
    {
        SortField = "sku";
        SortOrder = "asc";
    }

    public ObservableCollection<MaterialRow> Rows { get; } = [];

    [ObservableProperty]
    private bool _includeInactive;

    [ObservableProperty]
    private bool _onlyShortage;

    [ObservableProperty]
    private MaterialRow? _selected;

    [ObservableProperty]
    private decimal _receiptQuantity;

    public override async Task RefreshAsync()
    {
        await RunLoadAsync("Загружаем склад ЗИП…", async ct =>
        {
            var path =
                $"/api/materials?search={Uri.EscapeDataString(SearchTextOrEmpty)}" +
                $"&includeInactive={(IncludeInactive ? "true" : "false")}" +
                $"&onlyShortage={(OnlyShortage ? "true" : "false")}" +
                $"&page={Page}&pageSize={PageSize}";

            var result = await Api!.GetAsync<PagedResult<MaterialRow>>(path, ct);

            if (!result.Success || result.Data is null)
            {
                ErrorText = result.Message;
                OnPropertyChanged(nameof(ErrorText));
                Toasts!.Warn(result.Message);
                return;
            }

            Rows.Clear();
            foreach (var row in result.Data.Items)
            {
                Rows.Add(row);
            }

            Total = result.Data.Total;
            OnPropertyChanged(nameof(TotalPages));
            OnPropertyChanged(nameof(CanGoNext));
            OnPropertyChanged(nameof(CanGoPrevious));
            OnPropertyChanged(nameof(PageCaption));
        });
    }

    [RelayCommand]
    private void Select(MaterialRow? row)
    {
        Selected = row;
        ReceiptQuantity = 0m;
    }

    /// <summary>
    /// Приход на склад. Остаток меняется только здесь; расход делает
    /// сервер при списании на заявку.
    /// </summary>
    [RelayCommand]
    private async Task ReceiveAsync()
    {
        if (Selected is null)
        {
            Toasts!.Warn("Выберите материал.");
            return;
        }

        if (ReceiptQuantity <= 0m)
        {
            Toasts!.Warn("Количество должно быть больше нуля.");
            return;
        }

        await RunLoadAsync("Оформляем приход…", async ct =>
        {
            var result = await Api!.PostAsync<MaterialRow>(
                $"/api/materials/{Selected.Id}/receipt",
                new { quantity = ReceiptQuantity },
                ct);

            if (!result.Success || result.Data is null)
            {
                Toasts!.Error(result.Message);
                return;
            }

            Selected = result.Data;
            OnPropertyChanged(nameof(Selected));
            Toasts!.Success($"Принято {ReceiptQuantity.ToString("0.##", CultureInfo.InvariantCulture)}: остаток {result.Data.StockCaption}.");
            ReceiptQuantity = 0m;
            await RefreshAsync();
        });
    }

    [RelayCommand]
    private async Task ShowShortagesAsync()
    {
        OnlyShortage = true;
        Page = 1;
        await RefreshAsync();
    }
}
