Сессия 7. Desktop-клиент: экраны · 70–150 мин

# Что делаем на этой странице

Рисуем окно: вход, список задач с фильтрами-чипами, отметка выполнения,
удаление и панель сводки. Всё это уже работает на тех же запросах API,
что и веб-клиент, поэтому здесь меняется только разметка и обработчики.

Каркас и модель представления — на [19-Avalonia-проект-и-навигация](19-Avalonia-проект-и-навигация).
На этой странице мы достраиваем `MainWindow.axaml` и его code-behind.

# Шаг 1. Экран входа

Приложение открывается на форме входа: два поля, кнопка и строка ошибки.
Поля уже заполнены демо-данными, чтобы можно было нажать «Войти» сразу.

```xml
<StackPanel Width="380" Spacing="12"
            IsVisible="{Binding !IsLoggedIn}">
  <TextBlock Text="{Binding Error}" Foreground="#C0392B"
             IsVisible="{Binding Error, Converter={x:Static StringConverters.IsNotNullOrEmpty}}" />
  <TextBox Text="{Binding Email}" Watermark="student@college.ru" />
  <TextBox Text="{Binding Password}" PasswordChar="•" />
  <Button Content="Войти" Classes="primary" Click="OnSignIn" />
</StackPanel>
```

Одна строка `IsVisible` переключает весь блок: после входа форма исчезает, и
на её месте появляется список. Отдельной страницы входа в проекте нет —
это один `Window` с двумя состояниями.

![[images/desk20-s01-login.png]]
*Форма входа: почта, пароль и кнопка «Войти», имя клиента в шапке*

# Шаг 2. Неверный пароль

Введите любой неверный пароль и нажмите «Войти». Сервер вернёт `401`, и
клиент покажет текст из поля `message` — без своих формулировок:

```csharp
if (!payload.IsSuccessStatusCode)
{
    Error = json.GetProperty("message").GetString() ?? "Не удалось войти";
    return;
}
```

![[images/desk20-s02-error.png]]
*Ошибка входа выведена красным над полями: «Неверная почта или пароль»*

Проверять пароль на клиенте не нужно: правило одно на сервере, и клиент
показывает то же сообщение, которое вернул бэкенд.

# Шаг 3. Список задач

Верните правильный пароль и нажмите «Войти». Запрос уходит на
`/api/tasks?sort=dueDate&order=asc&pageSize=50`, рядом — `/api/tasks/summary`,
поэтому в списке и в сводке всегда одни и те же цифры.

```xml
<Button Content="Все" Click="OnFilterAll" Classes="chip" />
<Button Content="Новые" Click="OnFilterNew" Classes="chip" />
<Button Content="В работе" Click="OnFilterInProgress" Classes="chip" />
<Button Content="Готово" Click="OnFilterDone" Classes="chip" />
<Button Content="Обновить" Click="OnRefresh" Classes="ghost" />
```

Карточка задачи — четыре строки: галочка, название, описание и бейджи
со статусом и приоритетом:

```xml
<CheckBox IsChecked="{Binding Done, Mode=OneWay}" Click="OnToggleDone" Tag="{Binding}" />
<TextBlock Text="{Binding Title}" FontSize="15" FontWeight="SemiBold" />
<Border Classes="badge">
  <TextBlock Text="{Binding StatusRu}" Foreground="#398411" FontSize="11" />
</Border>
```

![[images/desk20-s03-list.png]]
*Список из семи задач: у каждой карточки галочка, название, описание, бейджи и «Удалить». Справа — сводка 7 / 4 / 0*

`Mode=OneWay` у галочки означает, что сама она не пишет в модель: значение
приходит из сервера. Иначе рассинхрон — нажали, отметили, а сервер
ответил иначе, и чекбокс остался бы в неверном состоянии.

# Шаг 4. Фильтры-чипы

Фильтр — это не отдельный компонент, а значение `StatusFilter` и тот же
запрос списка. Обработчик меняет значение и перезапрашивает данные:

```csharp
private async void OnFilterNew(object? sender, RoutedEventArgs e) => await FilterAsync("new");

private async Task FilterAsync(string status)
{
    _vm.StatusFilter = status;
    await _vm.RefreshAsync();
}
```

Внутри `RefreshAsync` значение превращается в параметр запроса, поэтому
остальной код не меняется:

```csharp
var query = new List<string> { "sort=dueDate", "order=asc", "pageSize=50" };
if (!string.IsNullOrWhiteSpace(StatusFilter))
    query.Add($"status={StatusFilter}");
```

![[images/desk20-s04-filter-new.png]]
*Чип «Новые» оставил в списке только задачи со статусом «Новая», сводка при этом не изменилась*

![[images/desk20-s05-filter-done.png]]
*Чип «Готово» показал четыре выполненные задачи — цифры совпадают со сводкой*

Сводка не меняется от фильтра специально: она всегда про все задачи
пользователя. Если нужна «выборка внутри выборки», счётчики придётся
считать на сервере отдельным запросом — но в задании этого не требуется.

