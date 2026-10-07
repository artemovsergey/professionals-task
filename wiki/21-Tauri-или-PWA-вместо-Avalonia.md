Сессия 7. Desktop-клиент: Tauri или PWA вместо Avalonia

Эта страница — **запасной вариант**. Основной для отбора — Avalonia
([19-Avalonia-проект-и-навигация](19-Avalonia-проект-и-навигация),
[20-Desktop-Avalonia-экраны](20-Desktop-Avalonia-экраны)), потому что раздел
2.4 задания требует нативный интерфейс:

> Настольное приложение. **Не гибрид и не WebView** — это должна быть
> самостоятельная нативная программа, использующая тот же API.

Tauri и PWA работают через web-движок, поэтому для **этого** задания не
подходят: за такой раздел снимают все 15 баллов.

| Этап | Можно ли web-обёртка |
|---|---|
| Отбор (это задание) | **нет** — только нативный UI |
| Региональный этап | **нет** — «не гибрид, не использовать WebView» |
| Финальный этап | **да** — «нативного UI или встроенного браузерного компонента» |

Дальше — PWA, потому что он у нас уже собран на web-клиенте из сессий 5–6
и показан в работе.

# Что делаем на этой странице

Тот же самый React-клиент превращается в устанавливаемое приложение:
манифест с иконками, service worker с кэшем оболочки и понятное поведение
без сети. Никаких новых зависимостей — только файлы в `public/` и десяток
строк в существующих.

# Шаг 1. Подключаем манифест

`web/index.html` — три строки в `<head>`:

```html
<link rel="manifest" href="/manifest.webmanifest" />
<meta name="theme-color" content="#1D1D1B" />
<link rel="apple-touch-icon" href="/icon-192.png" />
```

`theme-color` красит строку состояния у установленного приложения,
`apple-touch-icon` — иконку на iOS. Без манифеста браузер не считает
страницу устанавливаемой.

![[images/pwa21-index.png]]
*index.html: манифест, цвет темы и иконки подключены*

# Шаг 2. Пишем манифест

`web/public/manifest.webmanifest`:

```json
{
  "name": "Планировщик личных задач",
  "short_name": "Задачи",
  "display": "standalone",
  "start_url": "/",
  "scope": "/",
  "background_color": "#F2F2EF",
  "theme_color": "#1D1D1B",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "shortcuts": [{ "name": "Новая задача", "url": "/?action=new" }]
}
```

`display: "standalone"` — ключевое поле: из-за него приложение открывается
без вкладок и адресной строки. Иконка `maskable` нужна для Android, где
система обрезает квадрат по своей маске.

![[images/pwa21-manifest.png]]
*Манифест: имя, standalone, две иконки и ярлык «Новая задача» в меню приложения*

# Шаг 3. Рисуем иконки

Иконки не нарисовать руками в двух размерах — их проще сгенерировать.
Скрипт `tools/make-pwa-icons.mjs` открывает страницу нужного размера и
снимает её:

```js
for (const size of [192, 512]) {
  const page = await browser.newContext({ viewport: { width: size, height: size } }).then((c) => c.newPage());
  const pad = Math.round(size * 0.18);
  await page.setContent(`<body style="margin:0;background:#1D1D1B;display:flex;
    align-items:center;justify-content:center;">
    <img src="${logoDataUri}" style="width:${size - pad * 2}px">`);
  await page.screenshot({ path: `web/public/icon-${size}.png` });
}
```

```bash
node tools/make-pwa-icons.mjs
```

![[images/pwa21-icons.png]]
*Скрипт генерации иконок: два размера, отступ 18% от края под маску системы*

# Шаг 4. Регистрируем service worker

`web/src/main.jsx`:

```jsx
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  });
}
```

Регистрация после `load` — чтобы не мешать первой отрисовке, а ошибка
регистрации гасится: приложение должно работать и без service worker,
иначе его нельзя будет открыть обычным браузером.

![[images/pwa21-register.png]]
*main.jsx: регистрация worker после загрузки страницы*

# Шаг 5. Кэшируем оболочку, данные не кэшируем

`web/public/sw.js` — самый важный файл страницы. Стратегия одна строка:
статику кэшируем, задачи всегда берём из сети.

```js
const CACHE = 'taskplanner-shell-v1';
const SHELL = ['/', '/index.html', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png'];
```

