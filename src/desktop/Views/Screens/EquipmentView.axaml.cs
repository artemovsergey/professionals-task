using Avalonia.Controls;
using Avalonia.Input;
using ToirProf.Desktop.ViewModels.Screens;

namespace ToirProf.Desktop.Views.Screens;

public partial class EquipmentView : UserControl
{
    public EquipmentView()
    {
        InitializeComponent();
    }

    /// <summary>
    /// Enter в поле поиска запускает ту же команду, что и кнопка «Найти»:
    /// ждать нажатия мышью после ввода неудобно.
    /// </summary>
    private void OnSearchKey(object? sender, KeyEventArgs e)
    {
        if (e.Key != Key.Enter || DataContext is not EquipmentViewModel vm)
        {
            return;
        }

        e.Handled = true;
        vm.SearchCommand.Execute(null);
    }
}
