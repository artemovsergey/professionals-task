Сессия 7. Desktop-клиент: Tauri или PWA вместо Avalonia

Эта страница — **запасной вариант**. Основной для отбора — Avalonia
([19](19-Avalonia-проект-и-навигация), [20](20-Desktop-Avalonia-экраны)),
потому что раздел 2.4 задания требует нативный интерфейс:

> Настольное приложение. **Не гибрид и не WebView** — это должна быть
> самостоятельная нативная программа, использующая тот же API.

Tauri и PWA работают через web-движок, поэтому для **этого** задания не
подходят: за такой раздел снимаются все 15 баллов.

Когда вариант становится допустимым:

| Этап | Можно ли web-обёртка |
|---|---|
| Отбор (это задание) | **нет** — только нативный UI |
| Региональный этап | **нет** — «настольное приложение (не гибрид, не использовать WebView)» |
| Финальный этап | **да** — «C#/Java/Python/Golang с использованием встроенного браузерного компонента или нативного UI» |

Страница пригодится, когда вы дойдёте до финала и захотите перенести web-клиент
в окно, либо если с Avalonia возникнут непреодримые проблемы.

---

# 1. Вариант A: Tauri (системный WebView + Rust-ядро)

## Что это

Tauri — лёгкая оболочка: интерфейс остаётся вашим React-приложением, а
системный WebView используется нативно (WebView2 на Windows, WebKitGTK на
Linux, WKWebView на macOS). Никакого Chromium в комплекте — размер сборки
измеряется мегабайтами, а не сотнями.

## Требования

| Компонент | Версия | Замечание |
|---|---|---|
| Rust | stable | `curl https://sh.rustup.rs -sSf \| sh` |
| Node.js | 20+ | уже стоит |
| Tauri CLI | 2.x | `npm install -D @tauri-apps/cli` |
| Системные библиотеки Linux | webkit2gtk, libsoup | на РедОС ставятся из репозитория |

## Установка на РедОС

```bash
# Проверьте, что WebKitGTK есть. На площадке может отсутствовать —
# тогда Tauri-сборку проверить не удастся, а Avalonia соберётся везде.
rpm -q webkit2gtk4.0-devel 2>/dev/null || echo "webkit2gtk4.0-devel не установлен"

sudo dnf install -y webkit2gtk4.0-devel \
  openssl-devel \
  libsoup3-devel \
  libappindicator-gtk3-devel \
  librsvg2-devel \
  patchelf
```

> **Замечание:** именно поэтому для отбора выбран Avalonia — он собирается на
> чистой РедОС без системных зависимостей. Tauri требует `webkit2gtk-devel`,
> которого в инфраструктурном листе чемпионата нет.

## Инициализация поверх web-клиента

```bash
cd src/web
npm install -D @tauri-apps/cli @tauri-apps/api
npx tauri init

# npx tauri init спросит:
#   App name:            TaskPlanner
#   Window title:        Планировщик задач
#   Web assets location: ../dist        (путь к сборке Vite)
#   Dev server URL:      http://localhost:5173
#   Frontend dev command: npm run dev
#   Frontend build command: npm run build
```

Конфигурация `src/tauri.conf.json` (ключевые поля):

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "TaskPlanner",
  "version": "1.0.0",
  "identifier": "ru.college.taskplanner",
  "build": {
    "beforeDevCommand": "npm run dev",
    "devUrl": "http://localhost:5173",
    "beforeBuildCommand": "npm run build",
    "frontendDist": "../dist"
  },
  "app": {
    "windows": [
      {
        "title": "Планировщик задач",
        "width": 1000,
        "height": 680,
        "minWidth": 900,
        "minHeight": 600
      }
    ],
    "security": {
      "csp": "default-src 'self'; connect-src 'self' ipc: http://ipc.localhost http://localhost:5000"
    }
  },
  "bundle": {
    "active": true,
    "targets": "all"
  }
}
```

## Токен в Tauri

`localStorage` в Tauri живёт в каталоге данных приложения и переживает
перезапуск — web-клиент работает без изменений. Для чувствительного хранения
используйте плагин `tauri-plugin-store` с шифрованием:

```bash
npm install -D tauri-plugin-store
```

```typescript
// src/storage/secureSession.ts
import { load, Store } from '@tauri-apps/plugin-store';

const TOKEN_KEY = 'session';

export async function saveSession(token: string, user: unknown): Promise<void> {
  const store = await load('session.json', { autoSave: true });

  await store.set(TOKEN_KEY, { token, user });
}

export async function loadSession(): Promise<{ token: string; user: unknown } | null> {
  const store = await load('session.json', { autoSave: false });

  return (await store.get<{ token: string; user: unknown }>(TOKEN_KEY)) ?? null;
}

