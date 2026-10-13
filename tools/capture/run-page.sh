#!/usr/bin/env bash
#
# Выполнить команду шага и снять терминал для вики.
#
# Скрипт делает три вещи:
#   1. запускает команду из аргументов, сохраняя вывод в журнал;
#   2. по завершении снимает один кадр экрана в wiki/images/<имя>.png;
#   3. печатает, что именно нужно вписать в страницу вики.
#
# Запись гифки в реальном времени делает rec.py — этот скрипт только
# для статичных снимков после команды и для прогона подряд нескольких шагов.
#
# Использование:
#   ./tools/capture/run-page.sh <имя> <команда> [аргументы...]
#
# Примеры:
#   ./tools/capture/run-page.sh 07-schema-run psql -h 127.0.0.1 -U toirprof -d toirprof -f db/schema.sql
#   ./tools/capture/run-page.sh 12-api-start dotnet run --project src/api/ToirProf.Api.csproj
#
# Переменные окружения:
#   WIKI_DIR   каталог wiki (по умолчанию вычисляется от расположения скрипта)
#   NO_SHOT    если задано, снимок экрана не делается
#   REC        команда захвата кадра, по умолчанию python3 tools/capture/rec.py

set -euo pipefail

if [ $# -lt 2 ]; then
  cat >&2 <<'MSG'
Использование: run-page.sh <имя-файла-без-расширения> <команда> [аргументы...]

Пример:
  ./tools/capture/run-page.sh 07-schema-run psql -f db/schema.sql
MSG
  exit 1
fi

NAME="$1"
shift

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
WIKI_DIR="${WIKI_DIR:-$PROJECT_DIR/wiki}"
REC="${REC:-python3 $SCRIPT_DIR/rec.py}"

if [ -z "${NAME##*[!0-9a-zA-Z_-]*}" ]; then
  echo "Ошибка: имя '$NAME' содержит недопустимые символы." >&2
  echo "Разрешены латинские буквы, цифры, дефис и подчёркивание." >&2
  exit 1
fi

mkdir -p "$WIKI_DIR/images" "$WIKI_DIR/gifs"

echo "==> $NAME"
echo "--- команда: $* ---"

set +e
"$@"
STATUS=$?
set -e

echo "--- код возврата: $STATUS ---"

if [ "$STATUS" -ne 0 ]; then
  cat >&2 <<MSG
Команда завершилась с кодом $STATUS. Снимок всё равно сделан —
он покажет текст ошибки, а страница вики как раз для этого раздела
«Если что-то не получилось».
MSG
fi

if [ -z "${NO_SHOT:-}" ]; then
  echo "==> снимок экрана"
  # shellcheck disable=SC2086
  $REC --name "$NAME" --out "$WIKI_DIR" --single || {
    echo "Предупреждение: снимок не сделан. Проверьте, что есть графическая" >&2
    echo "сессия и установлен pillow: python3 -m pip install --user pillow" >&2
  }
fi

cat <<MSG

Готово. Впишите в страницу вики:

  ![описание](images/$NAME.png)
  *подпись: что видно на снимке*

Для гифки запустите запись заранее и повторите команду вручную:

  python3 tools/capture/rec.py --name $NAME --seconds 10
MSG

exit "$STATUS"