```js
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting())
  );
});
```

Данные в кэш не попадают:

```js
if (url.pathname.startsWith('/api/')) return;
```

Навигация — сначала сеть, при ошибке оболочка из кэша:

```js
if (request.mode === 'navigate') {
  event.respondWith(
    fetch(request).catch(() => caches.match('/index.html').then((r) => r ?? Response.error()))
  );
  return;
}
```

Если закэшировать `/api`, пользователь увидит старые задачи и будет
думать, что сервер сломан. Кэш должен хранить только оболочку.

![[images/pwa21-sw.png]]
*sw.js: оболочка кэшируется при установке, запросы к /api всегда идут в сеть*

# Шаг 6. Показываем метку «офлайн»

`web/src/components/TaskBoard.jsx`:

```jsx
const offline = typeof navigator !== 'undefined' && navigator.onLine === false;

{offline ? <span className="offline">офлайн</span> : null}
```

Пустой экран без объяснения выглядит как поломка. Одна метка честно
говорит, что произошло.

# Шаг 7. Запускаем как приложение

```bash
cd src/web
npm run build && npm run preview -- --port 4173
```

Откройте `http://localhost:4173` и установите приложение из меню браузера.

![[images/pwa21-app-window.png]]
*После установки: окно без вкладок и адресной строки, сверху только название и «×»*

![[images/pwa21-installed-mobile.png]]
*На телефоне то же приложение ставится из браузера и открывается во весь экран*

# Шаг 8. Проверяем работу без сети

Выключите сеть (в DevTools — вкладка Network → Offline) и перезагрузите
приложение. Оно должно открыться: оболочка из кэша, метка «офлайн» и
понятная ошибка вместо данных.

![[images/pwa21-offline.png]]
*Без сети приложение открывается: оболочка из кэша, метка «офлайн», данные не подменены мусором*

![[gifs/pwa-scenario.gif]]
*Сценарий целиком: вход, создание, фильтр, отметка выполнения и запуск без сети*

# Если выбрали Tauri

Tauri — это тот же React в системном WebView (WebView2 на Windows,
WebKitGTK на Linux) плюс маленькое ядро на Rust. Плагин ставится в тот же
web-клиент, конфигурация описывает окно, а `localStorage` продолжает
работать без изменений:

```bash
cd src/web
npm install -D @tauri-apps/cli @tauri-apps/api
npx tauri init          # Web assets: ../dist, Dev server URL: http://localhost:5173
npm run tauri build
```

Главная сложность — не код, а система: на РедОС нужны
`webkit2gtk4.0-devel`, `libsoup3-devel`, `openssl-devel`, `librsvg2-devel`,
`patchelf` и Rust. Если их нет, Tauri-сборка не запустится, а Avalonia
соберётся везде. Проверить заранее:

```bash
rpm -q webkit2gtk4.0-devel 2>/dev/null || echo "webkit2gtk не установлен — Tauri не собрать"
```

# Сравнение

| Критерий | Avalonia | Tauri | PWA |
|---|---|---|---|
| Нативный UI | да | нет (WebView) | нет (браузер) |
| Подходит для раздела 2.4 | **да** | нет | нет |
| Подходит для финала | да | да | да |
| Сборка на чистой РедОС | без доп. зависимостей | нужны webkit2gtk и Rust | обычная сборка Vite |
| Работает без сети | нет | нет | да |
| Установка на телефон | нет | нет | да |

# Коммит

```bash
git add src/web
git commit -m "PWA: манифест, иконки, service worker с кэшем оболочки и режим офлайн"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| Браузер не предлагает установку | нет `<link rel="manifest">` в `index.html` или манифест не отдаётся: проверьте `curl -I http://localhost:4173/manifest.webmanifest` |
| Иконка в окне — стандартная браузерная | в манифесте нет иконок нужных размеров или они не лежат в `public/` |
| Приложение не открывается без сети | не сработал `install` в service worker: оболочка не закэширована, проверьте имя `CACHE` |
| Список показывает старые задачи | в `fetch` пропала проверка `url.pathname.startsWith('/api/')` |
| Установка не работает на телефоне по http | нужен HTTPS: PWA ставится только с `https://` или с `localhost` |
| `XOpenDisplay`/окно Tauri не открывается | не установлен `webkit2gtk4.0-devel` — переходите на Avalonia |