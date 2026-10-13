#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генератор wiki-страниц системы «ТОиР-Проф».

Собирает 54 пошаговые страницы по 24 спринтам из таблицы `sprints.py`,
плюс Home.md и _Sidebar.md.

Использование:
    python3 tools/wiki/gen_pages.py            # перезаписать wiki/
    python3 tools/wiki/gen_pages.py --check    # только проверить, ничего не писать
    python3 tools/wiki/gen_pages.py --out DIR  # писать в другой каталог

Зависимостей нет — только стандартная библиотека Python 3.8+.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sprints import PAGES, SPRINTS  # noqa: E402

IMG_DIR = "images"
GIF_DIR = "gifs"
EXPECTED_PAGES = 54
EXPECTED_SPRINTS = 25  # спринты 0..24


# --------------------------------------------------------------------------
# Рендеринг
# --------------------------------------------------------------------------

def slug(text):
    """Кириллицу и пробелы превращает в латинский kebab-case для имени медиа."""
    table = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    out = []
    for ch in text.lower():
        if ch.isdigit():
            out.append(ch)
        elif "a" <= ch <= "z":
            out.append(ch)
        elif ch in table:
            out.append(table[ch])
        elif ch in " -_":
            out.append("-")
    slug_text = re.sub(r"-+", "-", "".join(out)).strip("-")
    return slug_text or "step"


def page_filename(n, title):
    return "%02d-%s.md" % (n, title)


def page_link(n, title):
    return "[%s](%s)" % (title, page_filename(n, title))


def page_minutes(page):
    return sum(step["m"] for step in page["steps"])


def sprint_of(n):
    for sprint in SPRINTS:
        if sprint["pages"][0] <= n <= sprint["pages"][1]:
            return sprint
    raise KeyError("страница %d не принадлежит ни одному спринту" % n)


def render_media(n, step, idx):
    """Возвращает блок со скриншотом и/или gif для шага."""
    parts = []
    if step.get("png"):
        path = "%s/%02d-%s.png" % (IMG_DIR, n, step["png"])
        parts.append("![%s](%s)\n*%s*" % (step["cap"], path, step["cap"]))
    if step.get("gif"):
        path = "%s/%02d-%s.gif" % (GIF_DIR, n, step["gif"])
        parts.append("![%s](%s)\n*%s*" % (step["cap"], path, step["cap"]))
    if not parts:
        return ""
    return "\n\n".join(parts)


def render_step(n, idx, step):
    num = "%02d-%02d" % (n, idx)
    out = ["## Шаг %d. %s — %d мин" % (idx, step["t"], step["m"]), ""]
    out.append(step["b"])
    out.append("")

    if step.get("f"):
        files = ", ".join("`%s`" % f for f in step["f"])
        out.append("**Файлы:** %s" % files)
        out.append("")

    if step.get("code"):
        out.append("**%s**" % step.get("path_hint", "Команда"))
        out.append("")
        out.append("```%s" % step.get("lang", "bash"))
        out.append(step["code"].rstrip())
        out.append("```")
        out.append("")

    if step.get("note"):
        for note in step["note"]:
            out.append("> **Замечание.** %s" % note)
            out.append("")

    media = render_media(n, step, idx)
    if media:
        out.append(media)
        out.append("")

    return "\n".join(out)


