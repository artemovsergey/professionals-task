"""Снимки desktop-клиента (Avalonia) для вики: PNG и GIF прямо из окна.

Зачем отдельный инструмент. Веб снимается Playwright, а desktop-окно так не
снять. Но Avalonia отдаёт дерево доступности Windows UI Automation: кнопки,
поля и подписи видны как элементы с именами. Значит, приложение можно
провести по сценарию (вход, переход в раздел, поиск) и снять окно
через PrintWindow — без фокуса и без риска заснять чужие окна.

Запуск:
    python tools/capture/desktop-shot.py --only 27
    python tools/capture/desktop-shot.py --list

Кадры GIF собираются из тех же снимков: сцена делает несколько снимков
подряд во время действия, затем они склеиваются Pillow.
"""

import argparse
import ctypes
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

import uiautomation as auto
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
IMAGES = ROOT / "wiki" / "images"
GIFS = ROOT / "wiki" / "gifs"
EXE = ROOT / "src" / "desktop" / "bin" / "Debug" / "net10.0" / "ToirProf.Desktop.exe"

FRAME_MS = 700
GIF_WIDTH = 960

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# Без явных типов ctypes считает HWND/HDC 32-битными и падает с
# «int too long to convert» на 64-битных дескрипторах Windows.
user32.GetWindowDC.argtypes = [wintypes.HWND]
user32.GetWindowDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
user32.PrintWindow.restype = wintypes.BOOL
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetClientRect.restype = wintypes.BOOL
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = wintypes.BOOL
user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
user32.ClientToScreen.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                wintypes.UINT]
user32.SetWindowPos.restype = wintypes.BOOL
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.CreateCompatibleBitmap.restype = ctypes.c_void_p
gdi32.SelectObject.argtypes = [wintypes.HDC, ctypes.c_void_p]
gdi32.SelectObject.restype = ctypes.c_void_p
gdi32.GetDIBits.argtypes = [wintypes.HDC, ctypes.c_void_p, wintypes.UINT,
                            wintypes.UINT, ctypes.c_void_p,
                            ctypes.c_void_p, wintypes.UINT]
gdi32.GetDIBits.restype = ctypes.c_int
gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
gdi32.DeleteDC.argtypes = [wintypes.HDC]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


def grab(hwnd: int, width: int, height: int) -> Image.Image:
    """Копия окна через PrintWindow: не требует фокуса и не берёт чужие окна."""
    window_dc = user32.GetWindowDC(hwnd)
    memory_dc = gdi32.CreateCompatibleDC(window_dc)
    bitmap = gdi32.CreateCompatibleBitmap(window_dc, width, height)
    gdi32.SelectObject(memory_dc, bitmap)
    # 2 = PW_RENDERFULLCONTENT: рисует и содержимое, отрисованное GPU.
    user32.PrintWindow(hwnd, memory_dc, 2)

    info = BITMAPINFO()
    info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    info.bmiHeader.biWidth = width
    info.bmiHeader.biHeight = -height
    info.bmiHeader.biPlanes = 1
    info.bmiHeader.biBitCount = 32
    info.bmiHeader.biCompression = 0

    buffer = ctypes.create_string_buffer(width * height * 4)
    gdi32.GetDIBits(memory_dc, bitmap, 0, height, buffer,
                    ctypes.byref(info), 0)
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(memory_dc)
    user32.ReleaseDC(hwnd, window_dc)

    image = Image.frombuffer("RGB", (width, height), buffer, "raw", "BGRX", 0, 1)
    return image


def walk(control):
    """Все потомки элемента доступности: у uiautomation нет готового обхода."""
    child = control.GetFirstChildControl()
    while child:
        yield child
        yield from walk(child)
        child = child.GetNextSiblingControl()


