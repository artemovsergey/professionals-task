#!/usr/bin/env bash
#
# Опубликовать содержимое wiki/ в GitHub Wiki репозитория задания.
#
# GitHub Wiki — отдельный git-репозиторий (repo.wiki.git), поэтому
# содержимое папки wiki/ нужно скопировать в клон вики и запушить отдельно.
#
# Использование:
#   ./tools/publish-wiki.sh                  # запушить в wiki ветки main
#   ./tools/publish-wiki.sh --dry-run        # только показать, что изменится
#   GITHUB_TOKEN=<token> ./tools/publish-wiki.sh   # если нет credential helper
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

cleanup() { rm -rf "$WORK_DIR"; [ -n "${ASKPASS_FILE:-}" ] && rm -f "$ASKPASS_FILE"; }
trap cleanup EXIT

# Если задан GITHUB_TOKEN, делаем askpass-помощник: секрет не попадает
# ни в аргументы команд, ни в вывод. Иначе работает обычный
# credential helper git (credential.store, credential.env и т.п.).
GIT_ENV=()
if [ -n "${GITHUB_TOKEN:-}" ]; then
  ASKPASS_FILE="$WORK_DIR/askpass.sh"
  cat > "$ASKPASS_FILE" <<'ASKPASS'
#!/bin/sh
case "$1" in
  *sername*) printf '%s' "x-access-token" ;;
  *assword*)  printf '%s' "$GITHUB_TOKEN" ;;
esac
ASKPASS
  chmod 700 "$ASKPASS_FILE"
  export GIT_ASKPASS="$ASKPASS_FILE"
  export GIT_TERMINAL_PROMPT=0
  export GITHUB_TOKEN
fi

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

# Ветка по умолчанию у вики — та, на которую указывает origin/HEAD.
# Обычно это master, а не main, и пушить в неё обязательно:
# GitHub показывает страницы именно из ветки по умолчанию.
DEFAULT_BRANCH="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || true)"
DEFAULT_BRANCH="${DEFAULT_BRANCH#origin/}"

if [ -z "$DEFAULT_BRANCH" ]; then
  DEFAULT_BRANCH="main"
fi

git checkout --quiet "$DEFAULT_BRANCH" 2>/dev/null || git checkout --quiet -b "$DEFAULT_BRANCH"

echo "==> Ветка вики по умолчанию: $DEFAULT_BRANCH"

# Коммит в вики делаем от того же автора, что и в основном репозитории,
# иначе git не сможет определить автора и коммит упадёт.
AUTHOR_NAME="$(git -C "$PROJECT_DIR" config user.name 2>/dev/null || true)"
AUTHOR_EMAIL="$(git -C "$PROJECT_DIR" config user.email 2>/dev/null || true)"

if [ -z "$AUTHOR_NAME" ] || [ -z "$AUTHOR_EMAIL" ]; then
  cat >&2 <<'MSG'
Ошибка: в исходном репозитории не настроен автор коммита.

Задайте его и повторите:
  git config user.name "Имя"
  git config user.email "почта@example.ru"
MSG
  exit 1
fi

git config user.name "$AUTHOR_NAME"
git config user.email "$AUTHOR_EMAIL"

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
git push origin "HEAD:$DEFAULT_BRANCH"

echo
echo "Готово: https://github.com/artemovsergey/professionals-task/wiki"
