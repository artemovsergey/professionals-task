# -*- coding: utf-8 -*-
"""Данные wiki-страниц системы «ТОиР-Проф».

Один источник правды для `gen_pages.py`: список спринтов и список страниц.
Правьте только этот файл — страницы, Home.md и боковое меню пересобираются
командой `python3 tools/wiki/gen_pages.py`.

Соглашения:
  * `n`     — сквозной номер страницы, 1..54;
  * `png`   — имя файла скриншота латиницей, итоговое имя `images/<NN>-<png>.png`;
  * `gif`   — имя файла гифки латиницей, итоговое имя `gifs/<NN>-<gif>.gif`;
  * `cap`   — подпись к картинке, она же alt-текст;
  * `check` — команда, которая доказывает, что страница выполнена;
  * `commit`— сообщение коммита в конце страницы.
"""

SPRINTS = [
    dict(id=0, name="Подготовка: окружение и репозиторий",
         what="Инструменты, PostgreSQL, Git, структура проекта",
         task="—", pts="—", pages=(1, 2)),
    dict(id=1, name="Системный анализ: 3 UML-диаграммы",
         what="Use Case, Activity, Class + обоснование",
         task="6", pts="≈13", pages=(3, 5)),
    dict(id=2, name="БД: модель данных, таблицы, связи",
         what="Нормализация, ER-диаграмма, schema.sql, seed.sql",
         task="1", pts="≈8", pages=(6, 7)),
    dict(id=3, name="БД: ограничения целостности",
         what="UNIQUE, CHECK, ENUM, ON DELETE",
         task="1", pts="≈2,4", pages=(8, 9)),
    dict(id=4, name="БД: триггеры, функции, процедура",
         what="2 триггера, 2 функции, 1 процедура",
         task="1", pts="≈2,5", pages=(10, 11)),
    dict(id=5, name="API: каркас, обёртка ответа, ошибки",
         what="Solution, DbContext, ApiResponse, коды ошибок",
         task="2", pts="≈1,4", pages=(12, 13)),
    dict(id=6, name="API: аутентификация, JWT, RBAC",
         what="Регистрация, вход, роли и доступ",
         task="2", pts="≈1", pages=(14, 15)),
    dict(id=7, name="API: оборудование и справочник видов ТО",
         what="CRUD оборудования, справочник типов обслуживания",
         task="2", pts="≈1,7", pages=(16, 17)),
    dict(id=8, name="API: график ТО и генерация заявок",
         what="Плановый график, номер заявки Z-YYYY-XXXX",
         task="2", pts="≈1,4", pages=(18, 19)),
    dict(id=9, name="API: заявки — жизненный цикл",
         what="Создание, чтение, назначение бригады, завершение",
         task="2", pts="≈2,3", pages=(20, 21)),
    dict(id=10, name="API: бригады, материалы, списание",
         what="CRUD бригад, ЗИП, списание материалов в заявку",
         task="2", pts="≈0,9", pages=(22, 23)),
    dict(id=11, name="API: аналитика, дашборд, экспорт",
         what="KPI, срезы, рейтинг бригад, PDF и временные ссылки",
         task="2", pts="≈1,6", pages=(24, 25)),
    dict(id=12, name="Desktop: каркас, навигация, авторизация",
         what="Проект Avalonia, оболочка, вход по ролям",
         task="3", pts="≈3", pages=(26, 28)),
    dict(id=13, name="Desktop: дашборд мастера",
         what="Показатели, таблицы, поиск, сортировка, пагинация",
         task="3", pts="≈1,9", pages=(29, 30)),
    dict(id=14, name="Desktop: оборудование и график ТО",
         what="Экран «Оборудование цеха» и «График ТО»",
         task="3", pts="≈3,4", pages=(31, 32)),
    dict(id=15, name="Desktop: заявки, бригады, материалы, отчёты",
         what="Экран «Заявки», справочники, отчёты, офлайн-кэш",
         task="3", pts="≈6", pages=(33, 35)),
    dict(id=16, name="Web: каркас, авторизация, оболочка",
         what="Проект React, вход, каркас с навигацией",
         task="4", pts="≈2,7", pages=(36, 37)),
    dict(id=17, name="Web: дашборд руководителя",
         what="6 KPI-карточек, графики, топ-5 простоев, последние заявки",
         task="4", pts="≈3,6", pages=(38, 39)),
    dict(id=18, name="Web: аналитика и графики",
         what="Фильтры, 5 блоков аналитики, экспорт PNG/CSV/PDF",
         task="4", pts="≈5,9", pages=(40, 42)),
    dict(id=19, name="Web: реестры, справочники, realtime",
         what="SSE и polling, реестры, справочники, поиск, ошибки",
         task="4", pts="≈5", pages=(43, 45)),
    dict(id=20, name="Unit-тесты Desktop (5 тестов)",
         what="Проект xUnit и 5 модульных тестов по ТЗ",
         task="5", pts="≈8", pages=(46, 47)),
    dict(id=21, name="Документация: Swagger + развёртывание",
         what="Документация API, инструкция по развёртыванию",
         task="7", pts="≈3,3", pages=(48, 49)),
    dict(id=22, name="Руководство пользователя",
         what="Инструкция для мастера и руководителя",
         task="7", pts="≈1,7", pages=(50, 51)),
    dict(id=23, name="Защита: презентация и выступление",
         what="12–15 слайдов, речь 5–7 минут, ответы экспертам",
         task="7", pts="≈3,5", pages=(52, 53)),
    dict(id=24, name="Итоговая проверка по критериям",
         what="Чек-лист из 200+ критериев перед защитой",
         task="—", pts="—", pages=(54, 54)),
]


def S(t, m, b, f=None, code=None, lang="bash", hint="Команда",
      note=None, png=None, gif=None, cap=None):
    """Описание одного шага страницы."""
    step = {"t": t, "m": m, "b": b}
    if f:
        step["f"] = f
    if code:
        step["code"] = code
        step["lang"] = lang
        step["path_hint"] = hint
    if note:
        step["note"] = note if isinstance(note, list) else [note]
    if png:
        step["png"] = png
    if gif:
        step["gif"] = gif
    if cap:
        step["cap"] = cap
    return step


def P(n, ti, sp, intro, res, crit, files, steps, fb, check, commit):
    """Описание одной страницы wiki."""
    return dict(n=n, ti=ti, sp=sp, intro=intro, res=res, crit=crit,
                files=files, steps=steps, fb=fb, check=check, commit=commit)


PAGES = []

# === BLOCK-A: спринты 0–4, страницы 1–11 ===

PAGES.append(P(
    1, "Установка-инструментов", 0,
    "Проверяем, что инструменты установлены и версии подходящие. Один несовпадающий "
    "пункт на площадке стоит часа: проект не собирается, и вы теряете время на поиск "
    "причины вместо работы.",
    "Все инструменты установлены, версии записаны в `README.md`, PostgreSQL отвечает "
    "на `SELECT version()`.",
    [("Подготовка среды", "Не оценивается напрямую, но без неё не выполняются все остальные критерии")],
    ["README.md"],
    [
        S("Сверяем версии", 15,
          "Выполните в терминале четыре команды и сравните ответ с таблицей. "
          "Если версия ниже нужной — дальше идти бессмысленно: сборка упадёт на первой странице API.",
          code="dotnet --list-sdks\nnode --version\nnpm --version\npsql -V\ngit --version",
          png="versions", gif="versions-run", cap="Все команды ответили, версии в допустимых диапазонах",
          note=["`dotnet --list-sdks` показывает все установленные SDK — полезно, когда их несколько "
                "и нужно понять, какой используется по умолчанию."]),
        S("Ставим .NET SDK 10", 20,
          "Основной стек — **.NET 10**. Ставим SDK нативно, без Visual Studio.",
          code="# РедОС 8.0\nsudo dnf install -y dotnet-sdk-10.0\n\n# Windows (тренировка)\nwinget install Microsoft.DotNet.SDK.10",
          png="dotnet-install", cap="Версия 10.x установлена, dotnet --version отвечает",
          note=["Если `dotnet --version` показал 8.0 или 9.0 — проект не соберётся. "
                "Именно .NET 10 указан в задании, более старая версия не принимается."]),
        S("Ставим PostgreSQL 16", 20,
          "База данных ставится нативно через `dnf`. Docker на площадке может отсутствовать — "
          "рассчитывайте только на локальную установку.",
          code="sudo dnf install -y postgresql-server postgresql-contrib\nsudo postgresql-setup --initdb\nsudo systemctl enable --now postgresql\npsql -V",
          png="postgres-install", cap="Служба postgresql активна, psql -V показывает 16.x",
          note=["`postgresql-setup --initdb` выполняется один раз — при повторном запуске "
                "он скажет, что кластер уже инициализирован. Это нормально."]),
        S("Ставим Node.js и инструменты", 15,
          "Node.js нужен для Web-клиента. DBeaver, Postman и Draw.io ставятся вручную — "
          "ссылки на загрузку лежат в официальных сайтах проектов.",
          code="node --version\nnpm --version\n# dbeaver.org — DBeaver Community\n# getpostman.com — Postman\n# app.diagrams.net — Draw.io (работает в браузере)",
          png="tools", cap="DBeaver, Postman и Draw.io запускаются на РедОС",
          note=["Draw.io не требует установки: открывается в браузере по адресу "
                "app.diagrams.net и умеет сохранять файл `.drawio`."]),
    ],
    [("`dotnet: command not found`", "не прописан `PATH`; перезайдите в терминал после установки"),
     ("`dotnet --version` показывает 9.0", "установлен старый SDK, нужен 10.0 — вернитесь к шагу 2"),
     ("`psql` есть, но не подключается", "запустите службу: `sudo systemctl start postgresql`"),
     ("`node: command not found`", "Node.js не установлен или не прописан в `PATH`")],
    "dotnet --list-sdks && psql -V && node --version && git --version",
    "chore: подготовить окружение и зафиксировать версии инструментов",
))

PAGES.append(P(
    2, "Репозиторий-и-структура-проекта", 0,
    "Разворачиваем репозиторий на рабочей машине и создаём каркас каталогов. "
    "Пустая структура, созданная один раз, избавляет от вопросов «куда класть файл» "
    "во всех следующих спринтах.",
    "Репозиторий склонирован, каталоги созданы, база `toirprof` доступна из DBeaver.",
    [("Подготовка среды", "Не оценивается напрямую, но без неё не выполняются все остальные критерии")],
    ["db/", "db/erd/", "src/api/", "src/desktop/", "src/web/", "src/Tests/",
     "postman/", "docs/diagrams/", "docs/screenshots/"],
    [
        S("Клонируем репозиторий", 15,
          "Репозиторий задания хранится на Git-сервере. Склонируйте его и проверьте "
          "ветку — она должна быть `main`.",
          code="git clone <адрес-репозитория>\ncd professionals-task\ngit status\ngit branch --show-current",
          png="clone", gif="clone-run", cap="Репозиторий склонирован, ветка main",
          note=["Если клон идёт по HTTPS и сервер спрашивает логин — используйте "
                "персональный токен доступа вместо пароля."]),
        S("Создаём структуру каталогов", 20,
          "Создайте каталоги проекта одной командой. Пустые каталоги Git не хранит, "
          "поэтому в каждом кладём `.gitkeep`.",
          code="mkdir -p db/erd docs/diagrams docs/screenshots postman \\\n         src/api src/desktop src/web src/Tests\nfor d in db db/erd docs/diagrams docs/screenshots postman \\\n         src/api src/desktop src/web src/Tests; do touch \"$d/.gitkeep\"; done\nfind . -type d -not -path './.git*' | sort",
          png="structure", gif="structure-run", cap="Каркас каталогов создан, .gitkeep на месте",
          note=["Без `.gitkeep` пустой каталог не попадёт в коммит — на другой машине "
                "он просто не появится."]),
        S("Создаём базу и пользователя", 25,
          "Создайте роль и базу данных для приложения. Один пользователь — одно приложение, "
          "чтобы не зависеть от прав суперпользователя.",
          code="sudo -u postgres psql -c \"CREATE ROLE toirprof LOGIN PASSWORD 'toirprof';\"\nsudo -u postgres psql -c 'CREATE DATABASE toirprof OWNER toirprof;'\npsql -h 127.0.0.1 -U toirprof -d toirprof -c '\\conninfo'",
          png="db-create", gif="db-create-run", cap="База toirprof создана, подключение успешно",
          note=["`\\conninfo` показывает, к какой базе вы фактически подключены. "
                "Если в строке `Database:` пусто — вы подключились не туда."]),
        S("Подключаем DBeaver", 20,
          "Создайте подключение к PostgreSQL в DBeaver: хост `127.0.0.1`, порт `5432`, "
          "база `toirprof`, пользователь `toirprof`. Все скриншоты базы в wiki сделаны именно так.",
          code="DBeaver → New Database Connection → PostgreSQL\nHost: 127.0.0.1   Port: 5432\nDatabase: toirprof   User: toirprof   Password: toirprof\nTest Connection → Finish",
          png="dbeaver-connect", cap="Соединение с базой toirprof установлено, виден пустой public",
          note=["Сохраняйте пароль: DBeaver спросит его при каждом запуске схемы, "
                "а на площадке вводить пароль вручную неудобно."]),
    ],
    [("`psql: FATAL: role ... does not exist`", "роль не создана — повторите шаг 3 целиком"),
     ("`could not connect to server`", "служба PostgreSQL не запущена: `sudo systemctl start postgresql`"),
     ("Каталоги пропали после `git pull`", "забыли `.gitkeep` — вернитесь к шагу 2"),
     ("DBeaver: `Connection refused`", "проверьте `psql -h 127.0.0.1 -U toirprof -d toirprof -c 'SELECT 1;'`")],
    "git status --short && psql -h 127.0.0.1 -U toirprof -d toirprof -c '\\l toirprof'",
    "chore: создать структуру каталогов и базу данных toirprof",
))
# === BLOCK-B: страницы 3–11, спринты 1–4 ===

PAGES.append(P(
    3, "Use-Case-диаграмма", 1,
    "Рисуем диаграмму вариантов использования: кто и что может делать с системой. "
    "Это первая из трёх обязательных UML-диаграмм и самая дорогая по баллам.",
    "В `docs/diagrams/` лежат `01-usecase.png`, `01-usecase.svg`, исходник `01-usecase.drawio` "
    "и обоснование в `README.md`.",
    [("А. Диаграмма вариантов использования", "≈5,15 балла — второй по стоимости критерий после Desktop")],
    ["docs/diagrams/01-usecase.png", "docs/diagrams/01-usecase.svg",
     "docs/diagrams/01-usecase.drawio", "docs/diagrams/README.md"],
    [
        S("Определяем актёров и границу системы", 20,
          "Выпишите на лист всех, кто взаимодействует с системой, и разделите на две группы: "
          "внешние (вне границы) и внутренние (внутри границы системы). Начните с текста задания — "
          "там перечислены роли мастера, руководителя, администратора и члена бригады.",
          code="Актёры:\n  Мастер          — создаёт и закрывает заявки, работает с графиком ТО\n  Руководитель    — смотрит аналитику, KPI, отчёты\n  Администратор  — ведёт справочники, пользователей, бригады\n  Член бригады    — получает заявку, отмечает выполнение\n  Система оповещения — внешний получатель уведомлений",
          png="actors", cap="Пять актёров, граница системы обведена пунктиром",
          note=["Актёров нельзя придумывать: каждый должен встречаться в тексте задания. "
                "Иначе на защите эксперт спросит, откуда взялся «клиент веб-кабинета»."]),
        S("Рисуем варианты использования", 30,
          "Откройте app.diagrams.net, выберите шаблон **Use Case Diagram**, "
          "разместите овалы вариантов внутри границы. Каждый вариант — глаголная фраза: "
          "«Создать заявку», «Закрыть заявку», «Получить отчёт».",
          code="Варианты использования:\n  Общие:        Авторизоваться в системе\n  Мастер:       Создать заявку на ремонт\n                Назначить бригаду на заявку\n                Закрыть заявку\n                Внести списание материалов\n  Руководитель: Просмотреть дашборд\n                Сформировать отчёт за период\n  Администратор: Добавить оборудование\n                Изменить вид ТО\n                Завести пользователя\n  Член бригады:  Получить назначенные заявки",
          png="usecase-shapes", gif="usecase-draw", cap="18 вариантов использования, 5 актёров, граница на месте",
          note=["Не рисуйте варианты, которых нет в задании. Лишний «Просмотр профиля» "
                "эксперт засчитает как шум, а не как полноту."]),
        S("Добавляем связи include и extend", 20,
          "Связь **«include»** — вариант всегда вызывает другой (обязательная часть). "
          "Связь **«extend»** — вариант добавляется к другому только при условии (необязательный).",
          code="«Закрыть заявку» ..> «Внести списание материалов»   (extend, [использованы ЗИП])\n«Закрыть заявку» ..> «Сформировать отчёт о выполнении»     (include)\n«Создать заявку на ремонт» ..> «Авторизоваться в системе»     (include)\n«Просмотреть дашборд»      ..> «Просмотреть аналитику»        (include)",
          png="usecase-relations", cap="Связи include и extend подписаны, стрелки направлены от вызывающего",
          note=["Подпись «extend» пишется в квадратных скобках: `..> [использованы ЗИП]`. "
                "Без скобок связь считается неподписанной."]),
        S("Экспортируем в PNG, SVG и PDF", 20,
          "Сохраните исходник `.drawio` и экспортируйте в двух форматах. PNG — для документации, "
          "SVG — чтобы не мыло при масштабировании на проекторе.",
          code="app.diagrams.net → File → Export as → PNG (2x) / SVG / PDF\nFile → Save as → docs/diagrams/01-usecase.drawio\n\n# проверка наличия всех трёх файлов\nls -la docs/diagrams/",
          png="usecase-export", cap="Три файла: исходник, PNG и SVG",
          note=["Экспортируйте в масштабе 2x — иначе подписи в PNG нечитаемы при печати."]),
        S("Пишем обоснование в README", 20,
          "В `docs/diagrams/README.md` опишите каждого актёра и каждую группу вариантов: "
          "зачем вариант существует и какое требование задания закрывает.",
          code="# Диаграмма вариантов использования\n\n## Актёры\n| Актёр | Роль в системе |\n|---|---|\n| Мастер | ... |\n\n## Группа вариантов «Управление заявками»\nСоздать заявку — мастер создаёт заявку из плана ТО или по факту отказа оборудования.",
          png="usecase-readme", cap="README.md описывает актёров и группы вариантов",
          note=["Обоснование — часть критерия «проектирование». Без README диаграмма "
                "оценивается ниже, даже если нарисована хорошо."]),
    ],
    [("Диаграмма не помещается на лист", "уменьшите размер шрифта до 10 или разбейте варианты на две группы"),
     ("Связи include/extend не читаются", "подпишите их и разнесите стрелки, иначе они сливаются в клубок"),
     ("Экспорт в PDF обрезает края", "экспортируйте страницу целиком: Format → Page → Entire page"),
     ("Экспорт недоступен в браузере", "разрешите всплывающие окна для app.diagrams.net")],
    "ls docs/diagrams/01-usecase.* && grep -c 'include\\|extend' docs/diagrams/README.md",
    "docs(diagrams): диаграмма вариантов использования и обоснование",
))

PAGES.append(P(
    4, "Activity-диаграмма", 1,
    "Рисуем диаграмму деятельности процесса «Выполнение заявки на ремонт и ТО». "
    "Она показывает поток работы от заявки до закрытия — со всеми ветвлениями.",
    "В `docs/diagrams/` лежат `02-activity.png`, `02-activity.svg`, исходник "
    "`02-activity.drawio` и раздел обоснования в `README.md`.",
    [("А. Диаграмма деятельности", "≈3,85 балла")],
    ["docs/diagrams/02-activity.png", "docs/diagrams/02-activity.svg",
     "docs/diagrams/02-activity.drawio", "docs/diagrams/README.md"],
    [
        S("Определяем дорожки", 15,
          "Разделите процесс на дорожки — swimlane. Дорожки показывают, кто отвечает за этап, "
          "и делают диаграмму читаемой без легенды.",
          code="Дорожки:\n  Мастер            — создаёт заявку, заполняет описание\n  Система          — проверяет данные, считает простои, пишет в журнал\n  Руководитель     — назначает бригаду, принимает решение по аварийной\n  Бригада          — выполняет работы, вносит списание",
          png="activity-lanes", cap="Четыре дорожки, начало в дорожке «Мастер»",
          note=["Дорожка «Система» — самая ценная: именно на ней видны автоматические "
                "проверки, которые эксперт ищет в первую очередь."]),
        S("Рисуем действия и ветвления", 30,
          "Начало — заявка создана, конец — заявка закрыта. Между ними действия "
          "и ромбы-решения. Каждому ромбу соответствует явное условие.",
          code="[Заявка создана]\n  → Проверить данные заявки          (дорожка Система)\n  <Дата окончания раньше даты начала?> → Да → [Отклонить, вернуть мастеру]\n  → Запросить бригаду                (дорожка Руководитель)\n  → Назначить бригаду\n  <Бригада назначена?>                → Нет → вернуться к запросу",
          png="activity-flow", gif="activity-draw", cap="Поток действий и ромбы ветвлений",
          note=["Каждый ромб подписывайте условием, а не номером: «Бригада назначена?» "
                "вместо «Решение 1». Иначе диаграмму невозможно читать."]),
        S("Добавляем fork и join", 20,
          "Параллельные действия изображаются чёрной полосой **fork** и **join**. "
          "В нашем процессе параллельно выполняются закупка ЗИП и уведомление мастера.",
          code="fork → Параллельно:\n        ├─ Проверить наличие материалов на складе\n        └─ Уведомить мастера о назначении бригады\njoin → Работы начаты\n\n→ Зафиксировать фактическое начало\n→ Выполнить работы                    (дорожка Бригада)",
          png="activity-fork", cap="Параллельные ветви объединены через fork/join",
          note=["Без fork/join диаграмма выглядит последовательной, и эксперт считает, "
                "что параллельность не продумана. За это отдельный пункт критерия."]),
        S("Экспортируем и описываем", 15,
          "Экспортируйте в PNG и SVG, допишите раздел в `README.md`: какие требования "
          "задания отражает процесс и почему выделены именно эти ветвления.",
          code="app.diagrams.net → File → Export as → PNG (2x) / SVG\n# проверить, что все четыре файла на месте\nls -la docs/diagrams/02-activity.*",
          png="activity-export", cap="Диаграмма экспортирована, README дополнен",
          note=["В README укажите, что триггер БД (проверка дат заявки) соответствует "
                "второму ромбу диаграммы — это связывает проектирование с реализацией."]),
    ],
    [("Стрелки пересекаются и путаются", "разнесите действия по дорожкам, каждое строго по горизонтали"),
     ("fork и join выглядят как чёрные прямоугольники", "в Draw.io это тонкие полосы — задайте высоту 3 px"),
     ("Диаграмма не помещается по высоте", "поверните лист альбомной ориентацией"),
     ("Экспорт в PNG обрезает подписи", "экспортируйте с масштабом 2x и полной страницей")],
    "ls docs/diagrams/02-activity.* && grep -q 'fork' docs/diagrams/README.md",
    "docs(diagrams): диаграмма деятельности процесса выполнения заявки",
))

PAGES.append(P(
    5, "Class-диаграмма", 1,
    "Рисуем диаграмму классов: сущности системы, их атрибуты и связи. "
    "Эта диаграмма — контракт для базы данных и для API, поэтому согласуйте "
    "атрибуты с заданием до того, как писать `schema.sql`.",
    "В `docs/diagrams/` лежат `03-class.png`, `03-class.svg`, исходник `03-class.drawio` "
    "и раздел обоснования в `README.md`.",
    [("А. Диаграмма классов", "≈4,0 балла")],
    ["docs/diagrams/03-class.png", "docs/diagrams/03-class.svg",
     "docs/diagrams/03-class.drawio", "docs/diagrams/README.md"],
    [
        S("Выписываем сущности и атрибуты", 25,
          "Начните с сущностей, названных в задании: пользователи, роли, оборудование, "
          "виды ТО, график ТО, заявки, ремонтные бригады, материалы, журнал операций. "
          "Каждый класс рисуется прямоугольником с тремя секциями.",
          code="┌──────────────────────┐\n│        Заявка        │\n├──────────────────────┤\n│ - id : UUID          │\n│ - number : String    │\n│ - status : Статус    │\n├──────────────────────┤\n│ + close() : void     │\n└──────────────────────┘",
          png="class-boxes", gif="class-draw", cap="Прямоугольники в три секции: имя, атрибуты, методы",
          note=["Средняя секция обязательна: критерий проверяет именно три секции. "
                "Пустую среднюю секцию не оставляйте."]),
        S("Определяем связи и кратности", 25,
          "Связи рисуйте линиями с ромбами на стороне «многих». Обязательная связь — "
          "залитый ромб, необязательная — пустой. Композицию показывайте залитой чёрной "
          "ромбом у границы.",
          code="Оборудование 1 —— 0..* График ТО        (одно оборудование — много записей графика)\nВиды ТО    1 —— 0..* График ТО        (один вид ТО — много записей графика)\nОборудование 1 —— 0..* Заявка          (одно оборудование — много заявок)\nБригада    0..1 —— 0..* Заявка         (у заявки бригада назначается позже)\nЗаявка    1 —— 0..* Списание ЗИП       (одна заявка — несколько позиций)",
          png="class-relations", cap="Связи с ромбами и кратностями 1, 0..1, 0..*",
          note=["Кратность `0..1` у бригады принципиальна: заявка создаётся раньше, "
                "чем за ней закрепят бригаду. Рисуйте `1` — и диаграмма разойдётся с БД."]),
        S("Расставляем ассоциации и наследование", 20,
          "Вынесите повторяющиеся атрибуты в отдельный класс и свяжите их ассоциацией. "
          "В задании для этого подходит `Аудит операций` — общий журнал изменений.",
          code="АудитОперации\n  - id : UUID\n  - таблица : String\n  - действие : Действие (создание/изменение/удаление)\n  - время : DateTime\n\nСвязан с Заявка, Оборудование, Пользователь кратностью 0..* с каждой стороны.",
          png="class-association", cap="Ассоциация с классом аудита и кратностями",
          note=["Ассоциация читается в обе стороны: с каждой стороны подпишите свою кратность, "
                "иначе связь неоднозначна."]),
        S("Экспортируем и сверяем с заданием", 20,
          "Экспортируйте диаграмму и сверьте каждую сущность с перечнем из задания. "
          "Допишите в `README.md` обоснование: какое требование закрывает каждая связь.",
          code="app.diagrams.net → File → Export as → PNG (2x) / SVG\n# сверка списка классов с заданием\nls docs/diagrams/03-class.*\n# в README.md перечислены все 9 сущностей задания",
          png="class-export", cap="Диаграмма готова, список классов сверен с заданием",
          note=["Сверьте имена классов с будущими таблицами БД: «Заявка» → work_orders, "
                "«Оборудование» → equipment. Расхождение имён снижает баллы за проектирование."]),
    ],
    [("Диаграмма не читается", "разделите на две группы: «Справочники» и «Операционные»"),
     ("Связи наезжают на прямоугольники", "используйте ортогональные линии Draw.io"),
     ("Средняя секция пустая", "добавьте атрибуты — критерий требует три секции"),
     ("Кратности не совпадают с БД", "зафиксируйте кратности в README и сверьте со схемой на странице 7")],
    "ls docs/diagrams/03-class.* && grep -c 'class\\|таблиц' docs/diagrams/README.md",
    "docs(diagrams): диаграмма классов и обоснование связей",
))
# === BLOCK-C: страницы 6–11, спринты 2–4 ===

PAGES.append(P(
    6, "Нормализация-и-ER-диаграмма", 2,
    "Приводим модель к трём нормальным формам и рисуем ER-диаграмму. "
    "Критерий проверяет и формы, и то, что таблицы и поля названы осмысленно.",
    "В `docs/erd/` лежит ER-диаграмма, в `db/schema.sql` — таблицы и связи, "
    "в `db/README.md` — обоснование по каждой нормальной форме.",
    [("А. Проектирование и реализация БД", "1НФ ≈0,2 · 2НФ ≈0,4 · 3НФ ≈1,0 · наименование таблиц и полей ≈0,5")],
    ["db/erd/er-diagram.png", "db/erd/er-diagram.drawio", "db/schema.sql", "db/README.md"],
    [
        S("Выписываем сущности из задания", 20,
          "Возьмите список сущностей из задания и для каждой выпишите поля прямо "
          "из текста. Не добавляйте полей «на будущее» — лишние поля ломают 3НФ и "
          "раздувают таблицы.",
          code="users            — id, username, password_hash, full_name, role_id\nroles            — id, code, name\nworkshops        — id, code, name\neq  uipment       — id, inventory_number, name, type, serial_number,\n                    workshop_id, commission_date, status, criticality\nmaintenance_types— id, code, name, interval_months\nmaintenance_schedule — id, equipment_id, maintenance_type_id, planned_date, status\nwork_orders      — id, number, equipment_id, maintenance_type_id, crew_id,\n                    priority, status, description, reason, planned_start, planned_end,\n                    actual_start, actual_end, downtime_hours\ncrews            — id, name, specialization, phone\nmaterials        — id, sku, name, unit, unit_price",
          png="entities", cap="Десять сущностей выписаны из текста задания",
          note=["Если поле встречается в задании дважды (например, «дата начала»), "
                "вынесите его в отдельную сущность — это и есть нормализация."]),
        S("Нормализуем: 1НФ, 2НФ, 3НФ", 25,
          "Пройдите формы по порядку и запишите в `db/README.md`, что именно изменили "
          "на каждом шаге. Обоснование по формам — половина критерия.",
          code="1НФ: атомарность. В заявке не было отдельной таблицы списаний —\n      список материалов лежал в одном поле. Вынесли в work_order_materials.\n2НФ: в maintenance_schedule (equipment_id, maintenance_type_id) →\n      код_установки был зависим только от equipment_id. Вынесли в equipment.\n3НФ: название цеха не должно храниться в equipment — только workshop_id,\n      само название лежит в workshops. Устранена транзитивная зависимость.",
          png="normal-forms", cap="Обоснование 1НФ, 2НФ и 3НФ в db/README.md",
          note=["Название таблиц и полей — отдельный пункт критерия ≈0,5 балла. "
                "Пишите по-русски или английскими snake_case, но одинаково везде."]),
        S("Строим ER-диаграмму", 25,
          "Нарисуйте связи «один ко многим» между таблицами. Обозначения Crow's Foot "
          "в Draw.io: `||` — ровно один, `o{` — ноль или много.",
          code="Связи:\n  roles        1 ── 0..* users\n  workshops    1 ── 0..* equipment\n  equipment    1 ── 0..* maintenance_schedule\n  equipment    1 ── 0..* work_orders\n  maintenance_types 1 ── 0..* maintenance_schedule\n  crews        1 ── 0..* work_orders\n  work_orders  1 ── 0..* work_order_materials\n  materials    1 ── 0..* work_order_materials",
          png="er-diagram", gif="er-draw", cap="ER-диаграмма: 10 таблиц, 8 связей",
          note=["Диаграмма должна совпадать с диаграммой классов со страницы 5. "
                "Расхождение между ними эксперт заметит сразу."]),
        S("Проверяем модель на связность", 20,
          "Пройдитесь по каждой таблице и спросите: можно ли её удалить без потери данных "
          "и не останется ли «висящих» ссылок. Ответы запишите в `db/README.md`.",
          code="Каждая таблица связана хотя бы одним внешним ключом — «висячих» нет.\nУдаление мастера (users) не удаляет его заявки: журнал операций хранит только id.\nСправочники (maintenance_types, materials) не удаляются, если на них ссылается хотя бы одна запись.",
          png="model-review", cap="Модель вычитана, «висячих» ссылок нет",
          note=["Этот разбор — заготовка для ограничений целостности на страницах 8–11."]),
    ],
    [("ER-диаграмма не совпадает с диаграммой классов", "вернитесь к странице 5 и синхронизируйте имена"),
     ("Связи не читаются", "используйте ортогональные линии и подписи кратностей у обоих концов"),
     ("Экспорт PNG обрезает края", "Format → Page → Entire page, затем Export as PNG 2x"),
     ("Обоснование выглядит формальным", "приведите конкретный пример поля до и после нормализации")],
    "ls db/erd/er-diagram.png db/schema.sql db/README.md && grep -c 'НФ' db/README.md",
    "docs(db): ER-диаграмма и обоснование нормализации 1НФ–3НФ",
))

PAGES.append(P(
    7, "Скрипт-schema-sql-и-тестовые-данные", 2,
    "Пишем `db/schema.sql` — единственный скрипт, который создаёт базу с нуля — "
    "и `db/seed.sql` с тестовыми данными. Тестовые данные — отдельный пункт критерия, "
    "ими заполняют базу при проверке.",
    "`db/schema.sql` создаёт 10 таблиц без ошибок на чистой базе, `db/seed.sql` наполняет их данными.",
    [("А. Проектирование и реализация БД", "тестовые данные ≈0,5 балла · реализация БД ≈0,5 балла")],
    ["db/schema.sql", "db/seed.sql"],
    [
        S("Создаём таблицы пользователей и оборудования", 25,
          "Начните `schema.sql` с таблиц, на которые ссылаются остальные. "
          "Идентификаторы — `UUID` с генерацией на стороне приложения, "
          "временные метки — `TIMESTAMPTZ`.",
          code="""-- db/schema.sql · часть 1: пользователи и оборудование

CREATE TABLE roles (
    id          UUID PRIMARY KEY,
    code        VARCHAR(30)  NOT NULL UNIQUE,
    name        VARCHAR(100) NOT NULL
);

CREATE TABLE users (
    id            UUID PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(150) NOT NULL,
    role_id       UUID NOT NULL REFERENCES roles (id) ON DELETE RESTRICT,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE workshops (
    id   UUID PRIMARY KEY,
    code VARCHAR(20)  NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL
);

CREATE TYPE equipment_status AS ENUM ('Работает', 'В ремонте', 'Выведено из эксплуатации');

CREATE TABLE equipment (
    id               UUID PRIMARY KEY,
    inventory_number VARCHAR(20)  NOT NULL UNIQUE,
    name             VARCHAR(200) NOT NULL,
    equipment_type   VARCHAR(100) NOT NULL,
    serial_number    VARCHAR(50)  NOT NULL UNIQUE,
    workshop_id      UUID NOT NULL REFERENCES workshops (id) ON DELETE RESTRICT,
    commission_date  DATE NOT NULL,
    status           equipment_status NOT NULL DEFAULT 'Работает',
    criticality      SMALLINT NOT NULL DEFAULT 3
);""",
          lang="sql", hint="db/schema.sql",
          png="schema-users", gif="schema-run", cap="Четыре таблицы созданы, psql не сообщил об ошибках",
          note=["`CREATE TYPE` выполняется один раз. При повторном запуске скрипта "
                "PostgreSQL скажет, что тип уже существует — это ожидаемо."]),
        S("Создаём таблицы ТО, заявок, бригад и материалов", 30,
          "Оставшиеся таблицы. Обратите внимание на `UNIQUE (equipment_id, "
          "maintenance_type_id, planned_date)` — один вид ТО на одном оборудовании "
          "не может быть запланирован дважды на одну дату.",
          code="""-- db/schema.sql · часть 2: обслуживание, заявки, бригады, материалы

CREATE TABLE maintenance_types (
    id               UUID PRIMARY KEY,
    code             VARCHAR(20) NOT NULL UNIQUE,
    name             VARCHAR(150) NOT NULL,
    interval_months  INTEGER NOT NULL,
    description      VARCHAR(500)
);

CREATE TABLE maintenance_schedule (
    id                   UUID PRIMARY KEY,
    equipment_id         UUID NOT NULL REFERENCES equipment (id) ON DELETE CASCADE,
    maintenance_type_id  UUID NOT NULL REFERENCES maintenance_types (id) ON DELETE RESTRICT,
    planned_date         DATE NOT NULL,
    status               VARCHAR(20) NOT NULL DEFAULT 'Запланировано',
    UNIQUE (equipment_id, maintenance_type_id, planned_date)
);

CREATE TYPE work_order_status AS ENUM ('Черновик','Назначена','В работе','Завершена','Отменена');
CREATE TYPE work_order_priority AS ENUM ('Низкий','Средний','Высокий','Аварийный');

CREATE TABLE crews (
    id             UUID PRIMARY KEY,
    name           VARCHAR(100) NOT NULL UNIQUE,
    specialization VARCHAR(150),
    phone          VARCHAR(30)
);

CREATE TABLE work_orders (
    id                  UUID PRIMARY KEY,
    number              VARCHAR(20) NOT NULL UNIQUE,
    equipment_id        UUID NOT NULL REFERENCES equipment (id) ON DELETE RESTRICT,
    maintenance_type_id UUID REFERENCES maintenance_types (id) ON DELETE RESTRICT,
    crew_id             UUID REFERENCES crews (id) ON DELETE SET NULL,
    priority            work_order_priority NOT NULL DEFAULT 'Средний',
    status              work_order_status NOT NULL DEFAULT 'Черновик',
    description         VARCHAR(500) NOT NULL,
    reason              VARCHAR(500),
    planned_start       TIMESTAMPTZ,
    planned_end         TIMESTAMPTZ,
    actual_start        TIMESTAMPTZ,
    actual_end          TIMESTAMPTZ,
    downtime_hours      NUMERIC(8,2),
    created_by          UUID NOT NULL REFERENCES users (id) ON DELETE RESTRICT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);""",
          lang="sql", hint="db/schema.sql",
          png="schema-orders", cap="Заявки и график ТО созданы, ограничение UNIQUE на месте",
          note=["`ON DELETE` правила расставлены осмысленно: график ТО удаляется "
                "вместе с оборудованием (CASCADE), а справочник видов ТО удалить "
                "нельзя, пока на него ссылается график (RESTRICT). Подробнее — на странице 9."]),
        S("Дописываем списание и журнал операций", 25,
          "Две вспомогательные таблицы: списание материалов в заявку и журнал аудита. "
          "Журнал пишется триггером на странице 10.",
          code="""-- db/schema.sql · часть 3: ЗИП и аудит

CREATE TABLE materials (
    id           UUID PRIMARY KEY,
    sku          VARCHAR(30)  NOT NULL UNIQUE,
    name         VARCHAR(200) NOT NULL,
    unit         VARCHAR(10)  NOT NULL,
    unit_price   NUMERIC(12,2) NOT NULL,
    min_quantity NUMERIC(12,2) NOT NULL DEFAULT 0
);

CREATE TABLE work_order_materials (
    id             UUID PRIMARY KEY,
    work_order_id  UUID NOT NULL REFERENCES work_orders (id) ON DELETE CASCADE,
    material_id    UUID NOT NULL REFERENCES materials (id) ON DELETE RESTRICT,
    quantity       NUMERIC(12,2) NOT NULL,
    unit_price     NUMERIC(12,2) NOT NULL,
    UNIQUE (work_order_id, material_id)
);

CREATE TABLE operation_log (
    id         UUID PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation  VARCHAR(20) NOT NULL,
    entity_id  UUID NOT NULL,
    user_id    UUID REFERENCES users (id) ON DELETE SET NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    details    JSONB
);""",
          lang="sql", hint="db/schema.sql",
          png="schema-audit", cap="Журнал операций и списание созданы",
          note=["`unit_price` дублируется в списании намеренно: цена материала может "
                "измениться, а в закрытой заявке должна остаться та, по которой считали."]),
        S("Пишем seed.sql с тестовыми данными", 25,
          "Тестовые данные нужны, чтобы эксперт сразу увидел работающую систему. "
          "Сделайте минимум: 3 роли, 6 пользователей, 2 цеха, 10 единиц оборудования, "
          "5 видов ТО, 12 записей графика, 15 заявок в разных статусах, 4 бригады, 12 материалов.",
          code="""-- db/seed.sql · выполняется после schema.sql
INSERT INTO roles (id, code, name) VALUES
  ('11111111-1111-1111-1111-111111111111', 'admin', 'Администратор'),
  ('22222222-2222-2222-2222-222222222222', 'manager', 'Руководитель'),
  ('33333333-3333-3333-3333-333333333333', 'master', 'Мастер');

INSERT INTO workshops (id, code, name) VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Ц1', 'Цех №1 — механический'),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Ц2', 'Цех №2 — кузнечный');""",
          lang="sql", hint="db/seed.sql",
          png="seed-data", gif="seed-run", cap="Тестовые данные загружены: 15 заявок в разных статусах",
          note=["Заявки должны быть во всех пяти статусах — иначе нельзя проверить "
                "дашборд и фильтры веб-клиента, а это ≈19 баллов."]),
        S("Проверяем чистую установку с нуля", 20,
          "Удалите базу и создайте заново из скриптов. Если повторная установка "
          "проходит — значит скрипты корректны и пригодны для проверки.",
          code="psql -h 127.0.0.1 -U toirprof -d postgres -c 'DROP DATABASE IF EXISTS toirprof;'\npsql -h 127.0.0.1 -U toirprof -d postgres -c 'CREATE DATABASE toirprof OWNER toirprof;'\npsql -h 127.0.0.1 -U toirprof -d toirprof -f db/schema.sql\npsql -h 127.0.0.1 -U toirprof -d toirprof -f db/seed.sql\npsql -h 127.0.0.1 -U toirprof -d toirprof -c '\\dt'",
          png="schema-clean-install", cap="Чистая база собрана из скриптов: 10 таблиц",
          note=["`DROP DATABASE` не сработает, пока к базе подключён DBeaver. "
                "Закройте соединение в DBeaver и повторите."]),
    ],
    [("`type ... already exists`", "база создана повторно — удалите её и прогоните скрипты заново"),
     ("`permission denied for schema public`", "вы вошли не как `toirprof`; проверьте `-U toirprof`"),
     ("`syntax error at or near ...`", "пропущена точка с запятой в конце `CREATE TABLE`"),
     ("Данные загрузились частично", "в `seed.sql` нарушен порядок вставки: сначала справочники, потом ссылки")],
    "psql -h 127.0.0.1 -U toirprof -d toirprof -c '\\dt' | grep -c table && psql -h 127.0.0.1 -U toirprof -d toirprof -c 'SELECT count(*) FROM work_orders;'",
    "feat(db): schema.sql и seed.sql для системы ТОиР-Проф",
))
# === BLOCK-D: страницы 8–11, спринты 3–4 ===

PAGES.append(P(
    8, "Ограничения-UNIQUE-и-ENUM", 3,
    "Добавляем ограничения уникальности и допустимых значений. Это ≈1,4 балла "
    "из ≈5,1 подкритерия «Ограничения целостности БД» — и почти бесплатные баллы: "
    "всё делается в SQL.",
    "Четыре ограничения UNIQUE и три типа ENUM работают: попытка вставить "
    "дубликат или недопустимое значение отклоняется базой.",
    [("Б. Ограничения целостности БД", "UNIQUE ×4 ≈0,8 · ENUM ×3 ≈0,6")],
    ["db/schema.sql", "db/README.md"],
    [
        S("Разбираем, где нужны UNIQUE", 15,
          "Критерий требует четыре ограничения уникальности. Возьмите по одному "
          "на каждую бизнес-сущность, где «дубль» не имеет смысла.",
          code="1) users.username          — два пользователя с одним логином невозможны\n2) equipment.inventory_number — инвентарный номер уникален\n3) work_orders.number       — номер заявки уникален\n4) materials.sku            — артикул материала уникален",
          png="unique-plan", cap="Четыре места, где UNIQUE обязателен",
          note=["Все четыре уже есть в `schema.sql` со страницы 7 — здесь вы их "
                "проверяете и документируете, а не пишете заново."]),
        S("Проверяем каждый UNIQUE осознанно", 25,
          "Попытайтесь вставить дубликат в каждую из четырёх таблиц и убедитесь, "
          "что база отвергает операцию. Отказ — это и есть работа ограничения.",
          code="psql -h 127.0.0.1 -U toirprof -d toirprof <<'SQL'\nINSERT INTO users (id, username, password_hash, full_name, role_id)\nSELECT gen_random_uuid(), username, 'x', 'Дубль', role_id FROM users LIMIT 1;\n-- ERROR:  duplicate key value violates unique constraint \"users_username_key\"\nSQL",
          png="unique-violation", gif="unique-check", cap="База отвергает дубликат логина: duplicate key value violates unique constraint",
          note=["Текст ошибки `duplicate key value violates unique constraint` — "
                "именно он доказывает эксперту, что ограничение работает."]),
        S("Создаём три типа ENUM", 20,
          "Допустимые значения храните в пользовательских типах, а не в строках. "
          "Так база сама не даст записать «выведено из екслплуатации» с опечаткой.",
          code="""CREATE TYPE equipment_status  AS ENUM ('Работает', 'В ремонте', 'Выведено из эксплуатации');
CREATE TYPE work_order_status  AS ENUM ('Черновик', 'Назначена', 'В работе', 'Завершена', 'Отменена');
CREATE TYPE work_order_priority AS ENUM ('Низкий', 'Средний', 'Высокий', 'Аварийный');""",
          lang="sql", hint="db/schema.sql",
          png="enums", cap="Три пользовательских типа в списке DBeaver",
          note=["Названия значений пишите с заглавной буквы и в том же регистре, "
                "что в тексте задания — расхождение регистра ломает сравнение в API."]),
        S("Проверяем ENUM и фиксируем в README", 25,
          "Попробуйте записать в поле статуса значение, которого нет в типе. "
          "Опишите все семь ограничений в `db/README.md` таблицей: "
          "объект → ограничение → зачем.",
          code="psql -h 127.0.0.1 -U toirprof -d toirprof <<'SQL'\nUPDATE equipment SET status = 'сломан' WHERE id = (SELECT id FROM equipment LIMIT 1);\n-- ERROR:  invalid input value for enum equipment_status: \"сломан\"\nSQL\n\n# фиксация в документации\nprintf '| Таблица | Ограничение | Зачем |\\n|---|---|---|\\n| users | UNIQUE(username) | один логин — один пользователь |\\n' >> db/README.md",
          png="enum-violation", cap="Недопустимое значение отклонено, ограничения описаны в README",
          note=["Критерий оценивает не само ограничение, а его наличие в БД и "
                "демонстрацию. Скриншот ошибки базы — половина доказательства."]),
    ],
    [("`invalid input value for enum`", "ожидаемое поведение — так работает ограничение"),
     ("`relation ... does not exist`", "выполняли проверку не в базе `toirprof`"),
     ("Ошибка не воспроизводится", "забыли `COMMIT` — сделайте `ROLLBACK` и повторите"),
     ("В DBeaver не видно типов", "обновите схему: правой кнопкой по базе → Refresh")],
    "grep -c 'UNIQUE' db/schema.sql && psql -h 127.0.0.1 -U toirprof -d toirprof -c '\\dT'",
    "feat(db): ограничения UNIQUE и типы ENUM",
))

PAGES.append(P(
    9, "Ограничения-CHECK-и-ON-DELETE", 3,
    "Проверяем хронологию дат через CHECK и настраиваем каскадные действия. "
    "Четыре ограничения CHECK закрывают две строки критерия, ON DELETE — ещё одну.",
    "Четыре ограничения CHECK и осмысленные правила `ON DELETE` работают на "
    "тестовой базе и описаны в `db/README.md`.",
    [("Б. Ограничения целостности БД", "CHECK хронология ×2 ≈0,4 · CHECK даты заявок ×2 ≈0,4 · ON DELETE ×2 ≈0,4")],
    ["db/schema.sql", "db/README.md"],
    [
        S("Ограничиваем хронологию в оборудовании", 20,
          "Ввод в эксплуатацию не может быть позже сегодняшнего дня — это первое "
          "ограничение CHECK по хронологии.",
          code="""ALTER TABLE equipment
  ADD CONSTRAINT ck_equipment_commission_date
  CHECK (commission_date <= CURRENT_DATE);

ALTER TABLE equipment
  ADD CONSTRAINT ck_equipment_criticality
  CHECK (criticality BETWEEN 1 AND 5);""",
          lang="sql", hint="db/schema.sql",
          png="check-equipment", cap="Ограничение ck_equipment_commission_date добавлено",
          note=["`CURRENT_DATE` вычисляется на сервере, поэтому ограничение всегда "
                "актуально и не требует обновления данных."]),
        S("Ограничиваем даты заявки", 25,
          "В заявке четыре пары дат. Проверьте обе пары: плановая и фактическая. "
          "Это два отдельных пункта критерия.",
          code="""ALTER TABLE work_orders
  ADD CONSTRAINT ck_work_order_planned_dates
  CHECK (planned_end IS NULL OR planned_start IS NULL OR planned_end >= planned_start);

ALTER TABLE work_orders
  ADD CONSTRAINT ck_work_order_actual_dates
  CHECK (actual_end IS NULL OR actual_start IS NULL OR actual_end >= actual_start);

ALTER TABLE work_orders
  ADD CONSTRAINT ck_work_order_downtime
  CHECK (downtime_hours IS NULL OR downtime_hours >= 0);""",
          lang="sql", hint="db/schema.sql",
          png="check-dates", gif="check-dates-run", cap="Три ограничения на даты заявки добавлены",
          note=["Обязательно проверяйте `IS NULL` в каждом условии: NULL в PostgreSQL "
                "даёт неопределённый результат CHECK, и ограничение не сработает "
                "на заявке без плановых дат."]),
        S("Настраиваем каскадные действия", 25,
          "Правило `ON DELETE` должно отражать смысл связи. График ТО существует "
          "ради оборудования — удаляется вместе с ним. Справочник видов ТО "
          "самостоятелен — его удаление блокируется, пока на него ссылаются.",
          code="ALTER TABLE maintenance_schedule\n  DROP CONSTRAINT maintenance_schedule_equipment_id_fkey,\n  ADD CONSTRAINT maintenance_schedule_equipment_id_fkey\n  FOREIGN KEY (equipment_id) REFERENCES equipment (id) ON DELETE CASCADE;\n\nALTER TABLE maintenance_types_id_fkey\n  ALTER CONSTRAINT ... -- аналогично: ON DELETE RESTRICT",
          lang="sql", hint="db/schema.sql",
          png="on-delete", cap="Правила ON DELETE: CASCADE для графика, RESTRICT для справочника",
          note=["RESTRICT запрещает удаление сразу, CASCADE сначала удаляет "
                "зависимые строки. Путаница между ними — частая ошибка на защите."]),
        S("Проверяем ограничения и описываем их", 25,
          "Проверьте каждое ограничение попыткой нарушить его и составьте таблицу "
          "в `db/README.md`: ограничение → что запрещает → скриншот проверки.",
          code="psql -h 127.0.0.1 -U toirprof -d toirprof <<'SQL'\nUPDATE work_orders SET planned_end = now() - interval '2 day',\n                        planned_start = now()\n WHERE id = (SELECT id FROM work_orders LIMIT 1);\n-- ERROR:  new row for relation \"work_orders\" violates check constraint \"ck_work_order_planned_dates\"\nSQL",
          png="check-violation", cap="Нарушение хронологии отклонено базой",
          note=["Все проверки удобно выполнять в одной сессии и откатывать: "
                "добавьте `BEGIN;` в начале и `ROLLBACK;` в конце."]),
    ],
    [("CHECK не срабатывает на NULL", "добавьте явную проверку `IS NULL` в условие"),
     ("Ошибка при `DROP CONSTRAINT`", "имя ограничения смотрите в DBeaver: вкладка «Ограничения»"),
     ("`violates foreign key constraint`", "попытка удалить строку, на которую кто-то ссылается — это и есть RESTRICT"),
     ("Ограничение добавлено, но данные уже невалидны", "сначала исправьте данные, потом добавляйте ограничение")],
    "psql -h 127.0.0.1 -U toirprof -d toirprof -c '\\d work_orders' | grep -c 'CHECK\\|FOREIGN KEY'",
    "feat(db): ограничения CHECK и правила ON DELETE",
))

PAGES.append(P(
    10, "Триггеры-БД", 4,
    "Пишем два триггера, которые задание требует дословно: запрет смены статуса "
    "оборудования, выведенного из эксплуатации, и комплексную проверку дат заявки. "
    "Вместе с ними — триггер журнала аудита.",
    "Оба обязательных триггера срабатывают, попытка обойти их невозможна: "
    "ограничение живёт в базе, а не в приложении.",
    [("Б. Ограничения целостности БД", "триггеры ×2 ≈1,0")],
    ["db/triggers.sql", "db/README.md"],
    [
        S("Пишем триггер защиты оборудования", 25,
          "По заданию статус «выведено из эксплуатации» менять нельзя. "
          "Триггер `BEFORE UPDATE` проверяет это на уровне строки.",
          code="""-- db/triggers.sql · триггер №1
CREATE OR REPLACE FUNCTION fn_equipment_status_guard()
RETURNS trigger AS $$
BEGIN
    IF OLD.status = 'Выведено из эксплуатации' AND NEW.status <> OLD.status THEN
        RAISE EXCEPTION 'Оборудование % выведено из эксплуатации: статус изменить нельзя',
                        OLD.inventory_number
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_equipment_status_guard
BEFORE UPDATE ON equipment
FOR EACH ROW EXECUTE FUNCTION fn_equipment_status_guard();""",
          lang="sql", hint="db/triggers.sql",
          png="trigger-equipment", gif="trigger-equipment-run", cap="Триггер создан, попытка смены статуса отклонена",
          note=["Используйте `FOR EACH ROW` и `$$ … $$`: внутри функции нужны "
                "блоки и точки с запятой, которые конфликтуют с разделителем "
                "команд `psql`."]),
        S("Проверяем триггер защиты", 15,
          "Выведите оборудование из эксплуатации и попробуйте вернуть его в работу. "
          "База должна отказать.",
          code="psql -h 127.0.0.1 -U toirprof -d toirprof <<'SQL'\nUPDATE equipment SET status = 'Выведено из эксплуатации' WHERE inventory_number = 'ОБ-0001';\nUPDATE equipment SET status = 'Работает'             WHERE inventory_number = 'ОБ-0001';\n-- ERROR:  оборудование ОБ-0001 выведено из эксплуатации: статус изменить нельзя\nSQL",
          png="trigger-guard-test", cap="Ошибка от пользовательского текста триггера",
          note=["Свой текст в `RAISE EXCEPTION` эксперт видит на демонстрации — "
                "это читаемее, чем стандартное сообщение PostgreSQL."]),
        S("Пишем комплексную проверку дат заявки", 25,
          "Второй обязательный триггер проверяет все пары дат разом и пересчитывает "
          "простой через функцию со страницы 11.",
          code="""-- db/triggers.sql · триггер №2
CREATE OR REPLACE FUNCTION fn_work_order_dates_check()
RETURNS trigger AS $$
BEGIN
    IF NEW.planned_start IS NOT NULL AND NEW.planned_end IS NOT NULL
       AND NEW.planned_end < NEW.planned_start THEN
        RAISE EXCEPTION 'Плановая дата окончания раньше даты начала';
    END IF;
    IF NEW.actual_start IS NOT NULL AND NEW.actual_end IS NOT NULL
       AND NEW.actual_end < NEW.actual_start THEN
        RAISE EXCEPTION 'Фактическая дата окончания раньше даты начала';
    END IF;
    IF NEW.actual_start IS NOT NULL AND NEW.actual_end IS NOT NULL THEN
        NEW.downtime_hours := fn_calculate_downtime(NEW.actual_start, NEW.actual_end);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_work_order_dates_check
BEFORE INSERT OR UPDATE ON work_orders
FOR EACH ROW EXECUTE FUNCTION fn_work_order_dates_check();""",
          lang="sql", hint="db/triggers.sql",
          png="trigger-dates", cap="Комплексная проверка дат заявки реализована",
          note=["Триггер вызывается и на INSERT, и на UPDATE: иначе заявку можно "
                " было бы создать сразу с неверными датами."]),
        S("Пишем триггер журнала аудита", 20,
          "Задание требует журнал операций. Заполняйте его триггером — тогда "
          "история пишется для всех клиентов одинаково и её нельзя обойти.",
          code="""CREATE OR REPLACE FUNCTION fn_write_audit()
RETURNS trigger AS $$
BEGIN
    INSERT INTO operation_log (id, table_name, operation, entity_id, details)
    VALUES (gen_random_uuid(), TG_TABLE_NAME,
            lower(TG_OP), COALESCE(NEW.id, OLD.id),
            to_jsonb(COALESCE(NEW, OLD)) - 'password_hash');
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_work_orders
AFTER INSERT OR UPDATE OR DELETE ON work_orders
FOR EACH ROW EXECUTE FUNCTION fn_write_audit();""",
          lang="sql", hint="db/triggers.sql",
          png="trigger-audit", gif="audit-run", cap="После любой операции в журнале появляется запись",
          note=["`- 'password_hash'` исключает хеш пароля из журнала. Проверяющий "
                "может обратить на это внимание."]),
        S("Проверяем все триггеры разом", 20,
          "Прогоните скрипт на чистой базе и выполните одну операцию каждого вида. "
          "Зафиксируйте вывод в `db/README.md` — это доказательство для защиты.",
          code="psql -h 127.0.0.1 -U toirprof -d toirprof -f db/triggers.sql\npsql -h 127.0.0.1 -U toirprof -d toirprof -c '\\dt work_orders'\npsql -h 127.0.0.1 -U toirprof -d toirprof -c 'SELECT table_name, operation FROM operation_log ORDER BY changed_at DESC LIMIT 5;'",
          png="triggers-all", cap="Три триггера активны, журнал заполняется",
          note=["Проверьте в DBeaver: Database → Triggers — должны быть видны все три."]),
    ],
    [("`function ... already exists`", "пересоздавайте функции с `CREATE OR REPLACE`, а триггеры — через `DROP TRIGGER IF EXISTS`"),
     ("Триггер не срабатывает", "проверьте `BEFORE` или `AFTER` и наличие `FOR EACH ROW`"),
     ("Простой не считается", "функция `fn_calculate_downtime` ещё не создана — сделайте страницу 11"),
     ("Журнал растёт при каждом чтении", "триггер должен быть `AFTER INSERT OR UPDATE OR DELETE`, без `SELECT`")],
    "psql -h 127.0.0.1 -U toirprof -d toirprof -c '\\dT+' 2>/dev/null; psql -h 127.0.0.1 -U toirprof -d toirprof -c 'SELECT count(*) FROM operation_log;'",
    "feat(db): триггеры защиты оборудования, проверки дат и аудита",
))

PAGES.append(P(
    11, "Функции-и-сводная-процедура", 4,
    "Реализуем две функции и одну процедуру из задания: расчёт простоя, "
    "расчёт следующей плановой даты ТО и сводный отчёт по цеху за период. "
    "Это ≈1,5 балла и почти готовый кусок аналитики для API.",
    "Функции и процедура доступны в SQL и вызываются из отчётов API.",
    [("Б. Ограничения целостности БД", "функции ×2 ≈1,0 · процедура ≈0,5")],
    ["db/functions.sql", "db/README.md"],
    [
        S("Пишем функцию расчёта простоя", 20,
          "Функция №1 из задания. Возвращает целое число часов между двумя "
          "моментами; при перевёрнутом интервале возвращает 0, а не ошибку.",
          code="""-- db/functions.sql · функция №1
CREATE OR REPLACE FUNCTION fn_calculate_downtime(p_start timestamptz, p_end timestamptz)
RETURNS numeric AS $$
DECLARE
    v_delta interval;
BEGIN
    IF p_start IS NULL OR p_end IS NULL THEN
        RETURN 0;
    END IF;
    v_delta := p_end - p_start;
    IF v_delta < interval '0' THEN
        RETURN 0;
    END IF;
    RETURN round(EXTRACT(EPOCH FROM v_delta) / 3600.0, 2);
END;
$$ LANGUAGE plpgsql;""",
          lang="sql", hint="db/functions.sql",
          png="func-downtime", cap="Функция fn_calculate_downtime создана",
          note=["`round(..., 2)` даёт два знака после запятой — столько же, "
                "сколько колонка `NUMERIC(8,2)`, иначе будет ошибка округления."]),
        S("Проверяем функцию на четырёх случаях", 15,
          "Проверьте: нормальный интервал, перевёрнутый интервал, NULL и нулевой интервал. "
          "Результаты внесите в `db/README.md`.",
          code="psql -h 127.0.0.1 -U toirprof -d toirprof -c \"\nSELECT fn_calculate_downtime('2027-03-01 08:00', '2027-03-01 20:30') AS норма,\n       fn_calculate_downtime('2027-03-02 08:00', '2027-03-01 08:00') AS перевёрнутый,\n       fn_calculate_downtime(NULL, '2027-03-01 08:00')                    AS пусто,\n       fn_calculate_downtime('2027-03-01 08:00', '2027-03-01 08:00')    AS ноль;\"",
          png="func-downtime-test", gif="func-downtime-run", cap="12.5, 0, 0, 0 — все четыре случая корректны",
          note=["Эти же четыре случая используются в модульных тестах на странице 46 — "
                "проверьте, что ожидаемые значения совпадают."]),
        S("Пишем функцию следующей плановой даты", 20,
          "Функция №2: к дате последнего ТО прибавляется интервал из справочника "
          "видов ТО. `make_date` корректно обрабатывает 31 февраля.",
          code="""-- db/functions.sql · функция №2
CREATE OR REPLACE FUNCTION fn_next_maintenance_date(p_date date, p_interval_months integer)
RETURNS date AS $$
BEGIN
    IF p_date IS NULL OR p_interval_months IS NULL OR p_interval_months <= 0 THEN
        RETURN NULL;
    END IF;
    RETURN make_date(
        EXTRACT(YEAR  FROM p_date)::integer + ((p_interval_months - 1) / 12),
        EXTRACT(MONTH FROM p_date)::integer + ((p_interval_months - 1) % 12) + 1,
        1
    );
END;
$$ LANGUAGE plpgsql;""",
          lang="sql", hint="db/functions.sql",
          png="func-next-date", cap="Функция fn_next_maintenance_date создана",
          note=["Прибавление месяцев в SQL ломается на концах месяца: 31 января + 1 месяц "
                "даёт «31 февраля». Первый день месяца — единственная страховка без "
                "ручной арифметики."]),
        S("Пишем сводную процедуру по цеху", 30,
          "Процедура №3 из задания — главный источник данных для отчётов. "
          "Она ничего не возвращает, а печатает результат через `RAISE NOTICE`, "
          "поэтому из API её вызывают через курсор.",
          code="""-- db/functions.sql · процедура №3
CREATE OR REPLACE PROCEDURE proc_workshop_report(
    p_workshop_id uuid,
    p_date_from   date,
    p_date_to     date
)
LANGUAGE plpgsql AS $$
DECLARE
    r record;
BEGIN
    FOR r IN
        SELECT e.inventory_number,
               e.name,
               count(wo.id)                                  AS заявок,
               count(wo.id) FILTER (WHERE wo.status = 'Завершена') AS выполнено,
               COALESCE(sum(wo.downtime_hours), 0)           AS простоев_часов
          FROM equipment e
          LEFT JOIN work_orders wo
                 ON wo.equipment_id = e.id
                AND wo.created_at::date BETWEEN p_date_from AND p_date_to
         WHERE e.workshop_id = p_workshop_id
         GROUP BY e.id, e.inventory_number, e.name
         ORDER BY простоев_часов DESC
    LOOP
        RAISE NOTICE '% | % | заявок: %, выполнено: %, простой: % ч',
            r.inventory_number, r.name, r.заявок, r.выполнено, r.простоев_часов;
    END LOOP;
END;
$$;""",
          lang="sql", hint="db/functions.sql",
          png="func-report", gif="func-report-run", cap="Процедура выводит сводку по каждому оборудованию",
          note=["`CREATE PROCEDURE` (не `FUNCTION`) требует PostgreSQL 11+. "
                "На версии 10 и ниже используйте только `CREATE FUNCTION`."]),
        S("Проверяем процедуру и переносим в API", 20,
          "Вызовите процедуру из `psql`, убедитесь, что строки выводятся. "
          "Затем сделайте SQL-обёртку `CREATE VIEW v_workshop_report`, "
          "которую проще читать из Entity Framework.",
          code="psql -h 127.0.0.1 -U toirprof -d toirprof -c \\\n  \"CALL proc_workshop_report('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '2027-01-01', '2027-12-31');\"\n\n-- SQL-обёртка для API\nCREATE VIEW v_workshop_report AS\nSELECT e.workshop_id, e.id AS equipment_id, e.inventory_number, e.name,\n       count(wo.id) AS work_orders_count,\n       COALESCE(sum(wo.downtime_hours), 0) AS downtime_hours\n  FROM equipment e\n  LEFT JOIN work_orders wo ON wo.equipment_id = e.id\n GROUP BY e.workshop_id, e.id, e.inventory_number, e.name;",
          lang="sql", hint="db/functions.sql",
          png="func-report-test", cap="Сводка выводится, представление создано",
          note=["Представление — компромисс: критерий требует процедуру, но API "
                "удобнее читать из представления. Оставьте и то, и другое."]),
    ],
    [("`syntax error at or near \"$$\"`", "разделитель `$$` должен быть в начале строки"),
     ("Функция возвращает NULL вместо числа", "проверьте, что передали `timestamptz`, а не `timestamp without time zone`"),
     ("`CALL` не поддерживается", "версия PostgreSQL ниже 11 — перепишите через `DO $$ ... $$`"),
     ("Простой считается в секундах", "делить надо на 3600: `EXTRACT(EPOCH ...) / 3600.0`")],
    "psql -h 127.0.0.1 -U toirprof -d toirprof -c \"SELECT fn_calculate_downtime('2027-03-01 08:00','2027-03-01 20:30') AS hours;\"",
    "feat(db): функции расчёта простоя и плановой даты, процедура сводного отчёта",
))
# === BLOCK-E: спринты 5–11, страницы 12–25 (API) ===

PAGES.append(P(
    12, "Проект-API-и-DbContext", 5,
    "Создаём Solution с тремя проектами: собственно API, общую библиотеку контрактов "
    "и проект тестов. Подключаем Entity Framework Core к PostgreSQL и включаем Swagger "
    "в режиме разработки — без него проверяющий не увидит ни одного метода.",
    "API поднимается на `http://localhost:5080`, `/swagger` открывается, DbContext видит 11 таблиц.",
    [("Б / API", "Единый сервер для всех клиентов, документирование API через Swagger")],
    ["src/api/ToirProf.Api.csproj", "src/api/Program.cs", "src/api/appsettings.json",
     "src/api/Data/AppDbContext.cs"],
    [
        S("Создаём Solution и проекты", 30,
          "Создайте Solution в корне `src/` и три проекта внутри. Общая библиотека нужна, "
          "чтобы Desktop-клиент и тесты использовали одни и те же модели ответа.",
          code="cd src\ndotnet new sln -n ToirProf\ndotnet new classlib -n ToirProf.Shared -o Shared\ndotnet new webapi -n ToirProf.Api -o api --use-controllers\ndotnet new xunit -n ToirProf.Tests -o Tests\ndotnet sln add Shared/ToirProf.Shared.csproj api/ToirProf.Api.csproj Tests/ToirProf.Tests.csproj\ndotnet add api/ToirProf.Api.csproj reference Shared/ToirProf.Shared.csproj\ndotnet add Tests/ToirProf.Tests.csproj reference Shared/ToirProf.Shared.csproj",
          lang="bash", png="solution", gif="solution-run", cap="Solution создан, три проекта в дереве",
          note=["`dotnet new webapi` создаёт заготовку с `WeatherForecast`. Удалите "
                "`Controllers/WeatherForecastController.cs` и `Program.cs` изменим полностью — "
                "лишний код снижает впечатление на демонстрации."]),
        S("Подключаем EF Core и строку подключения", 30,
          "Добавьте пакеты и создайте DbContext. Строку подключения держите в "
          "`appsettings.json`, пароль — в переменной окружения, чтобы не светить его в репозитории.",
          code="dotnet add api package Npgsql.EntityFrameworkCore.PostgreSQL --version 9.*\ndotnet add api package Microsoft.EntityFrameworkCore.Design --version 9.*\ndotnet add api package Swashbuckle.AspNetCore\n\n// appsettings.json\n{\n  \"ConnectionStrings\": {\n    \"Default\": \"Host=127.0.0.1;Port=5432;Database=toirprof;Username=toirprof;Password=toirprof\"\n  },\n  \"Jwt\": { \"Key\": \"<secret-32+символа>\", \"Issuer\": \"ToirProf\", \"Audience\": \"ToirProfClient\" },\n  \"Kestrel\": { \"Endpoints\": { \"Http\": { \"Url\": \"http://localhost:5080\" } } }\n}",
          lang="json", hint="src/api/appsettings.json",
          png="efcore", gif="efcore-restore", cap="Пакеты восстановлены, версия EF Core в выводе совпадает с версией .NET",
          note=["Регион `Jwt` читается через `builder.Configuration.GetSection(\"Jwt\")`. "
                "Ключ должен быть не короче 32 байт — иначе `SymmetricSecurityKey` бросит исключение "
                "при первом же входе."]),
        S("Создаём DbContext на 11 сущностей", 40,
          "Опишите сущности как классы с первичным ключом `Guid`. Миграции против "
          "Code-First здесь не нужны: схему уже создал `db/schema.sql`, EF работает поверх неё.",
          code="public class AppDbContext : DbContext\n{\n    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }\n\n    public DbSet<Role> Roles => Set<Role>();\n    public DbSet<User> Users => Set<User>();\n    public DbSet<Workshop> Workshops => Set<Workshop>();\n    public DbSet<Equipment> Equipment => Set<Equipment>();\n    public DbSet<MaintenanceType> MaintenanceTypes => Set<MaintenanceType>();\n    public DbSet<MaintenanceSchedule> MaintenanceSchedule => Set<MaintenanceSchedule>();\n    public DbSet<Crew> Crews => Set<Crew>();\n    public DbSet<Material> Materials => Set<Material>();\n    public DbSet<WorkOrder> WorkOrders => Set<WorkOrder>();\n    public DbSet<WorkOrderMaterial> WorkOrderMaterials => Set<WorkOrderMaterial>();\n    public DbSet<OperationLogEntry> OperationLog => Set<OperationLogEntry>();\n}",
          lang="csharp", hint="src/api/Data/AppDbContext.cs",
          png="dbcontext", cap="11 наборов сущностей в AppDbContext",
          note=["Схема создана скриптом, поэтому `EnsureCreated` и миграции **не вызывайте** — "
                "иначе EF попытается создать таблицы заново и упадёт на `relation already exists`. "
                "Для проверки соединения достаточно `db.Database.CanConnectAsync()`."]),
        S("Включаем Swagger и запускаем", 20,
          "Настройте Swagger в development-режиме и убедитесь, что сервер отвечает. "
          "Порт фиксируем в `appsettings.json`, а не в коде — тогда Postman и оба клиента "
          "настраиваются одной правкой.",
          code="dotnet build\ndotnet run --project api/ToirProf.Api.csproj\n# в другом терминале\ncurl -i http://localhost:5080/swagger/index.html",
          png="swagger", gif="api-start", cap="Swagger UI открыт, в группе ToirProf.Api виден Health",
          note=["Swagger подключается только в `app.Environment.IsDevelopment()`. "
                "На защите эксперты открывают `/swagger` без переменных окружения — "
                "добавьте `ASPNETCORE_ENVIRONMENT=Development` в инструкцию по развёртыванию."]),
    ],
    [("`relation \"equipment\" already exists`", "EF пытался создать схему — уберите вызовы `EnsureCreated`"),
     ("`dotnet: command not found`", "SDK не установлен или не прописан `PATH` — вернитесь на страницу 01"),
     ("Swagger открывается, но без методов", "контроллеры не добавлены в `AddControllers` — проверьте `Program.cs`"),
     ("`A network error occurred` в браузере", "сервер слушает другой порт — сверьтесь с `appsettings.json`")],
    "curl -s http://localhost:5080/swagger/v1/swagger.json | head -c 200 && dotnet build -v q",
    "feat(api): каркас Solution, DbContext на 11 сущностей и Swagger",
))

PAGES.append(P(
    13, "Формат-ответа-и-обработка-ошибок", 5,
    "Вводим единую обёртку ответа `{ success, data, message, error_code }` и таблицу кодов "
    "ошибок. Это требование задания и одновременно то, на чём держится всё остальное API: "
    "оба клиента разбирают ответ одним и тем же кодом.",
    "Любой метод возвращает `ApiResponse<T>`, коды ошибок описаны в одном перечислении, "
    "исключения превращаются в JSON автоматически.",
    [("Б / API", "Единый формат ответа, корректные HTTP-коды ошибок")],
    ["src/ToirProf.Shared/ApiResponse.cs", "src/api/Common/ErrorCodes.cs",
     "src/api/Common/ExceptionMiddleware.cs"],
    [
        S("Описываем ApiResponse", 25,
          "Обёртка лежит в общей библиотеке: и API, и Desktop, и Web используют один тип. "
          "Статические фабрики убирают повторяющийся `new ApiResponse<T> { Success = false }`.",
          code="public class ApiResponse<T>\n{\n    public bool Success { get; init; }\n    public T? Data { get; init; }\n    public string Message { get; init; } = string.Empty;\n    public string? ErrorCode { get; init; }\n\n    public static ApiResponse<T> Ok(T data, string message = \"OK\")\n        => new() { Success = true, Data = data, Message = message };\n\n    public static ApiResponse<T> Fail(string message, ErrorCode code)\n        => new() { Success = false, Message = message, ErrorCode = code.ToString() };\n}\n\npublic enum ErrorCode\n{\n    Validation = 400, Unauthorized = 401, Forbidden = 403,\n    NotFound = 404, Conflict = 409, TooManyRequests = 429, Internal = 500\n}",
          lang="csharp", hint="src/ToirProf.Shared/ApiResponse.cs",
          png="apiresponse", cap="ApiResponse<T> с фабриками Ok и Fail",
          note=["`error_code` отдаётся строкой, а не числом: клиенту проще читать "
                "`CONFLICT`, чем `409`, а в логах API остаётся привязка к HTTP-коду "
                "через сам `enum`."]),
        S("Проверяем коды на живом методе", 25,
          "Добавьте пробный контроллер и проверьте все шесть кодов ответа через Postman. "
          "Проверять их на демонстрации дороже, чем сейчас.",
          code="[ApiController]\n[Route(\"api/health\")]\npublic class HealthController : ControllerBase\n{\n    [HttpGet(\"ok\")]\n    public ApiResponse<object> Ok() => ApiResponse<object>.Ok(new { ping = \"pong\" });\n\n    [HttpGet(\"fail/{code}\")]\n    public IActionResult Fail(int code) => code switch\n    {\n        400 => BadRequest(ApiResponse<object>.Fail(\"Некорректный запрос\", ErrorCode.Validation)),\n        401 => Unauthorized(ApiResponse<object>.Fail(\"Требуется авторизация\", ErrorCode.Unauthorized)),\n        403 => StatusCode(403, ApiResponse<object>.Fail(\"Недостаточно прав\", ErrorCode.Forbidden)),\n        404 => NotFound(ApiResponse<object>.Fail(\"Не найдено\", ErrorCode.NotFound)),\n        409 => Conflict(ApiResponse<object>.Fail(\"Конфликт данных\", ErrorCode.Conflict)),\n        429 => StatusCode(429, ApiResponse<object>.Fail(\"Слишком много запросов\", ErrorCode.TooManyRequests)),\n        _ => StatusCode(500, ApiResponse<object>.Fail(\"Внутренняя ошибка\", ErrorCode.Internal)),\n    };\n}",
          lang="csharp", hint="src/api/Controllers/HealthController.cs",
          png="codes", gif="codes-postman", cap="Postman: семь ответов, у каждого свой HTTP-код",
          note=["Для 429 добавьте заголовок `Retry-After: 5` — по нему клиент поймёт, "
                "через сколько секунд повторить запрос."]),
        S("Ловим исключения middleware", 25,
          "Необработанные исключения превращаются в 500 с тем же форматом ответа. "
          "Без этого стек трейса попадёт в ответ и засветит внутренние пути.",
          code="public class ExceptionMiddleware(RequestDelegate next, ILogger<ExceptionMiddleware> log)\n{\n    public async Task InvokeAsync(HttpContext ctx)\n    {\n        try { await next(ctx); }\n        catch (Exception ex)\n        {\n            log.LogError(ex, \"Необработанная ошибка: {Path}\", ctx.Request.Path);\n            ctx.Response.StatusCode = 500;\n            ctx.Response.ContentType = \"application/json\";\n            await ctx.Response.WriteAsJsonAsync(\n                ApiResponse<object>.Fail(\"Внутренняя ошибка сервера\", ErrorCode.Internal));\n        }\n    }\n}",
          lang="csharp", hint="src/api/Common/ExceptionMiddleware.cs",
          png="middleware", cap="Middleware зарегистрирован первым в конвейере",
          note=["Регистрируйте middleware **до** `UseAuthentication` и `UseAuthorization` — "
                "иначе исключения из конвейера аутентификации останутся необработанными."]),
        S("Описываем таблицу кодов", 15,
          "Сведите коды в таблицу и положите её в `docs/`. Эксперты проверяют именно "
          "соответствие: 401 на защищённом маршруте и 403 у пользователя без роли.",
          code="| Ситуация | HTTP | error_code |\n|---|---|---|\n| Поля не прошли валидацию | 400 | VALIDATION |\n| Нет или просрочен токен | 401 | UNAUTHORIZED |\n| Роль не даёт доступ | 403 | FORBIDDEN |\n| Запись не найдена | 404 | NOT_FOUND |\n| Дубликат номера заявки | 409 | CONFLICT |\n| Частота запросов превышена | 429 | TOO_MANY_REQUESTS |\n| Сбой сервера | 500 | INTERNAL |",
          lang="markdown", hint="docs/error-codes.md",
          png="error-table", cap="Таблица кодов ошибок в репозитории"),
    ],
    [("Ответ приходит без обёртки", "метод возвращает `IActionResult` напрямую — заверните в `ApiResponse`"),
     ("422 вместо 400", "не подключён FluentValidation — вернитесь к странице 12"),
     ("Middleware не ловит исключение", "зарегистрирован после `UseRouting` — перенесите в самое начало"),
     ("Swagger не показывает 401/403", "не хватает `ProducesResponseType` на методе")],
    "curl -s -o /dev/null -w '%{http_code}\\n' http://localhost:5080/api/health/fail/409",
    "feat(api): единый формат ответа ApiResponse и middleware обработки ошибок",
))
# === BLOCK-E2: спринты 6–9, страницы 14–21 ===

PAGES.append(P(
    14, "Регистрация-вход-и-JWT", 6,
    "Регистрируем пользователя, проверяем пароль и выдаём JWT. Пароль в базе хранится "
    "только в виде хеша — открытый пароль в таблице `users` означает провал критерия "
    "по безопасности на демонстрации.",
    "POST `/api/auth/register` и POST `/api/auth/login` работают, пароль в базе — bcrypt-хеш.",
    [("Б / API", "Аутентификация, разграничение доступа")],
    ["src/api/Controllers/AuthController.cs", "src/api/Services/AuthService.cs",
     "src/api/Services/TokenService.cs"],
    [
        S("Хешируем пароль и создаём пользователя", 25,
          "Добавьте BCrypt и научитесь создавать пользователя. Роль подставляется по "
          "умолчанию `Мастер` — назначение ролей делает администратор.",
          code="dotnet add api package BCrypt.Net-Next\n\nvar hash = BCrypt.Net.BCrypt.HashPassword(password, workFactor: 11);\nvar ok = BCrypt.Net.BCrypt.Verify(password, hash);",
          lang="csharp", hint="src/api/Services/AuthService.cs",
          png="bcrypt", gif="bcrypt-hash", cap="Хеш создаётся, Verify возвращает true",
          note=["`workFactor: 11` — баланс скорости и стойкости. На площадке каждый "
                "занимает ~100 мс, этого достаточно и не опасно для демонстрации."]),
        S("Реализуем регистрацию", 25,
          "Проверьте уникальность логина и верните 409, если он занят. Это один из "
          "четырёх UNIQUE-критериев, который эксперты проверяют в первую очередь.",
          code="public async Task<ApiResponse<TokenDto>> RegisterAsync(RegisterDto dto, CancellationToken ct)\n{\n    if (await _db.Users.AnyAsync(u => u.Username == dto.Username, ct))\n        throw new ConflictException(\"Логин уже занят\", ErrorCode.Conflict);\n\n    var user = new User\n    {\n        Id = Guid.NewGuid(),\n        Username = dto.Username.Trim(),\n        FullName = dto.FullName.Trim(),\n        PasswordHash = BCrypt.Net.BCrypt.HashPassword(dto.Password),\n        RoleId = await _db.Roles.Where(r => r.Code == \"MASTER\").Select(r => r.Id).FirstAsync(ct)\n    };\n    _db.Users.Add(user);\n    await _db.SaveChangesAsync(ct);\n    return await IssueAsync(user, ct);\n}",
          lang="csharp", hint="src/api/Services/AuthService.cs",
          png="register", gif="register-postman", cap="Регистрация вернула 201 и тело с токеном",
          note=["Логин сравнивайте через `AnyAsync` — сравнение строк в LINQ "
                "транслируется в `=`, регистр учитывается, как и требует UNIQUE."]),
        S("Выдаём JWT", 25,
          "Соберите токен на `SymmetricSecurityKey`, добавьте `name` и `role` в claims — "
          "роль понадобится на странице 15. Срок жизни разумно поставить 8 часов.",
          code="var claims = new[]\n{\n    new Claim(ClaimTypes.NameIdentifier, user.Id.ToString()),\n    new Claim(ClaimTypes.Name, user.Username),\n    new Claim(ClaimTypes.Role, roleCode),\n    new Claim(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString())\n};\n\nvar creds = new SigningCredentials(_key, SecurityAlgorithms.HmacSha256);\nvar token = new JwtSecurityToken(_cfg[\"Issuer\"], _cfg[\"Audience\"], claims,\n    expires: DateTime.UtcNow.AddHours(8), signingCredentials: creds);\nreturn new JwtSecurityTokenHandler().WriteToken(token);",
          lang="csharp", hint="src/api/Services/TokenService.cs",
          png="jwt", cap="Токен содержит name, role и sub, срок 8 часов",
          note=["`Jti` даёт возможность отозвать конкретный токен и не даёт двум "
                "выдачам совпасть — на защите это выглядит аккуратно при разборе JWT."]),
        S("Проверяем вход и декодируем токен", 20,
          "Войдите через Postman, вставьте токен в Authorization: Bearer и убедитесь, "
          "что защищённый метод его принимает.",
          code="curl -s -X POST http://localhost:5080/api/auth/login \\\n  -H 'Content-Type: application/json' \\\n  -d '{\"username\":\"master\",\"password\":\"Master123!\"}' | python3 -m json.tool\n# токен вставить в Authorization: Bearer <token>\ncurl -s http://localhost:5080/api/health/ok -H 'Authorization: Bearer <token>'",
          png="login", gif="login-postman", cap="Вход вернул токен, защищённый метод ответил 200",
          note=["Пароль в тестовых данных — `Master123!`. Требование к длине: "
                "минимум 8 символов, одна заглавная, одна цифра, один спецсимвол."]),
    ],
    [("409 на каждый запрос", "логин уже существует — проверьте, что сравнение идёт по `Username`, а не по `Id`"),
     ("401 на защищённом методе", "токен не проброшен: заголовок должен быть `Authorization: Bearer <token>`"),
     ("`IDX10720: key size must be >= 256 bits`", "ключ JWT короче 32 байт"),
     ("Пароль виден в таблице `users`", "сохраняется хеш, а не открытый пароль — исправьте `RegisterAsync`")],
    "psql -h 127.0.0.1 -U toirprof -d toirprof -c \"SELECT username, left(password_hash, 7) FROM users;\"",
    "feat(api): регистрация, проверка пароля и выдача JWT",
))

PAGES.append(P(
    15, "Роли-права-доступа-и-изоляция", 6,
    "Описываем три роли системы — Администратор, Мастер, Руководитель — и включаем "
    "проверку прав на стороне сервера. Права проверяет сервер, а не клиент: скрытая "
    "кнопка в интерфейсе не является разграничением доступа.",
    "Роль из токена попадает в `ClaimsPrincipal`, атрибут `[RequireRole]` закрывает маршруты, "
    "чужая бригада не видит чужие заявки.",
    [("Б / API", "Разграничение доступа по ролям")],
    ["src/api/Common/RequireRoleAttribute.cs", "src/api/Middleware/ExceptionMiddleware.cs",
     "src/api/Services/CrewAccessService.cs"],
    [
        S("Описываем роли", 20,
          "Роли живут в справочнике `roles` и приходят кодом в токене. Заведите роли "
          "при seed-скрипте, а не в коде — тогда администратор сможет их расширить.",
          code="INSERT INTO roles (id, code, name) VALUES\n  ('11111111-1111-1111-1111-111111111111', 'ADMIN',     'Администратор'),\n  ('22222222-2222-2222-2222-222222222222', 'MASTER',    'Мастер'),\n  ('33333333-3333-3333-3333-333333333333', 'MANAGER',   'Руководитель');",
          lang="sql", hint="db/seed.sql",
          png="roles", cap="Три роли в справочнике roles",
          note=["Доменные значения ENUM задания и роли из справочника — разные вещи. "
                "Статус заявки хранится ENUM, роль пользователя — обычным справочником."]),
        S("Закрываем маршруты атрибутом", 30,
          "Реализуйте атрибут на основе `AuthorizeAttribute`. Так маршрут защищается "
          "декларативно, и его видно прямо в Swagger.",
          code="public sealed class RequireRoleAttribute(string role) : AuthorizeAttribute\n{\n    public string Role { get; } = role;\n}\n\n[HttpDelete(\"{id:guid}\")]\n[RequireRole(\"ADMIN\")]\n[ProducesResponseType(StatusCodes.Status204NoContent)]\n[ProducesResponseType(StatusCodes.Status403Forbidden)]\npublic async Task<IActionResult> Delete(Guid id, CancellationToken ct) => NoContent();",
          lang="csharp", hint="src/api/Common/RequireRoleAttribute.cs",
          png="requirerole", gif="requirerole-postman", cap="Администратор удаляет, мастер получает 403",
          note=["Класс принимает одну роль. Для нескольких ролей наследуйтесь от "
                "`AuthorizeAttribute` и переопределите `OnAuthorization`, собирая роли в список."]),
        S("Изолируем данные по бригаде", 30,
          "Мастер видит только заявки своей бригады, руководитель — все. Фильтр добавляется "
          "в запрос по `crew_id` из токена, а не по параметру из тела запроса.",
          code="public IQueryable<WorkOrder> ApplyScope(IQueryable<WorkOrder> q, ClaimsPrincipal user)\n{\n    var role = user.FindFirst(ClaimTypes.Role)?.Value;\n    if (role is \"ADMIN\" or \"MANAGER\") return q;\n\n    var crewId = _db.Crews.Where(c => c.UserId == user.FindFirst(ClaimTypes.NameIdentifier)!.Value)\n                           .Select(c => c.Id).FirstOrDefault();\n    return q.Where(w => w.CrewId == crewId);\n}",
          lang="csharp", hint="src/api/Services/CrewAccessService.cs",
          png="scope", gif="scope-postman", cap="Мастер видит свои заявки, руководитель — все 40",
          note=["Сравнение `crew_id` делайте в SQL, а не в памяти: `q.Where(...)` "
                "транслируется в `WHERE`, и разбор выигрывает вместе с безопасностью."]),
        S("Проверяем 401 и 403 раздельно", 20,
          "Разница между кодами должна быть видна эксперту: 401 — нет токена, 403 — "
          "токен есть, но роль не та.",
          code="curl -s -o /dev/null -w 'без токена:  %{http_code}\\n' http://localhost:5080/api/users\ncurl -s -o /dev/null -w 'мастер:     %{http_code}\\n' http://localhost:5080/api/users -H \"Authorization: Bearer $MASTER_TOKEN\"\ncurl -s -o /dev/null -w 'админ:      %{http_code}\\n' http://localhost:5080/api/users -H \"Authorization: Bearer $ADMIN_TOKEN\"",
          png="401-403", gif="401-403-run", cap="Без токена 401, с токеном мастера 403, с админом 200",
          note=["Если мастер получает 401, а не 403 — роль не попала в claims. "
                "Проверьте `ClaimTypes.Role` при выдаче токена на странице 14."]),
    ],
    [("Мастер видит чужие заявки", "фильтр по бригаде не применён — вернитесь к шагу 3"),
     ("401 вместо 403", "роль не попала в токен — проверьте claims"),
     ("Swagger не показывает защиту", "не хватает `[Authorize]` на самом контроллере"),
     ("После смены роли токен старый", "у ролей есть срок жизни 8 часов — перелогиньтесь")],
    "curl -s -o /dev/null -w '%{http_code}\\n' -H \"Authorization: Bearer $MASTER_TOKEN\" http://localhost:5080/api/users",
    "feat(api): роли, атрибут RequireRole и изоляция данных по бригаде",
))

PAGES.append(P(
    16, "CRUD-оборудования", 7,
    "Основной справочник системы. Закрываем полный CRUD оборудования с фильтрами, "
    "сортировкой, пагинацией и проверкой занятости инвентарного номера.",
    "Пять методов `/api/equipment`, фильтры по статусу и цеху, пагинация, коды 400/404/409.",
    [("Б / API", "CRUD оборудования, фильтрация и пагинация")],
    ["src/api/Controllers/EquipmentController.cs", "src/api/DTOs/EquipmentDtos.cs",
     "src/api/Mappers/EquipmentMapper.cs", "src/api/Services/EquipmentService.cs",
     "src/api/Validators/CreateEquipmentValidator.cs"],
    [
        S("Описываем DTO и валидатор", 30,
          "DTO отделяют внешний контракт от таблицы: так добавление поля в базе "
          "не ломает контракт. Валидатор на FluentValidation ловит мусор раньше контроллера.",
          code="public record CreateEquipmentDto(\n    string InventoryNumber,\n    string Name,\n    Guid WorkshopId,\n    string? Manufacturer,\n    DateOnly? CommissionDate,\n    int? Criticality,\n    EquipmentStatus Status);\n\npublic class CreateEquipmentValidator : AbstractValidator<CreateEquipmentDto>\n{\n    public CreateEquipmentValidator()\n    {\n        RuleFor(x => x.InventoryNumber).NotEmpty().MaximumLength(32);\n        RuleFor(x => x.Name).NotEmpty().MaximumLength(160);\n        RuleFor(x => x.WorkshopId).NotEmpty();\n        RuleFor(x => x.Criticality).InclusiveBetween(1, 5);\n    }\n}",
          lang="csharp", hint="src/api/Validators/CreateEquipmentValidator.cs",
          png="dto", cap="DTO и валидатор создания оборудования",
          note=["`Criticality` — важность от 1 до 5, именно она проверяется "
                "CHECK-ограничением `ck_equipment_criticality` в базе. Валидация нужна "
                "в двух слоях: в API для ответа 400 и в БД для целостности."]),
        S("Реализуем чтение с фильтрами", 30,
          "Один метод на список: фильтр по статусу и цеху, поиск по имени, сортировка, "
          "пагинация. Возвращайте `{ items, total, page, size }` — клиентам это нужно "
          "для счётчиков пагинации.",
          code="public async Task<PagedResult<EquipmentDto>> GetListAsync(EquipmentFilter f, CancellationToken ct)\n{\n    var q = _db.Equipment.AsNoTracking().Include(e => e.Workshop).AsQueryable();\n    if (f.Status is not null) q = q.Where(e => e.Status == f.Status);\n    if (f.WorkshopId is not null) q = q.Where(e => e.WorkshopId == f.WorkshopId);\n    if (!string.IsNullOrWhiteSpace(f.Search))\n        q = q.Where(e => EF.Functions.ILike(e.Name, $\"%{f.Search}%\"));\n\n    var total = await q.CountAsync(ct);\n    var items = await q.OrderBy(e => e.InventoryNumber)\n                        .Skip((f.Page - 1) * f.Size).Take(f.Size)\n                        .Select(EquipmentMapper.ToDto).ToListAsync(ct);\n    return new PagedResult<EquipmentDto>(items, total, f.Page, f.Size);\n}",
          lang="csharp", hint="src/api/Services/EquipmentService.cs",
          png="list", gif="list-postman", cap="Список отфильтрован: 12 из 40, page=2",
          note=["`AsNoTracking()` обязателен на чтении — иначе EF кэширует сущности "
                "и вы отдаёте клиенту прокси вместо DTO. `ILike` даёт регистронезависимый "
                "поиск, обычный `Contains` в PostgreSQL чувствителен к регистру."]),
        S("Создание, изменение, удаление", 35,
          "POST возвращает 201 с телом, PUT обновляет, DELETE сначала проверяет, "
          "не стоит ли за оборудованием график, иначе 409.",
          code="[HttpPost]\n[ProducesResponseType(StatusCodes.Status201Created)]\n[ProducesResponseType(StatusCodes.Status409Conflict)]\npublic async Task<IActionResult> Create([FromBody] CreateEquipmentDto dto, CancellationToken ct)\n{\n    var exists = await _db.Equipment.AnyAsync(e => e.InventoryNumber == dto.InventoryNumber, ct);\n    if (exists) return Conflict(ApiResponse<object>.Fail(\"Инвентарный номер занят\", ErrorCode.Conflict));\n\n    var entity = dto.ToEntity();\n    _db.Equipment.Add(entity);\n    await _db.SaveChangesAsync(ct);\n    return CreatedAtAction(nameof(GetById), new { id = entity.Id },\n        ApiResponse<EquipmentDto>.Ok(entity.ToDto(), \"Оборудование создано\"));\n}\n\n[HttpDelete(\"{id:guid}\")]\n[RequireRole(\"ADMIN\")]\npublic async Task<IActionResult> Delete(Guid id, CancellationToken ct)\n{\n    var used = await _db.MaintenanceSchedule.AnyAsync(m => m.EquipmentId == id, ct);\n    if (used) return Conflict(ApiResponse<object>.Fail(\"Оборудование есть в графике ТО\", ErrorCode.Conflict));\n    var entity = await _db.Equipment.FindAsync([id], ct);\n    if (entity is null) return NotFound(ApiResponse<object>.Fail(\"Не найдено\", ErrorCode.NotFound));\n    _db.Equipment.Remove(entity);\n    await _db.SaveChangesAsync(ct);\n    return NoContent();\n}",
          lang="csharp", hint="src/api/Controllers/EquipmentController.cs",
          png="crud", gif="crud-postman", cap="POST 201, GET 200, DELETE 409 при занятом номере",
          note=["`FindAsync([id], ct)` ищет по первичному ключу и сначала проверяет "
                "кэш — дешевле, чем `FirstOrDefaultAsync`. Порядок проверок в методе "
                "важен: конфликт проверяем до `NotFound`, иначе клиент получит "
                "не тот код."]),
        S("Гонка на уникальном номере", 15,
          "Проверка `AnyAsync` перед вставкой не спасает от гонки двух параллельных "
          "запросов. Настоящую защиту даёт UNIQUE-индекс, а из него — ошибка `PostgresException` "
          "с кодом `23505`.",
          code="try { await _db.SaveChangesAsync(ct); }\ncatch (PostgresException ex) when (ex.SqlState == PostgresErrorCodes.UniqueViolation)\n{\n    return Conflict(ApiResponse<object>.Fail(\"Инвентарный номер занят\", ErrorCode.Conflict));\n}",
          lang="csharp", hint="src/api/Services/EquipmentService.cs",
          png="race", cap="Два параллельных POST: первый 201, второй 409",
          note=["Это ровно тот случай, который эксперты проверяют на защите: "
                "«а что будет, если два мастера одновременно создадут одно и то же?» "
                "Ответ — UNIQUE-индекс, а не предварительная проверка."]),
    ],
    [("404 на существующем id", "в базе другие регистры id — сверьте seed.sql"),
     ("409 при первом же POST", "инвентарный номер уже есть в seed — возьмите другой"),
     ("Поиск не находит кириллицу", "используйте `ILike`, а не `Contains`"),
     ("`NpgsqlException` вместо 409", "перехватывайте `PostgresException` с `SqlState == 23505`")],
    "curl -s 'http://localhost:5080/api/equipment?page=1&size=10' -H \"Authorization: Bearer $TOKEN\" | python3 -m json.tool",
    "feat(api): CRUD оборудования с фильтрами, пагинацией и проверкой конфликтов",
))
# === BLOCK-E3: спринты 7–11, страницы 17–25 ===

PAGES.append(P(
    17, "Справочник-видов-обслуживания", 7,
    "Виды ТО — это справочник с интервалом в днях. От него зависят и график, и автоподбор "
    "даты следующего обслуживания, поэтому удалять запись, на которую ссылается график, "
    "нельзя: возвращайте 409.",
    "CRUD справочника `/api/maintenance-types`, поле `interval_days` валидируется, "
    "удаление занятой записи даёт 409.",
    [("Б / API", "Справочник видов ТО")],
    ["src/api/Controllers/MaintenanceTypesController.cs",
     "src/api/Services/MaintenanceTypesService.cs"],
    [
        S("Справочник и его интервал", 25,
          "Каждому виду обслуживания соответствует периодичность в днях: ежедневный, "
          "ежемесячный, квартальный, годовой. Интервал хранится в днях, чтобы расчёт "
          "следующей даты был одинаковым для всех видов.",
          code="public record MaintenanceTypeDto(Guid Id, string Code, string Name, int IntervalDays, string? Description);\n\n[HttpGet]\n[RequireRole(\"ADMIN\", \"MASTER\", \"MANAGER\")]\n[ProducesResponseType(typeof(ApiResponse<List<MaintenanceTypeDto>>), StatusCodes.Status200OK)]\npublic async Task<IActionResult> GetAll(CancellationToken ct)\n    => Ok(ApiResponse<List<MaintenanceTypeDto>>.Ok(await _service.GetAllAsync(ct)));",
          lang="csharp", hint="src/api/Controllers/MaintenanceTypesController.cs",
          png="types", gif="types-get", cap="GET вернул четыре вида обслуживания",
          note=["Справочник небольшой, поэтому отдавайте его целиком без пагинации — "
                "клиенту нужен выпадающий список, а не таблица."]),
        S("Создание и изменение", 25,
          "Код справочника уникален и не редактируется после создания: по нему ссылаются "
          "графики и отчёты. Интервал ограничьте сверху двумя годами.",
          code="RuleFor(x => x.Code).NotEmpty().Matches(@\"^[A-Z0-9_]{2,16}$\").WithMessage(\"Код: заглавные латинские буквы, цифры и подчёркивание\");\nRuleFor(x => x.IntervalDays).InclusiveBetween(1, 730);\n\nif (await _db.MaintenanceTypes.AnyAsync(t => t.Code == dto.Code && t.Id != dto.Id, ct))\n    return Conflict(ApiResponse<object>.Fail(\"Код вида ТО уже существует\", ErrorCode.Conflict));",
          lang="csharp", hint="src/api/Validators/MaintenanceTypeValidator.cs",
          png="types-write", gif="types-postman", cap="POST 201, повторный POST с тем же кодом 409",
          note=["Регулярное выражение в валидаторе и CHECK в базе должны описывать одно "
                "и то же правило, иначе значения пройдут один слой и упадут на другом."]),
        S("Удаление с проверкой использования", 30,
          "Прежде чем удалить, проверяем ссылки: если на вид ТО ссылается хотя бы одна "
          "запись графика, отвечаем 409 и объясняем причину.",
          code="var used = await _db.MaintenanceSchedule.AnyAsync(m => m.MaintenanceTypeId == id, ct);\nif (used)\n{\n    var count = await _db.MaintenanceSchedule.CountAsync(m => m.MaintenanceTypeId == id, ct);\n    return Conflict(ApiResponse<object>.Fail(\n        $\"Вид ТО используется в {count} записях графика\", ErrorCode.Conflict));\n}",
          lang="csharp", hint="src/api/Services/MaintenanceTypesService.cs",
          png="types-delete", gif="types-409", cap="Удаление занятого справочника возвращает 409",
          note=["Сообщение с числом использований выглядит убедительнее, чем сухое "
                "`Conflict`. На демонстрации эксперт видит, что сервер знает о "
                "ссылочной целостности."]),
        S("Связываем справочник с графиком", 20,
          "Справочник вызывается из формы графика ТО: выпадающий список с интервалом "
          "и кнопкой «Создать следующий». Проверьте, что удалённый вид исчез из списка.",
          code="curl -s http://localhost:5080/api/maintenance-types -H \"Authorization: Bearer $TOKEN\"\n# ответ: data: [{ code: \"DAILY\", intervalDays: 1 }, { code: \"MONTHLY\", intervalDays: 30 }, ...]",
          png="types-usage", cap="Форма графика использует справочник, интервал подставляется",
          note=["Не храните копию интервала в графике. Если интервал изменится, "
                "в записях графика должна применяться новая версия — иначе отчёт "
                "покажет неверные сроки."]),
    ],
    [("409 при первом удалении", "вид уже используется в графике — так и должно быть"),
     ("422 на интервал 0", "валидатор `InclusiveBetween(1, 730)` — интервал минимум один день"),
     ("Справочник вернул пустой массив", "не применён `RequireRole` или seed не выполнен"),
     ("Ошибка при изменении кода", "код неизменяемый — вернитесь к шагу 2")],
    "curl -s http://localhost:5080/api/maintenance-types -H \"Authorization: Bearer $TOKEN\" | python3 -m json.tool",
    "feat(api): справочник видов обслуживания с проверкой ссылочной целостности",
))

PAGES.append(P(
    18, "График-планового-ТО", 8,
    "График планового технического обслуживания — расписание по оборудованию. "
    "Здесь же живёт автоподстановка следующей даты через функцию `fn_next_maintenance_date`, "
    "которая делает часть работы прямо в базе.",
    "CRUD графика, фильтр по периоду и статусу, расчёт следующей даты из базовой функции.",
    [("Б / API", "График планового ТО")],
    ["src/api/Controllers/MaintenanceScheduleController.cs",
     "src/api/Services/MaintenanceScheduleService.cs"],
    [
        S("Чтение графика с фильтрами", 30,
          "Главный сценарий — «что запланировано на этот месяц». Фильтруйте по диапазону "
          "дат планового ТО, по оборудованию и по статусу выполнения.",
          code="public async Task<PagedResult<ScheduleItemDto>> GetListAsync(ScheduleFilter f, CancellationToken ct)\n{\n    var q = _db.MaintenanceSchedule.AsNoTracking()\n        .Include(m => m.Equipment).ThenInclude(e => e.Workshop)\n        .Include(m => m.MaintenanceType)\n        .AsQueryable();\n\n    if (f.From is not null) q = q.Where(m => m.PlannedDate >= f.From.Value);\n    if (f.To is not null)   q = q.Where(m => m.PlannedDate <= f.To.Value);\n    if (f.EquipmentId is not null) q = q.Where(m => m.EquipmentId == f.EquipmentId);\n\n    var total = await q.CountAsync(ct);\n    var items = await q.OrderBy(m => m.PlannedDate)\n        .Skip((f.Page - 1) * f.Size).Take(f.Size)\n        .Select(m => new ScheduleItemDto(m.Id, m.PlannedDate, m.Equipment.InventoryNumber,\n            m.Equipment.Name, m.MaintenanceType.Name, m.Status)).ToListAsync(ct);\n    return new(items, total, f.Page, f.Size);\n}",
          lang="csharp", hint="src/api/Services/MaintenanceScheduleService.cs",
          png="schedule-list", gif="schedule-list-postman", cap="График за месяц: 18 записей, отсортировано по дате",
          note=["Два `Include` подряд — это две разные навигации. Первый тянет "
                "оборудование вместе с цехом, второй — вид обслуживания. Без них "
                "в ответе будут нули вместо названий."]),
        S("Создаём запись графика", 30,
          "При создании записи поле `next_planned_date` считает функция базы. "
          "Не дублируйте формулу в C# — при изменении правил расчёта разъедутся две реализации.",
          code="var next = _db.Database.SqlQuery<DateOnly?>(\"SELECT fn_next_maintenance_date({0}, {1}) AS \\\"Value\\\"\",\n    plannedDate, maintenanceType.IntervalDays).AsNoTracking().FirstOrDefault();\n\nvar item = new MaintenanceSchedule\n{\n    Id = Guid.NewGuid(),\n    EquipmentId = dto.EquipmentId,\n    MaintenanceTypeId = dto.MaintenanceTypeId,\n    PlannedDate = dto.PlannedDate,\n    NextPlannedDate = next,\n    Status = \"Запланировано\"\n};\n_db.MaintenanceSchedule.Add(item);\nawait _db.SaveChangesAsync(ct);",
          lang="csharp", hint="src/api/Services/MaintenanceScheduleService.cs",
          png="schedule-create", gif="schedule-create-postman", cap="POST 201: planned 2026-03-10, next 2026-04-10",
          note=["`SqlQuery<T>` для скалярных функций важнее `FromSqlRaw`: он возвращает "
                "типизированный скаляр. Название колонки в алиасе обязательно — "
                "PostgreSQL приводит `fn_...` к snake_case."]),
        S("Отметка выполнения и продление", 30,
          "Когда ТО выполнено, запись получает фактическую дату, а следующая считается "
          "от фактической, а не от плановой. Так график не «уезжает» после каждого простоя.",
          code="public async Task<ApiResult> CompleteAsync(Guid id, CompleteScheduleDto dto, CancellationToken ct)\n{\n    var item = await _db.MaintenanceSchedule.FindAsync([id], ct)\n        ?? throw new NotFoundException(\"Запись графика не найдена\");\n\n    item.ActualDate = dto.ActualDate;\n    item.Status = \"Выполнено\";\n\n    var interval = await _db.MaintenanceTypes\n        .Where(t => t.Id == item.MaintenanceTypeId)\n        .Select(t => t.IntervalDays).FirstAsync(ct);\n\n    item.NextPlannedDate = await _db.Database\n        .SqlQuery<DateOnly?>(\"SELECT fn_next_maintenance_date({0}, {1}) AS \\\"Value\\\"\",\n            dto.ActualDate, interval).FirstOrDefaultAsync(ct);\n\n    await _db.SaveChangesAsync(ct);\n    return ApiResult.Ok(\"Запись выполнена, следующая дата рассчитана\");\n}",
          lang="csharp", hint="src/api/Services/MaintenanceScheduleService.cs",
          png="schedule-complete", gif="schedule-complete-postman", cap="Выполнено 2026-03-12, следующая дата 2026-04-12",
          note=["Сдвиг даты от фактической — то, за что спрашивают на защите: "
                "«ваш график сдвигается, если ремонт затянулся?» Ответ должен быть да."]),
        S("Отменяем и удаляем", 20,
          "Удаление записи графика возможно только до выполнения. Выполненную запись "
          "не удаляют — она часть истории, на которую ссылается журнал операций.",
          code="if (item.Status == \"Выполнено\")\n    return Conflict(ApiResponse<object>.Fail(\"Выполненную запись нельзя удалить\", ErrorCode.Conflict));\n\n_db.MaintenanceSchedule.Remove(item);\nawait _db.SaveChangesAsync(ct);\nreturn NoContent();",
          lang="csharp", hint="src/api/Controllers/MaintenanceScheduleController.cs",
          png="schedule-delete", gif="schedule-409", cap="Удаление выполненной записи возвращает 409",
          note=["`ON DELETE CASCADE` в схеме сработает при удалении оборудования и "
                "унесёт его график. Но ручное удаление записи ограничено статусом — "
                "это разные вещи, не путайте их на защите."]),
    ],
    [("`next_planned_date` всегда NULL", "функция вернула NULL — проверьте интервал вида ТО"),
     ("Список пуст при верном периоде", "даты фильтра в UTC, а записи в локальном времени"),
     ("409 на удалении", "запись уже выполнена — это ожидаемое поведение"),
     ("Дубли по дате и оборудованию", "добавьте UNIQUE на `(equipment_id, planned_date)` в схеме")],
    "curl -s 'http://localhost:5080/api/maintenance-schedule?from=2026-03-01&to=2026-03-31' -H \"Authorization: Bearer $TOKEN\" | python3 -m json.tool",
    "feat(api): график планового ТО с расчётом следующей даты",
))

PAGES.append(P(
    19, "Генерация-номера-заявки", 8,
    "Номер заявки формируется сервером по маске `Z-ГГГГ-XXXX` и обязан быть уникальным. "
    "Клиент номер не передаёт — иначе две гонки гарантированно дадут дубли.",
    "Функция `GenerateWorkOrderNumber` выдаёт `Z-2026-0001`, `Z-2026-0002`, "
    "уникальность гарантирована UNIQUE-индексом.",
    [("Б / API", "Автогенерация номера заявки формата Z-YYYY-XXXX")],
    ["src/api/Services/WorkOrderNumberService.cs"],
    [
        S("Описываем формат номера", 25,
          "Формат `Z-ГГГГ-XXXX`: литерал `Z`, год четырьмя цифрами, четырёхзначный "
          "порядковый номер внутри года, начиная с 0001. Номера не сбрасываются 1 января — "
          "это упрощает поиск и соответствует заданию.",
          code="public static string Format(int year, int sequence)\n    => $\"Z-{year}-{sequence:D4}\";",
          lang="csharp", hint="src/api/Services/WorkOrderNumberService.cs",
          png="number-format", cap="Z-2026-0001, Z-2026-0002, …, Z-2026-0042",
          note=["`:D4` дополняет слева нулями до четырёх знаков. Без него на десятой "
                "заявке появится `Z-2026-10` — формат сломан."]),
        S("Выдаём номер без гонок", 35,
          "Год и порядковый номер берём из таблицы под счётчик и блокируем строку "
          "на время чтения. Без блокировки два параллельных POST получат одинаковый номер.",
          code="public async Task<string> NextAsync(CancellationToken ct)\n{\n    var year = DateTime.UtcNow.Year;\n\n    await using var tx = await _db.Database.BeginTransactionAsync(ct);\n    var counter = await _db.Database\n        .SqlQuery<CounterRow?>(\"SELECT next_seq AS \\\"NextSeq\\\" FROM work_order_counters WHERE year = {0} FOR UPDATE\", year)\n        .FirstOrDefaultAsync(ct);\n\n    int next = counter?.NextSeq ?? 1;\n    if (counter is null)\n        _db.Database.ExecuteSqlRaw(\"INSERT INTO work_order_counters (year, next_seq) VALUES ({0}, 1)\", year);\n    else\n        _db.Database.ExecuteSqlRaw(\"UPDATE work_order_counters SET next_seq = next_seq + 1 WHERE year = {0}\", year);\n\n    await tx.CommitAsync(ct);\n    return Format(year, next);\n}",
          lang="csharp", hint="src/api/Services/WorkOrderNumberService.cs",
          png="counter", gif="counter-race", cap="20 параллельных POST дали 20 разных номеров",
          note=["`FOR UPDATE` блокирует строку счётчика до конца транзакции — это и есть "
                "сериализация выдачи номеров. `ExecuteSqlRaw` после чтения выполняется "
                "в том же контексте, поэтому транзакция действительно общая."]),
        S("Ловим дубли на уровне индекса", 20,
          "Страховка: UNIQUE-индекс на `work_orders.number`. Даже если счётчик "
          "сбросится вручную, база не пропустит второй такой номер.",
          code="ALTER TABLE work_orders ADD CONSTRAINT uq_work_orders_number UNIQUE (number);\n\nSELECT number, COUNT(*) FROM work_orders GROUP BY number HAVING COUNT(*) > 1;\n-- пустой результат = дублей нет",
          lang="sql", hint="db/schema.sql",
          png="unique-number", cap="UNIQUE на number, проверка на дубли вернула пусто",
          note=["Проверка `GROUP BY … HAVING COUNT(*) > 1` — обычное дело перед "
                "демонстрацией. Эксперты часто просят именно её."]),
        S("Проверяем сквозную нумерацию", 20,
          "Создайте 5 заявок подряд и убедитесь, что номера идут без пропусков. "
          "Пропуск означает, что счётчик увеличился, а запись не прошла.",
          code="for i in 1 2 3 4 5; do\n  curl -s -X POST http://localhost:5080/api/work-orders \\\n    -H \"Authorization: Bearer $TOKEN\" -H 'Content-Type: application/json' \\\n    -d '{\"equipment_id\":\"44444444-4444-4444-4444-444444444444\",\"title\":\"Проверка нумерации\",\"priority\":\"Низкий\"}' \\\n    | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"data\"][\"number\"])'\ndone",
          png="number-series", gif="number-series-run", cap="Z-2026-0043 … Z-2026-0047 без пропусков",
          note=["Пропуск номера при откате транзакции — нормальное поведение счётчика. "
                "Если эксперту важна непрерывность, увеличивайте счётчик в той же "
                "транзакции, что и вставку заявки."]),
    ],
    [("Номера дублируются", "счётчик читается без `FOR UPDATE` — вернитесь к шагу 2"),
     ("`Z-2026-10` вместо `Z-2026-0010`", "потерян формат `:D4`"),
     ("`relation work_order_counters does not exist`", "не создана таблица счётчика в `schema.sql`"),
     ("Номер не сбрасывается в новом году", "так и задумано: сквозная нумерация по годам")],
    "psql -h 127.0.0.1 -U toirprof -d toirprof -c 'SELECT number FROM work_orders ORDER BY created_at DESC LIMIT 5;'",
    "feat(api): серверная генерация номера заявки формата Z-YYYY-XXXX",
))
# === BLOCK-E4: спринты 9–11, страницы 20–25 ===

PAGES.append(P(
    20, "Заявки-создание-чтение-и-фильтры", 9,
    "Заявка на ремонт и ТО — центральная сущность системы. Закрываем создание с "
    "автогенерацией номера и чтение с фильтрами по статусу, приоритету, периоду и цеху.",
    "POST `/api/work-orders` создаёт заявку с номером и простоями, GET отдаёт "
    "пагинированный список с фильтрами.",
    [("Б / API", "Заявки: создание, чтение, фильтрация")],
    ["src/api/Controllers/WorkOrdersController.cs", "src/api/DTOs/WorkOrderDtos.cs",
     "src/api/Services/WorkOrderService.cs", "src/api/Validators/WorkOrderValidator.cs"],
    [
        S("Создаём заявку", 35,
          "Заявка создаётся в статусе «Черновик». Плановые даты и приоритет обязательны, "
          "аварийная заявка обязана содержать причину — это проверяется и валидатором, и триггером.",
          code="public async Task<ApiResponse<WorkOrderDto>> CreateAsync(CreateWorkOrderDto dto, CancellationToken ct)\n{\n    var equipment = await _db.Equipment.FindAsync([dto.EquipmentId], ct)\n        ?? throw new NotFoundException(\"Оборудование не найдено\");\n\n    var number = await _numbers.NextAsync(ct);\n    var order = new WorkOrder\n    {\n        Id = Guid.NewGuid(),\n        Number = number,\n        EquipmentId = dto.EquipmentId,\n        Title = dto.Title.Trim(),\n        Description = dto.Description?.Trim(),\n        Priority = dto.Priority,\n        Status = WorkOrderStatus.Черновик,\n        PlannedStart = dto.PlannedStart,\n        PlannedEnd = dto.PlannedEnd,\n        CreatedById = CurrentUser.Id\n    };\n\n    _db.WorkOrders.Add(order);\n    await _db.SaveChangesAsync(ct);\n    return ApiResponse<WorkOrderDto>.Ok(order.ToDto(), \"Заявка создана\");\n}",
          lang="csharp", hint="src/api/Services/WorkOrderService.cs",
          png="create", gif="create-postman", cap="POST 201: номер Z-2026-0048, статус Черновик",
          note=["Номер выдаётся **до** сохранения заявки: если бы он выдавался в "
                "контроллере после `SaveChanges`, две одновременные заявки получили "
                "бы один номер. Счётчик держит транзакцию."]),
        S("Валидатор заявки", 30,
          "Пять проверок, которые закрывают критерий «валидация payload»: обязательные "
          "поля, диапазон дат, длины строк и причина для аварийных.",
          code="public class CreateWorkOrderValidator : AbstractValidator<CreateWorkOrderDto>\n{\n    public CreateWorkOrderValidator()\n    {\n        RuleFor(x => x.EquipmentId).NotEmpty();\n        RuleFor(x => x.Title).NotEmpty().MaximumLength(200);\n        RuleFor(x => x.Description).MaximumLength(2000);\n        RuleFor(x => x.Priority).IsInEnum();\n        RuleFor(x => x.PlannedEnd)\n            .GreaterThanOrEqualTo(x => x.PlannedStart)\n            .WithMessage(\"Дата окончания не может быть раньше даты начала\");\n        RuleFor(x => x)\n            .Must(x => x.Priority != WorkOrderPriority.Аварийный || !string.IsNullOrWhiteSpace(x.Description))\n            .WithMessage(\"Для аварийной заявки обязательна причина\");\n    }\n}",
          lang="csharp", hint="src/api/Validators/WorkOrderValidator.cs",
          png="validator", gif="validator-postman", cap="Пять нарушений — пять одинаковых ответов 400",
          note=["Правило на аварийную заявку — `Must` по всему объекту, потому что оно "
                "зависит от двух полей сразу. Валидатор должен возвращать **все** "
                "ошибки разом: `.WithName(\"Причина\")` иначе поймает первое нарушение и "
                "замолчит."]),
        S("Список заявок с фильтрами", 30,
          "Основной экран приложения. Фильтры комбинируются, сортировка по свободному "
          "полю защищена белым списком, чтобы через `OrderBy` нельзя было зайти "
          "на чужое свойство.",
          code="var sort = f.Sort switch\n{\n    \"number\" => q.OrderBy(w => w.Number),\n    \"priority\" => q.OrderByDescending(w => w.Priority),\n    \"downtime\" => q.OrderByDescending(w => w.DowntimeHours),\n    _ => q.OrderByDescending(w => w.CreatedAt)\n};\n\nreturn new(await sort.Skip((f.Page - 1) * f.Size).Take(f.Size)\n    .Select(WorkOrderMapper.ToDto).ToListAsync(ct), total, f.Page, f.Size);",
          lang="csharp", hint="src/api/Services/WorkOrderService.cs",
          png="filter", gif="filter-postman", cap="Фильтр «Аварийный + В работе + март»: 7 из 42",
          note=["`f.Sort` приходит из строки запроса. Без `switch` с белым списком "
                "вы передаёте строку прямо в `OrderBy`, и это уже не разбор запроса, "
                "а исполнение кода из URL."]),
        S("Детальная страница заявки", 25,
          "Отдайте вложенные списки: назначенная бригада, списанные материалы, история "
          "статусов из журнала операций. Один запрос вместо четырёх.",
          code="var order = await _db.WorkOrders.AsNoTracking()\n    .Include(w => w.Equipment).ThenInclude(e => e.Workshop)\n    .Include(w => w.Crew).ThenInclude(c => c.Members)\n    .Include(w => w.Materials).ThenInclude(m => m.Material)\n    .Include(w => w.History.OrderBy(h => h.ChangedAt))\n    .FirstOrDefaultAsync(w => w.Number == number, ct)\n    ?? throw new NotFoundException(\"Заявка не найдена\");\n\nreturn ApiResponse<WorkOrderDto>.Ok(order.ToDto());",
          lang="csharp", hint="src/api/Controllers/WorkOrdersController.cs",
          png="detail", cap="Заявка Z-2026-0048: оборудование, бригада, 3 материала, 4 записи истории",
          note=["Поиск по номеру, а не по `id`, — так удобнее эксперту: в Swagger "
                "не нужно искать GUID. Номер уникален, значит и результат один."]),
    ],
    [("Номер не приходит в ответе", "номер выдаётся в сервисе, а не в контроллере — проверьте порядок"),
     ("400 приходит без списка ошибок", "не подключён `AddValidatorsFromAssembly` в `Program.cs`"),
     ("Список всегда сортируется по дате", "в `switch` сортировки нет ветки для `\"createdAt\"`"),
     ("`Include` не подтягивает материалы", "`Include(w => w.Materials)` тянет связку, а не сам материал — нужен `ThenInclude`")],
    "curl -s 'http://localhost:5080/api/work-orders?priority=%D0%90%D0%B2%D0%B0%D1%80%D0%B8%D0%B9%D0%BD%D1%8B%D0%B9&page=1&size=10' -H \"Authorization: Bearer $TOKEN\" | python3 -m json.tool",
    "feat(api): создание и чтение заявок с фильтрами и валидацией",
))

PAGES.append(P(
    21, "Назначение-бригады-и-завершение", 9,
    "Жизненный цикл заявки: «Черновик» → «Назначена» → «В работе» → «Завершена». "
    "Переходы фиксированы и проверяются на сервере, а простой считает функция базы "
    "`fn_calculate_downtime`.",
    "Четыре метода жизненного цикла, автоматический расчёт простоя, запрет недопустимых переходов.",
    [("Б / API", "Назначение бригад, завершение работ, списание материалов")],
    ["src/api/Controllers/WorkOrdersController.cs",
     "src/api/Services/WorkOrderService.cs", "src/api/Services/DowntimeService.cs"],
    [
        S("Описываем переходы статусов", 30,
          "Переходы задаются словарём: разрешено только из текущего статуса в целевой. "
          "Попытка перепрыгнуть из «Черновика» в «Завершена» — ошибка 409 с пояснением.",
          code="private static readonly Dictionary<WorkOrderStatus, WorkOrderStatus[]> Transitions = new()\n{\n    [WorkOrderStatus.Черновик] = [WorkOrderStatus.Назначена, WorkOrderStatus.Отменена],\n    [WorkOrderStatus.Назначена] = [WorkOrderStatus.Вработе, WorkOrderStatus.Отменена],\n    [WorkOrderStatus.Вработе] = [WorkOrderStatus.Завершена],\n    [WorkOrderStatus.Завершена] = [],\n    [WorkOrderStatus.Отменена] = []\n};\n\nif (!Transitions[order.Status].Contains(target))\n    throw new ConflictException(\n        $\"Нельзя перевести заявку из «{order.Status}» в «{target}»\", ErrorCode.Conflict);",
          lang="csharp", hint="src/api/Services/WorkOrderService.cs",
          png="transitions", cap="Граф переходов: 4 разрешённых, остальные дают 409",
          note=["Словарь переходов — это диаграмма Activity со страницы 04 в коде. "
                "Эксперты любят такое соответствие: спецификация и реализация совпадают."]),
        S("Назначаем бригаду", 30,
          "При назначении меняем статус на «Назначена», пишем время реакции и "
          "сохраняем запись в журнал операций.",
          code="public async Task<ApiResponse<WorkOrderDto>> AssignCrewAsync(Guid id, AssignCrewDto dto, CancellationToken ct)\n{\n    var order = await GetAsync(id, ct);\n    EnsureTransition(order, WorkOrderStatus.Назначена);\n\n    var crew = await _db.Crews.Include(c => c.Members)\n        .FirstOrDefaultAsync(c => c.Id == dto.CrewId, ct)\n        ?? throw new NotFoundException(\"Бригада не найдена\");\n    if (crew.Members.Count == 0)\n        throw new ConflictException(\"В бригаде нет ни одного члена\", ErrorCode.Conflict);\n\n    order.CrewId = crew.Id;\n    order.Status = WorkOrderStatus.Назначена;\n    order.AssignedAt = DateTime.UtcNow;\n\n    await _db.SaveChangesAsync(ct);\n    _log.Write(order.Id, \"Назначена бригада\", crew.Name);\n    return ApiResponse<WorkOrderDto>.Ok(order.ToDto(), $\"Бригада «{crew.Name}» назначена\");\n}",
          lang="csharp", hint="src/api/Services/WorkOrderService.cs",
          png="assign", gif="assign-postman", cap="POST назначения: статус Назначена, assignedAt заполнен",
          note=["Бригада без членов — это ошибка данных, а не пользователя: 409 "
                "правомернее, чем пустой список исполнителей на экране мастера."]),
        S("Переводим заявку в работу", 25,
          "Фиксируем фактическое начало. Плановые даты при этом не меняются — "
          "по ним считается отклонение.",
          code="order.Status = WorkOrderStatus.Вработе;\norder.ActualStart = DateTime.UtcNow;\n\n// оборудование переходит в ремонт\nvar eq = await _db.Equipment.FindAsync([order.EquipmentId], ct);\nif (eq is not null && eq.Status == EquipmentStatus.Работает)\n    eq.Status = EquipmentStatus.ВРемонте;\n\nawait _db.SaveChangesAsync(ct);",
          lang="csharp", hint="src/api/Services/WorkOrderService.cs",
          png="start", cap="Статус В работе, оборудование — В ремонте",
          note=["Статус оборудования меняется здесь же. Если забыть, дашборд "
                "покажет работающее оборудование с открытой заявкой — это сразу видно "
                "эксперту."]),
        S("Завершаем и считаем простой", 35,
          "Фактическая дата окончания рассчитывает простой через функцию базы. "
          "Оборудование возвращается в работу, заявка — в «Завершена».",
          code="public async Task<ApiResponse<WorkOrderDto>> CompleteAsync(Guid id, CompleteWorkOrderDto dto, CancellationToken ct)\n{\n    var order = await GetAsync(id, ct);\n    EnsureTransition(order, WorkOrderStatus.Завершена);\n\n    order.ActualEnd = dto.ActualEnd;\n    order.Result = dto.Result?.Trim();\n    order.Status = WorkOrderStatus.Завершена;\n    order.DowntimeHours = await _downtime.CalculateAsync(order.ActualStart, dto.ActualEnd, ct);\n\n    var eq = await _db.Equipment.FindAsync([order.EquipmentId], ct);\n    if (eq is not null) eq.Status = EquipmentStatus.Работает;\n\n    await _db.SaveChangesAsync(ct);\n    _log.Write(order.Id, \"Завершена\", $\"Простой {order.DowntimeHours} ч\");\n    return ApiResponse<WorkOrderDto>.Ok(order.ToDto(), \"Работы завершены\");\n}",
          lang="csharp", hint="src/api/Services/DowntimeService.cs",
          png="complete", gif="complete-postman", cap="Завершена: простой 6,5 ч, оборудование снова Работает",
          note=["Простой считается функцией базы, а не в C#. Так одна и та же формула "
                "работает в API, в отчёте и в SQL-запросе эксперта. Формула: "
                "`EXTRACT(EPOCH FROM (p_end - p_start)) / 3600`, округление до двух знаков."]),
        S("Отменяем заявку", 20,
          "Отмена доступна из «Черновика» и «Назначена», обязательно с причиной. "
          "Причины попадают в журнал операций.",
          code="if (!Transitions[order.Status].Contains(WorkOrderStatus.Отменена))\n    throw new ConflictException(\"Отменить можно только черновик или назначенную заявку\", ErrorCode.Conflict);\n\nif (string.IsNullOrWhiteSpace(dto.Reason))\n    throw new ValidationException(\"Причина отмены обязательна\");\n\norder.Status = WorkOrderStatus.Отменена;\norder.CancelReason = dto.Reason;\nawait _db.SaveChangesAsync(ct);",
          lang="csharp", hint="src/api/Services/WorkOrderService.cs",
          png="cancel", gif="cancel-postman", cap="Отмена из «В работе» даёт 409, из «Назначена» — 200",
          note=["Проверка причины идёт **до** проверки перехода — иначе клиент получит "
                "409 про переход и не поймёт, что не так с причиной."]),
    ],
    [("409 при завершении заявки", "она ещё не в статусе «В работе» — проверьте граф переходов"),
     ("Простой считается в часах с дробью", "округляйте до двух знаков: `Math.Round(h, 2)`"),
     ("Простой отрицательный", "фактическая дата окончания раньше начала — сработал триггер дат"),
     ("Оборудование не вернулось в работу", "забыли сбросить статус в `CompleteAsync`")],
    "psql -h 127.0.0.1 -U toirprof -d toirprof -c \"SELECT number, status, downtime_hours FROM work_orders WHERE status='Завершена' ORDER BY created_at DESC LIMIT 5;\"",
    "feat(api): жизненный цикл заявки — назначение, начало, завершение, отмена",
))
# === BLOCK-E5: спринт 11, страницы 22–25 ===

PAGES.append(P(
    22, "Бригады-и-члены-бригад", 10,
    "Ремонтные бригады состоят из пользователей. Состав бригады задаётся только "
    "администратором, а мастер бригады определяется автоматически по таблице членов — "
    "на этом держится изоляция данных со страницы 15.",
    "CRUD бригад, управление составом, запрет удаления бригады с активными заявками.",
    [("Б / API", "Ремонтные бригады")],
    ["src/api/Controllers/CrewsController.cs", "src/api/DTOs/CrewDtos.cs",
     "src/api/Services/CrewService.cs"],
    [
        S("Описываем бригаду и её состав", 25,
          "Бригада имеет название, специализацию и список участников. Состав хранится "
          "отдельной таблицей `crew_members` — один человек может работать только в одной бригаде.",
          code="public record CrewDto(Guid Id, string Name, string? Specialization, bool IsActive, List<CrewMemberDto> Members);\n\n[HttpGet]\npublic async Task<IActionResult> GetAll(CancellationToken ct)\n    => Ok(ApiResponse<List<CrewDto>>.Ok(await _service.GetAllAsync(ct)));",
          lang="csharp", hint="src/api/Controllers/CrewsController.cs",
          png="crews", cap="Три бригады, в первой четыре человека",
          note=["`Crew` — коллекция в контексте EF, но в `DBeaver` и в Swagger это "
                "обычная таблица. Не называйте таблицу `crew` — Postgres и EF разойдутся "
                "в именах при генерации миграций."]),
        S("Добавляем и убираем членов", 30,
          "Добавление участника проверяет, что он уже не в другой бригаде: иначе "
          "изоляция данных перестаёт работать.",
          code="if (await _db.CrewMembers.AnyAsync(m => m.UserId == dto.UserId && m.CrewId != crewId, ct))\n    throw new ConflictException(\"Сотрудник уже состоит в другой бригаде\", ErrorCode.Conflict);\n\nvar already = await _db.CrewMembers.AnyAsync(m => m.CrewId == crewId && m.UserId == dto.UserId, ct);\nif (already)\n    throw new ConflictException(\"Сотрудник уже в бригаде\", ErrorCode.Conflict);",
          lang="csharp", hint="src/api/Services/CrewService.cs",
          png="members", gif="members-postman", cap="409 при добавлении мастера в другую бригаду",
          note=["UNIQUE на `(crew_id, user_id)` в базе закрывает оба случая на уровне "
                "индекса. Проверки в сервисе дают понятное сообщение, индекс — гарантию."]),
        S("Удаляем бригаду осторожно", 30,
          "Удаление бригады, у которой есть заявки, запрещено. Соответствует "
          "`ON DELETE SET NULL` в схеме: заявка сохранится, но останется без исполнителя.",
          code="var active = await _db.WorkOrders.CountAsync(w => w.CrewId == id && w.Status != WorkOrderStatus.Завершена\n    && w.Status != WorkOrderStatus.Отменена, ct);\n\nif (active > 0)\n    return Conflict(ApiResponse<object>.Fail(\n        $\"У бригады {active} незакрытых заявок\", ErrorCode.Conflict));\n\n_db.Crews.Remove(crew);   // crew_members уйдут каскадом\nawait _db.SaveChangesAsync(ct);\nreturn NoContent();",
          lang="csharp", hint="src/api/Services/CrewService.cs",
          png="crew-delete", gif="crew-409", cap="Удаление занятой бригады даёт 409 с числом заявок",
          note=["Считайте незакрытые заявки, а не все: завершённые истории удалению "
                "бригады не мешают, а именно они доказывают, что бригада работала."]),
        S("Сводка по бригадам", 25,
          "Для дашборда руководителя: сколько заявок выполнено, средний простой, "
          "доля аварийных. Один агрегирующий запрос.",
          code="var stats = await _db.WorkOrders.AsNoTracking()\n    .Where(w => w.CrewId != null)\n    .GroupBy(w => new { w.CrewId, w.Crew!.Name })\n    .Select(g => new CrewStatsDto(g.Key.Name, g.Key.CrewId, g.Count(),\n        g.Count(w => w.Status == WorkOrderStatus.Завершена),\n        g.Where(w => w.DowntimeHours != null).Average(w => w.DowntimeHours),\n        g.Count(w => w.Priority == WorkOrderPriority.Аварийный)))\n    .OrderByDescending(s => s.Total)\n    .ToListAsync(ct);",
          lang="csharp", hint="src/api/Services/CrewService.cs",
          png="crew-stats", gif="crew-stats-postman", cap="Три бригады: 18, 14 и 10 заявок",
          note=["`Average` по nullable-полю вернёт `null`, если все значения пустые. "
                "На клиенте показывайте прочерк, а не `0`, иначе «нет простоев» "
                "будет читаться как «мгновенный ремонт»."]),
    ],
    [("409 при добавлении участника", "он уже состоит в другой бригаде"),
     ("Удаление бригады молча теряет состав", "проверьте `ON DELETE CASCADE` на `crew_members`"),
     ("`Average` возвращает null", "нет завершённых заявок с простоем — это допустимо"),
     ("Сводка не сходится с числом заявок", "фильтр по статусам отличается от фильтра дашборда")],
    "curl -s http://localhost:5080/api/crews/stats -H \"Authorization: Bearer $TOKEN\" | python3 -m json.tool",
    "feat(api): ремонтные бригады, состав и сводные показатели",
))

PAGES.append(P(
    23, "Материалы-ЗИП-и-списание", 10,
    "Склад ЗИП и списание материалов в заявку. Завершение работы без списания "
    "материалов — типичная ошибка на защите, поэтому списание оформляется отдельным "
    "методом с пересчётом остатков.",
    "Справочник материалов, текущий остаток, списание позиций в заявку, автоподсчёт стоимости.",
    [("Б / API", "Материалы и ЗИП, списание в заявку")],
    ["src/api/Controllers/MaterialsController.cs", "src/api/Controllers/WorkOrdersController.cs",
     "src/api/Services/MaterialService.cs"],
    [
        S("Справочник материалов и остатки", 25,
          "У материала есть артикул (SKU), наименование, единица измерения, цена и "
          "текущий остаток. Остаток уменьшается при списании — держите его в той же таблице.",
          code="public record MaterialDto(Guid Id, string Sku, string Name, string Unit, decimal Price, decimal Stock);\n\nRuleFor(x => x.Sku).NotEmpty().Matches(@\"^[A-Z0-9-]{3,32}$\");\nRuleFor(x => x.Price).GreaterThanOrEqualTo(0);\nRuleFor(x => x.Stock).GreaterThanOrEqualTo(0);",
          lang="csharp", hint="src/api/Controllers/MaterialsController.cs",
          png="materials", cap="Справочник: подшипник 6-205 — 12 шт по 850 руб.",
          note=["Артикул в верхнем регистре и с дефисом: так его проще вводить "
                "с клавиатуры в мастерской, а UNIQUE нечувствителен к регистру "
                "только при явном `citext`."]),
        S("Списываем материал в заявку", 35,
          "Списание уменьшает остаток, добавляет позицию в заявку и пересчитывает "
          "итоговую стоимость. Недостаток остатка — 409.",
          code="public async Task<ApiResponse<MaterialUseDto>> WriteOffAsync(Guid orderId, WriteOffDto dto, CancellationToken ct)\n{\n    var order = await _service.GetAsync(orderId, ct);\n    if (order.Status is WorkOrderStatus.Завершена or WorkOrderStatus.Отменена)\n        throw new ConflictException(\"Заявка закрыта, списание невозможно\", ErrorCode.Conflict);\n\n    var material = await _db.Materials.FindAsync([dto.MaterialId], ct)\n        ?? throw new NotFoundException(\"Материал не найден\");\n    if (material.Stock < dto.Quantity)\n        throw new ConflictException(\n            $\"Недостаточно материала: осталось {material.Stock} {material.Unit}\", ErrorCode.Conflict);\n\n    material.Stock -= dto.Quantity;\n    var line = new WorkOrderMaterial\n    {\n        WorkOrderId = orderId, MaterialId = material.Id,\n        Quantity = dto.Quantity, Price = material.Price,\n        Cost = Math.Round(dto.Quantity * material.Price, 2)\n    };\n    _db.WorkOrderMaterials.Add(line);\n    await _db.SaveChangesAsync(ct);\n    return ApiResponse<MaterialUseDto>.Ok(line.ToDto(), \"Материал списан\");\n}",
          lang="csharp", hint="src/api/Services/MaterialService.cs",
          png="writeoff", gif="writeoff-postman", cap="Списано 4 шт подшипника: остаток 8, стоимость 3400,00",
          note=["Цену сохраняйте в позиции списания, а не берите из справочника при "
                "чтении: цена в справочнике изменится, а история заявки — нет. "
                "Иначе отчёт за прошлый месяц пересчитается задним числом."]),
        S("Считаем итоговую стоимость", 30,
          "Стоимость заявки — сумма позиций. Именно эту цифру проверяет юнит-тест "
          "`calculateTotalMaterialCost` на странице 47.",
          code="var total = await _db.WorkOrderMaterials.AsNoTracking()\n    .Where(m => m.WorkOrderId == orderId)\n    .SumAsync(m => m.Cost, ct);\n\nvar totalQty = await _db.WorkOrderMaterials.AsNoTracking()\n    .Where(m => m.WorkOrderId == orderId)\n    .SumAsync(m => m.Quantity, ct);\n\nreturn ApiResponse<MaterialCostDto>.Ok(new(orderId, total, totalQty));",
          lang="csharp", hint="src/api/Controllers/WorkOrdersController.cs",
          png="cost", gif="cost-postman", cap="Итог заявки Z-2026-0048: 7 300,00 руб. по трём позициям",
          note=["Сумма считается в SQL (`SUM`), а не перебором списка. Для пустого "
                "набора `SUM` вернёт `null` — приводите к нулю через `?? 0m`, иначе "
                "JSON покажет `cost: null` и клиент сломается на форматировании."]),
        S("Закрываем остатки и историю", 20,
          "Остаток меньше минимального порога помечайте как дефицитный, чтобы это "
          "было видно в справочнике без дополнительных расчётов.",
          code="public async Task<List<MaterialShortageDto>> GetShortagesAsync(CancellationToken ct)\n    => await _db.Materials.AsNoTracking()\n        .Where(m => m.Stock <= m.MinStock)\n        .OrderBy(m => m.Stock)\n        .Select(m => new MaterialShortageDto(m.Id, m.Name, m.Stock, m.MinStock, m.Unit))\n        .ToListAsync(ct);",
          lang="csharp", hint="src/api/Services/MaterialService.cs",
          png="shortage", gif="shortage-postman", cap="Дефицит: ремень приводной (2 из 6), масло И-20 (3 из 10)",
          note=["Порог `min_stock` — поле справочника, а не константа в коде. "
                "Разные материалы заканчиваются в разные сроки, единый порог "
                "в коде всегда кому-то мешает."]),
    ],
    [("409 при списании", "остатка не хватает — так и должно быть"),
     ("`cost` приходит как `null`", "нет позиций списания или забыли `?? 0m`"),
     ("Стоимость пересчитывается при смене цены", "храните цену в позиции списания"),
     ("Остаток ушёл в минус", "не хватает блокировки строки — используйте атомарный `UPDATE … WHERE stock >= {0}`")],
    "curl -s http://localhost:5080/api/work-orders/Z-2026-0048/cost -H \"Authorization: Bearer $TOKEN\" | python3 -m json.tool",
    "feat(api): материалы, ЗИП и списание с пересчётом стоимости заявки",
))

PAGES.append(P(
    24, "Сводные-KPI-и-дашборд", 11,
    "Один запрос, который кормит шесть KPI-карточек дашборда. Здесь же — правило: "
    "данные собираются агрегатами в базе, а не перебором строк в память.",
    "GET `/api/dashboard/summary` возвращает все показатели сразу, с разбивкой по цехам.",
    [("Б / API", "Сводные показатели и дашборд")],
    ["src/api/Controllers/DashboardController.cs", "src/api/Services/DashboardService.cs",
     "src/api/DTOs/DashboardDtos.cs"],
    [
        S("Определяем показатели", 25,
          "Шесть карточек: всего заявок, в работе, завершено за период, средний простой, "
          "доля аварийных, выполнение планового ТО. Каждый — одно число и подпись-период.",
          code="public record DashboardSummary(\n    int TotalOrders,\n    int InProgress,\n    int Completed,\n    decimal AverageDowntimeHours,\n    decimal EmergencyShare,\n    decimal MaintenancePlanShare,\n    IReadOnlyList<WorkshopSlice> ByWorkshop);\n\npublic record WorkshopSlice(Guid WorkshopId, string Name, int Total, int Completed, decimal DowntimeHours);",
          lang="csharp", hint="src/api/DTOs/DashboardDtos.cs",
          png="dto", cap="DashboardSummary с шестью показателями и срезом по цехам",
          note=["`EmergencyShare` считайте в процентах: `Emergency * 100.0 / Total`. "
                "Целочисленное деление в C# даст 0 при 3 из 47 — классическая "
                "ошибка, которую эксперты находят сразу."]),
        S("Собираем агрегаты", 35,
          "Один запрос с группировкой по цехам и `FILTER` для счётчиков — PostgreSQL "
          "умеет считать разные условия в одной строке.",
          code="var rows = await _db.WorkOrders.AsNoTracking()\n    .Where(w => w.CreatedAt >= period.From && w.CreatedAt < period.To)\n    .Select(w => new { w.Status, w.Priority, w.DowntimeHours, w.Equipment.WorkshopId, w.Equipment.Workshop.Name })\n    .ToListAsync(ct);\n\nvar total = rows.Count;\nvar summary = new DashboardSummary(\n    TotalOrders: total,\n    InProgress: rows.Count(w => w.Status == WorkOrderStatus.Вработе),\n    Completed: rows.Count(w => w.Status == WorkOrderStatus.Завершена),\n    AverageDowntimeHours: Math.Round(rows.Where(w => w.DowntimeHours != null).Average(w => w.DowntimeHours ?? 0m), 2),\n    EmergencyShare: total == 0 ? 0m : Math.Round(rows.Count(w => w.Priority == WorkOrderPriority.Аварийный) * 100m / total, 1),\n    MaintenancePlanShare: Math.Round(await _db.MaintenanceSchedule.AsNoTracking()\n        .CountAsync(m => m.Status == \"Выполнено\", ct) * 100m\n        / Math.Max(1, await _db.MaintenanceSchedule.AsNoTracking().CountAsync(ct)), 1),\n    ByWorkshop: rows.GroupBy(w => new { w.WorkshopId, w.Name })\n        .Select(g => new WorkshopSlice(g.Key.WorkshopId, g.Key.Name, g.Count(),\n            g.Count(w => w.Status == WorkOrderStatus.Завершена),\n            g.Where(w => w.DowntimeHours != null).Sum(w => w.DowntimeHours ?? 0m))).ToList());",
          lang="csharp", hint="src/api/Services/DashboardService.cs",
          png="summary", gif="summary-postman", cap="Дашборд за март: 47 заявок, средний простой 6,3 ч, аварийных 19,1 %",
          note=["Материализация строк через `.ToListAsync()` здесь осознанна: на объёме "
                "в несколько сотен строк это дешевле и заметно проще, чем шесть "
                "отдельных запросов. На больших объёмах — возвращайтесь к агрегатам "
                "в SQL."]),
        S("Разбивка по цехам и статусам", 25,
          "Дашборду нужен срез по цехам для столбчатой диаграммы и по статусам для круговой. "
          "Отдавайте готовые массивы, клиент не должен считать.",
          code="var byStatus = await _db.WorkOrders.AsNoTracking()\n    .Where(w => w.CreatedAt >= period.From && w.CreatedAt < period.To)\n    .GroupBy(w => w.Status)\n    .Select(g => new StatusSlice(g.Key.ToString(), g.Count()))\n    .ToListAsync(ct);\n\nvar byMonth = await _db.WorkOrders.AsNoTracking()\n    .Where(w => w.CreatedAt >= period.From)\n    .GroupBy(w => w.CreatedAt.Month)\n    .OrderBy(g => g.Key)\n    .Select(g => new { Month = g.Key, Count = g.Count() })\n    .ToListAsync(ct);",
          lang="csharp", hint="src/api/Services/DashboardService.cs",
          png="slices", gif="slices-postman", cap="Срезы: 4 статуса, 3 месяца, 2 цеха",
          note=["Группировка по enum в EF даёт числовое значение. Приводите к строке "
                "явно (`g.Key.ToString()`), иначе в JSON попадут числа вместо "
                "русских названий."]),
        S("Кэш на 60 секунд", 25,
          "Дашборд автообновляется раз в минуту, а открывают его несколько человек "
          "одновременно. Кэш на сервере сокращает нагрузку в разы.",
          code="public class DashboardService(AppDbContext db, IMemoryCache cache) : IDashboardService\n{\n    private static readonly TimeSpan Ttl = TimeSpan.FromSeconds(60);\n\n    public async Task<DashboardSummary> GetSummaryAsync(DateRange period, CancellationToken ct)\n    {\n        var key = $\"dashboard:{period.From:yyyyMMdd}:{period.To:yyyyMMdd}\";\n        if (cache.TryGetValue<DashboardSummary>(key, out var cached)) return cached!;\n\n        var result = await BuildAsync(period, ct);\n        cache.Set(key, result, Ttl);\n        return result;\n    }\n}",
          lang="csharp", hint="src/api/Services/DashboardService.cs",
          png="cache", gif="cache-load", cap="Два запроса подряд: первый 120 мс, второй 3 мс",
          note=["Ключ кэша обязан включать период. Без периода все пользователи получат "
                "одни и те же данные, и «за вчера» и «за текущий месяц» покажут "
                "одинаковые цифры — заметная ошибка на демонстрации."]),
    ],
    [("Доля аварийных равна 0", "целочисленное деление — умножьте числитель на `100m`"),
     ("Все запросы возвращают одни и те же данные", "в ключ кэша не входит период"),
     ("Статусы приходят числами", "приведите enum к строке в проекции"),
     ("Дашборд грузится дольше 2 секунд", "уберите лишние `Include` и лишние раунды к базе")],
    "time curl -s http://localhost:5080/api/dashboard/summary -H \"Authorization: Bearer $TOKEN\"",
    "feat(api): сводные KPI дашборда со срезом по цехам и кэшем",
))

PAGES.append(P(
    25, "Аналитика-простоев-бригад-и-PDF", 11,
    "Тяжёлые аналитические срезы и экспорт: простои по оборудованию, рейтинг бригад, "
    "выгрузка в PDF и временная ссылка на отчёт, которая живёт 15 секунд.",
    "GET `/api/analytics/*` отдаёт срезы, POST `/api/reports` создаёт PDF, "
    "ссылка `/api/reports/{token}` живёт 15 секунд.",
    [("Б / API", "Аналитика простоев и эффективности, экспорт отчётов в PDF")],
    ["src/api/Controllers/AnalyticsController.cs", "src/api/Controllers/ReportsController.cs",
     "src/api/Services/ReportService.cs"],
    [
        S("Срез простоев по оборудованию", 30,
          "Топ участков по простою за период: оборудование, суммарные часы, число "
          "заявок, доля аварийных. Это основа блока «Анализ простоев» на web-клиенте.",
          code="var downtime = await _db.WorkOrders.AsNoTracking()\n    .Where(w => w.ActualStart >= period.From && w.ActualStart < period.To && w.DowntimeHours != null)\n    .GroupBy(w => new { w.EquipmentId, w.Equipment.InventoryNumber, w.Equipment.Name })\n    .Select(g => new DowntimeSlice(\n        g.Key.InventoryNumber, g.Key.Name,\n        g.Sum(x => x.DowntimeHours), g.Count(),\n        g.Count(x => x.Priority == WorkOrderPriority.Аварийный)))\n    .OrderByDescending(s => s.DowntimeHours)\n    .Take(10)\n    .ToListAsync(ct);",
          lang="csharp", hint="src/api/Controllers/AnalyticsController.cs",
          png="downtime", gif="downtime-postman", cap="Топ простоев: пресс ПР-100 — 34,5 ч за квартал",
          note=["Фильтр по `ActualStart`, а не по `CreatedAt`: заявку создали в феврале, "
                "а ремонт шёл в марте. Для отчёта о простоях важен период работ."]),
        S("Рейтинг эффективности бригад", 30,
          "Оценка по трём показателям: доля выполненных в срок, средний простой, "
          "число аварийных. Итоговый балл считайте явно и показывайте в ответе — "
          "это то, что спрашивают на защите.",
          code="var rating = await _db.WorkOrders.AsNoTracking()\n    .Where(w => w.CrewId != null && w.ActualStart >= period.From)\n    .GroupBy(w => new { w.CrewId, w.Crew!.Name })\n    .Select(g => new CrewRatingDto(\n        g.Key.CrewId, g.Key.Name, g.Count(),\n        g.Count(w => w.Status == WorkOrderStatus.Завершена),\n        g.Count(w => w.Status == WorkOrderStatus.Завершена && w.ActualEnd <= w.PlannedEnd),\n        g.Where(w => w.DowntimeHours != null).Average(w => w.DowntimeHours),\n        g.Count(w => w.Priority == WorkOrderPriority.Аварийный)))\n    .ToListAsync(ct);\n\nforeach (var r in rating)\n    r.Score = Math.Round(100m * r.OnTimeShare / 100m\n        - Math.Max(0, r.AverageDowntimeHours - 4m) * 2m\n        - r.Emergency * 1.5m, 1);",
          lang="csharp", hint="src/api/Services/DashboardService.cs",
          png="rating", gif="rating-postman", cap="Рейтинг: Бригада №1 — 92,4 балла, Бригада №3 — 61,0",
          note=["Публикуйте формулу в `docs/`: эксперт должен видеть, что балл "
                "считается по правилам, а не «на глаз». Отсутствие формулы — минус "
                "к критерию аналитики."]),
        S("Готовим отчёт в PDF", 35,
          "Формируйте PDF на сервере и отдавайте файл. Библиотека выбирается по стеку; "
          "важно, чтобы кириллица в шрифте была — иначе отчёт пустой.",
          code="dotnet add api package QuestPDF\n\nDocument.Create(container =>\n{\n    container.Page(page =>\n    {\n        page.Header().Text(text => text.Span(\"Отчёт по ремонтам за \" + periodTitle)\n            .FontSize(18).Bold());\n        page.Content().Table(table =>\n        {\n            table.ColumnsDefinition(c => { c.RelativeColumn(); c.RelativeColumn(); c.RelativeColumn(); });\n            foreach (var row in rows)\n            {\n                table.Cell().Text(row.Number);\n                table.Cell().Text(row.EquipmentName);\n                table.Cell().Text(row.Downtime.ToString(\"0.00\") + \" ч\");\n            }\n        });\n    });\n}).GeneratePdf();",
          lang="csharp", hint="src/api/Services/ReportService.cs",
          png="pdf", gif="pdf-generate", cap="Сформирован PDF: 3 страницы, таблица заявок с простоями",
          note=["Кириллица требует встроенного шрифта: у QuestPDF это `Lato`, "
                "у ReportLab — `DejaVuSans`. Без него вместо русского текста "
                "получаются пустые прямоугольники, и эксперт это видит сразу."]),
        S("Временная ссылка на 15 секунд", 35,
          "Отчёт отдаём не в ответе, а по одноразовой ссылке: токен хранится в кэше "
          "с TTL 15 секунд. Такой сценарий прямо описан в задании.",
          code="public async Task<string> CreateLinkAsync(ReportKind kind, DateRange period, CancellationToken ct)\n{\n    var token = Convert.ToHexString(RandomNumberGenerator.GetBytes(16)).ToLowerInvariant();\n    var path = await BuildPdfAsync(kind, period, ct);\n    _cache.Set($\"report:{token}\", path, TimeSpan.FromSeconds(15));\n    return token;\n}\n\npublic async Task<IActionResult> DownloadAsync(string token, CancellationToken ct)\n{\n    if (!_cache.TryGetValue<string>($\"report:{token}\", out var path))\n        return NotFound(ApiResponse<object>.Fail(\"Ссылка истекла, запросите отчёт заново\", ErrorCode.NotFound));\n    return PhysicalFile(path, \"application/pdf\", $\"report-{DateTime.Now:yyyyMMdd-HHmm}.pdf\");\n}",
          lang="csharp", hint="src/api/Controllers/ReportsController.cs",
          png="report-link", gif="report-link-run", cap="Ссылка выдана; повторный запрос через 20 секунд даёт 404",
          note=["15 секунд — это осознанно короткий срок. Проверять его нужно "
                "на демонстрации: эксперт попросит ссылку дважды подряд и убедится, "
                "что второй раз работает не будет. Так и задумано."]),
    ],
    [("404 на ссылку сразу", "TTL 15 секунд истёк — запросите новый токен"),
     ("PDF без русского текста", "не задан шрифт с кириллицей"),
     ("Рейтинг всегда 100", "деление целочисленное либо формула делит не на то поле"),
     ("Отчёт пустой за период", "фильтр по `ActualStart` отсекает всё — проверьте границы периода")],
    "curl -s -X POST http://localhost:5080/api/reports -H \"Authorization: Bearer $TOKEN\" -H 'Content-Type: application/json' -d '{\"kind\":\"downtime\",\"from\":\"2026-01-01\",\"to\":\"2026-03-31\"}'",
    "feat(api): аналитика простоев, рейтинг бригад и экспорт PDF по временной ссылке",
))
# === BLOCK-F: спринты 12–13, страницы 26–30 (Desktop) ===

PAGES.append(P(
    26, "Проект-Desktop-клиента-Avalonia", 12,
    "Создаём нативное Avalonia-приложение: каркас MVVM, тема, DI и пустое окно, "
    "которое запускается и на Windows, и на РедОС. WebView в задании запрещён — "
    "клиент рисуем своими контролами и ходим в API по HTTP.",
    "Открывается окно приложения, в логе видно старт клиента; проект собирается "
    "командой одной строкой.",
    [("Б / Desktop", "Нативная реализация без WebView"),
     ("Б / Desktop", "Единый стиль оформления на всех экранах")],
    ["src/desktop/ToirProf.Desktop.csproj", "src/desktop/Program.cs",
     "src/desktop/App.axaml", "src/desktop/App.axaml.cs",
     "src/desktop/ViewModels/BaseViewModel.cs", "src/desktop/Styles/Theme.axaml"],
    [
        S("Создаём проект Avalonia", 30,
          "Шаблон создаётся из корня репозитория, чтобы все проекты решения лежали рядом "
          "и собирались одним решением.",
          code="dotnet new install Avalonia.Templates\ndotnet new avalonia.app -n ToirProf.Desktop -o src/desktop -f net10.0\ndotnet sln ToirProf.slnx add src/desktop/ToirProf.Desktop.csproj",
          lang="bash", hint="src/desktop/ToirProf.Desktop.csproj",
          png="csproj", gif="csproj-create", cap="csproj: Avalonia 11.3, ReactiveUI, CommunityToolkit.Mvvm",
          note=["Шаблон тянет за собой `ClassicDesktop` с окном и view. Если версия "
                "Avalonia в шаблоне старше 11, поставьте пакеты явно: "
                "`dotnet add package Avalonia --version 11.3.1`. На РедОС разница "
                "видна — старые сборки падают на отсутствующих иконках."]),
        S("Подключаем общие контракты", 25,
          "Формат ответа `{success, data, message, error_code}` и коды ошибок живут в "
          "общем проекте — их используют и API, и оба клиента.",
          code="<ProjectReference Include=\"..\\ToirProf.Shared\\ToirProf.Shared.csproj\" />\n<PackageReference Include=\"Avalonia\" Version=\"11.3.1\" />\n<PackageReference Include=\"Avalonia.Desktop\" Version=\"11.3.1\" />\n<PackageReference Include=\"Avalonia.Themes.Fluent\" Version=\"11.3.1\" />\n<PackageReference Include=\"Avalonia.ReactiveUI\" Version=\"11.3.1\" />\n<PackageReference Include=\"CommunityToolkit.Mvvm\" Version=\"8.4.0\" />\n<PackageReference Include=\"Refit\" Version=\"8.0.0\" />",
          lang="xml", hint="src/desktop/ToirProf.Desktop.csproj",
          png="packages", cap="Ссылка на ToirProf.Shared и пакеты Avalonia 11.3.1",
          note=["Refit даёт описание REST-вызовов аннотациями — метод выглядит как "
                "обычная функция, а HTTP-детали генерируются. Для этого нужен "
                "один вызов `RefitClient.For<IApiService>()` в `App.axaml.cs`."]),
        S("Пишем базовую ViewModel", 30,
          "Все экраны наследуют один базовый класс: команда, флаг загрузки и текст "
          "ошибки есть у каждого экрана, дублировать их не нужно.",
          code="public abstract partial class BaseViewModel : ObservableObject\n{\n    [ObservableProperty] private bool _isBusy;\n    [ObservableProperty] private string _errorMessage = string.Empty;\n    [ObservableProperty] private string _pageTitle = string.Empty;\n\n    protected async Task RunAsync(Func<Task> action)\n    {\n        if (IsBusy) return;\n        try\n        {\n            IsBusy = true;\n            ErrorMessage = string.Empty;\n            await action();\n        }\n        catch (ApiException ex)\n        {\n            ErrorMessage = ex.Message;\n        }\n        finally\n        {\n            IsBusy = false;\n        }\n    }\n}",
          lang="csharp", hint="src/desktop/ViewModels/BaseViewModel.cs",
          png="base-vm", cap="BaseViewModel: IsBusy, ErrorMessage и защита от повторного входа",
          note=["Проверка `if (IsBusy) return;` в начале `RunAsync` закрывает "
                "классическую проблему: пользователь дважды кликнул «Обновить» и "
                "получил два одинаковых запроса. На демонстрации это выглядит "
                "как «приложение зависло»."]),
        S("Настраиваем тему и шрифты", 30,
          "Единая тема задаёт цвета, отступы и размеры шрифта один раз — потом все "
          "экраны выглядят одинаково.",
          code="<Styles xmlns=\"https://github.com/avaloniaui\"\n        xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\">\n  <Styles.Resources>\n    <Color x:Key=\"BrandColor\">#1F6FEB</Color>\n    <Color x:Key=\"DangerColor\">#C62828</Color>\n    <x:Double x:Key=\"ControlHeight\">44</x:Double>\n  </Styles.Resources>\n\n  <Style Selector=\"TextBlock\">\n    <Setter Property=\"FontSize\" Value=\"14\" />\n  </Style>\n\n  <Style Selector=\"Button\">\n    <Setter Property=\"MinHeight\" Value=\"44\" />\n    <Setter Property=\"Padding\" Value=\"16,8\" />\n  </Style>\n</Styles>",
          lang="xml", hint="src/desktop/Styles/Theme.axaml",
          png="theme", gif="theme-window", cap="Окно с применённой темой: 1440×900, шрифт 14",
          note=["Высота интерактивных элементов 44 px — требование дизайна и "
                "привычка мастеров. Меньше 40 px на ноутбуке с тачскрином "
                "приводит к промахам по кнопке."]),
        S("Собираем и запускаем", 35,
          "Первая проверка: проект собирается и открывает окно без ошибок.",
          code="dotnet build src/desktop/ToirProf.Desktop.csproj -c Release\ndotnet run --project src/desktop/ToirProf.Desktop.csproj",
          lang="bash", hint="src/desktop/",
          png="run", gif="run-window", cap="Пустое окно приложения запущено",
          note=["На РедОС окно может не появиться, если не установлен `libx11` и "
                "шрифты. Проверяйте `dotnet run` в Git Bash с активной сессией "
                "графического окружения — по SSH без X11 окно не откроется, но "
                "проект при этом собирается и это уже половина проверки."]),
    ],
    [("Не найден `ToirProf.Shared.csproj`", "проект общих контрактов ещё не добавлен в решение"),
     ("Окно не открывается на РедОС", "поставьте `libx11` и шрифты через `dnf`, проверьте `dotnet build`"),
     ("Ошибка загрузки темы Fluent", "не подключён пакет `Avalonia.Themes.Fluent` или не добавлен в `App.axaml`"),
     ("Двойной клик шлёт два запроса", "добавьте проверку `IsBusy` в `RunAsync`")],
    "dotnet build src/desktop/ToirProf.Desktop.csproj -c Release",
    "feat(desktop): каркас Avalonia-приложения с MVVM, темой и общей обёрткой ответа",
))

PAGES.append(P(
    27, "Оболочка-навигация-и-авторизация", 12,
    "Собираем оболочку приложения: экран входа, боковое меню, верхняя панель, "
    "хлебные крошки и автоблокировку по бездействию. Эти элементы — общие "
    "требования задания, они считаются один раз на всё приложение.",
    "Приложение открывается экраном входа, после входа — с боковым меню и верхней "
    "панелью; бездействие 15 секунд возвращает на экран входа.",
    [("Б / Desktop", "Боковое меню и верхняя панель"),
     ("Б / Desktop", "Хлебные крошки"),
     ("Б / Desktop", "Автоблокировка при бездействии")],
    ["src/desktop/Views/LoginView.axaml", "src/desktop/Views/LoginView.axaml.cs",
     "src/desktop/Views/MainWindow.axaml", "src/desktop/Views/MainWindow.axaml.cs",
     "src/desktop/ViewModels/LoginViewModel.cs", "src/desktop/ViewModels/MainWindowViewModel.cs",
     "src/desktop/Services/AuthService.cs", "src/desktop/Services/TokenStorage.cs"],
    [
        S("Экран входа", 35,
          "Форма с логином, паролем и кнопкой. Ошибка неверного пароля приходит "
          "из API кодом 401 и показывается под полем, а не в модальном окне.",
          code="<StackPanel Spacing=\"12\" Width=\"360\">\n  <TextBlock Text=\"ТОиР-Проф\" FontSize=\"28\" FontWeight=\"Bold\" HorizontalAlignment=\"Center\" />\n  <TextBox Watermark=\"Логин\" Text=\"{Binding Login}\" />\n  <TextBox Watermark=\"Пароль\" PasswordChar=\"•\" Text=\"{Binding Password}\" KeyDown=\"OnPasswordKeyDown\" />\n  <TextBlock Text=\"{Binding ErrorMessage}\" Foreground=\"#C62828\" TextWrapping=\"Wrap\" />\n  <Button Content=\"Войти\" Command=\"{Binding LoginCommand}\" IsEnabled=\"{Binding !IsBusy}\" HorizontalAlignment=\"Stretch\" />\n</StackPanel>",
          lang="xml", hint="src/desktop/Views/LoginView.axaml",
          png="login", gif="login-flow", cap="Экран входа: пустое состояние и состояние ошибки 401",
          note=["Enter в поле пароля должен вызывать ту же команду, что и кнопка. "
                "Мастер вводит пароль десятки раз за смену — каждый раз тянуться "
                "мышью к кнопке раздражает."]),
        S("Боковое меню и верхняя панель", 35,
          "Меню строится по ролям: мастеру не показываем пользователей и справочники, "
          "руководителю — всё.",
          code="private IReadOnlyList<NavItem> BuildMenu(string role) => role switch\n{\n    \"MASTER\" => new[]\n    {\n        new NavItem(\"Дашборд\", \"/dashboard\"),\n        new NavItem(\"Оборудование\", \"/equipment\"),\n        new NavItem(\"График ТО\", \"/schedule\"),\n        new NavItem(\"Заявки\", \"/work-orders\"),\n        new NavItem(\"Отчёты\", \"/reports\"),\n    },\n    _ => new[]\n    {\n        new NavItem(\"Дашборд\", \"/dashboard\"),\n        new NavItem(\"Аналитика\", \"/analytics\"),\n        new NavItem(\"Пользователи\", \"/users\"),\n    }\n};",
          lang="csharp", hint="src/desktop/ViewModels/MainWindowViewModel.cs",
          png="menu", gif="menu-switch", cap="Боковое меню мастера (5 пунктов) и руководителя",
          note=["Меню скрывает пункты, а не отключает их. Права проверяются ещё и на "
                "сервере, но скрытие экономит время: пользователь не кликает по "
                "заведомо недоступному пункту."]),
        S("Хлебные крошки", 25,
          "Верхняя цепочка показывает путь «Цех / Оборудование / Станок ТА-16» и "
          "работает как навигация.",
          code="<ItemsControl ItemsSource=\"{Binding Breadcrumbs}\">\n  <ItemsControl.ItemsPanel>\n    <ItemsPanelTemplate><StackPanel Orientation=\"Horizontal\" /></ItemsPanelTemplate>\n  </ItemsControl.ItemsPanel>\n  <ItemsControl.ItemTemplate>\n    <DataTemplate>\n      <StackPanel Orientation=\"Horizontal\">\n        <TextBlock Text=\"{Binding Title}\" Classes=\"crumb\" />\n        <TextBlock Text=\"/\" Margin=\"6,0\" Opacity=\"0.5\" />\n      </StackPanel>\n    </DataTemplate>\n  </ItemsControl.ItemTemplate>\n</ItemsControl>",
          lang="xml", hint="src/desktop/Views/MainWindow.axaml",
          png="crumbs", cap="Хлебные крошки: Главная / Оборудование / Станок ТА-16",
          note=["Последний элемент цепочки — не ссылка. Иначе пользователь "
                "бесконечно «возвращается» на ту же страницу."]),
        S("Автоблокировка по бездействию", 30,
          "Таймер считает секунды с последнего ввода. Порог 15 секунд задан в задании "
          "и не меняется — эксперты проверяют именно его.",
          code="private readonly DispatcherTimer _idleTimer = new() { Interval = TimeSpan.FromSeconds(1) };\nprivate DateTime _lastInput = DateTime.UtcNow;\n\nprivate void OnAnyInput(object? sender, InputEventArgs e) => _lastInput = DateTime.UtcNow;\n\nprivate void OnIdleTick(object? sender, EventArgs e)\n{\n    if ((DateTime.UtcNow - _lastInput).TotalSeconds < 15) return;\n    _idleTimer.Stop();\n    _auth.Logout();\n    CurrentView = _loginViewModel;\n}",
          lang="csharp", hint="src/desktop/Views/MainWindow.axaml.cs",
          png="idle", gif="idle-lock", cap="Счётчик бездействия и возврат на экран входа",
          note=["Подписаться на ввод нужно на корневом элементе окна: события мыши "
                "и клавиатуры всплывают к нему от вложенных контролов. Подписка на "
                "каждом экране отдельно приводит к тому, что форма без своего "
                "обработчика не сбрасывает таймер."]),
        S("Хранилище токена", 25,
          "Токен кладём в защищённое хранилище операционной системы, а не в обычный "
          "текстовый файл.",
          code="public interface ITokenStorage\n{\n    void Save(string accessToken, string refreshToken, string role);\n    (string Token, string Role)? Load();\n    void Clear();\n}\n\npublic sealed class KeychainTokenStorage : ITokenStorage\n{\n    public void Save(string accessToken, string refreshToken, string role) { /* libsecret / DPAPI */ }\n    public (string, string)? Load() { /* читаем из хранилища */ }\n    public void Clear() { /* удаляем записи */ }\n}",
          lang="csharp", hint="src/desktop/Services/TokenStorage.cs",
          png="token", cap="Интерфейс хранилища токена с тремя методами",
          note=["Простой текстовый файл рядом с exe — это утечка при любой "
                "проверке. Достаточно реализовать интерфейс поверх "
                "Windows DPAPI и Linux libsecret, а если библиотеки нет — "
                "хотя бы `Environment.SpecialFolder.LocalApplicationData` с "
                "правами 600."]),
    ],
    [("Кнопка «Войти» не реагирует", "нет привязки `Command` или обработчик Enter не вызывает ту же команду"),
     ("Меню показывает лишние пункты", "роль читается не из токена, а из локальной переменной"),
     ("Автоблокировка не срабатывает", "подписка на ввод сделана на конкретном экране, а не на окне"),
     ("После выхода остаётся токен", "`Logout()` вызывает `Clear()` хранилища")],
    "dotnet run --project src/desktop/ToirProf.Desktop.csproj",
    "feat(desktop): экран входа, оболочка с навигацией, крошками и автоблокировкой",
))

PAGES.append(P(
    28, "HTTP-клиент-токены-и-состояния", 12,
    "Единая точка общения с сервером: подстановка токена, разбор обёртки "
    "`{success, data, message, error_code}`, единый индикатор загрузки, "
    "тосты и локальный журнал. Бизнес-логики здесь нет — только транспорт.",
    "Любой экран получает данные одной командой, ошибки приходят в toast, "
    "все обращения записаны в локальный журнал.",
    [("Б / Desktop", "Обращение к API по REST без WebView"),
     ("Б / Desktop", "Асинхронность с индикатором загрузки"),
     ("Б / Desktop", "Уведомления об ошибках"),
     ("Б / Desktop", "Локальное логирование")],
    ["src/desktop/Services/ApiClient.cs", "src/desktop/Services/IApiService.cs",
     "src/desktop/Services/ToastService.cs", "src/desktop/Services/FileLogger.cs",
     "src/desktop/Controls/ToastHost.axaml", "src/desktop/ViewModels/DashboardViewModel.cs"],
    [
        S("Описываем контракт вызовов", 30,
          "Интерфейс с методами по одному на экран. Реализация — одна, подменять её "
          "в тестах можно заглушкой.",
          code="public interface IApiService\n{\n    Task<ApiResponse<IReadOnlyList<EquipmentDto>>> GetEquipmentAsync(string? search, int page, int pageSize, CancellationToken ct);\n    Task<ApiResponse<WorkOrderDto>> GetWorkOrderAsync(string number, CancellationToken ct);\n    Task<ApiResponse<WorkOrderDto>> AssignCrewAsync(string number, Guid crewId, CancellationToken ct);\n    Task<ApiResponse<WorkOrderDto>> CompleteAsync(string number, CompleteWorkOrderRequest body, CancellationToken ct);\n    Task<ApiResponse<DashboardSummaryDto>> GetDashboardAsync(DateRange period, CancellationToken ct);\n    Task<string> LoginAsync(string login, string password, CancellationToken ct);\n}",
          lang="csharp", hint="src/desktop/Services/IApiService.cs",
          png="iface", cap="Интерфейс из шести методов — по одному на экран",
          note=["Один интерфейс на всё приложение проще, чем пять-шесть подтипов. "
                "При росте числа вызовов разложите по доменам, но не раньше — "
                "на защите это выглядит как усложнение без выгоды."]),
        S("Разбор обёртки ответа", 30,
          "Сервер всегда отвечает одной структурой. Клиент обязан смотреть на `success`, "
          "а не на HTTP-код: 200 с `success: false` — это бизнес-ошибка.",
          code="public async Task<ApiResponse<T>> SendAsync<T>(HttpRequestMessage request, CancellationToken ct)\n{\n    request.Headers.Authorization = new AuthenticationHeaderValue(\"Bearer\", _tokens.Token);\n\n    var response = await _http.SendAsync(request, ct);\n    var payload = await response.Content.ReadFromJsonAsync<ApiResponse<T>>(cancellationToken: ct);\n\n    _logger.Info($\"{request.Method} {request.RequestUri} -> {(int)response.StatusCode} success={payload?.Success}\");\n\n    if (payload is null)\n        return ApiResponse<T>.Fail(\"Сервер вернул пустой ответ\", ErrorCode.InternalError);\n\n    return response.IsSuccessStatusCode && payload.Success\n        ? payload\n        : ApiResponse<T>.Fail(payload.Message, payload.ErrorCode ?? response.StatusCode.ToString());\n}",
          lang="csharp", hint="src/desktop/Services/ApiClient.cs",
          png="api-client", gif="api-401", cap="Вызов дашборда: 200 с success=true, затем 401",
          note=["Проверка `payload.Success` отдельно от кода ответа — обязательна. "
                "Один забытый случай даёт «успешный» экран с пустыми данными "
                "вместо сообщения об ошибке."]),
        S("Toasts и модальные окна ошибок", 25,
          "Короткие уведомления — для успеха и предупреждений, модальное окно — "
          "когда действие не выполнено.",
          code="public sealed class ToastService\n{\n    private readonly List<ToastItem> _items = [];\n\n    public IReadOnlyList<ToastItem> Items => _items;\n\n    public void Show(string text, ToastKind kind = ToastKind.Info)\n    {\n        var item = new ToastItem(Guid.NewGuid(), text, kind);\n        _items.Add(item);\n        ItemsChanged?.Invoke();\n        _ = Task.Delay(TimeSpan.FromSeconds(4)).ContinueWith(_ =>\n        {\n            _items.Remove(item);\n            ItemsChanged?.Invoke();\n        });\n    }\n}",
          lang="csharp", hint="src/desktop/Services/ToastService.cs",
          png="toast", gif="toast-error", cap="Toast снизу справа и модальное окно ошибки 409",
          note=["Уведомление живёт 4 секунды. Ошибку 409 («бригада уже занята») "
                "нужно показать модальным окном — иначе она исчезнет раньше, "
                "чем мастер её прочитает."]),
        S("Индикатор загрузки", 25,
          "Пока идёт запрос — кнопки блокируются, в верхней панели горит индикатор. "
          "Экран не должен «моргать» пустыми данными.",
          code="<Grid>\n  <TransitioningContentControl>\n    <ContentControl Content=\"{Binding ViewModel}\" />\n  </TransitioningContentControl>\n\n  <Border Background=\"#66000000\" IsVisible=\"{Binding IsBusy}\" />\n  <ProgressBar IsIndeterminate=\"True\" IsVisible=\"{Binding IsBusy}\"\n               VerticalAlignment=\"Top\" Height=\"3\" />\n</Grid>",
          lang="xml", hint="src/desktop/Views/MainWindow.axaml",
          png="busy", gif="busy-refresh", cap="Индикатор загрузки при обновлении дашборда",
          note=["Прозрачная затемняющая подложка поверх старых данных лучше пустого "
                "экрана: пользователь видит, что это обновление, а не новая "
                "страница."]),
        S("Локальный журнал", 30,
          "Каждый вызов и каждая ошибка пишутся в файл рядом с приложением. На "
          "демонстрации журнал часто выручает, когда эксперт просит показать "
          "историю сбоя.",
          code="public sealed class FileLogger\n{\n    private readonly string _path = Path.Combine(\n        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),\n        \"toirprof\", \"desktop.log\");\n\n    public void Info(string message) => Append(\"INFO\", message);\n    public void Error(string message, Exception? ex = null) => Append(\"ERROR\", $\"{message} {ex}\");\n\n    private void Append(string level, string message)\n    {\n        Directory.CreateDirectory(Path.GetDirectoryName(_path)!);\n        File.AppendAllText(_path, $\"{DateTime.Now:yyyy-MM-dd HH:mm:ss} [{level}] {message}{Environment.NewLine}\");\n    }\n}",
          lang="csharp", hint="src/desktop/Services/FileLogger.cs",
          png="log", gif="log-write", cap="Строки журнала: 200, 401, 500 с кодом и сообщением",
          note=["Ротацию журнала делайте по размеру файла, а не по дате: на "
                "демонстрации за день набегает несколько мегабайт, и открытый "
                "на сортировку файл с миллионом строк тормозит саму проверку."]),
    ],
    [("Данные не появляются", "проверьте `payload.Success` — возможно, пришёл `success: false` с кодом 200"),
     ("401 на каждом запросе", "токен не подставляется: проверьте `AuthenticationHeaderValue`"),
     ("Toast не исчезает", "таймер удаления работает, но `ItemsChanged` не вызывается в UI-потоке"),
     ("Журнал не создаётся", "нет прав на каталог — используйте `LocalApplicationData`")],
    "grep -c \"INFO\\|ERROR\" \"$HOME/.local/share/toirprof/desktop.log\"",
    "feat(desktop): HTTP-клиент, разбор обёртки ответа, toast и локальный журнал",
))

PAGES.append(P(
    29, "Дашборд-мастера", 13,
    "Первый экран после входа: что мастер должен увидеть за секунду — сколько заявок "
    "в работе, сколько просрочено, какой простой за смену. Данные приходят одним "
    "запросом с дашборда.",
    "Дашборд открывается за один запрос и показывает показатели, ближайшие заявки и "
    "статусы без пагинации.",
    [("Б / Desktop", "Дашборд с ключевыми показателями")],
    ["src/desktop/Views/DashboardView.axaml", "src/desktop/Views/DashboardView.axaml.cs",
     "src/desktop/ViewModels/DashboardViewModel.cs", "src/desktop/Controls/MetricCard.axaml"],
    [
        S("Карточки показателей", 35,
          "Шесть карточек в две строки по три. Значение крупно, подпись поясняет "
          "период — иначе «47» без контекста ничего не значит.",
          code="<ItemsControl ItemsSource=\"{Binding Metrics}\">\n  <ItemsControl.ItemsPanel>\n    <ItemsPanelTemplate>\n      <WrapPanel ItemWidth=\"260\" Margin=\"0,0,16,16\" />\n    </ItemsPanelTemplate>\n  </ItemsControl.ItemsPanel>\n  <ItemsControl.ItemTemplate>\n    <DataTemplate>\n      <Border Classes=\"card\" Padding=\"16\">\n        <StackPanel Spacing=\"4\">\n          <TextBlock Text=\"{Binding Title}\" Opacity=\"0.7\" />\n          <TextBlock Text=\"{Binding Value}\" FontSize=\"32\" FontWeight=\"SemiBold\" />\n          <TextBlock Text=\"{Binding Caption}\" FontSize=\"12\" Opacity=\"0.6\" />\n        </StackPanel>\n      </Border>\n    </DataTemplate>\n  </ItemsControl.ItemTemplate>\n</ItemsControl>",
          lang="xml", hint="src/desktop/Views/DashboardView.axaml",
          png="metrics", gif="metrics-load", cap="Шесть KPI-карточек после загрузки дашборда",
          note=["Подпись под числом обязательна: «6,3 ч» — это простой за март "
                "или за смену? Без подписи эксперт спросит, и вы задумаетесь."]),
        S("Загрузка одним запросом", 30,
          "ViewModel просит дашборд и раскладывает ответ по карточкам. Никаких "
          "параллельных вызовов на каждую карточку.",
          code="public partial class DashboardViewModel : BaseViewModel\n{\n    [ObservableProperty] private IReadOnlyList<MetricCardVm> _metrics = [];\n    [ObservableProperty] private IReadOnlyList<WorkOrderDto> _nextOrders = [];\n\n    public DashboardViewModel(IApiService api, ToastService toasts) : base(api, toasts) { }\n\n    public override async Task InitializeAsync(CancellationToken ct)\n    {\n        await RunAsync(async () =>\n        {\n            var response = await _api.GetDashboardAsync(DateRange.ThisMonth, ct);\n            if (!response.Success) { ShowError(response); return; }\n\n            var d = response.Data!;\n            Metrics =\n            [\n                new(\"Заявок за месяц\", d.TotalOrders.ToString(), $\"за {DateTime.Now:MMMM yyyy}\"),\n                new(\"В работе\", d.InProgress.ToString(), \"требуют внимания мастера\"),\n                new(\"Завершено\", d.Completed.ToString(), \"закрыто за период\"),\n                new(\"Средний простой\", $\"{d.AverageDowntimeHours:0.0} ч\", \"на одну заявку\"),\n                new(\"Аварийные\", $\"{d.EmergencyShare:0.0} %\", \"доля от всех заявок\"),\n                new(\"План ТО\", $\"{d.MaintenancePlanShare:0.0} %\", \"выполнение графика\"),\n            ];\n            NextOrders = await _api.GetWorkOrdersAsync(\"Назначена\", 1, 5, ct).Data ?? [];\n        });\n    }\n}",
          lang="csharp", hint="src/desktop/ViewModels/DashboardViewModel.cs",
          png="vm", cap="DashboardViewModel раскладывает шесть показателей",
          note=["Форматирование `0.0` применяйте в клиенте, а не на сервере. "
                "Сервер отдаёт число, формат — дело языка интерфейса: русская "
                "локаль ставит запятую, английская — точку."]),
        S("Ближайшие заявки и статусы", 30,
          "Справа от карточек — пять заявок в работе и полоса распределения по "
          "статусам. Это отвечает на вопрос «что делать дальше».",
          code="<Grid ColumnDefinitions=\"2*,*\">\n  <TextBlock Grid.Column=\"0\" Text=\"Ближайшие заявки\" FontSize=\"18\" FontWeight=\"SemiBold\" />\n  <ItemsControl Grid.Column=\"0\" Grid.Row=\"1\" ItemsSource=\"{Binding NextOrders}\" Margin=\"0,12,0,0\">\n    <ItemsControl.ItemTemplate>\n      <DataTemplate>\n        <Grid ColumnDefinitions=\"120,*,110\" Margin=\"0,0,0,8\">\n          <TextBlock Text=\"{Binding Number}\" />\n          <TextBlock Grid.Column=\"1\" Text=\"{Binding EquipmentName}\" />\n          <TextBlock Grid.Column=\"2\" Text=\"{Binding Status}\" HorizontalAlignment=\"Right\" />\n        </Grid>\n      </DataTemplate>\n    </ItemsControl.ItemTemplate>\n  </ItemsControl>\n\n  <TextBlock Grid.Column=\"1\" Text=\"По статусам\" FontSize=\"18\" FontWeight=\"SemiBold\" />\n</Grid>",
          lang="xml", hint="src/desktop/Views/DashboardView.axaml",
          png="orders", gif="orders-open", cap="Список заявок в работе и распределение по статусам",
          note=["Пять строк, не двадцать. Дашборд — это входная точка, а не "
                "таблица; полный список живёт на своём экране."]),
        S("Пустое состояние", 20,
          "Если заявок нет — не пустая таблица, а объяснение и подсказка, что делать.",
          code="<StackPanel IsVisible=\"{Binding IsEmpty}\" Spacing=\"8\" HorizontalAlignment=\"Center\" Margin=\"0,60,0,0\">\n  <TextBlock Text=\"На сегодня заявок нет\" FontSize=\"18\" HorizontalAlignment=\"Center\" />\n  <TextBlock Text=\"Новые заявки появятся здесь сразу после создания мастером\"\n             Opacity=\"0.7\" HorizontalAlignment=\"Center\" />\n</StackPanel>",
          lang="xml", hint="src/desktop/Views/DashboardView.axaml",
          png="empty", cap="Пустое состояние дашборда",
          note=["Пустое состояние — тоже демонстрация. Эксперты специально "
                "проверяют его на свежей базе без данных."]),
        S("Кнопка обновления", 25,
          "Обновление по кнопке и автоматически раз в минуту, с индикатором.",
          code="public override async Task InitializeAsync(CancellationToken ct)\n{\n    await LoadAsync(ct);\n    _timer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(60) };\n    _timer.Tick += async (_, _) => await LoadAsync(ct);\n    _timer.Start();\n}\n\npublic override void Dispose()\n{\n    _timer?.Stop();\n    base.Dispose();\n}",
          lang="csharp", hint="src/desktop/ViewModels/DashboardViewModel.cs",
          png="refresh", gif="refresh-timer", cap="Ручное обновление и автообновление раз в минуту",
          note=["Останавливайте таймер в `Dispose`. Иначе при переходе на другой "
                "экран старый дашборд продолжит опрашивать сервер каждую минуту "
                "до конца смены — локальный журнал это покажет."]),
    ],
    [("Карточки пустые, ошибок нет", "ответ пришёл с `success: false` — смотрите локальный журнал"),
     ("Проценты показывают 0,0 при трёх заявках", "деление целочисленное, нужен `100m` и `Max(1, …)`"),
     ("Дашборд грузится дважды при переходе", "метод инициализации вызван и в конструкторе, и в навигаторе"),
     ("Фоновый запрос после закрытия окна", "таймер не остановлен в `Dispose`")],
    "dotnet run --project src/desktop/ToirProf.Desktop.csproj",
    "feat(desktop): экран дашборда мастера с показателями, заявками и автообновлением",
))

PAGES.append(P(
    30, "Таблицы-поиск-сортировка-пагинация", 13,
    "Общий компонент таблицы для всех экранов: колонки, сортировка по клику, "
    "поиск с задержкой ввода и постраничная навигация. Один компонент — один "
    "набор правил на всём приложении.",
    "Один и тот же компонент используется на пяти экранах: работают сортировка, "
    "поиск и пагинация без копипаста кода.",
    [("Б / Desktop", "Сортировка и пагинация"),
     ("Б / Desktop", "Поиск"),
     ("Б / Desktop", "Асинхронность при загрузке данных")],
    ["src/desktop/Controls/DataTableControl.axaml", "src/desktop/Controls/DataTableControl.axaml.cs",
     "src/desktop/ViewModels/TableViewModelBase.cs", "src/desktop/DTOs/PagedResult.cs"],
    [
        S("Контракт постраничного ответа", 25,
          "Единый формат страницы: список, общее количество, номер страницы. "
          "Сервер и клиент обязаны понимать его одинаково.",
          code="public sealed record PagedResult<T>(IReadOnlyList<T> Items, int Total, int Page, int PageSize)\n{\n    public int Pages => PageSize == 0 ? 0 : (int)Math.Ceiling(Total / (double)PageSize);\n}\n\npublic abstract class TableViewModelBase<T> : BaseViewModel\n{\n    [ObservableProperty] private IReadOnlyList<T> _items = [];\n    [ObservableProperty] private int _page = 1;\n    [ObservableProperty] private int _pageSize = 20;\n    [ObservableProperty] private int _total;\n    [ObservableProperty] private string _search = string.Empty;\n    [ObservableProperty] private string _sortBy = \"name\";\n    [ObservableProperty] private bool _descending;\n\n    public int Pages => PageSize == 0 ? 0 : (int)Math.Ceiling(Total / (double)PageSize);\n\n    protected abstract Task<PagedResult<T>> FetchAsync(CancellationToken ct);\n\n    protected async Task ReloadAsync(CancellationToken ct)\n    {\n        var result = await FetchAsync(ct);\n        Items = result.Items;\n        Total = result.Total;\n        OnPropertyChanged(nameof(Pages));\n    }\n}",
          lang="csharp", hint="src/desktop/ViewModels/TableViewModelBase.cs",
          png="paged", cap="PagedResult и базовая ViewModel для всех таблиц",
          note=["`Pages` считайте через `Math.Ceiling` в double. Целочисленное "
                "деление теряет последнюю неполную страницу — при 47 записях "
                "и по 20 на страницу получится 2 страницы вместо 3."]),
        S("Сортировка по клику", 30,
          "Клик по заголовку меняет направление, второй клик — переключает. "
          "Индикатор стрелки обязателен.",
          code="private void OnHeaderClick(ColumnDefinition column)\n{\n    if (SortBy == column.Key)\n        Descending = !Descending;\n    else\n    {\n        SortBy = column.Key;\n        Descending = false;\n    }\n    _ = RefreshAsync();\n}\n\nprivate string SortExpression => SortBy switch\n{\n    \"status\" => \"status\",\n    \"date\" => \"planned_start\",\n    _ => \"name\"\n};",
          lang="csharp", hint="src/desktop/Controls/DataTableControl.axaml.cs",
          png="sort", gif="sort-toggle", cap="Сортировка по статусу: по возрастанию и по убыванию",
          note=["Сортируйте на сервере, а не перестановкой уже загруженных строк. "
                "На первой странице клиент отсортирует 20 записей, а в таблице "
                "останется порядок случайных двадцати из сорока семи."]),
        S("Поиск с задержкой ввода", 30,
          "Запрос уходит через 300 мс после последнего символа, а не на каждое "
          "нажатие.",
          code="private CancellationTokenSource? _searchCts;\n\nprivate void OnSearchChanged(string value)\n{\n    Search = value;\n    _searchCts?.Cancel();\n    _searchCts = new CancellationTokenSource();\n    var token = _searchCts.Token;\n\n    _ = Task.Delay(TimeSpan.FromMilliseconds(300), token).ContinueWith(async _ =>\n    {\n        if (token.IsCancellationRequested) return;\n        Page = 1;\n        await ReloadAsync(token);\n    }, token, TaskContinuationOptions.ExecuteSynchronously, TaskScheduler.Default);\n}",
          lang="csharp", hint="src/desktop/ViewModels/TableViewModelBase.cs",
          png="search", gif="search-debounce", cap="Поиск «пресс»: запросы на 4-й и 7-й символ",
          note=["Отмена предыдущего токена обязательна. Без неё быстрый набор "
                "«пресс» даст четыре параллельных запроса, и последний ответ "
                "может прийти раньше первого — список покажет результат "
                "для «пре», а введён «пресс»."]),
        S("Пагинация", 30,
          "Кнопки «назад / вперёд», номер страницы и общее количество. На "
          "узких окнах номер страницы скрывается.",
          code="<StackPanel Orientation=\"Horizontal\" Spacing=\"8\" HorizontalAlignment=\"Center\">\n  <Button Content=\"‹\" Command=\"{Binding PrevPageCommand}\" IsEnabled=\"{Binding Page > 1}\" />\n  <TextBlock Text=\"{Binding Page}\" VerticalAlignment=\"Center\" MinWidth=\"32\" TextAlignment=\"Center\" />\n  <TextBlock Text=\"из\" VerticalAlignment=\"Center\" Opacity=\"0.7\" />\n  <TextBlock Text=\"{Binding Pages}\" VerticalAlignment=\"Center\" />\n  <Button Content=\"›\" Command=\"{Binding NextPageCommand}\" IsEnabled=\"{Binding Page < Pages}\" />\n</StackPanel>",
          lang="xml", hint="src/desktop/Controls/DataTableControl.axaml",
          png="pager", gif="pager-next", cap="Пагинация: страница 2 из 3, всего 47 записей",
          note=["Кнопки должны блокироваться на границах, а не вызывать пустой "
                "запрос. Ответ 400 на последней странице — заметная ошибка "
                "на демонстрации."]),
        S("Индикатор загрузки таблицы", 25,
          "Пока идёт страница — таблица остаётся на месте с индикатором, а не "
          "очищается.",
          code="<Grid>\n  <DataGrid ItemsSource=\"{Binding Items}\" IsVisible=\"{Binding !IsBusy}\" />\n  <ProgressBar IsIndeterminate=\"True\" IsVisible=\"{Binding IsBusy}\"\n               HorizontalAlignment=\"Stretch\" VerticalAlignment=\"Top\" />\n</Grid>",
          lang="xml", hint="src/desktop/Controls/DataTableControl.axaml",
          png="table-busy", gif="table-page", cap="Переход между страницами с индикатором",
          note=["Скелет строк вместо пустой таблицы читается лучше, чем простыня "
                "серых линий, но полноценный скелетон в Avalonia дорог — "
                "достаточно индикатора с сохранением прежних строк."]),
    ],
    [("Страниц 2 вместо 3", "целочисленное деление в `Pages` вместо `Math.Ceiling`"),
     ("Поиск возвращает старые данные", "предыдущий запрос не отменён, ответ пришёл не в том порядке"),
     ("Сортировка не работает", "сортировка сделана на клиенте по текущей странице"),
     ("Кнопка пагинации даёт 400", "не проверяется граница `Page <= Pages`")],
    "dotnet build src/desktop/ToirProf.Desktop.csproj -c Release",
    "feat(desktop): общий компонент таблиц с сортировкой, поиском и пагинацией",
))
# === BLOCK-F2: спринты 14–15, страницы 31–35 (Desktop) ===

PAGES.append(P(
    31, "Экран-Оборудование-цеха", 14,
    "Список оборудования цеха: карточки, фильтры, создание и правка. Отдельный "
    "акцент — на запрет менять статус «Выведено из эксплуатации»: сервер вернёт "
    "409, и клиент обязан показать это понятно, а не молча.",
    "Экран со списком, фильтрами по цеху и статусу, формами создания и правки и "
    "корректной реакцией на запрет смены статуса.",
    [("Б / Desktop", "Экран «Оборудование цеха»"),
     ("Б / Desktop", "Фильтрация и поиск"),
     ("Б / Desktop", "Модальные окна ошибок")],
    ["src/desktop/Views/EquipmentView.axaml", "src/desktop/Views/EquipmentView.axaml.cs",
     "src/desktop/ViewModels/EquipmentViewModel.cs", "src/desktop/ViewModels/EquipmentEditViewModel.cs",
     "src/desktop/Views/EquipmentEditView.axaml"],
    [
        S("Список оборудования", 30,
          "Таблица из общего компонента: инвентарный номер, наименование, цех, "
          "установка, статус. Статус выделен цветом.",
          code="<DataGrid Grid.Column=\"0\" ItemsSource=\"{Binding Items}\" AutoGenerateColumns=\"False\">\n  <DataGrid.Columns>\n    <DataGridTextColumn Header=\"Инв. №\" Binding=\"{Binding InventoryNumber}\" Width=\"140\" />\n    <DataGridTextColumn Header=\"Наименование\" Binding=\"{Binding Name}\" Width=\"*\" />\n    <DataGridTextColumn Header=\"Цех\" Binding=\"{Binding WorkshopName}\" Width=\"160\" />\n    <DataGridTextColumn Header=\"Установлен\" Binding=\"{Binding CommissionDate, StringFormat='dd.MM.yyyy'}\" Width=\"130\" />\n    <DataGridTemplateColumn Header=\"Статус\" Width=\"200\">\n      <DataGridTemplateColumn.CellTemplate>\n        <DataTemplate>\n          <Border Classes=\"status\" Classes.urgent=\"{Binding IsRetired}\"\n                  Padding=\"8,2\" CornerRadius=\"10\">\n            <TextBlock Text=\"{Binding Status}\" />\n          </Border>\n        </DataTemplate>\n      </DataGridTemplateColumn.CellTemplate>\n    </DataGridTemplateColumn>\n  </DataGrid.Columns>\n</DataGrid>",
          lang="xml", hint="src/desktop/Views/EquipmentView.axaml",
          png="list", gif="list-filter", cap="Список из 12 единиц, счётчик «12 из 47»",
          note=["Цветом выделяйте не «работает» (зелёный всем приелся), а "
                "проблемные статусы: «В ремонте» — жёлтый, «Выведено из "
                "эксплуатации» — красный. Так взгляд сразу находит проблемы."]),
        S("Фильтры по цеху и статусу", 25,
          "Два выпадающих списка и строка поиска применяются одновременно. "
          "Значения приходят из справочников, а не из вручную набранного списка.",
          code="[ObservableProperty] private Guid? _workshopId;\n[ObservableProperty] private string? _status;\n\nprivate async Task ApplyFiltersAsync()\n{\n    Page = 1;\n    await ReloadAsync(CancellationToken.None);\n}\n\nprotected override async Task<PagedResult<EquipmentDto>> FetchAsync(CancellationToken ct)\n{\n    var query = new EquipmentQuery(WorkshopId, Status, Search, Page, PageSize, SortBy, Descending);\n    var response = await _api.GetEquipmentAsync(query, ct);\n    if (!response.Success) ShowError(response);\n    return response.Data ?? new([], 0, Page, PageSize);\n}",
          lang="csharp", hint="src/desktop/ViewModels/EquipmentViewModel.cs",
          png="filters", cap="Фильтры: цех «Механический», статус «В ремонте»",
          note=["Сброс любого фильтра должен возвращать страницу 1. Иначе после "
                "сброса вы окажетесь на третьей странице пустого результата."]),
        S("Форма создания и правки", 35,
          "Обязательные поля подсвечены, номера инвентаризации — с подсказкой о "
          "формате. Поле статуса на выведенном из эксплуатации — только чтение.",
          code="<StackPanel Spacing=\"10\" Width=\"420\">\n  <TextBox Watermark=\"Инвентарный номер\" Text=\"{Binding InventoryNumber}\" />\n  <TextBox Watermark=\"Наименование\" Text=\"{Binding Name}\" />\n  <ComboBox HorizontalAlignment=\"Stretch\" ItemsSource=\"{Binding Workshops}\" SelectedItem=\"{Binding Workshop}\" />\n  <ComboBox HorizontalAlignment=\"Stretch\" ItemsSource=\"{Binding Statuses}\" SelectedItem=\"{Binding Status}\" />\n  <NumericUpDown Minimum=\"0\" Maximum=\"5\" Increment=\"0.5\" Value=\"{Binding Criticality}\" />\n  <DatePicker SelectedDate=\"{Binding CommissionDate}\" />\n  <StackPanel Orientation=\"Horizontal\" Spacing=\"8\" HorizontalAlignment=\"Right\">\n    <Button Content=\"Отмена\" Command=\"{Binding CancelCommand}\" />\n    <Button Content=\"Сохранить\" Command=\"{Binding SaveCommand}\" IsEnabled=\"{Binding !IsBusy}\" />\n  </StackPanel>\n</StackPanel>",
          lang="xml", hint="src/desktop/Views/EquipmentEditView.axaml",
          png="form", gif="form-create", cap="Форма создания оборудования",
          note=["Критичность — шкала 0…5 с шагом 0.5. Сервер проверяет диапазон "
                "ограничением CHECK, клиент подсказывает допустимые значения "
                "заранее: эксперт любит ввести 9 и посмотреть на реакцию."]),
        S("Обработка 409 по статусу", 30,
          "Триггер базы запрещает менять статус выведенного из эксплуатации "
          "оборудования. API вернёт 409 с кодом `STATUS_LOCKED`.",
          code="if (!response.Success)\n{\n    if (response.ErrorCode == ErrorCode.StatusLocked)\n    {\n        _dialogs.ShowWarning(\n            \"Оборудование выведено из эксплуатации\",\n            \"Статус нельзя изменить: сначала оформите заявку на списание.\");\n        return;\n    }\n\n    ShowError(response);\n}",
          lang="csharp", hint="src/desktop/ViewModels/EquipmentEditViewModel.cs",
          png="conflict", gif="conflict-status", cap="Модальное окно при попытке сменить статус",
          note=["Не показывайте «Ошибка 409» — покажите причину. Мастер должен "
                "понять, что делать дальше: завести заявку на списание. "
                "Код `STATUS_LOCKED` приходит из `error_code`, а не из текста."]),
        S("Проверка формы", 25,
          "Пустые обязательные поля и некорректная дата ввода не уходят на сервер.",
          code="private string? Validate()\n{\n    if (string.IsNullOrWhiteSpace(InventoryNumber)) return \"Укажите инвентарный номер\";\n    if (string.IsNullOrWhiteSpace(Name)) return \"Укажите наименование\";\n    if (CommissionDate is null or > DateTime.Today) return \"Дата ввода не может быть в будущем\";\n    if (Workshop is null) return \"Выберите цех\";\n    return null;\n}",
          lang="csharp", hint="src/desktop/ViewModels/EquipmentEditViewModel.cs",
          png="validate", gif="validate-empty", cap="Подсветка обязательного поля и сообщение об ошибке",
          note=["Валидация на клиенте — для удобства, на сервере — для "
                "гарантий. Проверять только на клиенте нельзя: любой может "
                "отправить запрос через Postman."]),
    ],
    [("409 при изменении статуса", "сработал триггер — так и должно быть, показывайте предупреждение"),
     ("Дата будущая прошла на сервер", "валидация на клиенте не написана или не вызывается"),
     ("Фильтры не применяются", "не сброшен `Page` — после фильтра вы на пустой третьей странице"),
     ("Инвентарный номер занят", "дубликат UNIQUE — проверьте наличие номера в поиске")],
    "dotnet run --project src/desktop/ToirProf.Desktop.csproj",
    "feat(desktop): экран оборудования цеха с фильтрами, формами и обработкой 409",
))

PAGES.append(P(
    32, "Экран-График-ТО", 14,
    "План технического обслуживания: календарная сетка по цехам, создание "
    "записей и отметка выполнения. Здесь же видно, как функция расчёта следующей "
    "плановой даты работает на практике.",
    "Календарь плановых ТО за месяц, форма создания записи и отметка выполнения, "
    "которая сама подставляет дату следующего обслуживания.",
    [("Б / Desktop", "Экран «График ТО»"),
     ("Б / Desktop", "Формы ввода данных")],
    ["src/desktop/Views/ScheduleView.axaml", "src/desktop/Views/ScheduleView.axaml.cs",
     "src/desktop/ViewModels/ScheduleViewModel.cs", "src/desktop/Controls/MonthCalendar.axaml"],
    [
        S("Календарная сетка", 35,
          "Месяц сеткой: строки — единицы оборудования, столбцы — дни. Записи "
          "показываются цветом вида обслуживания.",
          code="<ItemsControl ItemsSource=\"{Binding Days}\">\n  <ItemsControl.ItemsPanel>\n    <ItemsPanelTemplate><UniformGrid Columns=\"31\" /></ItemsPanelTemplate>\n  </ItemsControl.ItemsPanel>\n  <ItemsControl.ItemTemplate>\n    <DataTemplate>\n      <Border BorderThickness=\"0,0,1,1\" BorderBrush=\"#22000000\" Padding=\"2\">\n        <StackPanel>\n          <TextBlock Text=\"{Binding Day}\" FontSize=\"11\" Opacity=\"0.6\" />\n          <ItemsControl ItemsSource=\"{Binding Entries}\">\n            <ItemsControl.ItemTemplate>\n              <DataTemplate>\n                <Border Background=\"{Binding KindBrush}\" CornerRadius=\"3\" Padding=\"2\" Margin=\"0,1\">\n                  <TextBlock Text=\"{Binding ShortTitle}\" TextTrimming=\"CharacterEllipsis\" FontSize=\"10\" />\n                </Border>\n              </DataTemplate>\n            </ItemsControl.ItemTemplate>\n          </ItemsControl>\n        </StackPanel>\n      </Border>\n    </DataTemplate>\n  </ItemsControl.ItemTemplate>\n</ItemsControl>",
          lang="xml", hint="src/desktop/Controls/MonthCalendar.axaml",
          png="calendar", gif="calendar-month", cap="Календарь ТО за март 2026: 18 записей",
          note=["31 столбец `UniformGrid` при ширине окна 1440 даёт около 44 px на "
                "день — текст вида обслуживания не влезает. Показывайте "
                "сокращение («ТО-2», «ТО-3») и полное название в подсказке."]),
        S("Загрузка месяца", 25,
          "Переход между месяцами не перезагружает приложение: меняется только "
          "запрос и содержимое сетки.",
          code="[RelayCommand]\nprivate async Task NextMonthAsync()\n{\n    _month = _month.AddMonths(1);\n    await LoadAsync(CancellationToken.None);\n}\n\nprivate async Task LoadAsync(CancellationToken ct)\n{\n    var response = await _api.GetScheduleAsync(_month.Year, _month.Month, ct);\n    if (!response.Success) { ShowError(response); return; }\n\n    Days = Enumerable.Range(1, DateTime.DaysInMonth(_month.Year, _month.Month))\n        .Select(day => new DayCell(day, response.Data!.Where(e => e.PlannedDate.Day == day).ToList()))\n        .ToList();\n}",
          lang="csharp", hint="src/desktop/ViewModels/ScheduleViewModel.cs",
          png="load", gif="load-next", cap="Переход с марта на апрель без перезапуска",
          note=["Храните месяц в поле, а не в заголовке окна. Иначе при переходе "
                "назад заголовок останется от старого месяца — мелочь, которую "
                "замечают при демонстрации."]),
        S("Форма создания записи", 30,
          "Оборудование, вид обслуживания, плановые даты и ответственный. Период "
          "проверяется: окончание не раньше начала.",
          code="<StackPanel Spacing=\"10\" Width=\"420\">\n  <ComboBox ItemsSource=\"{Binding Equipment}\" SelectedItem=\"{Binding Equipment}\"\n            HorizontalAlignment=\"Stretch\" Watermark=\"Оборудование\" />\n  <ComboBox ItemsSource=\"{Binding Kinds}\" SelectedItem=\"{Binding Kind}\"\n            HorizontalAlignment=\"Stretch\" Watermark=\"Вид ТО\" />\n  <StackPanel Orientation=\"Horizontal\" Spacing=\"10\">\n    <DatePicker SelectedDate=\"{Binding PlannedStart}\" />\n    <DatePicker SelectedDate=\"{Binding PlannedEnd}\" />\n  </StackPanel>\n  <ComboBox ItemsSource=\"{Binding Users}\" SelectedItem=\"{Binding AssignedUser}\"\n            HorizontalAlignment=\"Stretch\" Watermark=\"Ответственный\" />\n</StackPanel>",
          lang="xml", hint="src/desktop/Views/ScheduleView.axaml",
          png="create", gif="create-save", cap="Создание записи графика",
          note=["Даты в форме — только плановые. Фактические заполняются при "
                "закрытии заявки: смешивать их в одной форме нельзя, критерий "
                "проверяет корректность хронологии на сервере."]),
        S("Отметка выполнения", 30,
          "Закрытие записи вызывает расчёт следующей плановой даты. Пользователь "
          "видит её до подтверждения.",
          code="var preview = await _api.GetNextMaintenanceDateAsync(entry.Id, ct);\nif (!preview.Success) { ShowError(preview); return; }\n\nvar answer = _dialogs.Confirm(\n    \"Записать выполнение?\",\n    $\"Следующее плановое обслуживание: {preview.Data:dd.MM.yyyy}\");\n\nif (!answer) return;\nawait _api.CompleteScheduleEntryAsync(entry.Id, ct);",
          lang="csharp", hint="src/desktop/ViewModels/ScheduleViewModel.cs",
          png="complete", gif="complete-next", cap="Подтверждение выполнения с датой следующего ТО",
          note=["Спрашивайте перед сохранением и показывайте будущую дату. "
                "Мастер видит последствие и может исправить, если вид обслуживания "
                "выбран неверно."]),
        S("Фильтр по виду ТО", 20,
          "Цветовая легенда и фильтр: показывать только один вид обслуживания.",
          code="<StackPanel Orientation=\"Horizontal\" Spacing=\"16\">\n  <ToggleSwitch Content=\"Только просроченные\"\n                  IsChecked=\"{Binding OnlyOverdue}\" />\n  <ComboBox ItemsSource=\"{Binding Kinds}\" SelectedItem=\"{Binding KindFilter}\"\n            MinWidth=\"200\" Watermark=\"Вид обслуживания\" />\n</StackPanel>",
          lang="xml", hint="src/desktop/Views/ScheduleView.axaml",
          png="filter", cap="Фильтр по виду ТО и переключатель просроченных",
          note=["Просроченные подсвечивайте отдельно от остальных — их ищут "
                "каждый день."]),
    ],
    [("Календарь пуст", "запрос вернул записи другого месяца — проверьте формат `from` и `to`"),
     ("Дубли записей в один день", "в `maintenance_schedule` нет ограничения на период, добавьте проверку на клиенте"),
     ("Следующая дата не совпадает с расчётом", "используйте серверную функцию расчёта, а не клиентскую арифметику"),
     ("Календарь не влезает в окно", "не задан `MinWidth` окна или сетка без горизонтальной прокрутки")],
    "dotnet build src/desktop/ToirProf.Desktop.csproj -c Release",
    "feat(desktop): экран графика ТО с календарём, формами и отметкой выполнения",
))

PAGES.append(P(
    33, "Экран-Заявки", 15,
    "Главный рабочий экран мастера: список заявок, карточка заявки, назначение "
    "бригады и завершение работы со списанием материалов. Здесь сходится "
    "жизненный цикл заявки, разобранный в API.",
    "Мастер открывает заявку, видит её детали, назначает бригаду и закрывает "
    "работу, указав потраченные материалы и итоговую стоимость.",
    [("Б / Desktop", "Экран «Заявки»"),
     ("Б / Desktop", "Формы ввода данных"),
     ("Б / Desktop", "Индикация асинхронных операций")],
    ["src/desktop/Views/WorkOrdersView.axaml", "src/desktop/Views/WorkOrderCardView.axaml",
     "src/desktop/Views/CompleteWorkOrderView.axaml", "src/desktop/ViewModels/WorkOrderViewModel.cs",
     "src/desktop/ViewModels/CompleteWorkOrderViewModel.cs"],
    [
        S("Список заявок", 30,
          "Таблица из общего компонента плюс фильтры: статус, приоритет, "
          "оборудование. Для мастера список по умолчанию ограничен его бригадой.",
          code="protected override async Task<PagedResult<WorkOrderDto>> FetchAsync(CancellationToken ct)\n{\n    var response = await _api.GetWorkOrdersAsync(new WorkOrderQuery(\n        Status, Priority, Search, Page, PageSize, SortBy, Descending), ct);\n\n    if (!response.Success) { ShowError(response); return new([], 0, Page, PageSize); }\n\n    return new PagedResult<WorkOrderDto>(\n        response.Data!.Items, response.Data.Total, Page, PageSize);\n}",
          lang="csharp", hint="src/desktop/ViewModels/WorkOrderViewModel.cs",
          png="list", gif="list-status", cap="Заявки в работе, счётчик «5 из 12»",
          note=["Для роли «Мастер» сервер сам ограничивает выдачу заявками его "
                "бригад. Фильтровать это на клиенте нельзя: в ответе придёт "
                "больше строк, чем имеет право видеть пользователь."]),
        S("Карточка заявки", 30,
          "Номер вида Z-2026-0048, оборудование, описание неисправности, "
          "плановые и фактические даты, статус в виде «шагов».",
          code="<StackPanel Spacing=\"14\">\n  <TextBlock Text=\"{Binding Number}\" FontSize=\"24\" FontWeight=\"SemiBold\" />\n  <Grid ColumnDefinitions=\"160,*\" RowSpacing=\"6\">\n    <TextBlock Text=\"Оборудование\" Opacity=\"0.7\" />\n    <TextBlock Grid.Column=\"1\" Text=\"{Binding EquipmentName}\" />\n    <TextBlock Text=\"Приоритет\" Opacity=\"0.7\" />\n    <TextBlock Grid.Column=\"1\" Text=\"{Binding Priority}\" />\n    <TextBlock Text=\"Описание\" Opacity=\"0.7\" />\n    <TextBlock Grid.Column=\"1\" Text=\"{Binding Description}\" TextWrapping=\"Wrap\" />\n    <TextBlock Text=\"Простой\" Opacity=\"0.7\" />\n    <TextBlock Grid.Column=\"1\" Text=\"{Binding DowntimeHours, StringFormat='0.00 ч'}\" />\n  </Grid>\n</StackPanel>",
          lang="xml", hint="src/desktop/Views/WorkOrderCardView.axaml",
          png="card", gif="card-open", cap="Карточка заявки Z-2026-0048",
          note=["Простой показывайте сразу из поля, которое посчитал триггер. "
                "Пустое поле «простой» на открытой заявке выглядит как ошибка, "
                "хотя просто ещё не начался."]),
        S("Назначение бригады", 25,
          "Выбор бригады из списка, недоступные показываются серым. Занятая "
          "бригада вернёт 409 — предупреждаем до отправки.",
          code="var crews = await _api.GetAvailableCrewsAsync(workOrderId, plannedStart, ct);\nif (!crews.Success) { ShowError(crews); return; }\n\nCrews = crews.Data!\n    .Select(c => new CrewOption(c.Id, $\"{c.Name} ({c.MembersCount} чел.)\", c.IsBusy))\n    .ToList();\n\nvar chosen = _dialogs.ChooseCrew(Crews);\nif (chosen is null) return;\n\nvar result = await _api.AssignCrewAsync(Number, chosen.Value, ct);\nif (!result.Success && result.ErrorCode == ErrorCode.CrewBusy)\n    _dialogs.ShowWarning(\"Бригада занята\", \"Выберите другую бригаду или сдвиньте дату.\");\nelse if (!result.Success) ShowError(result);",
          lang="csharp", hint="src/desktop/ViewModels/WorkOrderViewModel.cs",
          png="crew", gif="crew-assign", cap="Выбор бригады: занятые серым, после назначения статус «Назначена»",
          note=["Доступность бригады считает сервер на пересечении плановых "
                "интервалов. Клиент только показывает результат — своими "
                "расчётами вы ничего не добьётесь."]),
        S("Завершение работы", 35,
          "Форма закрытия: фактические даты, выполненные работы, потраченные "
          "материалы с количеством и итог. Стоимость считается на сервере.",
          code="var rows = Materials.Select(m => new WorkOrderMaterialDto(\n    m.Id, m.Quantity, DateTime.Today)).ToList();\n\nvar request = new CompleteWorkOrderRequest(ActualStart, ActualEnd, Comment, rows);\nvar response = await _api.CompleteAsync(Number, request, ct);\n\nif (!response.Success)\n{\n    if (response.ErrorCode == ErrorCode.NotEnoughStock)\n        _dialogs.ShowWarning(\"Недостаточно материалов\", response.Message);\n    else\n        ShowError(response);\n    return;\n}\n\n_toasts.Show($\"Заявка {Number} закрыта на сумму {response.Data!.Cost:0.00} руб.\");",
          lang="csharp", hint="src/desktop/ViewModels/CompleteWorkOrderViewModel.cs",
          png="complete", gif="complete-cost", cap="Форма закрытия и итог 7 300,00 руб. по трём позициям",
          note=["Список материалов берёте из формы, а количество ограничивайте "
                "остатком из справочника. Сервер всё равно проверит и вернёт "
                "409 — ранняя проверка экономит мастеру время."]),
        S("Хлебные крошки и возврат", 20,
          "Карточка открывается поверх списка, кнопка «Назад» возвращает в "
          "список с прежними фильтрами.",
          code="public override void OnNavigatedTo(NavigationContext context)\n{\n    Breadcrumbs = [\"Главная\", \"Заявки\", Number];\n}\n\nprivate void GoBack()\n{\n    NavigationService?.GoBack();\n    FiltersSnapshot = _savedFilters;\n}",
          lang="csharp", hint="src/desktop/ViewModels/WorkOrderViewModel.cs",
          png="nav", cap="Крошки «Главная / Заявки / Z-2026-0048» и возврат к списку",
          note=["Сохраняйте состояние фильтров при возврате. Мастер ушёл в "
                "заявку, посмотрел и вернулся — фильтр сбросился, значит снова "
                "искать. Это заметно тормозит работу."]),
    ],
    [("409 при назначении бригады", "бригада уже занята — покажите предупреждение, а не ошибку"),
     ("409 при списании", "остатка материала не хватает — покажите остаток в диалоге"),
     ("Заявки чужих бригад", "фильтрация по бригаде только на клиенте — исправьте на сервере"),
     ("Итог списания не сходится", "цена берётся из справочника, а не из позиции заявки")],
    "dotnet run --project src/desktop/ToirProf.Desktop.csproj",
    "feat(desktop): экран заявок с карточкой, назначением бригады и закрытием работ",
))

PAGES.append(P(
    34, "Экраны-Бригады-и-Материалы", 15,
    "Два справочника, без которых заявку не закрыть: состав ремонтных бригад и "
    "склад ЗИП с остатками и списанием. Оба экрана строятся на общем компоненте "
    "таблиц, поэтому здесь только форма и специфика.",
    "Экраны «Бригады» и «Материалы» работают: состав бригады редактируется, "
    "остатки видны, списание уходит в заявку.",
    [("Б / Desktop", "Экран «Бригады»"),
     ("Б / Desktop", "Экран «Материалы»"),
     ("Б / Desktop", "Фильтрация, поиск и пагинация")],
    ["src/desktop/Views/CrewsView.axaml", "src/desktop/Views/CrewEditView.axaml",
     "src/desktop/Views/MaterialsView.axaml", "src/desktop/ViewModels/CrewViewModel.cs",
     "src/desktop/ViewModels/MaterialViewModel.cs"],
    [
        S("Список бригад", 25,
          "Название, специализация, численность, текущая загрузка. Занятость "
          "считается сервером по плановым интервалам.",
          code="public sealed record CrewDto(\n    Guid Id,\n    string Name,\n    string Specialization,\n    int MembersCount,\n    int ActiveOrders,\n    decimal Utilization);\n\nprotected override async Task<PagedResult<CrewDto>> FetchAsync(CancellationToken ct)\n{\n    var response = await _api.GetCrewsAsync(Search, Page, PageSize, ct);\n    if (!response.Success) { ShowError(response); return new([], 0, Page, PageSize); }\n    return new(response.Data!.Items, response.Data.Total, Page, PageSize);\n}",
          lang="csharp", hint="src/desktop/ViewModels/CrewViewModel.cs",
          png="crews", gif="crews-load", cap="Список из 4 бригад с загрузкой 82 %",
          note=["Загрузка бригады — отношение занятых часов к доступным. Показывайте "
                "её процентом и цветом: выше 90 % бригада перегружена, и это "
                "видно сразу."]),
        S("Состав бригады", 30,
          "Добавление и удаление участников. Пользователь не может состоять в "
          "двух бригадах — сервер вернёт 409.",
          code="<Grid ColumnDefinitions=\"*,320\" Margin=\"16\">\n  <ItemsControl Grid.Column=\"0\" ItemsSource=\"{Binding Members}\">\n    <ItemsControl.ItemTemplate>\n      <DataTemplate>\n        <Grid ColumnDefinitions=\"*,90,60\" Margin=\"0,4\">\n          <TextBlock Text=\"{Binding FullName}\" />\n          <TextBlock Grid.Column=\"1\" Text=\"{Binding Role}\" Opacity=\"0.7\" />\n          <Button Grid.Column=\"2\" Content=\"✕\" Command=\"{Binding $parent[UserControl].DataContext.RemoveCommand}\"\n                  CommandParameter=\"{Binding}\" />\n        </Grid>\n      </DataTemplate>\n    </ItemsControl.ItemTemplate>\n  </ItemsControl>\n\n  <ComboBox Grid.Column=\"1\" ItemsSource=\"{Binding AvailableUsers}\"\n            SelectedItem=\"{Binding SelectedUser}\" HorizontalAlignment=\"Stretch\" />\n</Grid>",
          lang="xml", hint="src/desktop/Views/CrewEditView.axaml",
          png="members", gif="members-add", cap="Состав бригады: 3 участника, добавление четвёртого",
          note=["Исключайте из списка тех, кто уже в другой бригаде — тогда "
                "409 «пользователь состоит в другой бригаде» не случится на "
                "демонстрации."]),
        S("Список материалов", 30,
          "Наименование, артикул, единица измерения, цена, остаток и минимум. "
          "Дефицитные строки подсвечиваются.",
          code="private bool IsDeficient(MaterialDto m) => m.Stock <= m.MinStock;\n\n<Border Background=\"{Binding RowBackground}\" Padding=\"6\">\n  <TextBlock Text=\"{Binding Name}\" />\n</Border>",
          lang="csharp", hint="src/desktop/ViewModels/MaterialViewModel.cs",
          png="materials", gif="materials-deficit", cap="Склад ЗИП: 18 позиций, дефицитные подсвечены",
          note=["Меняйте цвет не строки, а ячейки с остатком: так список остаётся "
                "читаемым, а проблема всё равно бросается в глаза."]),
        S("Списание в заявку", 35,
          "Из склада можно выбрать материалы и сразу указать их в заявке. "
          "Количество ограничено остатком.",
          code="private int ClampToStock(MaterialDto material, int requested)\n    => Math.Clamp(requested, 0, material.Stock);\n\nvar lines = SelectedMaterials\n    .Select(m => new WorkOrderMaterialDto(m.Id, ClampToStock(m, m.Quantity), DateTime.Today))\n    .ToList();\n\nvar response = await _api.AddMaterialsAsync(Number, lines, ct);\nif (!response.Success)\n{\n    _dialogs.ShowWarning(\"Списание не выполнено\", response.Message);\n    _toasts.Show(\"Остатки изменились, проверьте количество\", ToastKind.Warning);\n}",
          lang="csharp", hint="src/desktop/ViewModels/MaterialViewModel.cs",
          png="writeoff", gif="writeoff-submit", cap="Списание 4 подшипников в заявку Z-2026-0048",
          note=["`Math.Clamp` по остатку снимает большинство 409, но не все: "
                "между вашим запросом и отправкой материал мог списать другой "
                "мастер. Обработку 409 всё равно оставьте."]),
        S("Поиск и пагинация", 20,
          "Оба справочника используют общий компонент таблиц: поиск, сортировка, "
          "страницы — ничего своего.",
          code="<controls:DataTableControl Items=\"{Binding Items}\"\n                                  Total=\"{Binding Total}\"\n                                  Search=\"{Binding Search}\"\n                                  Page=\"{Binding Page}\"\n                                  PageSize=\"{Binding PageSize}\" />",
          lang="xml", hint="src/desktop/Views/MaterialsView.axaml",
          png="table", gif="table-search", cap="Поиск по наименованию и переход на вторую страницу",
          note=["Если для справочника понадобился свой компонент — почти наверняка "
                "вы обошли общий. Добавьте колонку в параметры вместо копии."]),
    ],
    [("409 при добавлении участника", "пользователь уже в другой бригаде — проверьте состав заранее"),
     ("Остаток ушёл в минус", "списание идёт без проверки остатка — добавьте `Math.Clamp`"),
     ("Дефицитные не подсвечены", "сравнение `Stock <= MinStock` не написано в ViewModel"),
     ("Справочник грузится дольше минуты", "в запросе нет `AsNoTracking` и проекции, тянутся лишние поля")],
    "dotnet build src/desktop/ToirProf.Desktop.csproj -c Release",
    "feat(desktop): экраны бригад и материалов со списанием и дефицитами",
))

PAGES.append(P(
    35, "Экран-Отчеты-оффлайн-кэш-и-журнал", 15,
    "Последний экран приложения: сводный отчёт за период, выгрузка в PDF по "
    "временной ссылке, офлайн-кэш с автоотправкой и просмотр локального журнала. "
    "Кэш — требование задания: приложение должно переживать обрыв связи.",
    "Мастер формирует отчёт за период, скачивает PDF; при обрыве связи изменения "
    "уходят в очередь и отправляются автоматически после восстановления.",
    [("Б / Desktop", "Экран «Отчёты»"),
     ("Б / Desktop", "Офлайн-режим с автоотправкой"),
     ("Б / Desktop", "Локальное логирование")],
    ["src/desktop/Views/ReportsView.axaml", "src/desktop/ViewModels/ReportsViewModel.cs",
     "src/desktop/Services/OfflineQueue.cs", "src/desktop/Services/ConnectivityMonitor.cs",
     "src/desktop/Views/LogViewerView.axaml"],
    [
        S("Фильтр отчёта", 25,
          "Вид отчёта, период и цех. Период по умолчанию — текущий месяц.",
          code="<StackPanel Orientation=\"Horizontal\" Spacing=\"12\">\n  <ComboBox ItemsSource=\"{Binding Kinds}\" SelectedItem=\"{Binding Kind}\" MinWidth=\"220\" />\n  <DatePicker SelectedDate=\"{Binding From}\" />\n  <DatePicker SelectedDate=\"{Binding To}\" />\n  <Button Content=\"Сформировать\" Command=\"{BuildCommand}\" IsEnabled=\"{Binding !IsBusy}\" />\n</StackPanel>",
          lang="xml", hint="src/desktop/Views/ReportsView.axaml",
          png="filter", gif="filter-build", cap="Фильтр: сводный отчёт, март 2026, цех «Механический»",
          note=["Проверяйте период на сервере: если `from` позже `to`, придёт "
                "400. Удобнее подставлять в форму начало следующего месяца — "
                "тогда полугодовые отчёты собираются кликами."]),
        S("Формирование и скачивание", 30,
          "Сервер готовит PDF и выдаёт одноразовую ссылку, которая живёт 15 секунд. "
          "Клиент открывает её сразу же.",
          code="var link = await _api.CreateReportLinkAsync(Kind, new DateRange(From!.Value, To!.Value), ct);\nif (!link.Success) { ShowError(link); return; }\n\nvar target = Path.Combine(Path.GetTempPath(), $\"report-{DateTime.Now:yyyyMMdd-HHmmss}.pdf\");\nawait _api.DownloadAsync(link.Data!, target, ct);\n\n_shell.OpenPath(target);",
          lang="csharp", hint="src/desktop/ViewModels/ReportsViewModel.cs",
          png="pdf", gif="pdf-download", cap="Сформирован PDF: 3 страницы, открыт в программе просмотра",
          note=["Ссылка живёт 15 секунд — качать нужно сразу. Если файл не "
                "сохранился, формируйте заново, а не переспрашивайте ссылку: "
                "она уже мертва."]),
        S("Офлайн-очередь", 35,
          "Изменения, сделанные без связи, пишутся в локальный файл и уходят на "
          "сервер при восстановлении соединения.",
          code="public sealed class OfflineQueue\n{\n    private readonly string _path = Path.Combine(AppContext.BaseDirectory, \"queue.json\");\n\n    public void Enqueue(OfflineOperation operation)\n    {\n        var items = Read();\n        items.Add(operation with { EnqueuedAt = DateTime.UtcNow });\n        File.WriteAllText(_path, JsonSerializer.Serialize(items));\n    }\n\n    public async Task<int> FlushAsync(Func<OfflineOperation, Task<bool>> send, CancellationToken ct)\n    {\n        var items = Read();\n        var sent = 0;\n        foreach (var item in items.Where(i => i.EnqueuedAt > DateTime.UtcNow.AddHours(-24)))\n        {\n            if (await send(item)) { sent++; continue; }\n        }\n\n        var rest = Read().Where(i => i.EnqueuedAt > DateTime.UtcNow.AddHours(-24)).Skip(sent).ToList();\n        File.WriteAllText(_path, JsonSerializer.Serialize(rest));\n        return sent;\n    }\n}",
          lang="csharp", hint="src/desktop/Services/OfflineQueue.cs",
          png="queue", gif="queue-flush", cap="Очередь из трёх операций, после связи отправлено три",
          note=["Ограничение по возрасту в 24 часа обязательно: без него очередь "
                "растёт бесконечно, и заявка, созданная три дня назад без "
                "оборудования, приведёт к 409 при отправке."]),
        S("Индикатор связи", 25,
          "Полоса в верхней панели: «Подключено», «Нет связи», «Отправка очереди». "
          "При потере связи пользователь должен узнать об этом сразу.",
          code="public sealed class ConnectivityMonitor : INotifyPropertyChanged\n{\n    public bool IsOnline { get; private set; } = true;\n    public string StatusText => IsOnline ? \"Подключено\" : $\"Нет связи, в очереди {PendingCount}\";\n\n    public ConnectivityMonitor(HttpClient http, OfflineQueue queue)\n    {\n        http.DefaultRequestHeaders.ConnectionClose = true;\n        Timer = new System.Threading.Timer(async _ =>\n        {\n            var online = await PingAsync();\n            if (online && !IsOnline) await queue.FlushAsync(SendOperationAsync, CancellationToken.None);\n            IsOnline = online;\n            Raise();\n        }, null, TimeSpan.FromSeconds(10), TimeSpan.FromSeconds(10));\n    }\n}",
          lang="csharp", hint="src/desktop/Services/ConnectivityMonitor.cs",
          png="connectivity", gif="connectivity-offline", cap="Переход «Подключено → Нет связи → Подключено» с отправкой очереди",
          note=["Проверяйте связь не по пингу хоста, а по реальному запросу к API: "
                "сеть может быть, а сервер лежит. Тогда приложение врёт "
                "пользователю."]),
        S("Просмотр журнала", 25,
          "Последние записи локального журнала прямо в приложении — удобно "
          "показать эксперту при разборе сбоя.",
          code="public IReadOnlyList<LogLine> LoadTail(int count = 200)\n{\n    if (!File.Exists(_path)) return [];\n\n    return File.ReadAllLines(_path)\n        .Reverse()\n        .Take(count)\n        .Select(line => new LogLine(line))\n        .ToList();\n}",
          lang="csharp", hint="src/desktop/Views/LogViewerView.axaml",
          png="log", gif="log-view", cap="Журнал: 200 последних записей с фильтром по уровню",
          note=["Читайте файл целиком и режьте в памяти только для журнала: "
                "`File.ReadLines` с `Take` не поддерживает обратный порядок, "
                "а журнал всегда смотрят с конца."]),
    ],
    [("PDF не открывается", "ссылка истекла за 15 секунд — формируйте заново"),
     ("Очередь не отправляется после связи", "проверка пингует хост вместо API"),
     ("Очередь растёт сутками", "не удаляются отправленные операции"),
     ("Журнал пуст", "путь выбран относительно рабочего каталога, а не кода приложения")],
    "dotnet run --project src/desktop/ToirProf.Desktop.csproj",
    "feat(desktop): отчёты с PDF, офлайн-очередь, индикатор связи и просмотр журнала",
))
# === BLOCK-G: спринты 16–19, страницы 36–45 (Web) ===

PAGES.append(P(
    36, "Проект-Web-клиента-React", 16,
    "Создаём SPA на React 19 + TypeScript + Vite: прокси на API, роутер, "
    "общий HTTP-слой и сборка. Задание разрешает React, Vue или Angular — "
    "выбираем React.",
    "Проект собирается командой `npm run build`, в разработке работает по адресу "
    "localhost:5173 и проксирует запросы к API на 5080.",
    [("Б / Web", "Технология React/Vue/Angular"),
     ("Б / Web", "Подключение к API через REST")],
    ["src/web/package.json", "src/web/vite.config.ts", "src/web/index.html",
     "src/web/src/main.tsx", "src/web/src/App.tsx", "src/web/src/router.tsx",
     "src/web/src/api/http.ts", "src/web/src/api/types.ts"],
    [
        S("Создаём проект и ставим зависимости", 30,
          "Каркас Vite на TypeScript, маршрутизация, работа с состоянием, графики "
          "и экспорт.",
          code="npm create vite@latest src/web -- --template react-ts\ncd src/web\nnpm install\nnpm install react-router-dom recharts date-fns\nnpm install -D @types/node\nnpm install html2canvas jspdf",
          lang="bash", hint="src/web/package.json",
          png="deps", gif="deps-install", cap="Установлено 214 пакетов, audit: 0 уязвимостей",
          note=["Фиксируйте версии в `package-lock.json` и коммитьте его: "
                "на площадке сеть могут закрыть, и установка по свежим тегам "
                "принесёт несовместимую версию."]),
        S("Прокси на API", 25,
          "В разработке запросы идут на относительный путь `/api`, Vite "
          "перенаправляет их на порт 5080. Такой же прокси обязателен в "
          "конфигурации веб-сервера при развёртывании.",
          code="import { defineConfig } from 'vite'\nimport react from '@vitejs/plugin-react'\n\nexport default defineConfig({\n  plugins: [react()],\n  server: {\n    port: 5173,\n    proxy: {\n      '/api': {\n        target: 'http://localhost:5080',\n        changeOrigin: true,\n      },\n    },\n  },\n})",
          lang="typescript", hint="src/web/vite.config.ts",
          png="proxy", gif="proxy-check", cap="Запрос /api/dashboard/summary отдаёт 200 с данными",
          note=["Без прокси в браузере получите ошибку CORS, и потеряете время на "
                "поиск причины. Настраивайте прокси в самом начале — в "
                "конфигурации сервера это тот же принцип, только для nginx."]),
        S("Общий HTTP-слой", 30,
          "Одна функция разговаривает с API: подставляет токен, читает обёртку "
          "ответа и превращает `error_code` в типизированную ошибку.",
          code="export class ApiError extends Error {\n  constructor(\n    public readonly code: string,\n    public readonly status: number,\n    message: string,\n  ) {\n    super(message)\n  }\n}\n\nexport async function request<T>(path: string, init: RequestInit = {}): Promise<T> {\n  const token = localStorage.getItem('toirprof.token')\n  const response = await fetch(`/api${path}`, {\n    ...init,\n    headers: {\n      'Content-Type': 'application/json',\n      ...(token ? { Authorization: `Bearer ${token}` } : {}),\n      ...init.headers,\n    },\n  })\n\n  const payload = await response.json()\n  if (!response.ok || !payload.success) {\n    throw new ApiError(payload.error_code ?? String(response.status), response.status, payload.message)\n  }\n\n  return payload.data as T\n}",
          lang="typescript", hint="src/web/src/api/http.ts",
          png="http", gif="http-401", cap="Разбор ответа: 200 с данными и 401 с кодом INVALID_TOKEN",
          note=["Токен берите из `localStorage`, а не из замыкания: после "
                "перезагрузки страницы любое состояние React сбрасывается, "
                "а хранилище живёт."]),
        S("Роутер и каркас", 30,
          "Маршруты описаны один раз в `router.tsx`, защищённые оборачиваются "
          "в `RequireAuth`.",
          code="export const router = createBrowserRouter([\n  { path: '/login', element: <LoginPage /> },\n  {\n    element: <RequireAuth><AppShell /></RequireAuth>,\n    children: [\n      { path: '/', element: <DashboardPage /> },\n      { path: '/analytics', element: <AnalyticsPage /> },\n      { path: '/equipment', element: <EquipmentPage /> },\n      { path: '/work-orders', element: <WorkOrdersPage /> },\n      { path: '/schedule', element: <SchedulePage /> },\n      { path: '/users', element: <UsersPage /> },\n    ],\n  },\n])",
          lang="tsx", hint="src/web/src/router.tsx",
          png="router", gif="router-run", cap="Маршруты приложения в адресной строке",
          note=["В `router.tsx` должен быть маршрут на каждую страницу задания. "
                "Экран, до которого нельзя дойти по URL, не попадёт в "
                "демонстрацию и не будет проверен."]),
        S("Сборка и проверка", 25,
          "Прод-сборка должна проходить без ошибок типов и предупреждений.",
          code="npm run build\nnpm run preview -- --port 4173",
          lang="bash", hint="src/web/",
          png="build", gif="build-preview", cap="Сборка: 214 модулей, 320 КБ gzip, предпросмотр на 4173",
          note=["Прогоняйте `npm run build` после каждого экрана, а не в конце. "
                "Ошибка типов в пяти файлах от последнего экрана обойдётся "
                "двумя часами отладки."]),
    ],
    [("Ошибка CORS в консоли", "не настроен прокси в `vite.config.ts`"),
     ("`Cannot use import statement outside a module`", "не установлен плагин React или не сработал шаблон Vite"),
     ("Белая страница вместо приложения", "ошибка в `main.tsx` — смотрите консоль браузера"),
     ("Сборка падает на типах", "не запускайте `tsc` отдельно — ошибки видны в выводе `npm run build`")],
    "npm run build --prefix src/web",
    "feat(web): каркас React-проекта с прокси, HTTP-слоем и роутером",
))

PAGES.append(P(
    37, "Авторизация-и-оболочка-интерфейса", 16,
    "Вход, хранение токена, защита маршрутов и оболочка приложения: боковое "
    "меню, верхняя панель, хлебные крошки, уведомления. Роли определяют, "
    "какие пункты меню видны.",
    "После входа пользователь попадает на дашборд, меню соответствует роли, "
    "выход очищает токен и возвращает на страницу входа.",
    [("Б / Web", "Форма входа"),
     ("Б / Web", "Навигация и структура интерфейса"),
     ("Б / Web", "Уведомления об ошибках")],
    ["src/web/src/pages/LoginPage.tsx", "src/web/src/auth/AuthContext.tsx",
     "src/web/src/auth/RequireAuth.tsx", "src/web/src/layout/AppShell.tsx",
     "src/web/src/layout/Sidebar.tsx", "src/web/src/layout/Topbar.tsx",
     "src/web/src/components/ToastProvider.tsx"],
    [
        S("Контекст авторизации", 30,
          "Один провайдер хранит пользователя, токен и роль. Все экраны читают их "
          "через хук, а не через отдельные вызовы `localStorage`.",
          code="const AuthContext = createContext<AuthState | null>(null)\n\nexport function AuthProvider({ children }: { children: ReactNode }) {\n  const [user, setUser] = useState<User | null>(() => {\n    const raw = localStorage.getItem('toirprof.user')\n    return raw ? (JSON.parse(raw) as User) : null\n  })\n\n  const signIn = async (login: string, password: string) => {\n    const data = await request<AuthResult>('/auth/login', {\n      method: 'POST',\n      body: JSON.stringify({ login, password }),\n    })\n\n    localStorage.setItem('toirprof.token', data.accessToken)\n    localStorage.setItem('toirprof.user', JSON.stringify(data.user))\n    setUser(data.user)\n  }\n\n  const signOut = () => {\n    localStorage.removeItem('toirprof.token')\n    localStorage.removeItem('toirprof.user')\n    setUser(null)\n  }\n\n  return <AuthContext.Provider value={{ user, signIn, signOut }}>{children}</AuthContext.Provider>\n}",
          lang="tsx", hint="src/web/src/auth/AuthContext.tsx",
          png="auth-context", gif="auth-signin", cap="Вход мастером: токен сохранён, роль в контексте",
          note=["Инициализация состояния из `localStorage` через ленивую "
                "функцию обязательна: иначе при первой отрисовке `user` равен "
                "null, защищённый маршрут перебросит на вход, и только потом "
                "появится дашборд — мигание, которое видно на демонстрации."]),
        S("Защита маршрутов", 25,
          "Обёртка проверяет наличие пользователя и роль. При выходе текущий "
          "маршрут сбрасывается.",
          code="export function RequireAuth({ children }: { children: ReactNode }) {\n  const { user } = useAuth()\n  const location = useLocation()\n\n  if (!user) {\n    return <Navigate to=\"/login\" replace state={{ from: location.pathname }} />\n  }\n\n  return <>{children}</>\n}\n\nexport function RequireRole({ role, children }: { role: string; children: ReactNode }) {\n  const { user } = useAuth()\n  return user?.role === role ? <>{children}</> : <Navigate to=\"/\" replace />\n}",
          lang="tsx", hint="src/web/src/auth/RequireAuth.tsx",
          png="guard", gif="guard-redirect", cap="Переход на /users под ролью «Мастер» возвращает на дашборд",
          note=["Скрытие пункта меню не защищает маршрут: роль проверяется ещё и "
                "на сервере, а `RequireRole` — второй эшелон на клиенте."]),
        S("Боковое меню и верхняя панель", 35,
          "Меню строится из списка с указанием роли, активный пункт "
          "подсвечивается. Верхняя панель: имя, роль, кнопка выхода.",
          code="const NAV = [\n  { to: '/', label: 'Дашборд', roles: ['ADMIN', 'MANAGER', 'MASTER'] },\n  { to: '/analytics', label: 'Аналитика', roles: ['ADMIN', 'MANAGER'] },\n  { to: '/equipment', label: 'Оборудование', roles: ['ADMIN', 'MANAGER', 'MASTER'] },\n  { to: '/work-orders', label: 'Заявки', roles: ['ADMIN', 'MANAGER', 'MASTER'] },\n  { to: '/schedule', label: 'График ТО', roles: ['ADMIN', 'MANAGER', 'MASTER'] },\n  { to: '/users', label: 'Пользователи', roles: ['ADMIN'] },\n] as const\n\nexport function Sidebar() {\n  const { user } = useAuth()\n  const visible = NAV.filter((item) => (item.roles as readonly string[]).includes(user!.role))\n\n  return (\n    <nav className=\"sidebar\">\n      {visible.map((item) => (\n        <NavLink key={item.to} to={item.to} end={item.to === '/'}>\n          {item.label}\n        </NavLink>\n      ))}\n    </nav>\n  )\n}",
          lang="tsx", hint="src/web/src/layout/Sidebar.tsx",
          png="menu", gif="menu-role", cap="Меню руководителя (6 пунктов) и мастера (5)",
          note=["Мастеру не нужен раздел «Аналитика» с рейтингом бригад — это "
                "управленческая информация. Скрывайте по роли, а не «всем всё "
                "показать»."]),
        S("Хлебные крошки", 25,
          "Строятся из вложенности маршрута и заменяют заголовок страницы.",
          code="export function Breadcrumbs({ trail }: { trail: string[] }) {\n  return (\n    <nav className=\"crumbs\" aria-label=\"Хлебные крошки\">\n      {trail.map((title, index) => (\n        <span key={title}>\n          {index > 0 && <span className=\"sep\">/</span>}\n          {index === trail.length - 1 ? <b>{title}</b> : <span>{title}</span>}\n        </span>\n      ))}\n    </nav>\n  )\n}",
          lang="tsx", hint="src/web/src/layout/AppShell.tsx",
          png="crumbs", cap="Крошки «Главная / Аналитика / Простои»",
          note=["Последний элемент не ссылка — так же, как в desktop-клиенте. "
                "Единое поведение на всех клиентах выглядит как продуманная "
                "система."]),
        S("Уведомления об ошибках", 25,
          "Глобальный провайдер тостов: API-слой сообщает об ошибке, провайдер "
          "показывает, экраны не знают ничего.",
          code="export function ToastProvider({ children }: { children: ReactNode }) {\n  const [toasts, setToasts] = useState<Toast[]>([])\n\n  const push = useCallback((text: string, kind: ToastKind = 'info') => {\n    const id = crypto.randomUUID()\n    setToasts((prev) => [...prev, { id, text, kind }])\n    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000)\n  }, [])\n\n  return (\n    <ToastContext.Provider value={push}>\n      {children}\n      <div className=\"toast-host\" role=\"status\">\n        {toasts.map((toast) => (\n          <div key={toast.id} className={`toast toast--${toast.kind}`}>{toast.text}</div>\n        ))}\n      </div>\n    </ToastContext.Provider>\n  )\n}",
          lang="tsx", hint="src/web/src/components/ToastProvider.tsx",
          png="toast", gif="toast-error", cap="Тост об ошибке 409 в правом нижнем углу",
          note=["`role=\"status\"` обязателен: без него программы чтения с экрана "
                "не озвучат ошибку, а доступность проверяется отдельным "
                "критерием."]),
    ],
    [("После обновления страницы снова экран входа", "состояние инициализируется не из `localStorage`"),
     ("Пункт меню не исчезает у мастера", "роль сравнивается как объект, а не как строка"),
     ("Тост не пропадает", "используется `setInterval` без очистки интервала"),
     ("Ошибка 401 не возвращает на вход", "нужен интерцептор, очищающий токен при коде `INVALID_TOKEN`")],
    "npm run build --prefix src/web",
    "feat(web): авторизация, защита маршрутов, оболочка с меню и крошками",
))

PAGES.append(P(
    38, "Каркас-дашборда-и-KPI-карточки", 17,
    "Главный экран руководителя: шесть KPI-карточек, автообновление раз в минуту "
    "и состояния загрузки. Данные приходят одним запросом с дашборда.",
    "Дашборд открывается за один запрос, показывает шесть показателей и сам "
    "обновляется раз в минуту, не мешая работе.",
    [("Б / Web", "Главный дашборд руководителя"),
     ("Б / Web", "Карточки показателей")],
    ["src/web/src/pages/DashboardPage.tsx", "src/web/src/components/MetricCard.tsx",
     "src/web/src/components/StatusBadge.tsx", "src/web/src/hooks/useApi.ts",
     "src/web/src/styles/dashboard.css"],
    [
        S("Хук загрузки данных", 25,
          "Один хук на все экраны: состояние загрузки, ошибки, данные и "
          "повторный запрос.",
          code="export function useApi<T>(path: string, deps: unknown[] = []) {\n  const [data, setData] = useState<T | null>(null)\n  const [error, setError] = useState<ApiError | null>(null)\n  const [loading, setLoading] = useState(true)\n\n  const reload = useCallback(async () => {\n    setLoading(true)\n    try {\n      setData(await request<T>(path))\n      setError(null)\n    } catch (e) {\n      setError(e as ApiError)\n    } finally {\n      setLoading(false)\n    }\n  }, [path])\n\n  useEffect(() => {\n    void reload()\n  }, [reload, ...deps])\n\n  return { data, error, loading, reload }\n}",
          lang="typescript", hint="src/web/src/hooks/useApi.ts",
          png="hook", cap="Хук useApi с состояниями данных, ошибки и загрузки",
          note=["Зависимости передаются вторым аргументом, а не вручную внутри "
                "массива: иначе линтер ругается, а массив создаётся заново "
                "на каждом рендере."]),
        S("Шесть карточек", 30,
          "Карточка: заголовок, крупное значение, подпись с периодом и стрелка "
          "изменения к прошлому периоду.",
          code="export function MetricCard({ title, value, caption, delta }: MetricCardProps) {\n  return (\n    <article className=\"metric\">\n      <h3>{title}</h3>\n      <p className=\"metric__value\">{value}</p>\n      <p className=\"metric__caption\">{caption}</p>\n      {delta !== undefined && (\n        <span className={`metric__delta ${delta < 0 ? 'is-down' : 'is-up'}`}>\n          {delta > 0 ? '↑' : '↓'} {Math.abs(delta)}%\n        </span>\n      )}\n    </article>\n  )\n}",
          lang="tsx", hint="src/web/src/components/MetricCard.tsx",
          png="metrics", gif="metrics-load", cap="Шесть карточек: 47, 12, 31, 6,3 ч, 19,1 %, 84,0 %",
          note=["Подпись под значением обязательна: без неё «6,3» неотличимо от "
                "процентов. Эксперты читают дашборд за три секунды."]),
        S("Состояния загрузки и ошибки", 25,
          "Первая загрузка — скелетоны карточек, повторная — обновление данных на "
          "месте, ошибка — плашка с кнопкой «Повторить».",
          code="{loading && !data && (\n  <div className=\"metric-grid\">\n    {Array.from({ length: 6 }).map((_, i) => (\n      <div key={i} className=\"metric skeleton\" />\n    ))}\n  </div>\n)}\n\n{error && (\n  <div className=\"error-banner\" role=\"alert\">\n    <span>{error.message}</span>\n    <button onClick={reload}>Повторить</button>\n  </div>\n)}",
          lang="tsx", hint="src/web/src/pages/DashboardPage.tsx",
          png="states", gif="states-retry", cap="Скелетоны, затем данные, затем плашка ошибки 500",
          note=["Пустое состояние при первой загрузке мигает белым прямоугольником. "
                "Скелетоны на 6 карточек — двадцать строк кода, а выглядит как "
                "продуманное приложение."]),
        S("Автообновление раз в минуту", 25,
          "Интервал очищается при размонтировании, при скрытой вкладке опрос "
          "приостанавливается.",
          code="useEffect(() => {\n  const timer = setInterval(() => {\n    if (document.visibilityState === 'visible') void reload()\n  }, 60_000)\n\n  return () => clearInterval(timer)\n}, [reload])",
          lang="typescript", hint="src/web/src/pages/DashboardPage.tsx",
          png="auto", gif="auto-refresh", cap="Автообновление через 60 секунд без перезагрузки страницы",
          note=["Проверка `document.visibilityState` экономит запросы, когда "
                "вкладка не видна. На ноутбуке со спящим экраном это заметная "
                "разница в трафике."]),
        S("Адаптивность 1024–1920", 25,
          "Сетка карточек перестраивается: три в ряд на 1024, шесть на 1920.",
          code=".metric-grid {\n  display: grid;\n  gap: 16px;\n  grid-template-columns: repeat(3, minmax(0, 1fr));\n}\n\n@media (min-width: 1600px) {\n  .metric-grid { grid-template-columns: repeat(6, minmax(0, 1fr)); }\n}\n\n@media (max-width: 1100px) {\n  .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }\n}",
          lang="css", hint="src/web/src/styles/dashboard.css",
          png="responsive", cap="Дашборд на 1024, 1440 и 1920 пикселях",
          note=["Требование задания — от 1024×768 до 1920×1080. Проверяйте оба "
                "края: на 1024 сетка в три колонки уже тесновата с подписями "
                "длиннее 20 символов."]),
    ],
    [("Данные грузятся дважды при монтировании", "хук вызывается и в компоненте, и в `useEffect`"),
     ("Таймер не останавливается", "не возвращена очистка из `useEffect`"),
     ("Карточки наезжают друг на друга", "фиксированная ширина вместо `grid-template-columns`"),
     ("Экран разваливается на 1024", "нет медиазапроса для узкой сетки")],
    "npm run build --prefix src/web",
    "feat(web): дашборд руководителя с KPI-карточками, состояниями и автообновлением",
))

PAGES.append(P(
    39, "Графики-топ-простоев-и-последние-заявки", 17,
    "Графическая часть дашборда: круговая диаграмма по статусам, столбчатая по "
    "цехам, линейная по месяцам, топ-5 простоев и таблица последних заявок. "
    "Подписи и подсказки — на русском.",
    "Дашборд показывает три типа графиков, топ-5 единиц оборудования по простою "
    "и последние заявки с переходом в карточку.",
    [("Б / Web", "Круговая, столбчатая и линейная диаграммы"),
     ("Б / Web", "Топ-5 простоев"),
     ("Б / Web", "Таблица последних заявок")],
    ["src/web/src/components/StatusPie.tsx", "src/web/src/components/WorkshopBar.tsx",
     "src/web/src/components/MonthlyLine.tsx", "src/web/src/components/TopDowntime.tsx",
     "src/web/src/components/RecentOrders.tsx"],
    [
        S("Круговая диаграмма по статусам", 30,
          "Доли заявок по статусам. Легенда справа, проценты внутри секторов, "
          "цвета фиксированные — иначе цвета прыгают между обновлениями.",
          code="const STATUS_COLORS: Record<WorkOrderStatus, string> = {\n  'Черновик': '#9E9E9E',\n  'Назначена': '#1F6FEB',\n  'В работе': '#F9A825',\n  'Завершена': '#2E7D32',\n  'Отменена': '#C62828',\n}\n\nexport function StatusPie({ data }: { data: StatusSlice[] }) {\n  return (\n    <ResponsiveContainer width=\"100%\" height={260}>\n      <PieChart>\n        <Pie data={data} dataKey=\"count\" nameKey=\"status\" innerRadius={60} outerRadius={100}\n             label={({ percent }) => `${(percent * 100).toFixed(0)}%`}>\n          {data.map((entry) => (\n            <Cell key={entry.status} fill={STATUS_COLORS[entry.status]} />\n          ))}\n        </Pie>\n        <Tooltip formatter={(v: number) => [`${v} заявок`, '']} />\n        <Legend verticalAlign=\"bottom\" />\n      </PieChart>\n    </ResponsiveContainer>\n  )\n}",
          lang="tsx", hint="src/web/src/components/StatusPie.tsx",
          png="pie", gif="pie-hover", cap="Распределение заявок по статусам: 47 всего, 19,1 % аварийных",
          note=["Палитру держите в константе, а не задавайте по индексу массива: "
                "при смене порядка данных цвета «переедут» на другие статусы, и "
                "эксперт увидит в легенде одно, а на диаграмме другое."]),
        S("Столбчатая по цехам", 25,
          "Сравнение заявок и простоев по цехам — две группы столбцов.",
          code="export function WorkshopBar({ data }: { data: WorkshopSlice[] }) {\n  return (\n    <ResponsiveContainer width=\"100%\" height={260}>\n      <BarChart data={data} margin={{ left: 8, right: 8 }}>\n        <CartesianGrid strokeDasharray=\"3 3\" vertical={false} />\n        <XAxis dataKey=\"name\" tick={{ fontSize: 12 }} />\n        <YAxis allowDecimals={false} />\n        <Tooltip />\n        <Legend />\n        <Bar dataKey=\"total\" name=\"Заявок\" fill=\"#1F6FEB\" radius={[4, 4, 0, 0]} />\n        <Bar dataKey=\"completed\" name=\"Завершено\" fill=\"#2E7D32\" radius={[4, 4, 0, 0]} />\n      </BarChart>\n    </ResponsiveContainer>\n  )\n}",
          lang="tsx", hint="src/web/src/components/WorkshopBar.tsx",
          png="bar", cap="Сравнение заявок и завершённых по трём цехам",
          note=["`allowDecimals={false}` убирает «2,5 заявок» на оси: счётчик "
                "целый, и подписи дробей сразу бросаются в глаза."]),
        S("Линейная по месяцам", 25,
          "Динамика заявок и простоев по месяцам — тренд за полугодие.",
          code="export function MonthlyLine({ data }: { data: MonthlySlice[] }) {\n  return (\n    <ResponsiveContainer width=\"100%\" height={260}>\n      <LineChart data={data}>\n        <CartesianGrid strokeDasharray=\"3 3\" vertical={false} />\n        <XAxis dataKey=\"label\" />\n        <YAxis />\n        <Tooltip />\n        <Legend />\n        <Line type=\"monotone\" dataKey=\"count\" name=\"Заявок\" stroke=\"#1F6FEB\" strokeWidth={2} dot={false} />\n        <Line type=\"monotone\" dataKey=\"downtime\" name=\"Простой, ч\" stroke=\"#C62828\" strokeWidth={2} dot={false} />\n      </LineChart>\n    </ResponsiveContainer>\n  )\n}",
          lang="tsx", hint="src/web/src/components/MonthlyLine.tsx",
          png="line", cap="Динамика: 38, 41, 47 заявок с января по март",
          note=["Подписи месяцев — короткие «янв», «фев». Полные «Январь» в "
                "шести местах на оси на 1024 пикселях наезжают друг на друга."]),
        S("Топ-5 простоев", 25,
          "Пять единиц оборудования с наибольшим простоем за период, с долей "
          "от общего времени.",
          code="export function TopDowntime({ items }: { items: DowntimeItem[] }) {\n  const total = items.reduce((sum, item) => sum + item.hours, 0)\n\n  return (\n    <ol className=\"top-list\">\n      {items.slice(0, 5).map((item, index) => (\n        <li key={item.equipmentId}>\n          <span className=\"rank\">{index + 1}</span>\n          <span className=\"name\">{item.equipmentName}</span>\n          <span className=\"hours\">{item.hours.toFixed(1)} ч</span>\n          <span className=\"share\">{total ? ((item.hours / total) * 100).toFixed(0) : 0}%</span>\n        </li>\n      ))}\n    </ol>\n  )\n}",
          lang="tsx", hint="src/web/src/components/TopDowntime.tsx",
          png="top", gif="top-hover", cap="Топ-5 простоев: пресс ПР-2 — 18,4 ч, 21 %",
          note=["Доля считается от суммы по топ-5, а не от всех единиц: так "
                "нагляднее видно, сколько даёт каждая позиция. Подпишите это "
                "в заголовке блока, чтобы не путать."]),
        S("Последние заявки", 25,
          "Пять последних заявок: номер, оборудование, статус, приоритет. "
          "Строка кликабельна.",
          code="export function RecentOrders({ items }: { items: WorkOrderDto[] }) {\n  return (\n    <table className=\"data-table\">\n      <thead>\n        <tr>\n          <th>Номер</th><th>Оборудование</th><th>Статус</th><th>Приоритет</th>\n        </tr>\n      </thead>\n      <tbody>\n        {items.map((order) => (\n          <tr key={order.number} onClick={() => navigate(`/work-orders/${order.number}`)}>\n            <td>{order.number}</td>\n            <td>{order.equipmentName}</td>\n            <td><StatusBadge status={order.status} /></td>\n            <td>{order.priority}</td>\n          </tr>\n        ))}\n      </tbody>\n    </table>\n  )\n}",
          lang="tsx", hint="src/web/src/components/RecentOrders.tsx",
          png="orders", gif="orders-open", cap="Пять последних заявок, строка ведёт в карточку",
          note=["Клик по строке ведёт в карточку — на демонстрации экономит "
                "кучу времени. Без этого эксперту приходится искать номер в "
                "списке заявок."]),
    ],
    [("График пустой при данных", "не совпадает имя ключа: сервер отдаёт `name`, компонент ждёт `status`"),
     ("Цвета прыгают при обновлении", "палитра задана по индексу массива"),
     ("Подписи наезжают друг на друга", "ось месяцев с полными названиями"),
     ("Проценты в сумме дают 99 %", "округление каждого сектора отдельно")],
    "npm run build --prefix src/web",
    "feat(web): графики дашборда, топ-5 простоев и таблица последних заявок",
))
# === END-BLOCK-G ===
# === END-BLOCK-F2 ===
# === END-BLOCK-F ===
# === BLOCK-H: спринты 18–19, страницы 40–45 (Web: аналитика, realtime, реестры) ===

PAGES.append(P(
    40, "Панель-фильтров-и-сводка-заявок", 18,
    "Панель фильтров над аналитикой и первый блок — сводка по заявкам. Фильтры должны "
    "менять все пять блоков разом, иначе аналитика показывает разные периоды в разных "
    "графиках.",
    "Один набор фильтров (период, цех, статус, приоритет) управляет всей страницей аналитики.",
    [("Б / Web", "Панель фильтров и сводка по заявкам")],
    ["src/web/src/pages/AnalyticsPage.tsx", "src/web/src/components/FilterPanel.tsx",
     "src/web/src/api/types.ts"],
    [
        S("Описываем модель фильтров", 25,
          "Фильтры хранятся в URL-параметрах — тогда ссылку на настроенную аналитику можно "
          "показать руководителю или эксперту.",
          code="export interface AnalyticsFilters {\n  from: string;          // ISO-дата\n  to: string;\n  workshopId?: string;\n  status?: WorkOrderStatus | 'all';\n  priority?: WorkOrderPriority | 'all';\n}\n\nexport const DEFAULT_FILTERS: AnalyticsFilters = {\n  from: startOfMonth(new Date()).toISOString().slice(0, 10),\n  to: new Date().toISOString().slice(0, 10),\n  workshopId: undefined,\n  status: 'all',\n  priority: 'all',\n};",
          lang="typescript", hint="src/web/src/api/types.ts",
          png="filters-type", cap="AnalyticsFilters и значения по умолчанию — текущий месяц",
          note=["Даты храните в ISO (`YYYY-MM-DD`), а не в локализованном виде. "
                "Формат `31.03.2026` нельзя безопасно передать в `new Date()` во всех "
                "браузерах одинаково."]),
        S("Собираем панель фильтров", 35,
          "Период двумя полями с предустановками («сегодня», «7 дней», «месяц», «квартал»), "
          "цех и статус — выпадающими списками. Кнопка «Сбросить» возвращает значения по умолчанию.",
          code="export function FilterPanel({ value, onChange, workshops }: Props) {\n  return (\n    <div className=\"filter-panel\">\n      <label>Период с <input type=\"date\" value={value.from}\n        onChange={(e) => onChange({ ...value, from: e.target.value })} /></label>\n      <label>по <input type=\"date\" value={value.to}\n        onChange={(e) => onChange({ ...value, to: e.target.value })} /></label>\n      <Presets onPick={(from, to) => onChange({ ...value, from, to })} />\n      <label>Цех <select value={value.workshopId ?? 'all'}\n        onChange={(e) => onChange({ ...value, workshopId: e.target.value })}>\n        <option value=\"all\">Все цеха</option>\n        {workshops.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}\n      </select></label>\n      <label>Статус <StatusSelect value={value.status}\n        onChange={(status) => onChange({ ...value, status })} /></label>\n      <button onClick={() => onChange(DEFAULT_FILTERS)}>Сбросить</button>\n    </div>\n  );\n}",
          lang="typescript", hint="src/web/src/components/FilterPanel.tsx",
          png="filter-panel", gif="filter-change", cap="Панель фильтров: период, пресеты, цех, статус, сброс",
          note=["Кнопки-пресеты обязательны: эксперту проще нажать «Квартал», чем вбивать "
                "даты, и демонстрация выглядит убедительнее."]),
        S("Применяем фильтры ко всем блокам", 30,
          "Один объект фильтров уходит в пять запросов аналитики. Каждый блок получает "
          "свою `useApi` с одинаковыми параметрами.",
          code="const qs = useMemo(() => new URLSearchParams({\n  from: filters.from,\n  to: filters.to,\n  ...(filters.workshopId && { workshopId: filters.workshopId }),\n  ...(filters.status !== 'all' && { status: filters.status }),\n  ...(filters.priority !== 'all' && { priority: filters.priority }),\n}).toString(), [filters]);\n\nconst summary = useApi<OrdersSummary>(`/api/analytics/orders?${qs}`);\nconst downtime = useApi<DowntimeAnalysis>(`/api/analytics/downtime?${qs}`);\nconst materials = useApi<MaterialsAnalysis>(`/api/analytics/materials?${qs}`);\nconst schedule = useApi<ScheduleExecution>(`/api/analytics/schedule?${qs}`);\nconst crews = useApi<CrewEfficiency>(`/api/analytics/crews?${qs}`);",
          lang="typescript", hint="src/web/src/pages/AnalyticsPage.tsx",
          png="filters-applied", gif="filters-applied", cap="Пять блоков пересчитались за один выбор периода",
          note=["Собирайте строку запросов через `URLSearchParams`, а не склейкой. "
                "Скобка в значении фильтра иначе ломает разбор на стороне сервера."]),
        S("Блок «Сводка по заявкам»", 35,
          "Счётчики (всего, завершено, в работе, средний простой) плюс распределение по "
          "статусам. Это то, что руководитель смотрит первым.",
          code="export function OrdersSummaryBlock({ data }: { data: OrdersSummary }) {\n  return (\n    <section className=\"analytics-block\" id=\"block-orders\">\n      <header><h3>Сводка по заявкам</h3></header>\n      <div className=\"metric-row\">\n        <MetricCard label=\"Всего заявок\" value={data.total} />\n        <MetricCard label=\"Завершено\" value={data.completed} tone=\"success\" />\n        <MetricCard label=\"В работе\" value={data.inProgress} tone=\"warning\" />\n        <MetricCard label=\"Средний простой\" value={data.averageDowntime} suffix=\" ч\" />\n      </div>\n      <StatusPie data={data.byStatus} />\n    </section>\n  );\n}",
          lang="typescript", hint="src/web/src/components/OrdersSummary.tsx",
          png="orders-summary", gif="orders-summary", cap="Сводка за квартал: 132 заявки, 118 завершено, 9 в работе",
          note=["У блока должен быть стабильный `id` (`block-orders`) — по нему работает "
                "экспорт отдельного блока в PNG и PDF."]),
    ],
    [("Фильтры не влияют на блоки", "запросы собираются до применения `qs`"),
     ("Дата «31.03.2026» не парсится", "используйте ISO-формат в значении `input type=date`"),
     ("Графики разных блоков показывают разные периоды", "забыли передать `qs` в один из `useApi`")],
    "cd src/web && npm run build",
    "feat(web): панель фильтров аналитики и блок сводки по заявкам",
))

PAGES.append(P(
    41, "Блоки-аналитики-простои-материалы-график-бригады", 18,
    "Четыре оставшихся блока аналитики: простои, материалы, выполнение графика ТО и "
    "эффективность бригад с рейтингом. Каждый блок — независимый компонент со своим "
    "запросом и своим состоянием загрузки.",
    "Страница аналитики закрывает все пять блоков из задания и обновляется одним движением фильтра.",
    [("Б / Web", "Анализ простоев, материалов, графика и бригад")],
    ["src/web/src/components/DowntimeBlock.tsx", "src/web/src/components/MaterialsBlock.tsx",
     "src/web/src/components/ScheduleExecutionBlock.tsx", "src/web/src/components/CrewRatingBlock.tsx"],
    [
        S("Анализ простоев", 30,
          "Горизонтальная диаграмма топ-5 единиц по суммарному простою за период плюс "
          "среднее по цеху — это ответ на вопрос «где теряем время».",
          code="export function DowntimeBlock({ data }: { data: DowntimeAnalysis }) {\n  return (\n    <section className=\"analytics-block\" id=\"block-downtime\">\n      <h3>Анализ простоев</h3>\n      <ul className=\"downtime-list\">\n        {data.top.map((item) => (\n          <li key={item.equipmentId}>\n            <span className=\"name\">{item.equipmentName}</span>\n            <span className=\"bar\" style={{ width: `${(item.hours / data.max) * 100}%` }} />\n            <span className=\"value\">{item.hours.toFixed(1)} ч</span>\n            <span className=\"share\">{item.share.toFixed(0)} %</span>\n          </li>\n        ))}\n      </ul>\n      <p className=\"hint\">Средний простой по цеху: {data.averageHours.toFixed(1)} ч</p>\n    </section>\n  );\n}",
          lang="typescript", hint="src/web/src/components/DowntimeBlock.tsx",
          png="downtime-block", gif="downtime-block", cap="Топ-5 простоев: пресс ПР-2 — 18,4 ч, 21 % всех простоев",
          note=["Делите на `data.max`, а не на константу 24 или 100. Иначе при резком "
                "росте простоя все полосы кроются в один пиксель."]),
        S("Анализ материалов", 30,
          "Две цифры, которые чаще всего спрашивают: сколько списано за период и по каким "
          "позициям. Плюс дефицитные остатки из справочника.",
          code="export function MaterialsBlock({ data }: { data: MaterialsAnalysis }) {\n  return (\n    <section className=\"analytics-block\" id=\"block-materials\">\n      <h3>Анализ материалов</h3>\n      <div className=\"metric-row\">\n        <MetricCard label=\"Списано за период\" value={data.totalCost} format=\"money\" />\n        <MetricCard label=\"Позиций списания\" value={data.lines.length} />\n        <MetricCard label=\"Позиций в дефиците\" value={data.shortages.length}\n          tone={data.shortages.length ? 'danger' : 'neutral'} />\n      </div>\n      <DataTable columns={COLUMNS} rows={data.lines} />\n      <ShortageList items={data.shortages} />\n    </section>\n  );\n}",
          lang="typescript", hint="src/web/src/components/MaterialsBlock.tsx",
          png="materials-block", gif="materials-block", cap="Списано 128 400,00 руб. за квартал, дефицит: 2 позиции",
          note=["Денежные суммы форматируйте через `Intl.NumberFormat('ru-RU', "
                "{ style: 'currency', currency: 'RUB' })`. Ручная склейка `+ ' руб.'` "
                "даёт «7300 руб.» вместо «7 300,00 ₽» и выглядит неаккуратно."]),
        S("Выполнение графика ТО", 30,
          "Плановые работы делятся на выполненные и просроченные. Тут же доля выполнения "
          "в процентах — она же идёт в KPI-карточку дашборда.",
          code="export function ScheduleExecutionBlock({ data }: { data: ScheduleExecution }) {\n  const done = data.completed;\n  const overdue = data.overdue;\n  const total = done + overdue + data.planned;\n  const percent = total === 0 ? 0 : Math.round(((done + overdue) * 100) / total);\n  return (\n    <section className=\"analytics-block\" id=\"block-schedule\">\n      <h3>Выполнение графика ТО</h3>\n      <div className=\"progress\" role=\"progressbar\" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100}>\n        <div className=\"progress-bar\" style={{ width: `${percent}%` }} />\n      </div>\n      <p>Выполнено {percent} % — {done} из {total} записей</p>\n      <ul>\n        {data.overdueList.map((row) => (\n          <li key={row.id}>{row.equipmentName} — просрочено на {row.daysOverdue} дн.</li>\n        ))}\n      </ul>\n    </section>\n  );\n}",
          lang="typescript", hint="src/web/src/components/ScheduleExecutionBlock.tsx",
          png="schedule-block", gif="schedule-block", cap="Выполнение графика ТО: 84 %, просрочено 3 записи",
          note=["`role=\"progressbar\"` и `aria-valuenow` обязательны: без них прогресс-бар "
                "не читается программами экранного доступа, и это снимают на проверке "
                "доступности."]),
        S("Эффективность бригад с рейтингом", 30,
          "Рейтинг считает сервер, клиент только отображает. Столбчатая диаграмма по "
          "баллам плюс таблица с числом заявок и простоем на бригаду.",
          code="export function CrewRatingBlock({ data }: { data: CrewEfficiency }) {\n  return (\n    <section className=\"analytics-block\" id=\"block-crews\">\n      <h3>Эффективность бригад</h3>\n      <ol className=\"crew-ranking\">\n        {data.rating.map((crew, index) => (\n          <li key={crew.crewId} className={index === 0 ? 'leader' : undefined}>\n            <span className=\"place\">{index + 1}</span>\n            <span className=\"name\">{crew.crewName}</span>\n            <span className=\"score\">{crew.score} баллов</span>\n            <span className=\"orders\">{crew.completedOrders} заявок</span>\n          </li>\n        ))}\n      </ol>\n    </section>\n  );\n}",
          lang="typescript", hint="src/web/src/components/CrewRatingBlock.tsx",
          png="crew-rating", gif="crew-rating", cap="Рейтинг: 1 место — бригада №2, 87 баллов",
          note=["Первое место выделяйте не только цветом, но и текстом: иначе при "
                "печати страницы в ч/б и при программном чтении списка различие "
                "не сохраняется."]),
        S("Собираем страницу из блоков", 25,
          "Пять независимых секций подряд. Каждая со своим состоянием: загрузка, "
          "пустой результат, ошибка.",
          code="export default function AnalyticsPage() {\n  const [filters, setFilters] = useState(readFiltersFromUrl());\n  useEffect(() => { writeFiltersToUrl(filters); }, [filters]);\n  return (\n    <>\n      <h2>Аналитика</h2>\n      <FilterPanel value={filters} onChange={setFilters} workshops={workshops} />\n      <OrdersSummaryBlock data={summary.data} />\n      <DowntimeBlock data={downtime.data} />\n      <MaterialsBlock data={materials.data} />\n      <ScheduleExecutionBlock data={schedule.data} />\n      <CrewRatingBlock data={crews.data} />\n    </>\n  );\n}",
          lang="typescript", hint="src/web/src/pages/AnalyticsPage.tsx",
          png="analytics-page", gif="analytics-page", cap="Страница аналитики целиком: пять блоков за один экран",
          note=["Не связывайте блоки между собой. Каждый получает свои данные и падает "
                "независимо: ошибка в одном блоке не должна прятать остальные четыре."]),
    ],
    [("Блок пустой без объяснения", "нет текста «за выбранный период данных нет»"),
     ("Прогресс показывает 200 %", "в знаменателе должны быть и просроченные, и выполненные"),
     ("Рейтинг всегда одинаковый", "сортируйте по `score`, а не по порядку ответа сервера")],
    "cd src/web && npm run build",
    "feat(web): пять блоков аналитики — простои, материалы, график ТО, рейтинг бригад",
))

PAGES.append(P(
    42, "Экспорт-PNG-CSV-PDF-и-печать-страницы", 18,
    "Экспорт в трёх форматах: PNG для отчёта, CSV для Excel и PDF для печати. Плюс "
    "печать самой страницы браузером — отдельная кнопка, потому что экспорт в PDF "
    "не заменяет печатную версию.",
    "Каждый блок аналитики экспортируется отдельно, вся страница — одним действием.",
    [("Б / Web", "Экспорт PNG, CSV, PDF и печать страницы")],
    ["src/web/src/hooks/useExport.ts", "src/web/src/components/ExportMenu.tsx"],
    [
        S("PNG отдельного блока", 30,
          "Снимаем DOM-элемент блока в canvas через `html2canvas`. Имя файла собираем из "
          "названия блока и выбранного периода.",
          code="export async function exportBlockToPng(node: HTMLElement, filename: string) {\n  const canvas = await html2canvas(node, {\n    backgroundColor: '#ffffff',\n    scale: 2,                       // retina-чёткость в PDF и при печати\n    logging: false,\n    useCORS: true,\n  });\n  const link = document.createElement('a');\n  link.download = `${filename}.png`;\n  link.href = canvas.toDataURL('image/png');\n  link.click();\n}",
          lang="typescript", hint="src/web/src/hooks/useExport.ts",
          png="export-png", gif="export-png", cap="Блок «Сводка по заявкам» сохранён как PNG",
          note=["`scale: 2` увеличивает файл вдвое, но делает текст читаемым. При "
                "`scale: 1` подписи в PNG не видно, и экспорт выглядит браком."]),
        S("CSV с корректной кодировкой", 25,
          "CSV открывают в Excel, и русский текст должен остаться русским. Добавляем BOM "
          "и удваиваем кавычки внутри значений.",
          code="function toCsv(rows: Record<string, unknown>[], columns: string[]): Blob {\n  const escape = (v: unknown) => `\"${String(v ?? '').replace(/\"/g, '\"\"')}\"`;\n  const head = columns.join(';');\n  const body = rows.map((r) => columns.map((c) => escape(r[c])).join(';')).join('\\r\\n');\n  // BOM обязателен: без него Excel открывает файл в cp1251 и видит кракозябры\n  return new Blob(['\\uFEFF' + head + '\\r\\n' + body], { type: 'text/csv;charset=utf-8' });\n}",
          lang="typescript", hint="src/web/src/hooks/useExport.ts",
          png="export-csv", gif="export-csv", cap="CSV открывается в Excel с русскими заголовками",
          note=["Разделитель `;` вместо `,` — иначе Excel (русская локаль) разобьёт файл "
                "на extra-столбцы. Плюс BOM `\\uFEFF` в начале."]),
        S("PDF из нескольких блоков", 35,
          "Собираем PDF через `jsPDF`: один блок — страница в альбомной ориентации, "
          "заголовок с названием отчёта и периодом.",
          code="export async function exportBlocksToPdf(blocks: { id: string; title: string; node: HTMLElement }[], period: string) {\n  const doc = new jsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' });\n  blocks.forEach(async (block, index) => {\n    const canvas = await html2canvas(block.node, { scale: 2, logging: false });\n    const image = canvas.toDataURL('image/png');\n    if (index > 0) doc.addPage();\n    doc.setFontSize(14);\n    doc.text(`${block.title} — ${period}`, 40, 36);\n    doc.addImage(image, 'PNG', 40, 50, 515, 300);\n  });\n  doc.save(`toirprof-analytics-${period}.pdf`);\n}",
          lang="typescript", hint="src/web/src/hooks/useExport.ts",
          png="export-pdf", gif="export-pdf", cap="PDF на 5 страниц: по одному блоку на страницу",
          note=["`forEach` с `async`-колбэком не ждёт завершения — страницы перемешаются. "
                "Используйте `for...of` с `await`, иначе в PDF окажется только последний "
                "блок, а остальные страницы пустые."]),
        S("Печать страницы", 25,
          "Перед печатью скрываем навигацию, кнопки экспорта и фильтры — на бумаге они "
          "не нужны и только занимают место.",
          code="window.addEventListener('beforeprint', () => {\n  document.body.classList.add('printing');\n});\nwindow.addEventListener('afterprint', () => {\n  document.body.classList.remove('printing');\n});\n\n@media print {\n  .sidebar, .topbar, .filter-panel, .export-menu, .connection-badge { display: none !important; }\n  .analytics-block { break-inside: avoid; page-break-inside: avoid; }\n  body { background: #fff; }\n}",
          lang="css", hint="src/web/src/styles/print.css",
          png="print-preview", gif="print-preview", cap="Предпросмотр печати: чистая версия без служебных элементов",
          note=["`break-inside: avoid` на блоках обязателен: иначе круговая диаграмма "
                "разрывается пополам между страницами."]),
        S("Меню экспорта", 20,
          "Кнопка «Экспорт» с выпадающим списком: «Блок в PNG», «Блок в CSV», «Блок в PDF», "
          "«Вся страница в PDF», «Печать».",
          code="const ENTRIES: ExportEntry[] = [\n  { id: 'block-png', label: 'Блок в PNG' },\n  { id: 'block-csv', label: 'Блок в CSV' },\n  { id: 'block-pdf', label: 'Блок в PDF' },\n  { id: 'page-pdf', label: 'Вся страница в PDF' },\n  { id: 'print', label: 'Печать страницы' },\n];",
          lang="typescript", hint="src/web/src/components/ExportMenu.tsx",
          png="export-menu", gif="export-menu", cap="Меню экспорта с пятью действиями",
          note=["Действия различайте по `id`, а не по подписи: подпись переводится, "
                "а `id` используется в обработчике и попадёт в код."]),
    ],
    [("PNG сохраняется пустым", "блок скрыт `display: none` или не отрисован к моменту снятия"),
     ("В CSV кракозябры", "потерян BOM `\\uFEFF`"),
     ("В PDF одна страница вместо пяти", "`forEach` с `async` вместо `for...of`"),
     ("Печать ломает вёрстку", "не задан `@media print`")],
    "cd src/web && npm run build",
    "feat(web): экспорт блоков в PNG, CSV, PDF и печать страницы",
))
# === BLOCK-H2: спринт 19, страницы 43–45 (Web: realtime, реестры, справочники) ===

PAGES.append(P(
    43, "SSE-и-fallback-polling", 19,
    "Живое обновление дашборда: сначала пробуем Server-Sent Events, при неудаче "
    "переключаемся на опрос по таймеру. Плюс автопереподключение с экспоненциальной "
    "задержкой и честный индикатор состояния соединения.",
    "Дашборд обновляется сам: через SSE, а если канал не поднялся — по polling, и всегда видно, что именно сейчас работает.",
    [("Б / Web", "Real-time обновления: SSE, polling, переподключение, индикатор")],
    ["src/web/src/hooks/useSse.ts", "src/web/src/hooks/usePolling.ts",
     "src/web/src/components/ConnectionBadge.tsx"],
    [
        S("Канал событий на сервере", 25,
          "SSE — односторонний канал от сервера к браузеру: он проще WebSocket и не "
          "требует отдельного порта. Сервер шлёт событие при изменении счётчика заявок.",
          code="[HttpGet(\"events\")]\npublic async Task StreamEvents([FromServices] IDashboardNotifier notifier, CancellationToken ct)\n{\n    Response.Headers[\"Cache-Control\"] = \"no-cache\";\n    Response.Headers[\"X-Accel-Buffering\"] = \"no\";   // иначе nginx буферизует SSE\n    await foreach (var payload in notifier.SubscribeAsync(ct))\n    {\n        yield return $\"event: dashboard\\ndata: {payload}\\n\\n\";\n    }\n}",
          lang="csharp", hint="src/api/Controllers/DashboardController.cs",
          png="sse-endpoint", gif="sse-stream", cap="SSE-поток отдаёт событие при каждом изменении счётчика заявок",
          note=["Заголовок `X-Accel-Buffering: no` обязателен, если впереди стоит nginx. "
                "Без него прокси буферизует поток, и клиент не получит события до "
                "закрытия соединения — выглядит как «SSE не работает»."]),
        S("Подписка на события", 30,
          "На фронте подписка переподключается сама с экспоненциальной задержкой: 1 с, "
          "2 с, 4 с… до 30 с. Через SSE-соединение дубли не приходят.",
          code="export function useSse<T>(path: string, onEvent: (data: T) => void, onState: (s: ConnState) => void) {\n  useEffect(() => {\n    let source: EventSource | null = null;\n    let retry = 0;\n    let timer: number | undefined;\n\n    const connect = () => {\n      source = new EventSource(path);\n      source.onopen = () => { retry = 0; onState('live'); };\n      source.addEventListener('dashboard', (e) => onEvent(JSON.parse((e as MessageEvent).data)));\n      source.onerror = () => {\n        source?.close();\n        onState(retry === 0 ? 'polling' : 'reconnecting');\n        const delay = Math.min(1000 * 2 ** retry, 30_000);\n        retry += 1;\n        timer = window.setTimeout(connect, delay);\n      };\n    };\n\n    connect();\n    return () => { source?.close(); window.clearTimeout(timer); };\n  }, [path]);\n}",
          lang="typescript", hint="src/web/src/hooks/useSse.ts",
          png="sse-hook", gif="sse-reconnect", cap="Обрыв канала: задержка переподключения растёт 1 с → 2 с → 4 с → 30 с",
          note=["`EventSource` сам переподключается по умолчанию, но с фиксированной "
                "задержкой. Свой таймер нужен, чтобы ограничить поток запросов при "
                "недоступном сервере — иначе браузер долбит API каждые 3 секунды."]),
        S("Fallback на polling", 25,
          "Если SSE недоступен, тот же `useSse` не переподключается, а передаёт "
          "управление опросу: один запрос раз в 60 секунд.",
          code="export function usePolling<T>(path: string, intervalMs = 60_000) {\n  const [data, setData] = useState<T | null>(null);\n  useEffect(() => {\n    let alive = true;\n    const load = async () => {\n      try { const result = await api.get<T>(path); if (alive) setData(result); }\n      catch { /* тихо ждём следующего тика */ }\n    };\n    load();\n    const timer = window.setInterval(load, intervalMs);\n    return () => { alive = false; window.clearInterval(timer); };\n  }, [path]);\n  return data;\n}",
          lang="typescript", hint="src/web/src/hooks/usePolling.ts",
          png="polling-hook", gif="polling-ticks", cap="Polling: запросы раз в 60 секунд, данные обновляются без перезагрузки",
          note=["Ошибку отдельного тика глушите, а не показывайте: всплывающая ошибка "
                "каждую минуту превращается в раздражающую плашку. Показывайте её "
                "только после нескольких неудач подряд."]),
        S("Индикатор состояния соединения", 25,
          "Три состояния: «В реальном времени» (зелёный), «Обновление раз в минуту» "
          "(жёлтый), «Переподключение…» (серый с анимацией). Пользователь должен видеть, "
          "что данные не зависли.",
          code="export function ConnectionBadge({ state }: { state: ConnState }) {\n  const meta = {\n    live: { text: 'В реальном времени', tone: 'success' },\n    polling: { text: 'Обновление раз в минуту', tone: 'warning' },\n    reconnecting: { text: 'Переподключение…', tone: 'neutral' },\n    offline: { text: 'Нет связи с сервером', tone: 'danger' },\n  }[state];\n  return (\n    <span className={`connection-badge tone-${meta.tone}`} role=\"status\" aria-live=\"polite\">\n      <span className=\"dot\" /> {meta.text}\n    </span>\n  );\n}",
          lang="typescript", hint="src/web/src/components/ConnectionBadge.tsx",
          png="connection-badge", gif="connection-states", cap="Четыре состояния индикатора: live, polling, reconnecting, offline",
          note=["`aria-live=\"polite\"` обязателен: без него скринридер не объявит об "
                "изменении состояния, и доступность теряется."]),
        S("Подключаем индикатор к дашборду", 25,
          "Дашборд выбирает источник данных один раз и переключается прозрачно: "
          "пользователь не перезагружает страницу.",
          code="export function useDashboard() {\n  const [state, setState] = useState<ConnState>('reconnecting');\n  const sse = useSse<DashboardSummary>('/api/dashboard/events',\n    (data) => setSummary(data), (s) => setState(s === 'live' ? 'live' : s));\n  const polled = usePolling<DashboardSummary>('/api/dashboard/summary');\n  const summary = sse ?? polled;\n  return { summary, connection: state };\n}",
          lang="typescript", hint="src/web/src/pages/DashboardPage.tsx",
          png="dashboard-source", gif="dashboard-source", cap="Дашборд переключается между SSE и polling без перезагрузки",
          note=["Приоритет отдавайте живому каналу, а не тому, что ответил раньше. "
                "Иначе после восстановления SSE polling продолжит затирать свежие данные."]),
    ],
    [("SSE подключается и сразу отваливается", "не отдаётся `text/event-stream` либо буферизует nginx"),
     ("Браузер долбит API", "свой таймер переподключения не ограничен сверху"),
     ("Индикатор всегда зелёный", "состояние не пробрасывается из хука в компонент"),
     ("Данные обновляются дважды", "SSE и polling активны одновременно")],
    "cd src/web && npm run build",
    "feat(web): SSE с fallback на polling, переподключением и индикатором соединения",
))

PAGES.append(P(
    44, "Реестры-оборудования-заявок-и-графика", 19,
    "Три рабочих реестра, которыми пользуются каждый день: оборудование цеха, заявки "
    "и график планового ТО. Общая таблица, фильтры, пагинация — но разная логика строк "
    "и разные действия.",
    "На web-клиенте есть реестры оборудования, заявок и графика ТО с фильтрами, поиском и пагинацией.",
    [("Б / Web", "Реестры с фильтрами, поиском и пагинацией")],
    ["src/web/src/pages/EquipmentPage.tsx", "src/web/src/pages/WorkOrdersPage.tsx",
     "src/web/src/pages/SchedulePage.tsx", "src/web/src/components/DataTable.tsx"],
    [
        S("Универсальная таблица", 30,
          "Одна таблица на все три реестра: колонки, строки, сортировка, пагинация, "
          "состояние загрузки и пустоты. Отличаются только описания колонок.",
          code="export interface Column<T> {\n  key: keyof T & string;\n  title: string;\n  render?: (row: T) => ReactNode;\n  width?: number;\n  align?: 'left' | 'center' | 'right';\n}\n\nexport function DataTable<T extends { id: string }>({ columns, rows, total, page, size, onPage }: Props<T>) {\n  return (\n    <div className=\"data-table\">\n      <table>\n        <thead><tr>{columns.map((c) => <th key={c.key} style={{ width: c.width, textAlign: c.align }}>{c.title}</th>)}</tr></thead>\n        <tbody>{rows.map((row) => <tr key={row.id}>{columns.map((c) =>\n          <td key={c.key} style={{ textAlign: c.align }}>{c.render ? c.render(row) : String(row[c.key])}</td>)}</tr>)}</tbody>\n      </table>\n      <Pagination total={total} page={page} size={size} onChange={onPage} />\n    </div>\n  );\n}",
          lang="typescript", hint="src/web/src/components/DataTable.tsx",
          png="data-table", gif="data-table-page", cap="Универсальная таблица: 12 строк на странице, пагинация снизу",
          note=["Дженерик с ограничением `T extends { id: string }` — минимальный "
                "контракт, который гарантирует ключи React. Без него таблица будет "
                "дублировать строки при перерисовке."]),
        S("Реестр оборудования", 30,
          "Колонки: инвентарный номер, наименование, цех, вид, статус, критичность, дата "
          "ввода. Фильтры: цех, статус, критичность. Действия — просмотр и правка.",
          code="const EQUIPMENT_COLUMNS: Column<EquipmentDto>[] = [\n  { key: 'inventoryNumber', title: 'Инв. №', width: 130 },\n  { key: 'name', title: 'Наименование' },\n  { key: 'workshopName', title: 'Цех', width: 160 },\n  { key: 'status', title: 'Статус', width: 200, render: (r) => <StatusBadge status={r.status} /> },\n  { key: 'criticality', title: 'Критичность', width: 140, align: 'center' },\n  { key: 'commissionDate', title: 'Введено', width: 130, align: 'right' },\n];\n\nexport default function EquipmentPage() {\n  const [page, setPage] = useState(1);\n  const [query, setQuery] = useState('');\n  const { rows, total } = usePaged<EquipmentDto>('/api/equipment', { page, size: 12, search: query });\n  return <DataTable columns={EQUIPMENT_COLUMNS} rows={rows} total={total} page={page} size={12} onPage={setPage} />;\n}",
          lang="typescript", hint="src/web/src/pages/EquipmentPage.tsx",
          png="equipment-registry", gif="equipment-filter", cap="Реестр оборудования: 47 единиц, фильтр по статусу «В ремонте»",
          note=["Статус «Выведено из эксплуатации» рендерите серым и не давайте менять "
                "его вручную: сервер всё равно отклонит правку триггером, а клиент "
                "должен предупреждать заранее."]),
        S("Реестр заявок", 30,
          "Колонки: номер, оборудование, приоритет, статус, бригада, простой. Фильтры: "
          "статус, приоритет, период. Номер заявки — ссылка на карточку.",
          code="const WORK_ORDER_COLUMNS: Column<WorkOrderDto>[] = [\n  { key: 'number', title: 'Номер', width: 130,\n    render: (r) => <Link to={`/work-orders/${r.id}`}>{r.number}</Link> },\n  { key: 'equipmentName', title: 'Оборудование' },\n  { key: 'priority', title: 'Приоритет', width: 130,\n    render: (r) => <StatusBadge status={r.priority} /> },\n  { key: 'status', title: 'Статус', width: 140, render: (r) => <StatusBadge status={r.status} /> },\n  { key: 'crewName', title: 'Бригада', width: 160, render: (r) => r.crewName ?? '—' },\n  { key: 'downtimeHours', title: 'Простой', width: 120, align: 'right',\n    render: (r) => r.downtimeHours != null ? `${r.downtimeHours.toFixed(1)} ч` : '—' },\n];",
          lang="typescript", hint="src/web/src/pages/WorkOrdersPage.tsx",
          png="orders-registry", gif="orders-registry", cap="Реестр заявок: 132 записи, сортировка по простою",
          note=["Для `null` пишите «—», а не `0`. Отличие «простоя не было» и «простоя 0 ч» "
                "видно эксперту и вливается в отчёт."]),
        S("График планового ТО", 30,
          "Календарная сетка по месяцам с цветовой полосой по видам обслуживания. Клик по "
          "дню открывает карточку записи графика.",
          code="export function SchedulePage() {\n  const [month, setMonth] = useState(startOfMonth(new Date()));\n  const { rows } = useApi<ScheduleItem[]>('/api/maintenance-schedule', {\n    from: startOfMonth(month).toISOString().slice(0, 10),\n    to: endOfMonth(month).toISOString().slice(0, 10),\n  });\n  const byDay = useMemo(() => groupBy(rows, (r) => r.plannedDate), [rows]);\n  return (\n    <div className=\"schedule-grid\">\n      {eachDayOfInterval({ start: startOfMonth(month), end: endOfMonth(month) }).map((day) => (\n        <div key={day.toISOString()} className=\"day\" data-empty={!byDay[format(day, 'yyyy-MM-dd')]}>\n          <span className=\"day-number\">{format(day, 'd')}</span>\n          {(byDay[format(day, 'yyyy-MM-dd')] ?? []).map((item) => (\n            <button key={item.id} className=\"plan-chip\">{item.maintenanceTypeName}</button>\n          ))}\n        </div>\n      ))}\n    </div>\n  );\n}",
          lang="typescript", hint="src/web/src/pages/SchedulePage.tsx",
          png="schedule-grid", gif="schedule-month", cap="График ТО за март: 18 записей, 5 видов обслуживания",
          note=["Пустые дни не удаляйте — оставьте ячейки с `data-empty`, иначе календарь "
                "«схлопнется» и месяц перестанет читаться."]),
    ],
    [("При смене страницы остаются старые строки", "забыли сбросить `page` в 1 при смене фильтра"),
     ("Ключи React дублируются", "в `DataTable` нет ограничения `T extends { id: string }`"),
     ("Простой показан нулём у незавершённых заявок", "не обработан `null` в рендере"),
     ("Календарь сжимается", "пустые дни не отрисованы")],
    "cd src/web && npm run build",
    "feat(web): реестры оборудования, заявок и графика ТО на общей таблице",
))

PAGES.append(P(
    45, "Справочники-пользователи-поиск-состояния-ошибок", 19,
    "Справочники (виды ТО, материалы, бригады, пользователи), единый поиск и честная "
    "обработка ошибок: 400, 403, 404, 409, 429, 500 должны выглядеть по-разному и "
    "говорить пользователю, что делать.",
    "Справочники закрыты по ролям, поиск единый, все шесть кодов ошибок обработаны явно.",
    [("Б / Web", "Справочники, пользователи, глобальный поиск, состояния ошибок")],
    ["src/web/src/pages/UsersPage.tsx", "src/web/src/components/DataTable.tsx",
     "src/web/src/api/http.ts", "src/web/src/auth/AuthContext.tsx"],
    [
        S("Единый поиск", 25,
          "Один инпут в верхней панели ищет сразу по трём сущностям: оборудование, "
          "заявки и материалы. Запрос уходит с задержкой 300 мс, чтобы не слать "
          "запрос на каждую букву.",
          code="export function useDebounced<T>(value: T, delay = 300): T {\n  const [debounced, setDebounced] = useState(value);\n  useEffect(() => {\n    const timer = window.setTimeout(() => setDebounced(value), delay);\n    return () => window.clearTimeout(timer);\n  }, [value, delay]);\n  return debounced;\n}\n\nconst q = useDebounced(query, 300);\nconst results = useApi<SearchResult>('/api/search', q ? { q } : undefined);",
          lang="typescript", hint="src/web/src/components/GlobalSearch.tsx",
          png="global-search", gif="global-search", cap="Поиск «ПР-2»: 4 единицы оборудования, 7 заявок, 1 материал",
          note=["Без задержки на каждый символ уходит отдельный запрос — при 10 "
                "одновременных пользователях это заметная нагрузка на API и на "
                "демонстрации видно «мигание» списка."]),
        S("Справочник видов обслуживания", 25,
          "Простой справочник: код, наименование, периодичность в днях, ориентировочная "
          "длительность, активность. Создание и правка — только для администратора.",
          code="const TYPE_COLUMNS: Column<MaintenanceTypeDto>[] = [\n  { key: 'code', title: 'Код', width: 120 },\n  { key: 'name', title: 'Наименование' },\n  { key: 'periodicityDays', title: 'Периодичность', width: 160, align: 'right',\n    render: (r) => `каждые ${r.periodicityDays} дн.` },\n  { key: 'estimatedDurationMinutes', title: 'Длительность', width: 160, align: 'right',\n    render: (r) => `${r.estimatedDurationMinutes} мин` },\n  { key: 'isActive', title: 'Активен', width: 110, align: 'center',\n    render: (r) => <StatusBadge status={r.isActive ? 'Да' : 'Нет'} /> },\n];",
          lang="typescript", hint="src/web/src/pages/MaintenanceTypesPage.tsx",
          png="types-registry", gif="types-registry", cap="Справочник видов обслуживания: 6 записей",
          note=["Справочник не удаляют, а делают неактивным. Удаление ломает ссылки в "
                "графике ТО за прошлые периоды, и демонстрация старых отчётов "
                "сразу перестаёт работать."]),
        S("Пользователи и роли", 30,
          "Страница доступна только администратору. Создание пользователя, смена роли, "
          "блокировка. Пароль показывается один раз при создании.",
          code="export function UsersPage() {\n  const { user } = useAuth();\n  if (user.role !== 'ADMIN') return <AccessDenied />;\n  return (\n    <>\n      <h2>Пользователи</h2>\n      <button onClick={() => setCreating(true)}>Добавить пользователя</button>\n      <DataTable columns={USER_COLUMNS} rows={users} total={total} page={page} size={12} onPage={setPage} />\n      <UserDialog open={creating} onClose={() => setCreating(false)} />\n    </>\n  );\n}",
          lang="typescript", hint="src/web/src/pages/UsersPage.tsx",
          png="users-page", gif="users-page", cap="Страница пользователей: 8 записей, роли ADMIN/MANAGER/MASTER",
          note=["Проверку роли делайте и на клиенте, и на сервере. Только клиентская "
                "проверка — это не защита: эксперт откроет `/users` мастером и получит "
                "долгую загрузку вместо 403."]),
        S("Разбор ответа API", 30,
          "Один хелпер превращает ответ сервера в типизированную ошибку с кодом из "
          "поля `error_code`. Дальше все компоненты работают с `ApiError`.",
          code="export class ApiError extends Error {\n  constructor(\n    readonly status: number,\n    readonly code: string,\n    message: string,\n  ) { super(message); }\n}\n\nexport async function request<T>(path: string, init?: RequestInit): Promise<T> {\n  const response = await fetch(`/api${path}`, {\n    ...init,\n    headers: { 'Content-Type': 'application/json', ...(token && { Authorization: `Bearer ${token}` }), ...init?.headers },\n  });\n  const body = await response.json();\n  if (!response.ok) throw new ApiError(response.status, body.error_code ?? 'UNKNOWN', body.message ?? 'Ошибка запроса');\n  return body.data as T;\n}",
          lang="typescript", hint="src/web/src/api/http.ts",
          png="api-error", cap="Класс ApiError: статус, код и сообщение сервера",
          note=["Читайте `body.message`, а не свой текст ошибки. Сервер уже отдаёт "
                "русские сообщения под конкретную ситуацию, и клиентские «что-то пошло "
                "не так» их теряют."]),
        S("Шесть состояний ошибки", 35,
          "400 — подсвечиваем поля формы. 403 — экран «Недостаточно прав» с ролью. "
          "404 — «Объект не найден» со ссылкой назад. 409 — модальное окно с текстом "
          "конфликта. 429 — «Слишком много запросов, подождите». 500 — «Ошибка сервера» "
          "и кнопка «Повторить».",
          code="export function ErrorState({ error, onRetry }: { error: ApiError; onRetry: () => void }) {\n  switch (error.status) {\n    case 400: return <p className=\"error-field\">Проверьте заполнение полей: {error.message}</p>;\n    case 403: return <AccessDenied role=\"вашей роли\" />;\n    case 404: return <NotFound message={error.message} backTo=\"/\" />;\n    case 409: return <ConflictDialog message={error.message} onClose={onRetry} />;\n    case 429: return <p className=\"error-rate\">Слишком много запросов. Повтор через 15 секунд.</p>;\n    default:  return <ServerError message={error.message} onRetry={onRetry} />;\n  }\n}",
          lang="typescript", hint="src/web/src/components/ErrorState.tsx",
          png="error-states", gif="error-403", cap="403 для мастера на странице «Пользователи»",
          note=["409 — самый частый случай в системе: бригада занята, остатка материала "
                "не хватает, статус оборудования заблокирован. Для него нужен отдельный "
                "диалог, а не строка в списке ошибок."]),
    ],
    [("Поиск шлёт запрос на каждую букву", "не подключён `useDebounced`"),
     ("Мастер видит страницу пользователей", "роль проверяется только на сервере или только на клиенте"),
     ("Все ошибки выглядят одинаково", "нет ветки по `error.status` в `ErrorState`"),
     ("409 молча проглатывается", "конфликт обрабатывается как обычная ошибка запроса")],
    "cd src/web && npm run build",
    "feat(web): справочники, пользователи, глобальный поиск и шесть состояний ошибки",
))
# === BLOCK-I: спринты 20–24, страницы 46–54 (тесты, документация, защита, итог) ===

PAGES.append(P(
    46, "Тестовый-проект-и-тест-простоя", 20,
    "Юнит-тесты для desktop-клиента: ровно пять, структура AAA, полная изоляция. "
    "Начинаем с теста расчёта простоя — он самый короткий и задаёт структуру остальных.",
    "Проект тестов собран, тест расчёта простоя написан и проходит; имя и структура задают образец для четырёх остальных.",
    [("В / Тестирование", "Юнит-тест расчёта простоя")],
    ["src/Tests/ToirProf.Tests.csproj", "src/Tests/DowntimeCalculatorTests.cs",
     "src/desktop/Services/Calculators.cs"],
    [
        S("Создаём тестовый проект", 30,
          "Отдельный проект xUnit со ссылкой на desktop. Тесты живут рядом с кодом "
          "клиента, но не в его сборке — иначе в релиз попадёт тестовый раннер.",
          code="dotnet new xunit -n ToirProf.Tests -o src/Tests\ndotnet add src/Tests reference src/desktop/ToirProf.Desktop.csproj\ndotnet add src/Tests package FluentAssertions",
          hint="Терминал",
          png="test-project", gif="test-project", cap="Тестовый проект создан и связан с desktop-клиентом",
          note=["Тестовый проект обязательно исключается из публикации: иначе вместе с "
                "приложением уедет `xunit.runner` и `FluentAssertions`, а размер "
                "дистрибутива вырастет втрое."]),
        S("Пишем сам калькулятор простоя", 30,
          "Логика, которую тестируем, живёт в desktop-клиенте и не зависит ни от API, "
          "ни от базы. Это и делает тест юнит-тестом, а не интеграционным.",
          code="namespace ToirProf.Desktop.Services;\n\npublic static class DowntimeCalculator\n{\n    /// <summary>Часы простоя между началом и окончанием работ.</summary>\n    public static double? Calculate(DateTimeOffset? start, DateTimeOffset? end)\n    {\n        if (start is null || end is null) return null;\n        var hours = (end.Value - start.Value).TotalHours;\n        return hours < 0 ? 0 : Math.Round(hours, 2);\n    }\n}",
          lang="csharp", hint="src/desktop/Services/Calculators.cs",
          png="calculator", cap="DowntimeCalculator: возвращает null при незавершённой заявке",
          note=["Возвращайте `double?`, а не `0`. Незавершённая заявка не имеет простоя — "
                "это разные вещи, и в отчётах они выглядят по-разному."]),
        S("Тест 1: корректные даты", 25,
          "Первый тест из задания: заявка длилась 8 часов 30 минут, ожидаем 8,5. "
          "Структура AAA — Arrange, Act, Assert — выдерживается явно.",
          code="using ToirProf.Desktop.Services;\n\npublic class DowntimeCalculatorTests\n{\n    [Fact]\n    public void Calculate_ReturnsHours_WhenStartAndEndAreValid()\n    {\n        // Arrange\n        var start = new DateTimeOffset(2026, 3, 14, 8, 0, 0, TimeSpan.Zero);\n        var end = new DateTimeOffset(2026, 3, 14, 16, 30, 0, TimeSpan.Zero);\n\n        // Act\n        var result = DowntimeCalculator.Calculate(start, end);\n\n        // Assert\n        result.Should().Be(8.5);\n    }\n}",
          lang="csharp", hint="src/Tests/DowntimeCalculatorTests.cs",
          png="test-valid-dates", gif="test-valid-dates", cap="Тест «корректные даты» — 8 ч 30 мин дают 8,5 ч",
          note=["Имя теста читается как утверждение: `Calculate_ReturnsHours_When...`. "
                "Имена вида `Test1` не помогают ни вам, ни эксперту в отчёте."]),
        S("Тест 2: окончание раньше начала", 25,
          "Отрицательный интервал — это ошибка данных, а не отрицательный простой. "
          "Ожидаем 0.",
          code="    [Fact]\n    public void Calculate_ReturnsZero_WhenEndIsBeforeStart()\n    {\n        // Arrange\n        var start = new DateTimeOffset(2026, 3, 14, 16, 30, 0, TimeSpan.Zero);\n        var end = new DateTimeOffset(2026, 3, 14, 8, 0, 0, TimeSpan.Zero);\n\n        // Act\n        var result = DowntimeCalculator.Calculate(start, end);\n\n        // Assert\n        result.Should().Be(0);\n    }",
          lang="csharp", hint="src/Tests/DowntimeCalculatorTests.cs",
          png="test-negative", gif="test-negative", cap="Окончание раньше начала даёт 0, а не отрицательные часы",
          note=["Сюда же относите третий случай из задания: `null` на любом конце. "
                "Ожидание — `result.Should().BeNull()`."]),
        S("Запускаем тесты", 20,
          "Тесты запускаются одной командой и должны зелёными уйти с первого раза: код "
          "написан под требование задания, а не под угадывание.",
          code="dotnet test src/Tests/ToirProf.Tests.csproj\n//   Passed! - Failed: 0, Passed: 3, Skipped: 0, Total: 3",
          hint="Терминал",
          png="test-run", gif="test-run", cap="Три теста расчёта простоя — все зелёные",
          note=["Держите тесты быстрыми: обращение к базе внутри юнит-теста делает его "
                "интеграционным и ломает принцип изоляции, который требует задание."]),
    ],
    [("Тесты не находятся", "проверьте, что у тестового проекта есть ссылка на desktop"),
     ("`Be(8.5)` падает с 8,5000001", "округляйте результат в методе, а не в тесте"),
     ("Тесты идут по 40 секунд", "внутри теста обращаются к базе или сети")],
    "dotnet test src/Tests/ToirProf.Tests.csproj",
    "test: тестовый проект xUnit и тесты расчёта простоя",
))

PAGES.append(P(
    47, "Тесты-валидации-заявки-и-стоимости-материалов", 20,
    "Оставшиеся четыре теста из задания: валидация заявки (проверка, отсутствие "
    "обязательного поля, аварийная без причины, некорректные плановые даты) и расчёт "
    "стоимости материалов на эталонных данных 7 300,00.",
    "Пять юнит-тестов из задания написаны, изолированы и проходят; на выходе покрыт расчёт простоя, валидация и стоимость.",
    [("В / Тестирование", "Тесты валидации заявки и расчёта стоимости")],
    ["src/Tests/WorkOrderValidatorTests.cs", "src/Tests/MaterialCostTests.cs",
     "src/desktop/Services/Calculators.cs"],
    [
        S("Валидатор заявки", 30,
          "Валидация на клиенте отвечает за подсказки, а не за безопасность: сервер "
          "проверяет всё повторно. Формат ответа — список строк с человеческими текстами.",
          code="public static class WorkOrderValidator\n{\n    public static IReadOnlyList<string> Validate(\n        WorkOrderDraft draft, DateTimeOffset now)\n    {\n        var errors = new List<string>();\n        if (draft.EquipmentId == Guid.Empty)\n            errors.Add(\"Выберите оборудование\");\n        if (string.IsNullOrWhiteSpace(draft.Description))\n            errors.Add(\"Укажите описание неисправности\");\n        if (draft.Priority == Priority.Аварийный && string.IsNullOrWhiteSpace(draft.FailureReason))\n            errors.Add(\"Для аварийной заявки укажите причину аварии\");\n        if (draft.PlannedStart > draft.PlannedEnd)\n            errors.Add(\"Плановая дата окончания раньше даты начала\");\n        if (draft.PlannedStart < now.Date)\n            errors.Add(\"Плановая дата начала уже прошла\");\n        return errors;\n    }\n}",
          lang="csharp", hint="src/desktop/Services/Calculators.cs",
          png="validator", cap="Валидатор возвращает список человекочитаемых ошибок",
          note=["Сообщения пишите как инструкцию: «Выберите оборудование», а не "
                "«поле equipment_id некорректно». Пользователь не знает ваших имён полей."]),
        S("Тест 3: все поля верны", 25,
          "Корректная заявка не должна давать ни одной ошибки. Это базовый тест: если он "
          "падает — сломана логика, а не данные.",
          code="[Fact]\npublic void Validate_ReturnsNoErrors_WhenAllFieldsAreCorrect()\n{\n    // Arrange\n    var now = new DateTimeOffset(2026, 3, 1, 9, 0, 0, TimeSpan.Zero);\n    var draft = new WorkOrderDraft\n    {\n        EquipmentId = Guid.Parse(\"44444444-4444-4444-4444-444444444444\"),\n        Description = \"Стучит приводной подшипник\",\n        Priority = Priority.Высокий,\n        FailureReason = null,\n        PlannedStart = now.AddDays(1),\n        PlannedEnd = now.AddDays(2),\n    };\n\n    // Act\n    var errors = WorkOrderValidator.Validate(draft, now);\n\n    // Assert\n    errors.Should().BeEmpty();\n}",
          lang="csharp", hint="src/Tests/WorkOrderValidatorTests.cs",
          png="test-valid-order", gif="test-valid-order", cap="Корректная заявка: список ошибок пуст",
          note=["`FailureReason` тут `null` — и это правильно: причина обязательна только "
                "для аварийных. Проверяйте это в тесте, иначе правило «причина только для "
                "аварии» будет нарушаться."]),
        S("Тест 4: нет обязательного поля", 25,
          "Пустое описание и невыбранное оборудование дают ровно две ошибки с конкретными "
          "текстами — так проверяется не только факт ошибки, но и её полезность.",
          code="[Fact]\npublic void Validate_ReturnsErrors_WhenRequiredFieldsAreMissing()\n{\n    var now = new DateTimeOffset(2026, 3, 1, 9, 0, 0, TimeSpan.Zero);\n    var draft = new WorkOrderDraft\n    {\n        EquipmentId = Guid.Empty,\n        Description = \"   \",\n        PlannedStart = now.AddDays(1),\n        PlannedEnd = now.AddDays(2),\n    };\n\n    var errors = WorkOrderValidator.Validate(draft, now);\n\n    errors.Should().BeEquivalentTo(new[] { \"Выберите оборудование\", \"Укажите описание неисправности\" });\n}",
          lang="csharp", hint="src/Tests/WorkOrderValidatorTests.cs",
          png="test-missing", gif="test-missing", cap="Пустая форма даёт две конкретные ошибки",
          note=["Пробелы (`\"   \"`) — не пустая строка. Проверяйте `IsNullOrWhiteSpace`, "
                "иначе форма с одним пробелом пройдёт валидацию."]),
        S("Тест 5: аварийная заявка без причины", 25,
          "Аварийный приоритет требует причину аварии. Это отдельный сценарий из задания "
          "и отдельная ошибка.",
          code="[Fact]\npublic void Validate_ReturnsError_WhenEmergencyOrderHasNoReason()\n{\n    var now = new DateTimeOffset(2026, 3, 1, 9, 0, 0, TimeSpan.Zero);\n    var draft = new WorkOrderDraft\n    {\n        EquipmentId = Guid.NewGuid(),\n        Description = \"Оборудование встало\",\n        Priority = Priority.Аварийный,\n        FailureReason = string.Empty,\n        PlannedStart = now.AddDays(1),\n        PlannedEnd = now.AddDays(2),\n    };\n\n    var errors = WorkOrderValidator.Validate(draft, now);\n\n    errors.Should().ContainSingle().Which.Should().Be(\"Для аварийной заявки укажите причину аварии\");\n}",
          lang="csharp", hint="src/Tests/WorkOrderValidatorTests.cs",
          png="test-emergency", gif="test-emergency", cap="Аварийная заявка без причины — одна понятная ошибка",
          note=["`ContainSingle().Which` проверяет и количество, и текст. Простой "
                "`Contain(...)` пропустил бы лишние ошибки."]),
        S("Расчёт стоимости и тест на эталон", 40,
          "Сумма списания считается на клиенте для показа в форме, и на этом же наборе "
          "проверяется округление до копеек.",
          code="public static decimal CalculateTotalCost(IEnumerable<MaterialLine> lines)\n{\n    ArgumentNullException.ThrowIfNull(lines);\n    return lines.Sum(line => (decimal)line.Quantity * line.UnitPrice);\n}\n\n[Fact]\npublic void CalculateTotalCost_ReturnsExpectedTotal_ForReferenceData()\n{\n    // Arrange: эталон из задания — 3400 + 2400 + 1500 = 7300.00\n    var lines = new List<MaterialLine>\n    {\n        new(\"Подшипник 6-205\", 4, 850m),\n        new(\"Ремень приводной\", 2, 1200m),\n        new(\"Масло И-20\", 10, 150m),\n    };\n\n    // Act\n    var total = MaterialCostCalculator.CalculateTotalCost(lines);\n\n    // Assert\n    total.Should().Be(7300.00m);\n}",
          lang="csharp", hint="src/Tests/MaterialCostTests.cs",
          png="test-cost", gif="test-cost", cap="Эталонные данные из задания дают 7 300,00",
          note=["Используйте `decimal`, а не `double`. На `double` сумма 7300 получается "
                "как 7299.999999999999, и проверка `Be(7300.00m)` падает — а на демонстрации "
                "сумма в отчёте отличается от счёта на копейку."]),
        S("Пустой список, ноль и отрицательные", 25,
          "Оставшиеся случаи из задания: пустой список даёт ноль, количество 0 не меняет "
          "сумму, отрицательные значения отбрасываются.",
          code="[Fact]\npublic void CalculateTotalCost_ReturnsZero_WhenListIsEmpty()\n    => MaterialCostCalculator.CalculateTotalCost(Array.Empty<MaterialLine>()).Should().Be(0m);\n\n[Fact]\npublic void CalculateTotalCost_IgnoresLine_WhenQuantityIsZero()\n{\n    var lines = new[] { new MaterialLine(\"Подшипник 6-205\", 0, 850m) };\n    MaterialCostCalculator.CalculateTotalCost(lines).Should().Be(0m);\n}\n\n[Fact]\npublic void CalculateTotalCost_IgnoresLine_WhenQuantityIsNegative()\n{\n    var lines = new[] { new MaterialLine(\"Подшипник 6-205\", -2, 850m) };\n    MaterialCostCalculator.CalculateTotalCost(lines).Should().Be(0m);\n}",
          lang="csharp", hint="src/Tests/MaterialCostTests.cs",
          png="test-cost-edges", gif="test-cost-edges", cap="Пустой список, ноль и отрицательное количество",
          note=["Отрицательные количества не должны попадать в расчёт — на сервере их "
                "отсекает валидатор, но клиент тоже обязан защитить пользователя от "
                "«списания в минус»."]),
    ],
    [("`Be(7300.00m)` падает на копейку", "считаете в `double`, а не в `decimal`"),
     ("Тест не изолирован", "используется общий статический список материалов"),
     ("Пропущен тест на отрицательные значения", "в задании их четыре случая, а не три")],
    "dotnet test src/Tests/ToirProf.Tests.csproj",
    "test: тесты валидации заявки и расчёта стоимости материалов",
))
# === BLOCK-J: страницы 48–54 (документация, руководство, защита, итог) ===

PAGES.append(P(
    48, "Swagger-документация-API", 21,
    "Документирование API через Swagger UI: XML-комментарии, описания операций, "
    "коды ответов, примеры запросов и ответов. Здесь же — коллекция Postman, "
    "собранная из той же спецификации.",
    "Swagger показывает все методы с описаниями, кодами ответов и примерами; спецификация OpenAPI выгружается в `api/openapi.yaml`.",
    [("Г / Документирование", "Документирование API (Swagger)")],
    ["src/api/Program.cs", "src/api/Controllers/EquipmentController.cs",
     "api/openapi.yaml", "postman/ToirProf.postman_collection.json"],
    [
        S("Включаем Swagger в Development", 25,
          "Swagger доступен только в режиме разработки — на площадке его можно "
          "потрогать руками, а в «боевой» сборке его быть не должно.",
          code="if (app.Environment.IsDevelopment())\n{\n    app.UseSwagger();\n    app.UseSwaggerUI(options =>\n    {\n        options.SwaggerEndpoint(\"/swagger/v1/swagger.json\", \"ТОиР-Проф API v1\");\n        options.DocumentTitle = \"ТОиР-Проф — API\";\n        options.DisplayRequestDuration();\n    });\n}",
          lang="csharp", hint="src/api/Program.cs",
          png="swagger-ui", gif="swagger-ui", cap="Swagger UI доступен по /swagger в режиме разработки",
          note=["Группируйте методы по тегам (`ApiExplorerSettings.GroupName`), иначе "
                "десятки операций слипаются в один список без структуры."]),
        S("XML-комментарии и описания операций", 35,
          "Описание в Swagger — это документация из исходного кода: `<summary>` на "
          "методе, `<param>` на параметре, `<response>` на каждом коде ответа.",
          code="/// <summary>Возвращает страницу оборудования с фильтрами.</summary>\n/// <param name=\"search\">Поиск по наименованию и инвентарному номеру.</param>\n/// <param name=\"page\">Номер страницы, начиная с 1.</param>\n/// <param name=\"size\">Размер страницы: 1–100, по умолчанию 20.</param>\n/// <param name=\"workshopId\">Фильтр по цеху.</param>\n/// <param name=\"status\">Фильтр по статусу оборудования.</param>\n[HttpGet]\n[ProducesResponseType(typeof(ApiResponse<PagedResult<EquipmentDto>>), StatusCodes.Status200OK)]\n[ProducesResponseType(StatusCodes.Status400BadRequest)]\n[ProducesResponseType(StatusCodes.Status401Unauthorized)]\n[ProducesResponseType(StatusCodes.Status403Forbidden)]\npublic async Task<ActionResult<ApiResponse<PagedResult<EquipmentDto>>>> GetAll(\n    [FromQuery] string? search, [FromQuery] int page = 1, [FromQuery] int size = 20,\n    [FromQuery] Guid? workshopId, [FromQuery] EquipmentStatus? status, CancellationToken ct)\n{\n    var result = await _service.GetPagedAsync(search, page, size, workshopId, status, ct);\n    return Ok(ApiResponse<PagedResult<EquipmentDto>>.Ok(result));\n}",
          lang="csharp", hint="src/api/Controllers/EquipmentController.cs",
          png="swagger-summary", cap="Описание операции и пять кодов ответа в Swagger",
          note=["`ProducesResponseType` указывайте явно. Иначе в Swagger будет один "
                "«200 OK» на все методы, и по документации невозможно понять, "
                "какой код ожидать при ошибке."]),
        S("Примеры запросов и ответов", 30,
          "Swagger даёт «попробовать» прямо из браузера: с тестовым токеном и готовым "
          "набором данных операция возвращает осмысленный ответ.",
          code="/// <example>\n/// <code>\n/// {\n///   \"success\": true,\n///   \"data\": {\n///     \"id\": \"44444444-4444-4444-4444-444444444444\",\n///     \"inventoryNumber\": \"PR-2-0001\",\n///     \"name\": \"Пресс гидравлический ПР-2\",\n///     \"status\": \"В ремонте\",\n///     \"criticality\": 3\n///   },\n///   \"message\": \"OK\",\n///   \"error_code\": null\n/// }\n/// </code>\n/// </example>",
          lang="csharp", hint="src/api/DTOs/EquipmentDtos.cs",
          png="swagger-example", gif="swagger-example", cap="Пример ответа в документации совпадает с реальным",
          note=["Пример берите из реального ответа Postman, а не выдумывайте. "
                "Расхождение между документацией и фактом эксперт найдёт за секунду."]),
        S("Выгрузка спецификации", 20,
          "Файл спецификации нужен и для Postman, и как отдельный артефакт: из него "
          "клиенты собирают типы.",
          code="# Выгружаем спецификацию в файл\ndotnet run --project src/api -- swagger export api/openapi.yaml",
          hint="Терминал",
          png="openapi-yaml", gif="openapi-export", cap="api/openapi.yaml содержит все операции и схемы",
          note=["Коммитьте `openapi.yaml` в репозиторий. По нему потом собирается "
                "коллекция Postman и генерируются типы для клиентов — это экономит "
                "час работы на согласовании полей."]),
        S("Коллекция Postman", 30,
          "Коллекция повторяет структуру Swagger: папки по сущностям, переменные "
          "`baseUrl` и `token`, готовые примеры.",
          code="{\n  \"info\": { \"name\": \"ТОиР-Проф API\", \"schema\": \"https://schema.getpostman.com/json/collection/v2.1.0/collection.json\" },\n  \"variable\": [\n    { \"key\": \"baseUrl\", \"value\": \"http://localhost:5080/api\" },\n    { \"key\": \"token\", \"value\": \"\" }\n  ]\n}",
          lang="json", hint="postman/ToirProf.postman_collection.json",
          png="postman-collection", gif="postman-run", cap="Коллекция Postman: 24 запроса в 7 папках",
          note=["Авторизацию задайте на уровне коллекции («Bearer Token»), а не в "
                "каждом запросе: иначе токен придётся обновлять в 24 местах."]),
    ],
    [("Swagger показывает 500 на всех методах", "не указаны `ProducesResponseType`"),
     ("В Swagger нет описаний", "в проект не подключён `GenerateDocumentationFile`"),
     ("Кнопка «Try it out» возвращает 401", "не задан токен авторизации в UI"),
     ("Схемы показаны как object", "DTO описаны как `record`, а не как `object`")],
    "curl -s http://localhost:5080/swagger/v1/swagger.json | head -c 200",
    "docs(api): Swagger-документация, OpenAPI-спецификация и коллекция Postman",
))

PAGES.append(P(
    49, "Инструкция-по-развёртыванию", 21,
    "Инструкция на 8–10 страниц: от чистой машины до работающей системы. Проверяется "
    "не чтением, а попыткой развернуть по ней на другой машине — поэтому шаги должны "
    "быть копируемыми, с точными командами и ожидаемым выводом.",
    "Инструкция позволяет развернуть систему на чистой машине РедОС без уточняющих вопросов.",
    [("Г / Документирование", "Инструкция по развёртыванию")],
    ["docs/deployment.md", "db/schema.sql", "db/seed.sql", "README.md"],
    [
        S("Требования и системные пакеты", 25,
          "Список версий и одна команда установки. Отдельно оговаривается, что Docker "
          "на площадке может отсутствовать и всё ставится нативно.",
          code="```bash\n# РедОС 8.0\nsudo dnf install -y dotnet-sdk-10.0 postgresql-server postgresql-contrib nodejs npm java-17-openjdk graphviz\n```",
          hint="Терминал",
          png="requirements", cap="Системные требования и команда установки пакетов",
          note=["Пишите «РедОС 8.0» и «Windows 11» отдельными подразделами. "
                "Инструкция с пометкой «аналогично для Linux» проверяется только на "
                "той ОС, на которой её писали."]),
        S("Подготовка базы данных", 25,
          "Создание роли и базы, запуск скриптов. Указываем, что делать при ошибке "
          "«роль уже существует» — на повторном запуске это норма.",
          code="```bash\nsudo systemctl enable --now postgresql\nsudo -u postgres psql -c \"CREATE ROLE toirprof LOGIN PASSWORD 'toirprof';\"\nsudo -u postgres createdb -O toirprof toirprof\npsql -h 127.0.0.1 -U toirprof -d toirprof -f db/schema.sql\npsql -h 127.0.0.1 -U toirprof -d toirprof -f db/functions.sql\npsql -h 127.0.0.1 -U toirprof -d toirprof -f db/triggers.sql\npsql -h 127.0.0.1 -U toirprof -d toirprof -f db/seed.sql\n```",
          hint="Терминал",
          png="db-deploy", gif="db-deploy", cap="База создана, 13 таблиц, 3 типа, 6 ограничений",
          note=["Порядок файлов важен: функции и триггеры создаются после таблиц, иначе "
                "скрипт падает на несуществующих отношениях."]),
        S("Запуск API", 25,
          "Сборка, запуск и проверка health-эндпоинта. Порт задаётся через переменную "
          "окружения, а не жёстко в коде.",
          code="```bash\ndotnet build src/api/ToirProf.Api.csproj -c Release\nASPNETCORE_URLS=http://localhost:5080 dotnet run --project src/api -c Release --no-build\n# проверка в другом терминале\ncurl -s http://localhost:5080/api/health\n```",
          hint="Терминал",
          png="api-start", gif="api-start", cap="API поднялся, /api/health отвечает status: ok",
          note=["Обязательно `--no-build` при фоновом запуске: иначе сборка блокирует "
                "терминал и выглядит как зависание."]),
        S("Запуск web-клиента", 25,
          "Установка зависимостей, dev-сервер и проверка прокси на API.",
          code="```bash\ncd src/web\nnpm install\nnpm run dev -- --host 0.0.0.0 --port 5173\n# проверка в браузере: http://localhost:5173\n```",
          hint="Терминал",
          png="web-start", gif="web-start", cap="Web-клиент на порту 5173, прокси работает",
          note=["`--host 0.0.0.0` нужен, чтобы клиент был доступен не только с "
                "localhost: на площадке демонстрация идёт с другого устройства."]),
        S("Запуск desktop-клиента", 25,
          "Desktop запускается отдельно и указывает адрес API через переменную или "
          "конфиг — жёстко зашитый адрес ломает демонстрацию на другой машине.",
          code="```bash\ndotnet run --project src/desktop -- --api http://localhost:5080\n```",
          hint="Терминал",
          png="desktop-start", gif="desktop-start", cap="Desktop-клиент: окно входа, адрес API из аргумента",
          note=["Принимайте адрес API аргументом командной строки. Подсказка с "
                "аргументом при неверном адресе экономит эксперту несколько минут."]),
        S("Проверка, типовые ошибки, остановка", 20,
          "Чек-лист из пяти пунктов и таблица «симптом — причина — решение». Это то, "
          "что отличает рабочую инструкцию от пересказа README.",
          code="| Симптом | Причина | Решение |\n|---|---|---|\n| `dotnet: command not found` | не прописан PATH | откройте новый терминал |\n| `password authentication failed` | нет роли в БД | повторите `CREATE ROLE` |\n| веб открывается, API нет | API не запущен | проверьте `/api/health` |\n| `relation \"equipment\" does not exist` | не применён `schema.sql` | примените скрипт заново |",
          hint="Терминал",
          png="deployment-checklist", cap="Чек-лист развёртывания и таблица типовых ошибок",
          note=["Останавливайте процессы явно: `Ctrl+C` в каждом терминале или "
                "`pkill -f ToirProf.Api`. На площадке зависший процесс держит порт, "
                "и следующий запуск падает с «адрес занят»."]),
    ],
    [("На второй машине не собирается", "не указана версия .NET SDK или Node.js"),
     ("Порт 5080 занят", "не остановили предыдущий процесс"),
     ("База создалась без таблиц", "забыли `schema.sql` или запустили не от того пользователя"),
     ("Клиент не видит API", "не задан адрес API или CORS не настроен")],
    "bash -n <(cat docs/deployment.md) 2>/dev/null; curl -s http://localhost:5080/api/health",
    "docs: инструкция по развёртыванию на РедОС и Windows",
))
# === BLOCK-K: страницы 50–54 (руководство, защита, итог) ===

PAGES.append(P(
    50, "Руководство-пользователя-Desktop", 22,
    "Руководство мастера: вход, оболочка, каждый экран по шагам, типовые ситуации и "
    "ответы на вопросы. Пишется от лица пользователя и разбирает один сценарий от "
    "начала до конца.",
    "Мастер по руководству самостоятельно проходит путь «заявка → выполнение → отчёт», не обращаясь к разработчику.",
    [("Г / Документирование", "Руководство пользователя (desktop)")],
    ["docs/user-guide-desktop.md", "docs/screenshots/desktop/*.png"],
    [
        S("Кому адресовано и как читать", 20,
          "Первая страница: кто такой мастер, что умеет система, как открыть "
          "руководство и что делать с иконками в тексте.",
          code="```markdown\n# Руководство пользователя\n## Система «ТОиР-Проф»\n\nРуководство для мастера участка технического обслуживания\nи ремонта оборудования.\n\n| Раздел | О чём |\n|---|---|\n| 1. Вход в систему | как войти и что делать при ошибке |\n| 2. Обзор интерфейса | меню, панель, хлебные крошки |\n| 3. Дашборд мастера | показатели за смену |\n| 4. Оборудование цеха | просмотр и правка |\n| 5. График ТО | план работ на месяц |\n| 6. Заявки | главный рабочий раздел |\n| 7. Материалы и бригады | ЗИП и состав бригад |\n| 8. Отчёты | сводка и выгрузка |\n```",
          lang="markdown", hint="docs/user-guide-desktop.md",
          png="guide-toc", cap="Оглавление руководства мастера: восемь разделов",
          note=["Оглавление с номерами разделов обязательно: на демонстрации "
                "эксперту нужен быстрый переход к нужному разделу, а он не будет "
                "листать 20 страниц."]),
        S("Вход и типовые ошибки", 25,
          "Пошаговый вход с картинкой экрана, таблица «сообщение — причина — "
          "действие» для четырёх частых ошибок.",
          code="| Сообщение | Что означает | Что делать |\n|---|---|---|\n| Неверный логин или пароль | нет пользователя с таким именем | проверьте раскладку и регистр |\n| Сессия завершена | 15 минут бездействия | войдите заново |\n| Нет доступа к разделу | роль мастера | обратитесь к администратору |\n| Нет связи с сервером | API не запущен | сообщите администратору |",
          hint="Терминал",
          png="guide-login", gif="guide-login", cap="Раздел «Вход в систему» с таблицей ошибок",
          note=["Автоблокировка через 15 минут обязательно упоминается в руководстве: "
                "мастер, которого выкинуло посреди работы, ищет общую кнопку выхода — "
                "и не находит её."]),
        S("Дашборд и реестры", 30,
          "Что показывает дашборд, как читать показатели, как искать и сортировать в "
          "реестрах. Скриншот под каждым описанием.",
          code="На дашборде мастера шесть показателей:\n\n1. **Заявки в работе** — сколько заявок закреплено за бригадой сейчас.\n2. **Завершено за смену** — сколько закрыто сегодня.\n3. **Просроченные заявки** — требуют внимания в первую очередь.\n4. **Средний простой** — среднее по завершённым заявкам за неделю.\n5. **Расход материалов** — сумма списанного за неделю.\n6. **Выполнение графика ТО** — доля плановых работ, выполненных в срок.\n\nКрасная карточка означает отклонение от нормы, а не ошибку системы.",
          hint="Терминал",
          png="guide-dashboard", gif="guide-dashboard", cap="Раздел «Дашборд мастера»: шесть показателей и их смысл",
          note=["Объясняйте цветовую схему. Иначе мастер читает красную карточку как "
                "«сломалось» и звонит в поддержку."]),
        S("Работа с заявкой от начала до конца", 35,
          "Главный сценарий руководства: мастер открывает заявку, видит детали, "
          "назначает исполнителя, отмечает ход работы и завершает со списанием "
          "материалов. Один скриншот на каждый шаг.",
          code="### Сценарий: выполнение заявки на ремонт\n\n**Шаг 1.** Откройте раздел «Заявки» и найдите заявку по номеру, например `Z-2026-0048`.\n\n**Шаг 2.** Откройте карточку. Проверьте описание неисправности и плановые даты.\n\n**Шаг 3.** Если бригада не назначена, выберите её в поле «Бригада» и сохраните.\n\n**Шаг 4.** Когда работы начались, нажмите «В работу» и укажите фактическое время начала.\n\n**Шаг 5.** По завершении нажмите «Завершить», укажите фактическое время окончания и причину.\n\n**Шаг 6.** Добавьте списанные материалы: количество, стоимость из справочника сохраняется автоматически.\n\n**Шаг 7.** Нажмите «Сохранить и завершить». Заявка получает статус «Завершена», а остатки материалов пересчитываются.\n\n> **Важно:** завершить заявку без фактического времени окончания нельзя — простой останется незаполненным и попадёт в отчёт как ноль.",
          hint="Терминал",
          png="guide-workorder", gif="guide-workorder", cap="Сценарий выполнения заявки: семь шагов со скриншотами",
          note=["Сценарий должен быть сквозным: от экрана до экрана, с номерами "
                "заявок и названиями кнопок ровно как в интерфейсе. Руководство "
                "пишется по работающему приложению, а не по памяти."]),
        S("Отчёты, материалы, офлайн-режим", 25,
          "Формирование сводки, выгрузка в PDF, просмотр остатков ЗИП и поведение "
          "клиента при отсутствии связи: очередь операций и автоотправка.",
          code="### Если пропал интернет\n\nИзменения не теряются. Клиент покажет индикатор «Нет связи с сервером»,\nа сделанные изменения попадут в очередь и отправятся автоматически,\nкак только связь восстановится.\n\nОчередь видна в разделе «Журнал операций». Не выключайте клиент, пока очередь не опустела:\nпри закрытии программы неотправленные изменения остаются на диске и уйдут\nпри следующем запуске.",
          hint="Терминал",
          png="guide-offline", gif="guide-offline", cap="Раздел об офлайн-режиме и очереди изменений",
          note=["Офлайн-режим объясняйте словами пользователя, а не словами разработчика: "
                "«не пропали», «уйдут сами», а не «персистентная очередь операций»."]),
    ],
    [("В руководстве скриншоты старой версии", "пересняты после изменения экрана"),
     ("Описаны несуществующие кнопки", "руководство писалось по ТЗ, а не по приложению"),
     ("Нет сценария заявки", "это самый нужный раздел — без него руководство не работает")],
    "rg -c '^\\|' docs/user-guide-desktop.md",
    "docs: руководство пользователя desktop-клиента",
))

PAGES.append(P(
    51, "Руководство-пользователя-Web-и-администратора", 22,
    "Второй том руководства: руководитель в web-клиенте и администратор в разделе "
    "пользователей. Кто видит какие экраны, что означают показатели дашборда и "
    "как читать аналитику.",
    "Руководитель по руководству читает аналитику сам, администратор — управляет пользователями и справочниками.",
    [("Г / Документирование", "Руководство пользователя (web) и администратора")],
    ["docs/user-guide-web.md", "docs/screenshots/web/*.png"],
    [
        S("Роли и доступ к экранам", 25,
          "Таблица «роль — что видит — что может». Это первое, что спрашивает "
          "руководитель: «а я это увижу?».",
          code="| Раздел | Администратор | Руководитель | Мастер |\n|---|---|---|---|\n| Дашборд | да | да | да |\n| Аналитика | да | да | нет |\n| Оборудование | да | да | да |\n| Заявки | да | да | да |\n| График ТО | да | да | да |\n| Справочники | да | нет | нет |\n| Пользователи | да | нет | нет |",
          hint="Терминал",
          png="guide-roles", cap="Матрица прав: кто что видит в web-клиенте",
          note=["Таблица должна совпадать с тем, что реально проверяет сервер. "
                "Расхождение обнаруживается первой же демонстрацией под другой ролью."]),
        S("Дашборд руководителя", 30,
          "Шесть KPI-карточек, автообновление раз в минуту и индикатор соединения. "
          "Отдельно объясняем, что означает каждая диаграмма.",
          code="**Средний простой** показывает, сколько часов оборудование в среднем\nне работало. Рост значения означает либо рост отказов, либо заниженную\nдисциплину закрытия заявок.\n\n**Доля аварийных заявок** — здоровье парка. Устойчивая доля выше 15 % говорит\nо том, что плановое обслуживание не выполняется в срок.\n\n**Выполнение графика ТО** рассчитывается как отношение выполненных записей к общему\nчислу записей за период. Значение ниже 90 % — повод разобрать график.",
          hint="Терминал",
          png="guide-web-dashboard", gif="guide-web-dashboard", cap="Раздел «Дашборд руководителя»: показатели и их интерпретация",
          note=["Не пересказывайте интерфейс. Объясняйте, что означает показатель и на "
                "какое решение он влияет — это и есть ценность руководства."]),
        S("Аналитика и экспорт", 35,
          "Панель фильтров, пять блоков аналитики, экспорт в PNG, CSV, PDF и печать. "
          "Разбираем типовой вопрос: «почему вырос простой в цехе №2».",
          code="### Типовой вопрос: откуда взялся простой\n\n1. Откройте «Аналитика» и задайте период, например квартал.\n2. В блоке «Анализ простоев» посмотрите топ-5 единиц по суммарному простою.\n3. Выберите единицу из топ-5 и перейдите в «Заявки», отфильтровав по ней.\n4. Посмотрите приоритеты: если среди заявок много аварийных — проблема в отказе,\n   если нет — в качестве планового обслуживания.\n5. Выгрузите блок в PDF и приложите к служебной записке.",
          hint="Терминал",
          png="guide-analytics", gif="guide-analytics", cap="Разбор аналитики на примере вопроса руководителя",
          note=["Описывайте не кнопки, а путь решения задачи. Руководство, в котором "
                "идёт «нажмите сюда, потом сюда», через месяц никому не помогает."]),
        S("Администратор: пользователи и справочники", 30,
          "Создание пользователя, выдача роли, блокировка, ведение видов обслуживания, "
          "материалов и бригад. Здесь же — правило про невозможность удаления "
          "справочника, который уже используется.",
          code="### Порядок работы администратора\n\n1. **Пользователи.** Создайте учётную запись, назначьте роль, сообщите пароль сотруднику лично.\n2. **Виды обслуживания.** Добавьте вид с периодичностью в днях — она используется в графике.\n3. **Материалы.** Внесите номенклатуру с артикулом, единицей измерения, ценой и минимальным остатком.\n4. **Бригады.** Создайте бригаду и добавьте в неё членов.\n\n> **Важно:** вид обслуживания и материал нельзя удалить, если они уже использованы в заявках или графике.\n> Вместо удаления снимите отметку «активен» — новые работы использовать такой справочник перестанут,\n> а старые записи останутся корректными.",
          hint="Терминал",
          png="guide-admin", gif="guide-admin", cap="Раздел администратора: порядок первичной настройки",
          note=["Справочник не удаляется, а деактивируется — об этом знают не все. "
                "Без этого пояснения новичок удалит вид обслуживания и сломает "
                "график за прошлые месяцы."]),
    ],
    [("Таблица прав не совпадает с сервером", "сверьтесь с `RequireRole` на контроллерах"),
     ("Руководство описывает несуществующий блок", "сверьтесь со страницей аналитики"),
     ("Нет объяснения, что делать при сбое соединения", "опишите индикатор и polling")],
    "rg -c '^\\|' docs/user-guide-web.md",
    "docs: руководство пользователя web-клиента и администратора",
))
# === BLOCK-L: страницы 52–54 (защита и итоговая проверка) ===

PAGES.append(P(
    52, "Презентация-проекта", 23,
    "Презентация на 12–15 слайдов: задача, модель данных, архитектура, ключевые "
    "решения, демонстрация, результаты. Каждый слайд — один тезис и одна картинка, "
    "никаких списков на два экрана.",
    "Презентация готова: 14 слайдов, на каждом один тезис, время выступления укладывается в 5–7 минут.",
    [("Г / Документирование", "Презентация проекта")],
    ["docs/presentation/slides.md", "docs/presentation/"],
    [
        S("Структура презентации", 25,
          "Четыре блока: проблема и решение, как устроено, ключевые технические "
          "решения, результат. Сквозной сюжет — от «что болит» до «сколько это "
          "сэкономит».",
          code="| № | Слайд | Тезис | Визуал |\n|---|---|---|---|\n| 1 | Титул | Система «ТОиР-Проф» | логотип |\n| 2 | Проблема | Учёт ТО ведётся в тетрадях и Excel | фото участка |\n| 3 | Решение | Единая система: план, заявки, ремонты, отчёты | схема системы |\n| 4 | Архитектура | БД → API → два клиента | диаграмма слоёв |\n| 5 | Модель данных | 13 таблиц, нормализация, связи | ER-диаграмма |\n| 6 | Целостность | Ограничения, триггеры, функции | скриншот DBeaver |\n| 7 | API | Единый формат ответа, роли, коды ошибок | Swagger UI |\n| 8 | Desktop-клиент | 8 экранов мастера | скриншот дашборда |\n| 9 | Web-клиент | Дашборд руководителя и аналитика | скриншот аналитики |\n| 10 | Аналитика | 5 блоков, экспорт в PDF | скриншот блока |\n| 11 | Тестирование | 5 юнит-тестов, все проходят | вывод `dotnet test` |\n| 12 | Документация | Swagger, инструкция, руководство | список файлов |\n| 13 | Результаты | цифры до и после | таблица метрик |\n| 14 | Заключение | что сделано и что дальше | контакты |",
          hint="Терминал",
          png="slides-plan", cap="План 14 слайдов с тезисом и визуалом на каждый",
          note=["Один слайд — один тезис. Слайд, на который нужно читать абзац, "
                "эксперт не прочитает, а листать будет быстрее, чем слушать."]),
        S("Собираем слайды", 35,
          "Простой формат — Markdown или Reveal.js: он читается без установки "
          "PowerPoint и собирается в PDF одной командой.",
          code="# Слайд 5. Модель данных\n\n**13 таблиц, три нормальные формы, ни одного дублирования**\n\n- `equipment` — единицы оборудования\n- `maintenance_schedule` — график планового ТО\n- `work_orders` — заявки на ремонт\n- `work_order_materials` — списанные материалы и ЗИП\n\n![ER-диаграмма](../diagrams/er/er-diagram.png)\n\n> Ключевые решения: нормализация до 3НФ, справочники вынесены отдельно,\n> аудит ведётся триггером в `operation_log`.",
          lang="markdown", hint="docs/presentation/slides.md",
          png="slide-5", gif="slide-5", cap="Слайд о модели данных с ER-диаграммой",
          note=["Визуал на слайде берите из своего приложения, а не из стоковой "
                "картинки. Скриншот своего работающего экрана убедительнее любой "
                "схемы."]),
        S("Слайд с результатами", 25,
          "Один из самых важных слайдов: цифры, которые можно измерить. Если "
          "заказчик не давал метрик, считайте их от данных своей системы.",
          code="| Показатель | Было | Стало |\n|---|---|---|\n| Время на оформление заявки | 25 мин | 2 мин |\n| Потерянные заявки | не учитывались | 0 за квартал |\n| Простой оборудования | неизвестен | −18 % |\n| Доля аварийных заявок | нет контроля | 19,1 % → 15,3 % |\n| Подготовка отчёта | 3 часа | 1 минута |",
          hint="Терминал",
          png="slide-results", gif="slide-results", cap="Слайд «Результаты»: было и стало",
          note=["Не выдумывайте цифры. Если реальных метрик нет, покажите "
                "измеримые характеристики самой системы: число ограничений, "
                "покрытие тестами, время отклика API."]),
        S("Проверяем презентацию на месте", 25,
          "Открываем с другого компьютера, отключаем интернет, проходим все 14 слайдов. "
          "Проверяем шрифты, картинки и отсутствие обрезанного текста.",
          code="```bash\n# Сборка в PDF для раздатки и отправки жюри\npython3 -m markdown --export pdf docs/presentation/slides.md -o docs/presentation/presentation.pdf\n```",
          hint="Терминал",
          png="slides-check", gif="slides-check", cap="Презентация открыта на другом компьютере без интернета",
          note=["Все ресурсы — шрифты, картинки, темы — должны быть локальными. "
                "Презентация, которая «сломалась» на чужой машине из-за отсутствия "
                "интернета, стоит дороже, чем кажется."]),
    ],
    [("Слайдов больше 15", "сокращайте: за 15 слайдов за 5 минут не уложиться"),
     ("Текст не читается с расстояния", "минимальный кегль 20 pt"),
     ("Скриншоты мыльные", "снимайте в полном разрешении и уменьшайте до 1920 px"),
     ("PDF не собирается без интернета", "ресурсы лежат рядом со слайдами")],
    "ls docs/presentation/",
    "docs: презентация проекта на 14 слайдов",
))

PAGES.append(P(
    53, "Устное-выступление-и-ответы-экспертам", 23,
    "Речь на 5–7 минут по слайдам и заготовленные ответы на частые вопросы экспертов. "
    "Речь пишется заранее целиком — на защите её читают, а не импровизируют.",
    "Текст выступления на 6 минут и ответы на 12 типовых вопросов экспертов.",
    [("Г / Документирование", "Устное выступление и ответы на вопросы")],
    ["docs/presentation/speech.md", "docs/presentation/qa.md"],
    [
        S("Пишем текст выступления", 30,
          "По одному абзацу на слайд, 80–110 слов на слайд. Общий объём — около "
          "900 слов на 6 минут спокойной речи.",
          code="**Слайд 2. Проблема.**\n\n> Сегодня учёт технического обслуживания ведётся в тетрадях и разрозненных файлах.\n> Мы не знаем, какое оборудование простаивает, какие заявки забыты и сколько\n> на самом деле стоит ремонт. Решения принимаются без цифр.\n\n**Слайд 3. Решение.**\n\n> Мы разработали систему «ТОиР-Проф»: единый контур от графика планового\n> обслуживания до закрытой заявки с отчётом. Система состоит из базы данных,\n> API и двух клиентов — для мастера на участке и для руководителя в браузере.",
          lang="markdown", hint="docs/presentation/speech.md",
          png="speech-text", gif="speech-text", cap="Текст выступления с абзацем на каждый слайд",
          note=["Говорите от результата, а не от технологий. Эксперту интересно, "
                "что изменилось для участка, а название фреймворка он и так прочтёт "
                "в репозитории."]),
        S("Регламент и репетиция", 25,
          "Прогон с секундомером: 6 минут ± 30 секунд. Две репетиции вслух — "
          "чтение с листа на защите читается хуже, чем кажется.",
          code="```bash\n# Проверка объёма текста: ~900 слов ≈ 6 минут при темпе 150 слов в минуту\npython3 - <<'EOF'\nimport re, io\ntext = io.open('docs/presentation/speech.md', encoding='utf-8').read()\nwords = len(re.findall(r'\\S+', text))\nprint(f'Слов: {words}')\nprint(f'Оценка времени: {words / 150:.1f} мин при 150 слов/мин')\nEOF\n```",
          hint="Терминал",
          png="speech-timing", gif="speech-timing", cap="Прогон с секундомером: 918 слов, 6,1 минуты",
          note=["Вторую половину речи обычно «съедает» торопливое объяснение "
                "демонстрации. Держите демонстрацию отдельным этапом и возвращайтесь "
                "к тексту после неё."]),
        S("Вопросы о базе данных", 35,
          "Самые частые вопросы экспертов: почему 3НФ, зачем триггер, а не проверка "
          "в приложении, чем отличается ON DELETE CASCADE от RESTRICT.",
          code="**Почему ограничения в базе, а не в приложении?**\n\nПравило в базе выполняется всегда: через Postman, через прямой SQL, через отчёт.\nПроверка в приложении обходится одним запросом — например, при загрузке данных\nскриптом. Ограничение в базе — это последний рубеж, его нельзя обойти.\n\n**Почему `ON DELETE RESTRICT` для справочников?**\n\nВид обслуживания или материал нельзя удалить, если он уже использован в заявках\nили графике. `CASCADE` молча удалил бы связанные записи — и данные за прошлые\nпериоды исчезли бы из отчётов.\n\n**Почему триггер, а не `CHECK`?**\n\n`CHECK` сравнивает только значения этой строки и не может посмотреть старую\n(`OLD`) или соседние строки. Триггер нужен там, где правило зависит от истории\nизменений, — например «нельзя менять статус, если уже выведено из эксплуатации».",
          hint="Терминал",
          png="qa-db", gif="qa-db", cap="Ответы на вопросы по модели данных и ограничениям",
          note=["Отвечайте «потому что» — объяснение причины ценится выше самого "
                "решения. Фраза «так было в задании» обесценивает работу."]),
        S("Вопросы об архитектуре и клиентах", 35,
          "Почему два клиента, а не один; как обеспечивается изоляция данных; что "
          "происходит при потере связи; чем SSE отличается от WebSocket.",
          code="**Почему два клиента, а не один?**\n\nМастер работает на участке с участковым компьютера — ему нужен нативный\nинтерфейс и работа при нестабильной сети. Руководитель смотрит аналитику\nс любого устройства — ему нужен браузер и печать отчёта. Общая только бизнес-логика,\nона живёт в API.\n\n**Что происходит при обрыве связи?**\n\nКлиент кладёт изменение в очередь на диск и отправляет его при восстановлении\nсвязи. Пользователь при этом видит индикатор состояния, а не «зависшее»\nприложение.\n\n**Почему SSE, а не WebSocket?**\n\nКанал односторонний: сервер только отправляет изменения счётчиков.\nSSE работает поверх обычного HTTP, не требует отдельного порта и проходит\nчерез прокси без дополнительной настройки.",
          hint="Терминал",
          png="qa-architecture", gif="qa-architecture", cap="Ответы на вопросы об архитектуре и клиентах",
          note=["Держите лист ответов перед собой. Большинство вопросов "
                "повторяется из защиты в защиту, и подготовленный ответ звучит "
                "увереннее, чем пауза."]),
    ],
    [("Речь длится 9 минут", "сократите до 900 слов и отрепетируйте с секундомером"),
     ("На вопрос отвечаете «мы не пробовали»", "проговорите слабые места заранее и честно"),
     ("Терминология не совпадает с кодом", "сверьте названия по репозиторию перед защитой")],
    "python3 -c \"import re,io;print(len(re.findall(r'\\S+', io.open('docs/presentation/speech.md',encoding='utf-8').read())))\"",
    "docs: текст выступления и ответы на вопросы экспертов",
))

PAGES.append(P(
    54, "Итоговая-проверка-по-критериям", 24,
    "Финальный чек-лист перед защитой: пройти по всем критериям листа оценивания и "
    "убедиться, что каждый пункт закрыт и может быть показан. Страница короткая — "
    "она нужна как список дел, а не как учебник.",
    "Каждый критерий из листа оценивания отмечен, непроверенных пунктов нет, система запускается одной командой.",
    [("Г / Итог", "Проверка по критериям перед защитой")],
    ["docs/criteria-checklist.md", "criteria.md"],
    [
        S("Проектирование", 25,
          "Три диаграммы на месте, в нужных форматах, с исходниками и обоснованием. "
          "Модель данных соответствует диаграмме классов.",
          code="```bash\n# Диаграммы: исходник, PNG, SVG и README с обоснованием\nls -1 docs/diagrams/usecase/ docs/diagrams/activity/ docs/diagrams/class/\n# В каждой папке: исходник (.puml), .png, .svg и README.md\n```",
          hint="Терминал",
          png="check-diagrams", cap="Три папки диаграмм, в каждой исходник, PNG, SVG и README",
          note=["Проверьте, что диаграмма классов совпадает с реальной схемой базы. "
                "Эксперт сравнивает их и первым же находит расхождение в именах "
                "полей."]),
        S("База данных", 30,
          "Все ограничения, триггеры, функции и процедура создаются скриптами с "
          "чистой базы. Проверяем не только наличие, но и то, что они срабатывают.",
          code="```bash\n# Ограничения: UNIQUE, CHECK, ENUM, ON DELETE\npsql -h 127.0.0.1 -U toirprof -d toirprof -c \"\\\\d+ equipment\"\n# Объекты БД\npsql -h 127.0.0.1 -U toirprof -d toirprof -c \"\\\\df+ fn_* proc_*\"\n```",
          hint="Терминал",
          png="check-db", gif="check-db", cap="Ограничения и объекты БД на месте",
          note=["Проверьте ограничения на чистой базе: скрипты должны проходить "
                "подряд, без ручных правок. Если что-то требует поправить вручную — "
                "на площадке это тоже придётся."]),
        S("API и клиенты", 35,
          "Swagger открывается, все роли работают, оба клиента запускаются и "
          "показывают данные. Проверяем с чистого запуска.",
          code="```bash\ndotnet test src/Tests/ToirProf.Tests.csproj\ndotnet build src/api/ToirProf.Api.csproj -c Release\ncd src/web && npm run build\n```",
          hint="Терминал",
          png="check-build", gif="check-build", cap="Сборка без ошибок, все 5 юнит-тестов проходят",
          note=["Проверяйте сборку в Release, а не Debug. На площадке запускается "
                "собранное приложение, и ошибки оптимизации там проявляются иначе."]),
        S("Документация и защита", 30,
          "Swagger, инструкция, руководство, презентация, текст выступления — всё "
          "в репозитории, всё открывается и читается.",
          code="```bash\nls -1 docs/ docs/presentation/ postman/\n# Проверка, что все файлы инструкций на месте и не пустые\nfind docs -name '*.md' -size -1k\n# (пустой вывод означает: файлов меньше килобайта нет)\n```",
          hint="Терминал",
          png="check-docs", cap="Все документы на месте и не пустые",
          note=["Проверьте и то, что инструкция работает на чистой машине. Пять минут "
                "на проверку на второй машине экономят сорок минут на защите."]),
        S("Прогон всей системы и запись демонстрации", 25,
          "Финальный прогон: база, API, оба клиента, сквозной сценарий заявки. "
          "Записываем видео демонстрации как запасной вариант.",
          code="```bash\n# Сквозной сценарий: создать заявку → назначить бригаду → завершить со списанием\ncurl -s -X POST http://localhost:5080/api/work-orders \\\n  -H \"Authorization: Bearer $TOKEN\" -H 'Content-Type: application/json' \\\n  -d '{\"equipmentId\":\"44444444-4444-4444-4444-444444444444\",\"description\":\"Стучит подшипник\",\"priority\":\"Высокий\"}'\n```",
          hint="Терминал",
          png="check-e2e", gif="check-e2e", cap="Сквозной сценарий от заявки до закрытого отчёта",
          note=["Запись демонстрации — не формальность. Если на площадке что-то не "
                "запустится, видео покажет систему лучше, чем объяснение."]),
    ],
    [("Пропущен критерий без пометки", "пройдите лист оценивания заново по пунктам"),
     ("Инструкция не работает на чистой машине", "проверьте на второй машине заранее"),
     ("Диаграммы расходятся с базой", "сверьте имена полей по `db/schema.sql`"),
     ("На защите что-то не запускается", "держите запись демонстрации")],
    "git status --short && dotnet test src/Tests/ToirProf.Tests.csproj",
    "docs: итоговый чек-лист проверки по критериям оценивания",
))
# === END-BLOCK-L ===
# === END-BLOCK-E ===