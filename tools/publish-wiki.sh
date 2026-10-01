#!/usr/bin/env bash
#
# Опубликовать содержимое wiki/ в GitHub Wiki репозитория задания.
#
# GitHub Wiki — отдельный git-репозиторий (repo.wiki.git), поэтому
# содержимое папки wiki/ нужно скопировать в клон вики и запушить отдельно.
#
# Использование:
#   ./tools/publish-wiki.sh              # запушить в wiki ветки main
#   ./tools/publish-wiki.sh --dry-run    # только показать, что изменится
#
# Требуется: git, доступ на запись в репозиторий задания.

set -euo pipefail

REPO_URL="https://github.com/artemovsergey/professionals-task.git"
WIKI_URL="https://github.com/artemovsergey/professionals-task.wiki.git"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
WIKI_SRC="$PROJECT_DIR/wiki"
WORK_DIR="$(mktemp -d)"
DRY_RUN=false

if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=true
fi

if [ ! -d "$WIKI_SRC" ]; then
  echo "Ошибка: папка $WIKI_SRC не найдена" >&2
  exit 1
fi

cleanup() { rm -rf "$WORK_DIR"; }
trap cleanup EXIT

echo "==> Клонирую wiki в $WORK_DIR"
if ! git clone --quiet "$WIKI_URL" "$WORK_DIR/wiki" 2>/dev/null; then
  cat >&2 <<'MSG'
Ошибка: wiki-репозиторий недоступен.

Скорее всего, wiki ещё не создан. GitHub создаёт его вручную:
  1. Откройте https://github.com/artemovsergey/professionals-task/wiki
  2. Нажмите «Create the first page»
  3. Назовите её Home и сохраните
  4. Запустите этот скрипт снова
MSG
  exit 1
fi

cd "$WORK_DIR/wiki"
git checkout --quiet main 2>/dev/null || git checkout --quiet master

echo "==> Копирую страницы из wiki/"
# Удаляем только .md, чтобы не потерять .git и служебные файлы вики
find . -maxdepth 1 -name '*.md' -delete
cp "$WIKI_SRC"/*.md .

echo "==> Изменения:"
git status --short

if [ "$DRY_RUN" = true ]; then
  echo
  echo "Режим --dry-run: ничего не коммичу и не пушу."
  exit 0
fi

if git diff --quiet --cached 2>/dev/null && [ -z "$(git status --porcelain)" ]; then
  echo "Изменений нет — wiki уже актуальна."
  exit 0
fi

git add -A
git commit -m "Wiki отбора: 28 страниц по сессиям (сессии 0–9)"

echo "==> Пушу"
git push origin HEAD:main

echo
echo "Готово: https://github.com/artemovsergey/professionals-task/wiki"
