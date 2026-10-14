"""Разовая подсказка: печатает публичные члены вьюмодели.

Нужен, когда пишется разметка экрана и надо точно знать имена свойств
и команд, — иначе опечатка в Binding обнаружится только на запуске.
"""
import re
import sys
from pathlib import Path

target = Path(sys.argv[1])
text = target.read_text(encoding="utf-8")

print("=== поля [ObservableProperty] / [RelayCommand] ===")
for m in re.finditer(r"\[(ObservableProperty|RelayCommand[^\]]*)\]", text):
    tail = text[m.end(): m.end() + 400]
    fields = re.findall(r"private\s+[\w\.<>\?\[\]]+\s+(_?\w+)\s*(?:=|;|\{)", tail)
    if fields:
        name = fields[0]
        kind = "Observable" if m.group(1) == "ObservableProperty" else "Command"
        generated = name.lstrip("_")
        print(f"  {kind}: поле {name} -> свойство {generated}")

print("=== публичные свойства и методы ===")
for m in re.finditer(
    r"^\s*public\s+(?:static\s+)?(?:readonly\s+)?(?:sealed\s+)?"
    r"([\w\.<>\?\[\]]+)\s+(\w+)\s*(\{|\(|=>|;)",
    text,
    re.MULTILINE,
):
    print(f"  {m.group(1)} {m.group(2)}")

print("=== коллекции ===")
for m in re.finditer(r"ObservableCollection<\s*([\w\.<>\?]+)\s*>\s+(\w+)", text):
    print(f"  {m.group(2)} : ObservableCollection<{m.group(1)}>")

print("=== конструкторы ===")
for m in re.finditer(r"public\s+(\w+)\s*\(([^)]*)\)", text):
    print(f"  {m.group(1)}({m.group(2).strip()})")