class Desk:
    """Окно приложения и операции над ним."""

    def __init__(self, width: int = 1440, height: int = 960):
        self.process = None
        self.window = None
        self.width = width
        self.height = height

    def launch(self):
        subprocess.run(
            ["taskkill", "/IM", "ToirProf.Desktop.exe", "/F"],
            capture_output=True, check=False,
        )
        time.sleep(0.6)
        self.process = subprocess.Popen([str(EXE)], cwd=str(ROOT))
        deadline = time.time() + 25
        while time.time() < deadline:
            # auto.WindowControl(ProcessId=...) в uiautomation 2.0.29 не
            # фильтрует по процессу и возвращает чужое окно (проверено:
            # приходил Chrome). Поэтому перебираем окна верхнего уровня сами.
            for child in auto.GetRootControl().GetChildren():
                try:
                    if (child.ProcessId == self.process.pid
                            and child.ControlTypeName == "WindowControl"):
                        self.window = child
                        # Вики нужны крупные кадры: окно по умолчанию 1080×760,
                        # а на 1440×960 текст и таблицы читаются без прищура.
                        # SWP_NOMOVE|SWP_NOZORDER|SWP_NOACTIVATE = 0x0002|0x0004|0x0010
                        user32.SetWindowPos(child.NativeWindowHandle, None, 0, 0,
                                            self.width, self.height, 0x0016)
                        time.sleep(1.5)
                        return self
                except Exception:  # noqa: BLE001 — окно могло закрыться
                    continue
            time.sleep(0.5)
        raise RuntimeError("окно desktop-клиента не появилось")

    # --- поиск элементов -------------------------------------------------

    def button(self, label: str):
        """Кнопка с подписью `label`.

        У навигационных кнопок имя класса (`Avalonia.Controls.StackPanel`),
        а подпись лежит внутри Text-потомком; у обычных кнопок подпись
        попадает в Name самой кнопки. Проверяем оба варианта.
        """
        for control in walk(self.window):
            if control.ControlTypeName != "ButtonControl":
                continue
            if (control.Name or "") == label:
                return control
            for child in walk(control):
                if (child.Name or "") == label:
                    return control
        return None

    def text(self, label: str):
        for control in walk(self.window):
            if control.ControlTypeName == "TextControl" and label in (control.Name or ""):
                return control
        return None

    def edits(self):
        return [c for c in walk(self.window) if c.ControlTypeName == "EditControl"]

    # --- действия --------------------------------------------------------

    def click(self, label: str, wait: float = 1.2):
        button = self.button(label)
        if button is None:
            raise RuntimeError("кнопка не найдена: " + label)
        button.GetInvokePattern().Invoke()
        time.sleep(wait)

    def try_click(self, label: str, wait: float = 1.2) -> bool:
        """Нажимает кнопку, если она есть. Для необязательных шагов сцены."""
        button = self.button(label)
        if button is None:
            return False
        try:
            button.GetInvokePattern().Invoke()
        except Exception:  # noqa: BLE001 — кнопка может быть недоступна
            return False
        time.sleep(wait)
        return True

    def click_last(self, label: str, wait: float = 1.2) -> bool:
        """Нажимает последнюю кнопку с подписью.

        Внутри DataGrid есть свои кнопки прокрутки с именами `>`, `<`:
        они идут в дереве раньше пагинации, и обычный поиск цепляет их.
        Пагинация — последняя такая кнопка на экране.
        """
        found = [c for c in walk(self.window)
                 if c.ControlTypeName == "ButtonControl" and (c.Name or "") == label]
        if not found:
            return False
        try:
            found[-1].GetInvokePattern().Invoke()
        except Exception:  # noqa: BLE001
            return False
        time.sleep(wait)
        return True

    def toggle(self, label: str, wait: float = 1.2):
        """Переключает чекбокс по подписи."""
        for control in walk(self.window):
            if control.ControlTypeName != "CheckBoxControl":
                continue
            if label in (control.Name or ""):
                control.GetTogglePattern().Toggle()
                time.sleep(wait)
                return True
        return False

    def rows(self):
        """Строки таблиц: у DataGrid каждая запись — DataItem."""
        return [c for c in walk(self.window)
                if c.ControlTypeName in ("DataItemControl", "ListItemControl")]

    def click_row(self, index: int = 0, wait: float = 1.2) -> bool:
        """Щёлкает по строке таблицы мышью.

        DataGrid не отдаёт Invoke на строку, поэтому считаем экранные
        координаты центра строки и щёлкаем в неё. Окно перед этим
        поднимаем на передний план — иначе клик уйдёт в чужое окно.
        """
        rows = self.rows()
        if len(rows) <= index:
            return False
        user32.SetForegroundWindow(self.window.NativeWindowHandle)
        time.sleep(0.3)
        rect = rows[index].BoundingRectangle
        auto.Click(rect.xcenter(), rect.ycenter())
        time.sleep(wait)
        return True

    def fill(self, index: int, value: str):
        edit = self.edits()[index]
        edit.GetValuePattern().SetValue(value)

    def login(self, user: str, password: str):
        # После старта окно появляется раньше, чем Avalonia строит дерево
        # элементов, — ждём, пока найдутся оба поля.
        deadline = time.time() + 15
        while time.time() < deadline and len(self.edits()) < 2:
            time.sleep(0.4)

        # После изменения размера окна Avalonia перестраивает форму, и
        # первая попытка ввода может уйти в старые контролы: приложение
        # отвечает «Неверный логин или пароль». Поэтому проверяем результат
        # и при неудаче вводим заново.
        for attempt in range(3):
            self.fill(0, "")
            self.fill(1, "")
            time.sleep(0.2)
            self.fill(0, user)
            self.fill(1, password)
            time.sleep(0.2)
            self.click("Войти", wait=2.5)
            if self.button("Войти") is None:
                return
            time.sleep(1.0)

        raise RuntimeError("вход не выполнен: приложение не пустило")

    # --- съёмка ----------------------------------------------------------

    def shot(self) -> Image.Image:
        """Кадр ровно по клиентской области: без заголовка окна и рамок.

        PrintWindow отдаёт всё окно вместе с заголовком и границей, а нам
        нужен чистый прямоугольник приложения: иначе на вики кадры
        обрезаны по-разному и видно кнопки «свернуть/закрыть». Поэтому
        считаем клиентский прямоугольник (GetClientRect), его смещение
        внутри окна (ClientToScreen минус GetWindowRect) и вырезаем.
        """
        handle = self.window.NativeWindowHandle
        try:
            user32.SetForegroundWindow(handle)
            time.sleep(0.25)
        except Exception:  # noqa: BLE001 — фокус мог не переключиться
            pass

        client = wintypes.RECT()
        window_rect = wintypes.RECT()
        user32.GetClientRect(handle, ctypes.byref(client))
        user32.GetWindowRect(handle, ctypes.byref(window_rect))
        origin = wintypes.POINT(0, 0)
        user32.ClientToScreen(handle, ctypes.byref(origin))

        width = window_rect.right - window_rect.left
        height = window_rect.bottom - window_rect.top
        image = grab(handle, width, height)

        left = max(0, origin.x - window_rect.left)
        top = max(0, origin.y - window_rect.top)
        right = min(image.width, left + client.right - client.left)
        bottom = min(image.height, top + client.bottom - client.top)
        if right > left and bottom > top:
            image = image.crop((left, top, right, bottom))
        return image

    def save_png(self, name: str) -> Path:
        path = IMAGES / (name + ".png")
        self.shot().save(path, optimize=True)
        print("PNG  %s  %dx%d  %d КБ"
              % (path.name, *Image.open(path).size, path.stat().st_size // 1024))
        return path

    def save_gif(self, name: str, frames) -> Path:
        """GIF из кадров одного размера; качество — 256 цветов.

        Раньше кадры сжимались в 960 px и 128 цветов: текст на скриншотах
        desktop-клиента становился мыльным. Теперь размер кадра родной,
        а цвета снижаем только если файл перевалил за бюджет.
        """
        path = GIFS / (name + ".gif")
        width = max(frame.width for frame in frames)
        height = max(frame.height for frame in frames)
        aligned = []
        for frame in frames:
            if frame.size != (width, height):
                canvas = Image.new("RGB", (width, height), (24, 24, 27))
                canvas.paste(frame, (0, 0))
                frame = canvas
            aligned.append(frame)

        for scale, colors in ((1.0, 256), (0.85, 192), (0.75, 128)):
            if scale == 1.0:
                prepared = [frame.quantize(colors=colors) for frame in aligned]
            else:
                target_w = int(width * scale)
                resized = [frame.resize(
                    (target_w, round(frame.height * scale)), Image.LANCZOS)
                    for frame in aligned]
                prepared = [frame.quantize(colors=colors) for frame in resized]
            prepared[0].save(path, save_all=True, append_images=prepared[1:],
                             duration=FRAME_MS, loop=0, optimize=True, disposal=2)
            if path.stat().st_size <= 900 * 1024:
                break

        print("GIF  %s  кадров=%d  %dx%d  %d КБ"
              % (path.name, len(prepared), prepared[0].width,
                 prepared[0].height, path.stat().st_size // 1024))
        return path

    def burst(self, count: int = 3, every: float = 0.45):
        """Несколько кадров подряд — для гифки движения."""
        frames = []
        for _ in range(count):
            frames.append(self.shot())
            time.sleep(every)
        return frames


# --- сценарии -----------------------------------------------------------

def scene_27_login(desk: Desk):
    """Экран входа до авторизации."""
    desk.save_png("27-login")
    frames = [desk.shot()]
    desk.fill(0, "admin")
    time.sleep(0.4)
    frames.append(desk.shot())
    desk.fill(1, "Admin123!")
    time.sleep(0.4)
    frames.append(desk.shot())
    desk.save_gif("27-login-flow", frames)


def scene_27_menu(desk: Desk):
    """Боковое меню и верхняя панель после входа."""
    desk.save_png("27-menu")
    frames = [desk.shot()]
    desk.click("Оборудование цеха", wait=1.4)
    frames.append(desk.shot())
    desk.click("График ТО", wait=1.4)
    frames.append(desk.shot())
    desk.click("Дашборд мастера", wait=1.4)
    frames.append(desk.shot())
    desk.save_gif("27-menu-switch", frames)


def scene_27_crumbs(desk: Desk):
    """Хлебные крошки на вложенном экране."""
    desk.click("Оборудование цеха", wait=1.6)
    desk.save_png("27-crumbs")


def scene_27_idle(desk: Desk):
    """Автоблокировка: бездействие возвращает на экран входа."""
    desk.click("Дашборд мастера", wait=1.0)
    frames = [desk.shot()]
    # Приложение блокируется по таймеру бездействия: ждём и снимаем.
    for _ in range(6):
        time.sleep(3)
        frames.append(desk.shot())
        if desk.button("Войти") is not None:
            break
    desk.save_gif("27-idle-lock", frames)
    desk.save_png("27-idle")


def scene_27_token(desk: Desk):
    """Токен и текущий пользователь в верхней панели."""
    desk.save_png("27-token")


def scene_26_run(desk: Desk):
    """Запуск desktop-клиента: окно входа и рабочий экран после входа."""
    desk.save_png("26-run")
    frames = [desk.shot()]
    desk.login("admin", "Admin123!")
    frames.append(desk.shot())
    desk.click("Оборудование цеха", wait=1.6)
    frames.append(desk.shot())
    desk.save_gif("26-run-window", frames)


def scene_28_unauthorized(desk: Desk):
    """Вход с неверным паролем: 401, тост об ошибке, экран остаётся."""
    frames = [desk.shot()]
    desk.fill(0, "admin")
    desk.fill(1, "wrong-password")
    frames.append(desk.shot())
    desk.click("Войти", wait=2.5)
    frames.append(desk.shot())
    time.sleep(1.0)
    frames.append(desk.shot())
    desk.save_gif("28-api-401", frames)
    desk.save_gif("28-toast-error", frames[1:])


def scene_28_busy(desk: Desk):
    """Признак занятости: кнопка «Обновить» запускает перезагрузку данных."""
    desk.save_png("28-busy")
    frames = [desk.shot()]
    desk.click("Обновить", wait=0.15)
    frames += desk.burst(3, every=0.25)
    desk.save_gif("28-busy-refresh", frames)


def scene_29_dashboard(desk: Desk):
    """Дашборд: загрузка метрик и обновление по кнопке."""
    desk.click("Дашборд мастера", wait=1.5)
    frames = [desk.shot()]
    desk.click("Обновить", wait=0.2)
    frames += desk.burst(4, every=0.3)
    desk.save_gif("29-metrics-load", frames)
    desk.save_png("29-refresh")

    desk.click("Дашборд мастера", wait=1.5)
    frames = [desk.shot()]
    desk.click("Обновить", wait=1.5)
    frames.append(desk.shot())
    desk.save_gif("29-refresh-timer", frames)

    desk.save_png("29-orders")
    frames = [desk.shot()]
    desk.click_row(0)
    frames.append(desk.shot())
    desk.save_gif("29-orders-open", frames)


def scene_30_tables(desk: Desk):
    """Таблица оборудования: поиск с задержкой и пагинация."""
    desk.click("Оборудование цеха", wait=2.0)
    edit = desk.edits()[0]
    frames = [desk.shot()]
    for part in ("П", "ПР", "ПР-"):
        edit.GetValuePattern().SetValue(part)
        frames.append(desk.shot())
        time.sleep(0.35)
    desk.save_png("30-search")
    desk.click("Найти", wait=2.0)
    frames.append(desk.shot())
    desk.save_gif("30-search-debounce", frames)

    desk.click("Оборудование цеха", wait=2.0)
    desk.save_png("30-pager")
    frames = [desk.shot()]
    for _ in range(2):
        if not desk.click_last(">"):
            break
        frames.append(desk.shot())
    if len(frames) < 2:
        desk.click_last("<")
        frames.append(desk.shot())
    desk.save_gif("30-pager-next", frames)
    frames = [desk.shot()]
    desk.click_row(0)
    frames.append(desk.shot())
    desk.save_gif("30-table-page", frames)


def scene_31_equipment(desk: Desk):
    """Оборудование: фильтр по строке и показ выведенного из эксплуатации."""
    desk.click("Оборудование цеха", wait=2.0)
    frames = [desk.shot()]
    desk.fill(0, "ПР")
    frames.append(desk.shot())
    desk.click("Найти", wait=2.0)
    frames.append(desk.shot())
    desk.save_png("31-filters")
    desk.toggle("Показать выведенное из эксплуатации")
    frames.append(desk.shot())
    desk.save_gif("31-list-filter", frames)


def scene_32_schedule(desk: Desk):
    """График ТО: загрузка, листание месяцев, выполнение и возврат в план."""
    desk.click("График ТО", wait=2.2)
    desk.save_png("32-calendar")
    frames = [desk.shot()]
    desk.try_click(">")
    frames.append(desk.shot())
    desk.save_gif("32-calendar-month", frames)

    desk.save_png("32-load")
    frames = [desk.shot()]
    desk.click("Обновить", wait=0.2)
    frames += desk.burst(3, every=0.3)
    desk.save_gif("32-load-next", frames)

    desk.save_png("32-filter")
    desk.click_row(0)
    frames = [desk.shot()]
    if desk.try_click("Отметить выполненным"):
        frames.append(desk.shot())
        desk.try_click("Вернуть в план")
        frames.append(desk.shot())
    desk.save_gif("32-complete-next", frames)


def scene_33_orders(desk: Desk):
    """Заявки: фильтр по номеру, открытие карточки, история."""
    desk.click("Заявки", wait=2.2)
    desk.save_png("33-list")
    frames = [desk.shot()]
    desk.fill(0, "0047")
    frames.append(desk.shot())
    desk.click("Найти", wait=2.0)
    frames.append(desk.shot())
    desk.save_gif("33-list-status", frames)

    desk.save_png("33-card")
    frames = [desk.shot()]
    desk.click_row(0)
    frames.append(desk.shot())
    desk.save_gif("33-card-open", frames)

    desk.save_png("33-nav")
    desk.click("Обновить", wait=1.6)
    frames = [desk.shot()]
    desk.click_row(1)
    frames.append(desk.shot())
    desk.save_gif("33-complete-cost", frames)
    desk.save_png("33-complete")
    desk.save_png("33-crew")


def scene_34_crews(desk: Desk):
    """Бригады: загрузка списка и показ неактивных."""
    desk.click("Бригады", wait=2.0)
    desk.save_png("34-crews")
    frames = [desk.shot()]
    desk.click("Обновить", wait=0.2)
    frames += desk.burst(3, every=0.3)
    desk.save_gif("34-crews-load", frames)

    frames = [desk.shot()]
    desk.toggle("Показать неактивные")
    frames.append(desk.shot())
    desk.click_row(0)
    frames.append(desk.shot())
    desk.save_png("34-members")
    desk.save_gif("34-members-add", frames)


def scene_34_materials(desk: Desk):
    """Материалы: реестр, дефицит, приход на склад."""
    desk.click("Материалы и ЗИП", wait=2.2)
    desk.save_png("34-materials")
    desk.save_png("34-table")
    frames = [desk.shot()]
    desk.fill(0, "подшипник")
    frames.append(desk.shot())
    desk.click("Применить", wait=1.8)
    frames.append(desk.shot())
    desk.save_gif("34-table-search", frames)

    desk.click("Материалы и ЗИП", wait=2.0)
    frames = [desk.shot()]
    desk.click("Дефицит", wait=1.8)
    frames.append(desk.shot())
    desk.save_gif("34-materials-deficit", frames)
    desk.save_png("34-writeoff")


def scene_35_reports(desk: Desk):
    """Отчёты: сборка отчёта и переключение вкладок."""
    desk.click("Отчёты", wait=2.2)
    desk.save_png("35-pdf")
    frames = [desk.shot()]
    desk.click("Показать", wait=1.2)
    frames += desk.burst(3, every=0.35)
    desk.save_gif("35-filter-build", frames)

    for tab in ("Бригады", "Материалы"):
        if desk.try_click(tab, wait=1.4):
            frames.append(desk.shot())
    desk.save_gif("35-pdf-download", frames)
    desk.save_png("35-log")


SCENES = {
    "26-run": ("anonymous", scene_26_run),
    "27-login": ("anonymous", scene_27_login),
    "27-menu": ("admin", scene_27_menu),
    "27-crumbs": ("admin", scene_27_crumbs),
    "27-idle": ("admin", scene_27_idle),
    "27-token": ("admin", scene_27_token),
    "28-unauthorized": ("anonymous", scene_28_unauthorized),
    "28-busy": ("admin", scene_28_busy),
    "29-dashboard": ("admin", scene_29_dashboard),
    "30-tables": ("admin", scene_30_tables),
    "31-equipment": ("admin", scene_31_equipment),
    "32-schedule": ("admin", scene_32_schedule),
    "33-orders": ("admin", scene_33_orders),
    "34-crews": ("admin", scene_34_crews),
    "34-materials": ("admin", scene_34_materials),
    "35-reports": ("admin", scene_35_reports),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Снимки desktop-клиента")
    parser.add_argument("--only", nargs="*", help="начало имени сцены")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list:
        for name, (role, _) in SCENES.items():
            print("%-18s %s" % (name, role))
        return 0

    IMAGES.mkdir(parents=True, exist_ok=True)
    GIFS.mkdir(parents=True, exist_ok=True)

    selected = [name for name in SCENES
                if not args.only or any(name.startswith(p) for p in args.only)]
    if not selected:
        print("нечего снимать: --only не совпал ни с одной сценой", file=sys.stderr)
        return 1

    desk = Desk().launch()
    done, failed = 0, []
    try:
        for name in selected:
            role, scene = SCENES[name]
            try:
                if role == "anonymous":
                    desk.launch()
                else:
                    desk.launch()
                    desk.login("admin", "Admin123!")
                scene(desk)
                done += 1
            except Exception as error:  # noqa: BLE001 — одна сцена не должна рушить прогон
                message = str(error).encode("ascii", "replace").decode("ascii")
                failed.append("%s: %s" % (name, message))
                print("FAIL %s: %s" % (name, message), file=sys.stderr)
    finally:
        if desk.process:
            subprocess.run(["taskkill", "/PID", str(desk.process.pid), "/F"],
                           capture_output=True, check=False)

    print("\nЗаписано: %d, ошибок: %d" % (done, len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
