Сессия 4. Мобильный клиент: проект и вход · 0–35 мин

# Что делаем на этой странице

Мобильный клиент пишется на API React Native, но проверять его на телефоне
долго. Поэтому в эталоне используется приём из документации Expo: в веб-сборке
пакет `react-native` подменяется на `react-native-web`, и те же самые экраны
запускаются в браузере на ширине телефона.

Код при этом остаётся настоящим React Native: `View`, `Text`, `Pressable`,
`FlatList` — без единой браузерной строки в компонентах.

# Шаг 1. Запуск

```bash
cd src/mobile
npm install
npm run dev
```

![[images/mob22-s1-dev.png]]
*Vite поднял клиент на своём порту — 5174, чтобы не конфликтовать с web*

# Шаг 2. Клиент видит API

```bash
curl -s http://127.0.0.1:5174/api/health
```

![[images/mob22-s2-api.png]]
*Прокси отработал: запрос ушёл на тот же API, что и web-клиент*

Мобильный клиент обслуживает **тот же** API, отдельного бэкенда для него нет.
Это и проверяет критерий про единый сервис для всех клиентов.

# Шаг 3. Подмена react-native

`vite.config.js`:

```javascript
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [{ find: /^react-native$/, replacement: 'react-native-web' }],
    extensions: ['.web.jsx', '.web.js', '.jsx', '.js', ...],
  },
  define: { global: 'window', __DEV__: 'true', 'process.env.NODE_ENV': '"development"' },
});
```

Три вещи, без которых сборка не поедет:

- **alias** — импорт `react-native` перенаправляется на `react-native-web`;
- **extensions** — сначала файлы `.web.jsx`: браузер получит веб-реализацию,
  а на телефоне соберётся обычный `.jsx`;
- **define** — `__DEV__` и `global` есть только в среде React Native; в
  браузере их нужно объявить, иначе будет `ReferenceError`.

![[images/mob22-s3-alias.png]]
*Подмена пакета и расширения — весь приём помещается в конфиг*

# Шаг 4. Импорты компонентов

`src/App.jsx`:

```javascript
import { useCallback, useEffect, useState } from 'react';
import {
  FlatList,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
```

Ни одного `div` и ни одного `onClick`: привычные для браузера конструкции
здесь просто не существуют. Если понадобилась мышь или таблица — значит
компонент уже не переносится на телефон без переписывания.

![[images/mob22-s4-imports.png]]
*Только API React Native: View, Text, Pressable, FlatList*

# Шаг 5. Экран входа

```javascript
function Login({ onSignedIn }) {
  const [email, setEmail] = useState('ivanov@college.ru');
  const [password, setPassword] = useState('Password123');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    try {
      await api.login(email, password);
      onSignedIn();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
```

Экран написан один раз и используется и в мобильном, и в веб-сборке —
разница только в ширине окна.

![[images/mob22-s5-login.png]]
*Состояния формы и защита от повторного нажатия — как в web-клиенте*

# Шаг 6. Токен

`src/api.js`:

```javascript
const TOKEN_KEY = 'taskplanner.token';

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (token) => localStorage.setItem(TOKEN_KEY, token);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);
```

Тот же `localStorage`, что и в веб-клиенте. В настоящем мобильном приложении
этот код переносится в `AsyncStorage` — но ключ и логика остаются прежними.

![[images/mob22-s6-token.png]]
*Три функции: прочитать, записать и очистить токен*

# Шаг 7. Экран входа на телефоне

Откройте `http://127.0.0.1:5174` в окне шириной 390 px:

![[images/mob22-s7-login.png]]
*Тот же компонент, но на ширине телефона: поля и кнопка в столбик*

# Проверка

| Проверка | Ожидание |
|---|---|
| `npm run dev` | клиент на порту 5174 |
| `curl http://127.0.0.1:5174/api/health` | `{"status":"ok"}` |
| окно 390 px | вход в одну колонку |
| вход демо-пользователем | открывается список |
| перезагрузка страницы | остаёмся внутри |
| «Выйти» | снова экран входа |

# Коммит

```bash
git add src/mobile
git commit -m "Мобильный клиент: React Native-проект, подмена на react-native-web и вход"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| `Failed to resolve import "react-native"` | не задан alias на `react-native-web` в `vite.config.js` |
| `__DEV__ is not defined` | добавьте `define: { __DEV__: 'true' }` |
| `global is not defined` | добавьте `global: 'window'` в тот же `define` |
| В браузере пусто, а на телефоне работает | проверьте `extensions`: `.web.jsx` должен идти первым |
| Порт занят | смените `--port` в скрипте `dev` |
| Запросы уходят напрямую и падает CORS | не задан `server.proxy` для `/api` |

# Что должно быть в репозитории к концу сессии 4, блок 1

- [ ] Проект мобильного клиента с React Native
- [ ] Конфиг с подменой на `react-native-web` и `define`
- [ ] `api.js` с хранением токена
- [ ] Экран входа, работающий на телефоне

---

Дальше: [23-Mobile-React-Native-экраны](23-Mobile-React-Native-экраны)