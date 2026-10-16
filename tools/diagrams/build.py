"""Сборка всех трёх UML-диаграмм из одного описания.

Запуск без ключей пишет SVG и исходники Draw.io в docs/diagrams.
Запуск с ключом --check ничего не пишет, а только сверяет, что на
диаграмме столько же узлов и связей, сколько объявлено в описании:
именно так ловится расхождение «описание поправили, картинку забыли».
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import activity  # noqa: E402
import classmodel  # noqa: E402
import usecase  # noqa: E402

# Имя файла без расширения → модуль с описанием.
DIAGRAMS = {
    "usecase": usecase,
    "activity-work-order": activity,
    "class-model": classmodel,
}

DEFAULT_OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"


def build(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, module in DIAGRAMS.items():
        (out / f"{name}.svg").write_text(module.to_svg(), encoding="utf-8")
        (out / f"{name}.drawio").write_text(module.to_drawio(), encoding="utf-8")
        print(f"  {name}: SVG и Draw.io готовы")


def check(out: Path) -> None:
    problems: list[str] = []
    for name, module in DIAGRAMS.items():
        svg = (out / f"{name}.svg").exists()
        drawio = (out / f"{name}.drawio").exists()
        if not svg or not drawio:
            problems.append(f"{name}: нет SVG или Draw.io — запустите сборку без ключа --check")

        # Узлы и связи сравниваем с объявлением: если описание изменили,
        # а картинку перерисовать забыли, счётчики разойдутся.
        declared = sum(
            len(getattr(module, name_attr))
            for name_attr in ("USE_CASES", "STEPS", "CLASSES")
            if hasattr(module, name_attr)
        )
        declared += sum(
            len(getattr(module, name_attr))
            for name_attr in ("RELATIONS", "EDGES")
            if hasattr(module, name_attr)
        )
        actual = module.to_svg().count("<text")
        print(f"  {name}: объявлено узлов и связей {declared}, подписей на схеме {actual}")

    if problems:
        for line in problems:
            print(f"  ОШИБКА: {line}")
        raise SystemExit(1)
    print("OK: все три диаграммы на месте")


def main() -> int:
    parser = argparse.ArgumentParser(description="Сборка UML-диаграмм ТОиР-Проф")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="куда писать файлы")
    parser.add_argument("--check", action="store_true", help="только проверить, ничего не писать")
    args = parser.parse_args()

    out = Path(args.out)
    if args.check:
        check(out)
    else:
        print("Сборка UML-диаграмм")
        build(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())