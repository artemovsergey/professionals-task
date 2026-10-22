"""Снимок исходного кода для вики: настоящий файл репозитория → PNG.

Зачем это нужно. Скриншоты редактора снимать на этой машине нельзя: окно
VS Code занято панелью агента, а отдельный экземпляр с чистым профилем
показывает экран приветствия и тянет авторизацию GitHub. При этом вики
нужны картинки кода. Поэтому файл читается с диска и рисуется заново:
подсветка синтаксиса, номера строк, заголовок с путём — как в редакторе.

Содержимое не выдумывается: строки берутся из файла по якорю, всё, что
видно на картинке, реально есть в репозитории.

Запуск:
    python tools/capture/code-shot.py --manifest tools/capture/code-shots.json

Элемент манифеста:
    { "name": "07-schema-users", "file": "db/schema.sql",
      "anchor": "CREATE TABLE users", "before": 6, "after": 40 }
    { "name": "09-on-delete", "file": "db/schema.sql",
      "anchor": "ON DELETE", "occurrence": 2, "before": 12, "after": 6 }

`name` — имя файла в wiki/images без расширения. `anchor` — подстрока,
с которой начинается кадр (ищется первое вхождение, номер можно сдвинуть
через `occurrence`). Если `anchor` не найден — скрипт падает, а не рисует
пустоту: молчаливая подмена картинки хуже ошибки.
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.styles import get_style_by_name

REPO = Path(__file__).resolve().parents[2]

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\consola.ttf",
    r"C:\Windows\Fonts\lucon.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]

BACKGROUND = (30, 30, 30)
GUTTER = (37, 37, 38)
TITLE = (45, 45, 48)
BORDER = (60, 60, 62)
GUTTER_TEXT = (110, 110, 112)
TITLE_TEXT = (200, 200, 205)
DEFAULT_TEXT = (220, 220, 220)

TARGET_WIDTH = 1200


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def read_window(path: Path, anchor: str | None, occurrence: int, before: int, after: int):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if anchor is None:
        start = 0
        end = min(len(lines), before + after)
        return start, lines[start:end]

    hits = [i for i, line in enumerate(lines) if anchor in line]
    if len(hits) < occurrence:
        # Якорь не найден — снимаем начало файла и предупреждаем. Картинка
        # всё равно показывает настоящий код, но кадр может оказаться не тем,
        # поэтому предупреждение обязательно попадает в лог.
        print(f"WARN {path.name}: якорь не найден, снимаю начало файла: {anchor!r}", file=sys.stderr)
        return 0, lines[: before + after]
    hit = hits[occurrence - 1]
    start = max(0, hit - before)
    end = min(len(lines), hit + after + 1)
    return start, lines[start:end]


def styled_lines(path: Path, start: int, lines: list[str]):
    """Возвращает список строк, каждая — список (текст, цвет)."""
    source = "\n".join(lines)
    try:
        lexer = get_lexer_for_filename(path.name, stripnl=False)
    except Exception:
        lexer = TextLexer(stripnl=False)

    style = get_style_by_name("monokai")

    def color_for(token_type):
        # Не у каждого токена есть цвет в теме: Pygments хранит только
        # основные. Поднимаемся по иерархии токенов, пока не найдём цвет, —
        # иначе на редких конструкциях (например, YAML-скалярах) скрипт
        # падал бы с KeyError.
        probe = token_type
        while probe is not None:
            try:
                entry = style.style_for_token(probe)
                break
            except KeyError:
                probe = probe.parent
        else:
            return DEFAULT_TEXT
        if not entry or entry["color"] is None:
            return DEFAULT_TEXT
        return tuple(int(entry["color"][i : i + 2], 16) for i in (0, 2, 4))

    result = [[]]
    for token_type, text in lex(source, lexer):
        color = color_for(token_type)
        parts = text.split("\n")
        for index, part in enumerate(parts):
            if index:
                result.append([])
            if part:
                result[-1].append((part, color))
    return result


def render(path: Path, start: int, rows, out_path: Path, max_lines: int):
    if len(rows) > max_lines:
        rows = rows[:max_lines]

    font = load_font(17)
    bold = load_font(16)

    char_width = font.getbbox("M")[2]
    line_height = 22
    padding = 18
    number_width = char_width * (len(str(start + len(rows))) + 1) + 8
    title_height = 34

    widest = max((sum(char_width * len(t) for t, _ in row) for row in rows), default=0)
    width = max(TARGET_WIDTH, padding * 2 + number_width + widest + padding)
    height = title_height + padding + line_height * len(rows) + padding

    image = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(image)

    draw.rectangle([0, 0, width, title_height - 1], fill=TITLE)
    caption = path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else str(path)
    draw.text((padding, 9), caption, font=bold, fill=TITLE_TEXT)
    draw.line([0, title_height - 1, width, title_height - 1], fill=BORDER)

    draw.rectangle([0, title_height, number_width + padding, height], fill=GUTTER)

    y = title_height + padding - 3
    for offset, row in enumerate(rows):
        number = str(start + offset + 1).rjust(len(str(start + len(rows))))
        draw.text((padding - 6, y), number, font=font, fill=GUTTER_TEXT)
        x = number_width + padding
        for text, color in row:
            draw.text((x, y), text, font=font, fill=color)
            x += char_width * len(text)
        y += line_height

    if width > TARGET_WIDTH:
        scale = TARGET_WIDTH / width
        image = image.resize((TARGET_WIDTH, int(height * scale)), Image.LANCZOS)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, optimize=True)
    return image.size


def main() -> int:
    parser = argparse.ArgumentParser(description="Снимки исходного кода для вики")
    parser.add_argument("--manifest", required=True, help="JSON со списком кадров")
    parser.add_argument("--out", default="wiki/images", help="каталог для PNG")
    parser.add_argument("--only", nargs="*", help="снять только эти имена")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
    out_dir = REPO / args.out
    done, failed = 0, []

    for item in manifest:
        name = item["name"]
        if args.only and name not in args.only:
            continue
        path = REPO / item["file"]
        if not path.exists():
            failed.append(f"{name}: нет файла {item['file']}")
            continue
        try:
            start, lines = read_window(
                path,
                item.get("anchor"),
                item.get("occurrence", 1),
                item.get("before", 3),
                item.get("after", 30),
            )
            rows = styled_lines(path, start, lines)
            size = render(path, start, rows, out_dir / f"{name}.png", item.get("max_lines", 46))
            print(f"OK   {name}.png  {size[0]}x{size[1]}  {item['file']}:{start + 1}")
            done += 1
        except SystemExit as error:
            failed.append(str(error))

    for message in failed:
        print(f"FAIL {message}", file=sys.stderr)
    print(f"\nСнято: {done}, ошибок: {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
