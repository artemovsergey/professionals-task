#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Захват экрана в PNG и GIF для вики «ТОиР-Проф».

Снимки нужны для двух вещей:

* `wiki/images/NN-<slug>.png` — статичная иллюстрация к шагу;
* `wiki/gifs/NN-<slug>.gif` — короткая запись того, как выполнялась команда.

Зависимости: pillow, numpy. ffmpeg не нужен — GIF собирается самим Pillow.

Примеры:

    # 8 секунд записи экрана, 8 кадров в секунду
    python3 tools/capture/rec.py --name 07-schema-run --seconds 8

    # один кадр (для скриншота окна или терминала)
    python3 tools/capture/rec.py --name 07-schema-equipment --single

    # ограниченная область 1280x800 + левый верхний угол
    python3 tools/capture/rec.py --name 07-dbeaver --single --region 0 0 1280 800

Код возврата: 0 — снимок сделан, 1 — ошибка (нет Pillow, нет дисплея,
неверные аргументы).
"""

import argparse
import os
import sys
import time

try:
    from PIL import Image, ImageGrab
except ImportError:  # pragma: no cover - зависит от окружения
    print(
        "Ошибка: не установлен Pillow.\n"
        "  python3 -m pip install --user pillow numpy",
        file=sys.stderr,
    )
    sys.exit(1)


# Ширина, до которой кадр ужимается перед сохранением.
# 960 px — компромисс между читаемостью и размером файла:
# страница вики открывается и в браузере на ноутбуке, и в режиме правки.
TARGET_WIDTH = 960

# Кадры ниже этой разницы считаются одинаковыми и не пишутся в GIF.
# Без этого гифка получается в разы больше той же записи без экрана.
MIN_FRAME_DIFF = 2.0

# Имя фильтра передискретизации изменилось в Pillow 10:
# Image.ANTIALIAS стал Image.LANCZOS. Поддерживаем обе версии,
# иначе скрипт падает на РедОС со старым пакетом pillow.
_RESAMPLING = getattr(Image, "Resampling", Image)
RESAMPLE = getattr(_RESAMPLING, "LANCZOS", getattr(_RESAMPLING, "ANTIALIAS", 1))


def wiki_dirs(out_dir):
    """Создаёт каталоги images и gifs и возвращает их путями."""
    images = os.path.join(out_dir, "images")
    gifs = os.path.join(out_dir, "gifs")
    for path in (images, gifs):
        os.makedirs(path, exist_ok=True)
    return images, gifs


def fit_width(image):
    if image.width <= TARGET_WIDTH:
        return image
    height = round(image.height * TARGET_WIDTH / image.width)
    return image.resize((TARGET_WIDTH, height), RESAMPLE)


def grab(region):
    """Снимок экрана. region = (left, top, right, bottom) либо None."""
    try:
        if region is None:
            shot = ImageGrab.grab()
        else:
            shot = ImageGrab.grab(bbox=region)
    except Exception as error:  # нет дисплея, нет прав, Wayland без портала
        print(
            "Ошибка: не удалось снять экран (%s).\n"
            "На РедОС проверьте, что запущена графическая сессия (DISPLAY=%s) "
            "и что процесс запущен не из-под sudo." % (error, os.environ.get("DISPLAY", "<пусто>")),
            file=sys.stderr,
        )
        sys.exit(1)
    if shot.width == 1 and shot.height == 1:
        print(
            "Ошибка: снимок получился пустым (1x1). "
            "Похоже, нет доступа к дисплею — запустите из графической сессии.",
            file=sys.stderr,
        )
        sys.exit(1)
    return fit_width(shot.convert("RGB"))


def frame_diff(left, right):
    """Средняя разница кадров в процентах яркости."""
    small = left.resize((64, 36))
    a = small.convert("L").tobytes()
    b = right.convert("L").tobytes()
    total = sum(abs(x - y) for x, y in zip(a, b))
    return total * 100.0 / (len(a) * 255.0)


def save_single(image, name, out_dir):
    images, _ = wiki_dirs(out_dir)
    path = os.path.join(images, "%s.png" % name)
    image.save(path, "PNG", optimize=True)
    print(path)
    return path


def record(name, seconds, fps, out_dir, region, delay):
    images, gifs = wiki_dirs(out_dir)
    interval = 1.0 / fps

    frames = []
    previous = None
    deadline = time.time() + seconds

    print("Запись %d с, %d кадр/с. Нажмите Ctrl+C для остановки." % (seconds, fps), file=sys.stderr)
    try:
        while time.time() < deadline:
            shot = grab(region)
            if previous is None or frame_diff(previous, shot) >= MIN_FRAME_DIFF:
                frames.append(shot)
                previous = shot
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nОстановлено по Ctrl+C, сохраняю кадры.", file=sys.stderr)

    if not frames:
        print("Ошибка: запись пуста — экран не менялся.", file=sys.stderr)
        sys.exit(1)

    gif_path = os.path.join(gifs, "%s.gif" % name)
    png_path = os.path.join(images, "%s.png" % name)

    # Первый кадр — эталон размера: окно могло открыться позже и изменить
    # размер, приведение остальных кадров к нему иначе ломает анимацию.
    width, height = frames[0].size
    frames = [f if f.size == (width, height) else f.resize((width, height), RESAMPLE) for f in frames]

    duration_ms = max(20, int(round(1000.0 / fps)))
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )
    frames[-1].save(png_path, "PNG", optimize=True)

    print("Кадров: %d, gif: %.1f КБ, png: %.1f КБ"
          % (len(frames),
             os.path.getsize(gif_path) / 1024.0,
             os.path.getsize(png_path) / 1024.0))
    print(gif_path)
    print(png_path)


def parse_region(value):
    if not value:
        return None
    parts = [int(p) for p in value.replace("x", ",").replace(" ", ",").split(",") if p != ""]
    if len(parts) != 4:
        print("Ошибка: --region ожидает четыре числа: left top right bottom", file=sys.stderr)
        sys.exit(1)
    if parts[2] <= parts[0] or parts[3] <= parts[1]:
        print("Ошибка: правый нижний угол должен быть правее и ниже левого верхнего", file=sys.stderr)
        sys.exit(1)
    return tuple(parts)


def main():
    parser = argparse.ArgumentParser(description="Захват экрана в PNG и GIF")
    parser.add_argument("--name", required=True,
                        help="имя файла без каталога и расширения, например 07-schema-run")
    parser.add_argument("--out", default=None,
                        help="корень wiki (по умолчанию каталог wiki рядом с репозиторием)")
    parser.add_argument("--seconds", type=float, default=8.0, help="длительность записи в секундах")
    parser.add_argument("--fps", type=int, default=8, help="кадров в секунду")
    parser.add_argument("--delay", type=float, default=0.0,
                        help="пауза перед стартом записи, чтобы успеть открыть нужное окно")
    parser.add_argument("--region", default=None,
                        help="область съёмки: left top right bottom")
    parser.add_argument("--single", action="store_true",
                        help="снять один кадр и сохранить только PNG")
    args = parser.parse_args()

    if os.path.basename(args.name) != args.name:
        print("Ошибка: --name не должно содержать путь и расширение.", file=sys.stderr)
        sys.exit(1)

    out_dir = args.out or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "wiki")

    if args.fps < 1 or args.fps > 30:
        print("Ошибка: --fps должен быть от 1 до 30.", file=sys.stderr)
        sys.exit(1)

    region = parse_region(args.region)

    if args.single:
        save_single(grab(region), args.name, out_dir)
        return

    if args.seconds <= 0 or args.seconds > 120:
        print("Ошибка: --seconds должен быть от 0 до 120.", file=sys.stderr)
        sys.exit(1)

    if args.delay > 0:
        print("Пауза %.1f с… запустите, что нужно снять." % args.delay, file=sys.stderr)
        time.sleep(args.delay)

    record(args.name, args.seconds, args.fps, out_dir, region, args.delay)


if __name__ == "__main__":
    main()