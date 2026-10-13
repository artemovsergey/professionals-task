#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка GIF из готовых PNG-кадров.

Нужен, когда кадры сняты по отдельности — например, для гифки, где нужно
показать последовательность состояний экрана: «до», «после», «ошибка».
`rec.py` так не умеет: он снимает экран в реальном времени.

Зависимость: pillow. ffmpeg не нужен.

Примеры:

    # три кадра в одну гифку по 800 мс на кадр
    python3 tools/capture/make-gifs.py shots/01-before.png shots/02-after.png \\
        -o wiki/gifs/11-func-downtime.gif --duration 800

    # ширина 960, 128 цветов, как в остальной вики
    python3 tools/capture/make-gifs.py shots/*.png -o wiki/gifs/33-lifecycle.gif

Код возврата: 0 — gif записан, 1 — ошибка (нет Pillow, нет кадров,
кадры разного размера и не удалось привести к общему).
"""

import argparse
import glob
import os
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover - зависит от окружения
    print(
        "Ошибка: не установлен Pillow.\n"
        "  python3 -m pip install --user pillow",
        file=sys.stderr,
    )
    sys.exit(1)


# Ширина гифки. Совпадает с TARGET_WIDTH в rec.py, иначе картинки
# на одной странице прыгают по размеру при переходе между шагами.
DEFAULT_WIDTH = 960

# 256 цветов — максимум для GIF. Меньше не нужно: интерфейс со сглаженным
# текстом и так ужимается палитрой, а гифка растёт.
DEFAULT_COLORS = 256

# Имя фильтра передискретизации переехало в Image.Resampling в Pillow 10.
# Берём через getattr, иначе скрипт падает на РедОС со старым пакетом.
_RESAMPLING = getattr(Image, "Resampling", Image)
RESAMPLE = getattr(_RESAMPLING, "LANCZOS", getattr(_RESAMPLING, "ANTIALIAS", 1))


def resolve_paths(patterns):
    """Раскрывает списки файлов и маски в отсортированный список путей."""
    paths = []
    for pattern in patterns:
        if os.path.isfile(pattern):
            paths.append(pattern)
        else:
            matches = sorted(glob.glob(pattern))
            if not matches:
                print("Ошибка: не найдено ни одного файла по маске %s" % pattern, file=sys.stderr)
                sys.exit(1)
            paths.extend(matches)
    return paths


def load_frames(paths, width, colors):
    """Читает кадры и приводит их к общему размеру по первому кадру."""
    frames = [Image.open(path).convert("RGB") for path in paths]

    # Размер задаёт первый кадр: он же определяет пропорции всей гифки.
    if width:
        first_width, first_height = frames[0].size
        height = round(first_height * width / first_width)
        frames = [f.resize((width, height), RESAMPLE) for f in frames]
    else:
        frames = [f if f.size == frames[0].size
                  else f.resize(frames[0].size, RESAMPLE) for f in frames]

    # Общая палитра: иначе каждый кадр получает свою, и переходы
    # между ними «мерцают» разными цветами.
    # Метод квантования и дизеринг берём из Pillow по умолчанию:
    # MEDIANCUT и FLOYDSTEINBERG — это как раз значения по умолчанию,
    # поэтому результат одинаковый на Pillow 9 и на Pillow 11,
    # а перечислять константы с двумя разными именами в разных версиях не нужно.
    palette_source = frames[0].quantize(colors=colors)
    return [frame.quantize(palette=palette_source) for frame in frames]


def main():
    parser = argparse.ArgumentParser(description="Сборка GIF из PNG-кадров")
    parser.add_argument("inputs", nargs="+",
                        help="файлы PNG или маски вида shots/*.png")
    parser.add_argument("-o", "--output", required=True,
                        help="путь к итоговому gif")
    parser.add_argument("--duration", type=int, default=800,
                        help="миллисекунд на кадр (по умолчанию 800)")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH,
                        help="ширина гифки в пикселях; 0 — не менять")
    parser.add_argument("--colors", type=int, default=DEFAULT_COLORS,
                        help="цветов в палитре, 2..256")
    args = parser.parse_args()

    if len(args.inputs) < 2:
        print("Ошибка: нужно минимум два кадра.", file=sys.stderr)
        sys.exit(1)
    if args.duration < 40:
        print("Ошибка: --duration меньше 40 мс, браузеры округляют кадр до 100 мс.", file=sys.stderr)
        sys.exit(1)
    if not 2 <= args.colors <= 256:
        print("Ошибка: --colors должен быть от 2 до 256.", file=sys.stderr)
        sys.exit(1)

    paths = resolve_paths(args.inputs)
    frames = load_frames(paths, args.width, args.colors)

    out_dir = os.path.dirname(os.path.abspath(args.output))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    frames[0].save(
        args.output,
        save_all=True,
        append_images=frames[1:],
        duration=args.duration,
        loop=0,
        optimize=True,
        disposal=2,
    )

    print("Кадров: %d, размер %dx%d, %.1f КБ"
          % (len(frames), frames[0].width, frames[0].height,
             os.path.getsize(args.output) / 1024.0))
    print(args.output)


if __name__ == "__main__":
    main()