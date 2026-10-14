using System;
using Avalonia.Controls;
using Avalonia.Controls.Templates;
using ToirProf.Desktop.ViewModels.Screens;

namespace ToirProf.Desktop;

/// <summary>
///     Подставляет окно экрана по имени его вьюмодели.
///     Вьюмодели лежат в <c>ToirProf.Desktop.ViewModels.Screens</c>,
///     окна — в <c>ToirProf.Desktop.Views.Screens</c>, поэтому правило
///     подстановки одно: заменить последний сегмент пространства имён
///     и суффикс <c>ViewModel</c> на <c>View</c>.
///     Оболочке не нужно знать, какой экран открыт: она отдаёт вьюмодель
///     в <c>ContentControl</c>, а шаблон находит окно сам.
/// </summary>
public class ViewLocator : IDataTemplate
{
    private const string ViewModelsNamespace = "ToirProf.Desktop.ViewModels.Screens.";
    private const string ViewsNamespace = "ToirProf.Desktop.Views.Screens.";

    public Control? Build(object? param)
    {
        if (param is null)
        {
            return null;
        }

        var name = param.GetType().FullName;
        if (name is null || !name.StartsWith(ViewModelsNamespace, StringComparison.Ordinal))
        {
            return new TextBlock
            {
                Text = "Экран без представления: " + param.GetType().Name,
                Classes = { "muted" },
            };
        }

        // ToirProf.Desktop.ViewModels.Screens.DashboardViewModel
        //   -> ToirProf.Desktop.Views.Screens.DashboardView
        var target = ViewsNamespace
            + name[ViewModelsNamespace.Length..].Replace("ViewModel", "View", StringComparison.Ordinal);
        var type = Type.GetType(target);

        if (type is null)
        {
            return new TextBlock
            {
                Text = "Не найдено представление: " + target,
                Classes = { "muted" },
            };
        }

        return (Control)Activator.CreateInstance(type)!;
    }

    /// <summary>
    ///     Шаблон применяется только к экранам: у оболочки и служебных
    ///     моделей своих окон нет, подменять их нечем.
    /// </summary>
    public bool Match(object? data)
    {
        return data is PageViewModel;
    }
}