def render_page(page):
    n = page["n"]
    sprint = sprint_of(n)
    name = page_filename(n, page["ti"])
    minutes = page_minutes(page)

    out = ["# %s" % page["ti"], ""]
    out.append("> Спринт %d. %s · %d мин · страница %d из %d"
               % (page["sp"], sprint["name"], minutes, n, EXPECTED_PAGES))
    out.append("")
    out.append(page["intro"])
    out.append("")

    out.append("**Итог страницы.** %s" % page["res"])
    out.append("")

    if page.get("crit"):
        out.append("| Критерий оценивания | Что закрывает страница |")
        out.append("|---|---|")
        for row in page["crit"]:
            out.append("| %s | %s |" % (row[0], row[1]))
        out.append("")

    if page.get("files"):
        out.append("**Результат в репозитории:**")
        out.append("")
        for f in page["files"]:
            out.append("- `%s`" % f)
        out.append("")

    for idx, step in enumerate(page["steps"], start=1):
        out.append(render_step(n, idx, step))
        out.append("")

    if page.get("fb"):
        out.append("## Если что-то не получилось")
        out.append("")
        out.append("| Симптом | Что делать |")
        out.append("|---|---|")
        for row in page["fb"]:
            out.append("| %s | %s |" % (row[0], row[1]))
        out.append("")

    out.append("## Проверка")
    out.append("")
    out.append("```bash")
    out.append(page["check"].rstrip())
    out.append("```")
    out.append("")

    out.append("## Коммит")
    out.append("")
    out.append("```bash")
    out.append("git add -A")
    out.append('git commit -m "%s"' % page["commit"])
    out.append("```")
    out.append("")

    out.append("---")
    out.append("")
    prev_link = page_link(n - 1, PAGES[n - 2]["ti"]) if n > 1 else "← назад"
    next_link = page_link(n + 1, PAGES[n]["ti"]) if n < EXPECTED_PAGES else "дальше →"
    out.append("%s · [все спринты](Home) · %s" % (prev_link, next_link))
    out.append("")
    return "\n".join(out)


def render_home():
    out = []
    out.append("# ТОиР-Проф — система управления техническим обслуживанием")
    out.append("")
    out.append("**Компетенция:** Программные решения для бизнеса · "
               "Чемпионат «Профессионалы» 2027")
    out.append("")
    out.append("Задание разобрано **по спринтам**: 24 спринта, 54 страницы, "
               "каждая страница — 2–3 часа работы.")
    out.append("Каждый шаг описан словами, подкреплён кодом, скриншотом и гифкой.")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Как устроен тренинг")
    out.append("")
    out.append("| Параметр | Значение |")
    out.append("|---|---|")
    out.append("| Всего спринтов | **24** |")
    out.append("| Всего страниц | **54** |")
    out.append("| Длина страницы | **2–3 часа** |")
    out.append("| Результат сессии | рабочий код в репозитории + коммит |")
    out.append("")
    out.append("Проходите страницы по порядку. Страница заканчивается коммитом, "
               "даже если что-то не успели: незавершённый код полезнее, чем ничего.")
    out.append("")
    out.append("> **Не застревайте.** Если блок не получается за 20–25 минут — "
               "переходите по таблице «Если что-то не получилось» и возвращайтесь "
               "на следующей сессии.")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Стек")
    out.append("")
    out.append("| Часть | Технология | Версия |")
    out.append("|---|---|---|")
    out.append("| База данных | PostgreSQL | 16+ |")
    out.append("| API | ASP.NET Core Web API (.NET) + Entity Framework Core | .NET 10 |")
    out.append("| Web-клиент | React + TypeScript + Vite | React 19 |")
    out.append("| Desktop-клиент | C# / Avalonia (MVVM) | Avalonia 11 |")
    out.append("| Модульные тесты | xUnit | 3.x |")
    out.append("| Инструменты | Git, Gogs, DBeaver, Postman, Swagger UI, Draw.io, VS Code | — |")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Карта спринтов")
    out.append("")
    out.append("| Спринт | Страницы | Что делаем | Задание | Баллы |")
    out.append("|---|---|---|---|---|")
    for sprint in SPRINTS:
        links = " · ".join(
            page_link(p["n"], p["ti"]) for p in PAGES if p["n"] in sprint["pages"]
        )
        out.append("| **%d. %s** | %s | %s | %s | %s |"
                   % (sprint["id"], sprint["name"], links, sprint["what"],
                      sprint["task"], sprint["pts"]))
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Куда сдают работу")
    out.append("")
    out.append("| Куда | Что положить |")
    out.append("|---|---|")
    out.append("| `db/` | `schema.sql`, `seed.sql`, ER-диаграмма, скрипты триггеров, функций и процедур |")
    out.append("| `src/api/` | Web API .NET 10 |")
    out.append("| `src/desktop/` | Desktop-клиент Avalonia |")
    out.append("| `src/web/` | Web-клиент React |")
    out.append("| `src/Tests/` | Модульные тесты xUnit |")
    out.append("| `postman/` | Коллекция Postman |")
    out.append("| `docs/diagrams/` | Три UML-диаграммы (PNG + SVG + исходник + README) |")
    out.append("| `docs/screenshots/` | Скриншоты клиентов и Swagger |")
    out.append("| `README.md` | Инструкция по запуску |")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Важные правила")
    out.append("")
    out.append("1. **Целевая ОС — РедОС 8.0.** Никаких Windows-путей, обратных "
               "слэшей, `cmd` и PowerShell. Команды в wiki — только bash.")
    out.append("2. **PostgreSQL ставится нативно** через `dnf`; Docker на площадке "
               "может отсутствовать.")
    out.append("3. **ИИ запрещён** для кода, SQL, триггеров, функций, архитектуры БД "
               "и тестов. Разрешён только для текстов документации и презентации, "
               "и только в браузере без авторизации.")
    out.append("4. **Формат ответа API единый:** "
               "`{ \"success\", \"data\", \"message\", \"error_code\" }` — "
               "см. [13-Формат-ответа-и-обработка-ошибок](13-Формат-ответа-и-обработка-ошибок).")
    out.append("5. **Номер заявки** формируется автоматически в формате "
               "`Z-YYYY-XXXX` — см. "
               "[19-Генерация-номера-заявки](19-Генерация-номера-заявки).")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Справка")
    out.append("")
    out.append("- [Как устроена страница wiki](docs/wiki-plan.md) — формат, "
               "имена файлов, чек-лист перед коммитом")
    out.append("- [Чек-лист захвата скриншотов и гиф](docs/capture-checklist.md) — "
               "что снимать на каждой странице")
    out.append("- [Список всех критериев оценивания](criteria.md) — 100 баллов")
    out.append("")
    return "\n".join(out)