# Шаг 5. Отметка выполнения

Снимите галочку у задачи. Клик уходит на `PATCH /api/tasks/{id}/complete`,
после чего список перечитывается целиком — так состояние приходит из
одного источника:

```csharp
public async Task ToggleAsync(TaskRow task)
{
    await _http.PatchAsJsonAsync($"/api/tasks/{task.Id}/complete", new { done = !task.Done });
    await RefreshAsync();
}
```

![[images/desk20-s06-toggle.png]]
*Задача вернулась в статус «В работе», счётчик «Выполнено» уменьшился с 4 до 3*

Обработчик достаёт строку из `Tag` — того же элемента, на котором
произошёл клик:

```csharp
private async void OnToggleDone(object? sender, RoutedEventArgs e)
{
    if (sender is CheckBox { Tag: TaskRow task }) await _vm.ToggleAsync(task);
}
```

# Шаг 6. Удаление

Кнопка «Удалить» в карточке отправляет `DELETE /api/tasks/{id}` и так же
перечитывает список:

```csharp
public async Task DeleteAsync(TaskRow task)
{
    await _http.DeleteAsync($"/api/tasks/{task.Id}");
    await RefreshAsync();
}
```

![[images/desk20-s07-delete.png]]
*Задача исчезла из списка, «Всего задач» стало 6 — счётчик обновился вместе со строкой*

Удаление происходит сразу, без подтверждения. Для на отборе этого
достаточно, но в рабочем приложении перед `DELETE` стоит показывать диалог
с вопросом — об этом ниже.

# Шаг 7. Панель сводки

Справа от списка — три числа из `GET /api/tasks/summary`:

```xml
<Border Background="#FFFFFF" CornerRadius="12" Padding="18" VerticalAlignment="Top">
  <TextBlock Text="Сводка" FontSize="16" FontWeight="SemiBold" />
  <TextBlock Text="Всего задач" Foreground="#6B6B6B" />
  <TextBlock Text="{Binding Total}" FontWeight="Bold" Foreground="#398411" />
  <TextBlock Text="Выполнено" Foreground="#6B6B6B" />
  <TextBlock Text="{Binding Done}" FontWeight="Bold" />
  <TextBlock Text="Просрочено" Foreground="#6B6B6B" />
  <TextBlock Text="{Binding Overdue}" FontWeight="Bold" />
</Border>
```

Счётчики только читают ответ сводки — считать их вручную на клиенте нельзя,
тогда как после любой операции числа разойдутся с сервером.

# Что добавить сверх эталона

Раздел «Desktop-клиент» просит 3–4 экрана и хранение токена между запусками.
В эталоне окно одно, токен живёт в памяти процесса, поэтому три вещи
дописываются руками — каждая независима от остальных:

- **Форма создания задачи.** По клику «Новая задача» показывается
  `Window` с полями `title`, `description`, `status`, `priority`, `dueDate`,
  а `POST /api/tasks` добавляет строку в тот же `Tasks`.
- **Карточка задачи.** Отдельное окно с деталями и редактированием через
  `PUT /api/tasks/{id}` — сейчас в списке видны только название, описание и
  бейджи.
- **Сохранение токена.** Токен из ответа `login` кладётся в файл
  `session.json` в каталоге данных приложения, при старте читается обратно
  и подставляется в заголовок `Authorization`. На РедОС это
  `~/.local/share/TaskPlanner/session.json`, на Windows — `%APPDATA%\TaskPlanner`.
- **Подтверждение удаления.** Перед `DELETE` показывается диалог
  «Удалить задачу?». Отмена ничего не отправляет.

Токен в файле — компромисс для учебного проекта: в рабочем приложении его
нужно шифровать или хранить в системном хранилище секретов. Сам формат
ответа при этом не меняется — это тот же контракт, что и в веб-клиенте.

# Коммит

```bash
git add src/desktop
git commit -m "Desktop-клиент: вход, список с фильтрами, отметка выполнения, удаление, сводка"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| Форма входа не исчезает после входа | свойство называется `IsLoggedIn`, а в разметке `{Binding !IsLoggedIn}` |
| Ошибка не показывается | у `TextBlock` с ошибкой должен быть `IsVisible` с `StringConverters.IsNotNullOrEmpty` |
| Фильтр-чип ничего не меняет | в `RefreshAsync` проверка `StatusFilter` добавляет параметр `status` |
| Галочка не отправляет запрос | у чекбокса нужен `Tag="{Binding}"`, иначе обработчик не найдёт строку |
| Чекбокс «щёлкает» назад | у него стоит `IsChecked="{Binding Done, Mode=OneWay}"` — значение приходит с сервера |
| Счётчики в сводке не меняются | счётчики читаются из ответа `summary`, а не считаются в клиенте |
| `404` на `PATCH` или `DELETE` | в пути должен быть префикс `/api` и id задачи: `/api/tasks/{id}/complete` |