export async function clearSession(): Promise<void> {
  const store = await load('session.json', { autoSave: true });

  await store.delete(TOKEN_KEY);
}
```

> **Замечание:** `@tauri-apps/plugin-store` — упрощённая обёртка над
> `localStorage`, а не системное шифрование. Если нужна реальная защита
> секретов, добавляйте `tauri-plugin-keyring` и храните токен в системном
> хранилище (Windows Credential Manager, libsecret на Linux, Keychain на macOS).

## Проверка

```bash
npm run tauri dev      # разработка с горячей перезагрузкой
npm run tauri build    # сборка установщиков
```

Откройте DevTools в окне (правая кнопка → «Open DevTools» или `Ctrl`+`Shift`+`I`)
и убедитесь, что в `Application → Local Storage` лежит `taskplanner.token`.

---

# 2. Вариант B: PWA (без установки, только браузер)

## Что это

PWA — это тот же web-клиент плюс `manifest.json` и service worker. При
определённых условиях браузер предлагает «Установить приложение», и оно
запускается в отдельном окне без адресной строки.

## Как добавить PWA к готовому web-клиенту

Установите плагин:

```bash
cd src/web
npm install -D vite-plugin-pwa
```

`src/web/vite.config.ts`:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'Планировщик задач',
        short_name: 'Задачи',
        description: 'Планировщик личных задач',
        lang: 'ru',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        background_color: '#f1f6f2',
        theme_color: '#0f9346',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
      workbox: {
        // Токен и данные задач не кэшируем — только статика
        globPatterns: ['**/*.{js,css,html,woff2}'],
        navigateFallback: 'index.html',
      },
    }),
  ],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
});
```

Иконки сгенерируйте простой командой (или сделайте скриншот квадрата 512×512):

```bash
mkdir -p public
# положите сюда pwa-192x192.png и pwa-512x512.png
```

Проверка в браузере:

1. `npm run build && npm run preview`
2. DevTools → Application → Manifest: поля заполнены, ошибок нет.
3. DevTools → Application → Service Workers: worker зарегистрирован.
4. Application → Manifest → «Installability»: нет ошибок.
5. В адресной строке или в меню браузера появится значок установки.
6. После установки приложение открывается в окне без адресной строки.
7. **Обязательно:** DevTools → Application → Service Workers → «Offline»,
   затем перезагрузка — статика грузится из кэша, а `/api` даёт понятную
   ошибку «Нет связи с сервером», а не пустой экран.

> **Замечание:** PWA без HTTPS не работает как приложение (кроме
> `localhost`). На площадке по HTTPS может не быть — поэтому PWA годится для
> демонстрации на своём компьютере, но не для сдачи.

---

# 3. Сравнение вариантов

| Критерий | Avalonia | Tauri | PWA |
|---|---|---|---|
| Нативный UI | да | нет (WebView) | нет (браузер) |
| Подходит для раздела 2.4 | **да** | нет | нет |
| Подходит для финала | да | да | зависит от формулировки |
| Сборка на чистой РедОС | да, без доп. зависимостей | нужны `webkit2gtk4.0-devel` и Rust | обычная сборка Vite |
| Размер сборки | ~15 МБ | ~5 МБ | ~2 МБ |
| Скорость разработки | медленнее (XAML + MVVM) | быстро (тот же React) | быстро |
| Работа на мобильном | нет | нет | частично |

# 4. Что делать, если Avalonia не получается

1. Соберите **web-клиент полностью** (сессии 5–6). Это уже готовая основа.
2. Сделайте desktop-клиент на **Avalonia** минимально: вход, список, сводка.
   Три экрана закрывают требование «минимум 3–4 экрана».
3. Если Avalonia не собирается на РедОС — запишите это в README с точными
   текстом ошибки и инструкцией, что проверено на Windows. Это честнее, чем
   сдавать Tauri и потерять 15 баллов.

# Проверка

Если вы дошли до финала и выбрали Tauri или PWA:

```bash
# Tauri
npm run tauri build
ls -la src-tauri/target/release/bundle/

# PWA
npm run build
grep -c "manifest" dist/index.html
ls dist/manifest.webmanifest dist/sw.js 2>/dev/null || echo "manifest не создан"
```

В README обязательно напишите, каким вариантом является desktop-клиент и
почему. Эксперт оценивает соответствие требованиям задания, а не симпатию к
фреймворку.

# Коммит

```bash
git add src/web src/desktop
git commit -m "Desktop-клиент: вариант Tauri/PWA вместо Avalonia (для финального этапа)"
```

---

Дальше: [22-React-Native-проект-и-авторизация](22-React-Native-проект-и-авторизация)
