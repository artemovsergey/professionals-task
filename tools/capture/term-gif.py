"""Гифка терминала для вики: настоящая команда → настоящий вывод → GIF.

Зачем. На страницах вики шаг «выполните команду» хочется показать движением:
как команда набирается, как печатается ответ. Снимать окно консоли на этой
машине ненадёжно — окно уходит на второй план, шрифт зависит от темы, а
человек за машиной может открыть своё. Поэтому скрипт запускает команду
по-настоящему, забирает её вывод и рисует кадры сам.

Вывод не придумывается: командная строка, ответ базы и текст ошибки — те
самые байты, что вернула программа. Анимируется только появление текста.

Запуск:
    python tools/capture/term-gif.py --manifest tools/capture/term-gifs.json

Элемент манифеста — тот же, что у term-shot.py, плюс необязательные
`max_lines` и `expect_failure`:
    { "name": "07-schema-run",
      "title": "psql — создание схемы",
      "command": ["psql", "-h", "127.0.0.1", "-U", "toirprof", "-d", "toirprof", "-f", "db/schema.sql"],
      "env": { "PGPASSWORD": "toirprof" },
      "max_lines": 24 }
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent

# term-shot.py и make-gifs.py названы с дефисом (так удобнее запускать из
# консоли), поэтому обычный import их не берёт — загружаем по пути.
def _load(module_name: str, file_name: str):
    spec = importlib.util.spec_from_file_location(module_name, TOOLS / file_name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


term = _load("term_shot", "term-shot.py")

FRAME_SECONDS = 0.9  # сколько кадр висит в браузере
REVEAL_FRAMES = 7    # на сколько порций делим вывод
TYPE_STEP = 8        # сколько символов команды появляется за кадр
TYPE_LIMIT = 120     # длинные команды не «печатаем» — кадров будет слишком много


def common_size(frames):
    """Кадры разной высоты приводим к общему размеру — так требует GIF."""
    width = max(f.width for f in frames)
    height = max(f.height for f in frames)
    return width, height


def pad(frame, width, height):
    """Дополняет кадр фоном терминала до общего размера."""
    if frame.size == (width, height):
        return frame
    canvas = Image.new("RGB", (width, height), term.BACKGROUND)
    canvas.paste(frame, (0, 0))
    return canvas


def build_frames(item, tmp_dir):
    """Снимает команду и возвращает список кадров GIF.

    term.render() рисует кадр и сохраняет его на диск, возвращая только
    размер, поэтому каждый кадр сразу читаем обратно — иначе пришлось бы
    угадывать порядок файлов в каталоге.
    """
    lines, code = term.run(item)
    failed = code != 0 and not item.get("expect_failure")
    max_lines = item.get("max_lines", 24)
    shown_total = min(len(lines), max_lines)

    title = item.get("title", item["name"])
    command = item["command"]
    as_text = command if isinstance(command, str) else None

    images = []
    counter = 0

    def shoot(command_value, visible_lines):
        """Рисует кадр и возвращает его как картинку."""
        nonlocal counter
        counter += 1
        path = tmp_dir / ("frame%04d.png" % counter)
        term.render(title, command_value, item.get("sql"), visible_lines,
                    failed, path, max_lines)
        return Image.open(path).convert("RGB")

    # 1. Набор команды. Для списка argv набор показывать нечего — там
    # готовая строка вызова. Длинные командыPowerShell тоже не печатаем
    # посимвольно: на полторы тысячи знаков вышло бы двести кадров и
    # гифка на мегабайт.
    if as_text and len(" ".join(as_text.split())) <= TYPE_LIMIT:
        flat = " ".join(as_text.split())
        for end in range(TYPE_STEP, len(flat) + 1, TYPE_STEP):
            images.append(shoot(flat[:end], []))
    images.append(shoot(command, []))

    # 2. Появление вывода порциями: не больше REVEAL_FRAMES кадров.
    if shown_total:
        step = max(1, -(-shown_total // REVEAL_FRAMES))
        revealed = 0
        while revealed < shown_total:
            revealed = min(shown_total, revealed + step)
            images.append(shoot(command, lines[:revealed]))

    if len(images) < 2:
        images.append(shoot(command, lines[:shown_total]))

    return images, failed


def main() -> int:
    parser = argparse.ArgumentParser(description="Гифки терминала для вики")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", default="wiki/gifs")
    parser.add_argument("--only", nargs="*")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
    out_dir = REPO / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = REPO / "wiki" / "_gif_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    done, failed = 0, []

    for item in manifest:
        name = item["name"]
        if args.only and name not in args.only:
            continue
        try:
            for stale in tmp_dir.glob("*.png"):
                stale.unlink()
            frames, is_failed = build_frames(item, tmp_dir)
            if len(frames) < 2:
                frames = frames * 2
            width, height = common_size(frames)
            frames = [pad(f, width, height) for f in frames]

            # Тёмное окно терминала с мелким текстом сжимается плохо:
            # если файл вышел тяжёлым, снижаем ширину и число цветов.
            target = out_dir / f"{name}.gif"
            for gif_width, colors in ((width, 128), (880, 96), (800, 64)):
                prepared = []
                for frame in frames:
                    image = frame
                    if image.width != gif_width:
                        height_px = round(image.height * gif_width / image.width)
                        image = image.resize((gif_width, height_px), Image.LANCZOS)
                    prepared.append(image.quantize(colors=colors))
                prepared[0].save(target, save_all=True, append_images=prepared[1:],
                                 duration=int(FRAME_SECONDS * 1000), loop=0,
                                 optimize=True, disposal=2)
                if target.stat().st_size <= 320 * 1024:
                    break

            print("OK   %s.gif  кадров=%d  %dx%d  %.1f КБ%s"
                  % (name, len(frames), gif_width, prepared[0].height,
                     target.stat().st_size / 1024.0,
                     "  (ошибка команды — так и задумано)" if is_failed else ""))
            done += 1
        except Exception as error:  # noqa: BLE001 — снимаем любую беду и идём дальше
            failed.append(f"{name}: {error}")

    for stale in tmp_dir.glob("*.png"):
        stale.unlink()
    try:
        tmp_dir.rmdir()
    except OSError:
        pass

    for message in failed:
        print("FAIL " + message, file=sys.stderr)
    print("\nЗаписано: %d, ошибок: %d" % (done, len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