def render_sidebar():
    out = []
    out.append("## ТОиР-Проф")
    out.append("")
    out.append("- [Все спринты](Home)")
    out.append("")
    for sprint in SPRINTS:
        out.append("### %d. %s" % (sprint["id"], sprint["name"]))
        out.append("")
        for p in PAGES:
            if p["n"] in sprint["pages"]:
                out.append("  - %s" % page_link(p["n"], p["ti"]))
        out.append("")
    return "\n".join(out)


def render_checklist():
    """Чек-лист захвата: что снять на каждой странице.

    Строится из тех же данных, что и страницы, поэтому расхождение
    между чек-листом и подписями к картинкам невозможно по построению.
    """
    out = []
    out.append("# Чек-лист захвата скриншотов и гиф")
    out.append("")
    out.append("Файл собран генератором `tools/wiki/gen_pages.py` из данных "
               "`tools/wiki/sprints.py`. Правьте источник, а не этот файл — "
               "иначе чек-лист разойдётся со страницами при следующей сборке.")
    out.append("")
    total_png = sum(1 for p in PAGES for s in p["steps"] if s.get("png"))
    total_gif = sum(1 for p in PAGES for s in p["steps"] if s.get("gif"))
    out.append("**Всего:** %d страниц, %d скриншотов, %d гифок."
               % (len(PAGES), total_png, total_gif))
    out.append("")

    for sprint in SPRINTS:
        pages = [p for p in PAGES if p["n"] in sprint["pages"]]
        if not pages:
            continue
        out.append("## Спринт %d. %s"
                   % (sprint["id"], sprint["name"]))
        out.append("")
        out.append("| Стр. | Шаг | Что снять | Файл скриншота | Файл гифки |")
        out.append("|---|---|---|---|---|")
        for p in pages:
            if not any(s.get("png") or s.get("gif") for s in p["steps"]):
                out.append("| %02d | — | %s | — | — |"
                           % (p["n"], p["ti"]))
                continue
            first = True
            for idx, step in enumerate(p["steps"], start=1):
                if not step.get("png") and not step.get("gif"):
                    continue
                out.append("| %s | %s | %s | %s | %s |" % (
                    ("%02d" % p["n"]) if first else "",
                    ("%d. %s" % (idx, step["t"])) if first else "",
                    step.get("b", "").split(". ")[0][:90].replace("|", "/"),
                    "`images/%02d-%s.png`" % (p["n"], step["png"]) if step.get("png") else "—",
                    "`gifs/%02d-%s.gif`" % (p["n"], step["gif"]) if step.get("gif") else "—",
                ))
                first = False
        out.append("")

    out.append("---")
    out.append("")
    out.append("## Как снимать")
    out.append("")
    out.append("```bash")
    out.append("# Один кадр — для статичной иллюстрации")
    out.append("python3 tools/capture/rec.py --name 07-schema-equipment --single")
    out.append("")
    out.append("# Короткая запись — для гифки")
    out.append("python3 tools/capture/rec.py --name 07-schema-run --seconds 8 --delay 2")
    out.append("")
    out.append("# Запуск команды шага и снимок окна терминала с её выводом")
    out.append("NO_SHOT= python3 tools/capture/run-page.sh 07-schema-run psql -f db/schema.sql")
    out.append("")
    out.append("# Гифка из готовых кадров, если снимали поштучно")
    out.append("python3 tools/capture/make-gifs.py /tmp/07-*.png -o wiki/gifs/07-schema-run.gif")
    out.append("```")
    out.append("")
    out.append("## Перед коммитом")
    out.append("")
    out.append("- [ ] Файл называется по схеме `images/NN-<slug>.png` / `gifs/NN-<slug>.gif`.")
    out.append("- [ ] На скриншоте видно результат шага, а не пустой экран.")
    out.append("- [ ] В кадре нет лишних окон, уведомлений и курсора в текстовом поле.")
    out.append("- [ ] Текст на скриншоте читается без увеличения.")
    out.append("- [ ] Подпись под картинкой совпадает с `cap` в `sprints.py`.")
    out.append("- [ ] Гифка короче 10 секунд и меньше 5 МБ.")
    out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Проверки
