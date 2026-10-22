"""Снимок терминала для вики: настоящая команда → настоящий вывод → PNG.

Зачем это нужно. Вики показывает шаги работы с базой и командной строкой.
Снимать окно консоли на этой машине ненадёжно (окно уходит на второй план,
шрифт зависит от темы), а показать нужно именно то, что печатает psql или
dotnet. Поэтому скрипт запускает команду по-настоящему, забирает её вывод
и рисует его как окно терминала: строка приглашения, команда, результат.

Вывод не придумывается: если команда упала, на картинке будет её настоящая
ошибка — как раз это и требуется для кадров «как база отвергает дубликат».

Запуск:
    python tools/capture/term-shot.py --manifest tools/capture/term-shots.json

Элемент манифеста:
    { "name": "08-unique-violation",
      "title": "psql — попытка вставить дубликат",
      "command": ["psql", "-h", "127.0.0.1", "-U", "toirprof", "-d", "toirprof",
                  "-c", "INSERT INTO ..."],
      "env": { "PGPASSWORD": "toirprof" },
      "max_lines": 30 }

Если `command` — строка, она выполняется через PowerShell (для dotnet, git
и прочих команд, которым нужен интерпретатор).
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\consola.ttf",
    r"C:\Windows\Fonts\lucon.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]

BACKGROUND = (12, 12, 12)
TITLE = (45, 45, 48)
BORDER = (60, 60, 62)
TITLE_TEXT = (200, 200, 205)
PROMPT = (120, 200, 120)
COMMAND = (235, 235, 235)
OUTPUT = (200, 200, 200)
ERROR = (235, 120, 110)
MUTED = (130, 130, 130)

TARGET_WIDTH = 1200


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def run(item: dict) -> tuple[list[tuple[str, tuple]], int]:
    """Выполняет команду и возвращает (строки вывода, код возврата)."""
    command = item["command"]
    env = os.environ.copy()
    env.update({k: str(v) for k, v in item.get("env", {}).items()})
    env.setdefault("PGCLIENTENCODING", "UTF8")

    payload = None

    if isinstance(command, str):
        argv = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command]
    else:
        argv = command

    # SQL передаём потоком на вход psql. Причина: кириллица в аргументах
    # командной строки на Windows доезжает до psql в кодировке консоли
    # (cp866), и он отвечает «неверная последовательность байт для кодировки
    # UTF8». Через stdin байты приходят ровно те, что мы записали.
    if item.get("sql") is not None:
        payload = item["sql"].encode("utf-8")
        if "-f" not in argv:
            argv = argv + ["-f", "-"]

    completed = subprocess.run(
        argv,
        cwd=str(REPO / item.get("cwd", ".")),
        env=env,
        input=payload,
        capture_output=True,
        timeout=item.get("timeout", 120),
    )

    raw = completed.stdout + completed.stderr
    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n")
    lines = [line for line in text.split("\n")]
    while lines and not lines[-1].strip():
        lines.pop()
    return lines, completed.returncode


def render(
    title: str,
    command: list[str] | str,
    command_sql: str | None,
    lines: list,
    failed: bool,
    out_path: Path,
    max_lines: int,
):
    font = load_font(16)
    bold = load_font(15)
    char_width = font.getbbox("M")[2]
    line_height = 21
    padding = 16
    title_height = 34

    shown = lines[:max_lines]
    truncated = len(lines) - len(shown)

    prompt_text = "psql> " if command_sql else "$ "
    if command_sql:
        command_text = command_sql.strip().splitlines()[0]
        if len(command_sql.strip().splitlines()) > 1:
            command_text += " …"
    else:
        if isinstance(command, str):
            first_line = command.strip().splitlines()[0]
            command_text = first_line + (" …" if len(command.strip().splitlines()) > 1 else "")
        else:
            command_text = subprocess.list2cmdline(command)

    longest = max([len(prompt_text) + len(command_text)] + [len(line) for line in shown])
    width = max(TARGET_WIDTH, padding * 2 + char_width * longest + padding)
    height = title_height + padding + line_height * (1 + len(shown) + (1 if truncated else 0)) + padding

    image = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(image)

    draw.rectangle([0, 0, width, title_height - 1], fill=TITLE)
    draw.text((padding, 9), title, font=bold, fill=TITLE_TEXT)
    draw.line([0, title_height - 1, width, title_height - 1], fill=BORDER)

    y = title_height + padding - 3
    x = padding
    draw.text((x, y), prompt_text, font=font, fill=PROMPT)
    x += char_width * len(prompt_text)
    draw.text((x, y), command_text, font=font, fill=COMMAND)
    y += line_height

    for line in shown:
        draw.text((padding, y), line, font=font, fill=ERROR if failed else OUTPUT)
        y += line_height

    if truncated:
        draw.text((padding, y), f"… ещё строк: {truncated}", font=font, fill=MUTED)

    if width > TARGET_WIDTH:
        scale = TARGET_WIDTH / width
        image = image.resize((TARGET_WIDTH, int(height * scale)), Image.LANCZOS)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, optimize=True)
    return image.size


def main() -> int:
    parser = argparse.ArgumentParser(description="Снимки терминала для вики")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", default="wiki/images")
    parser.add_argument("--only", nargs="*")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
    out_dir = REPO / args.out
    done, failed = 0, []

    for item in manifest:
        name = item["name"]
        if args.only and name not in args.only:
            continue
        try:
            lines, code = run(item)
            size = render(
                item.get("title", name),
                item["command"],
                item.get("sql"),
                lines,
                code != 0 and not item.get("expect_failure"),
                out_dir / f"{name}.png",
                item.get("max_lines", 34),
            )
            print(f"OK   {name}.png  {size[0]}x{size[1]}  код={code}  строк={len(lines)}")
            done += 1
        except Exception as error:  # noqa: BLE001 — снимаем любую беду и идём дальше
            failed.append(f"{name}: {error}")

    for message in failed:
        print(f"FAIL {message}", file=sys.stderr)
    print(f"\nСнято: {done}, ошибок: {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
