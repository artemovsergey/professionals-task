using CommunityToolkit.Mvvm.Input;
using System.Collections.Generic;
using System;
using System.Collections.ObjectModel;
using System.Threading;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using ToirProf.Desktop.Models;
using ToirProf.Desktop.Services;

namespace ToirProf.Desktop.ViewModels.Screens;

/// <summary>
/// Бригады: состав и загрузка. Экран доступен администратору и
/// руководителю — мастер в меню его не видит вовсе.
/// </summary>
public sealed partial class CrewsViewModel : PageViewModel
{
    public CrewsViewModel(ApiClient api, ToastService toasts, FileLogger log)
        : base(api, toasts, log)
    {
        SortField = "name";
        SortOrder = "asc";
    }

    public ObservableCollection<CrewRow> Rows { get; } = [];

    [ObservableProperty]
    private bool _includeInactive;

    public override async Task RefreshAsync()
    {
        await RunLoadAsync("Загружаем бригады…", async ct =>
        {
            var path =
                $"/api/crews?search={Uri.EscapeDataString(SearchTextOrEmpty)}" +
                $"&includeInactive={(IncludeInactive ? "true" : "false")}" +
                $"&page={Page}&pageSize={PageSize}";

            var result = await Api!.GetAsync<PagedResult<CrewRow>>(path, ct);

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

    /// <summary>
    /// Рейтинг в реестре не показываем: список приходит коротким
    /// (код, название, число членов), а формулу рейтинга держит сервер —
    /// рисовать нули там, где данных нет, значит врать пользователю.
    /// </summary>
    public static string RatingCaption(CrewRow row) => row.StateCaption;
}