# --------------------------------------------------------------------------

def collect_targets(out_dir):
    return {page_filename(p["n"], p["ti"]) for p in PAGES} | {"Home.md", "_Sidebar.md"}


def check(out_dir):
    problems = []

    if len(PAGES) != EXPECTED_PAGES:
        problems.append("ожидалось %d страниц, в таблице %d" % (EXPECTED_PAGES, len(PAGES)))
    if len(SPRINTS) != EXPECTED_SPRINTS:
        problems.append("ожидалось %d спринтов, в таблице %d" % (EXPECTED_SPRINTS, len(SPRINTS)))

    numbers = [p["n"] for p in PAGES]
    if numbers != list(range(1, EXPECTED_PAGES + 1)):
        problems.append("нумерация страниц не сплошная 1..%d" % EXPECTED_PAGES)

    names = [page_filename(p["n"], p["ti"]) for p in PAGES]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        problems.append("дубли имён файлов: %s" % ", ".join(sorted(dupes)))

    # каждая страница принадлежит ровно одному спринту
    covered = []
    for sprint in SPRINTS:
        covered.extend(range(sprint["pages"][0], sprint["pages"][1] + 1))
    if covered != list(range(1, EXPECTED_PAGES + 1)):
        problems.append("диапазоны спринтов не покрывают 1..%d ровно по одному разу" % EXPECTED_PAGES)

    # ссылки на другие страницы существуют.
    # Генератор пишет ссылки БЕЗ расширения (.md) — так их понимают и
    # GitHub Wiki, и Obsidian, и Gogs. Расшижение допускается, но не нужно.
    valid = {n[:-3] for n in names}
    link_re = re.compile(r"\]\(([^)#]+?)(?:\.md)?\)")
    for name in sorted(valid) + ["Home.md", "_Sidebar.md"]:
        text = (out_dir / name).read_text(encoding="utf-8") if (out_dir / name).exists() else ""
        if not text:
            continue
        for target in link_re.findall(text):
            if target.startswith(("http", "docs/", "criteria", "assets/",
                                "images/", "gifs/", "..", "#")):
                continue
            if target not in valid and target != "Home":
                problems.append("битая ссылка в %s: %s" % (name, target))

    # каждое объявленное медиа уникально; скриншоты и гифки лежат
    # в разных каталогах, поэтому одинаковый slug в png и gif — не дубль
    media = []
    for p in PAGES:
        for step in p["steps"]:
            if step.get("png"):
                media.append("images/%02d-%s.png" % (p["n"], step["png"]))
            if step.get("gif"):
                media.append("gifs/%02d-%s.gif" % (p["n"], step["gif"]))
    dup_media = {m for m in media if media.count(m) > 1}
    if dup_media:
        problems.append("дубли имён медиа: %s" % ", ".join(sorted(dup_media)))

    if problems:
        for problem in problems:
            print("ПРОБЛЕМА: %s" % problem, file=sys.stderr)
        return 1

    print("OK: %d страницы, %d уникальных имён, %d файлов медиа, битых ссылок: 0"
          % (len(PAGES), len(names), len(media)))
    return 0


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Генератор wiki ТОиР-Проф")
    parser.add_argument("--out", default=None,
                        help="каталог для записи (по умолчанию ../wiki от этого файла)")
    parser.add_argument("--check", action="store_true",
                        help="только проверить, ничего не записывать")
    parser.add_argument("--checklist", default=None,
                        help="куда писать чек-лист захвата (по умолчанию docs/capture-checklist.md)")
    args = parser.parse_args()

    out_dir = Path(args.out) if args.out else Path(__file__).resolve().parents[2] / "wiki"

    if args.check:
        return check(out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / IMG_DIR).mkdir(exist_ok=True)
    (out_dir / GIF_DIR).mkdir(exist_ok=True)
    for keeper in (out_dir / IMG_DIR / ".gitkeep", out_dir / GIF_DIR / ".gitkeep"):
        keeper.touch()

    stale = out_dir / ".stale-targets.txt"
    known = collect_targets(out_dir)
    removed = []
    for old in sorted(out_dir.glob("*.md")):
        if old.name not in known:
            old.unlink()
            removed.append(old.name)

    for page in PAGES:
        (out_dir / page_filename(page["n"], page["ti"])).write_text(
            render_page(page), encoding="utf-8")

    (out_dir / "Home.md").write_text(render_home(), encoding="utf-8")
    (out_dir / "_Sidebar.md").write_text(render_sidebar(), encoding="utf-8")

    checklist = Path(args.checklist) if args.checklist else (
        out_dir.parent / "docs" / "capture-checklist.md")
    checklist.parent.mkdir(parents=True, exist_ok=True)
    checklist.write_text(render_checklist(), encoding="utf-8")
    print("Чек-лист захвата: %s" % checklist)

    stale.write_text("\n".join(removed) + ("\n" if removed else ""), encoding="utf-8")

    print("Записано %d страниц + Home.md + _Sidebar.md в %s"
          % (len(PAGES), out_dir))
    if removed:
        print("Удалено устаревших файлов: %d" % len(removed))
    return check(out_dir)


if __name__ == "__main__":
    sys.exit(main())