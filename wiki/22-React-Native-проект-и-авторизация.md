Сессия 8. Mobile-клиент: проект и авторизация · 0–75 мин

Стек: **React Native (Expo)**. На площадке стоят Android Studio 2024.3.1,
Android 10 SDK и React Native Tools (инфраструктурный лист чемпионата).

# 1. Создание проекта (0–20 мин)

```bash
cd src
npx create-expo-app@latest mobile --template blank-typescript
cd mobile
npm install
npm install expo-secure-store @react-navigation/native @react-navigation/native-stack
npx expo install react-native-screens react-native-safe-area-context
```

Проверка версий:

```bash
npx expo --version
npm ls react-native expo
```

> **Замечание:** `create-expo-app` скачивает шаблон с актуальными версиями.
> Не берите версию из чужого `package.json` — расхождение SDK и Expo даёт
> ошибку `Error: Cannot read property 'version' of undefined` при запуске.

# 2. Запуск на устройстве (20–35 мин)

```bash
npx expo start
```

Появится QR-код. Варианты подключения:

| Способ | Что нужно |
|---|---|
| **Expo Go** на телефоне | установить из магазина, отсканировать QR. Самый быстрый путь |
| Android-эмулятор | Android Studio → AVD; `npx expo start --android` |
| Реальный Android по USB | включить «Отладка по USB», `npx expo start --device` |

> **Замечание:** телефон и компьютер должны быть в одной сети. Если не
> соединяются — откройте точку доступа на телефоне или укажите адрес вручную:
> `npx expo start --lan`.

# 3. Адрес API и мобильные особенности (35–45 мин)

Это главный грабли-момент мобильного клиента. В эмуляторе Android
`localhost` — это **сам эмулятор**, а не ваш компьютер. Нужны разные адреса:

| Где запущено | Адрес API |
|---|---|
| Android-эмулятор (AVD) | `http://10.0.2.2:5000` |
| Реальный телефон по USB | `http://127.0.0.1:5000` с пробросом, либо IP компьютера в локальной сети |
| iOS-симулятор | `http://localhost:5000` |
| Телефон и компьютер в одной Wi-Fi сети | `http://<ip-компьютера>:5000` |

Определите адрес компьютера:

```bash
# Linux / РедОС / macOS
ip addr show | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig | findstr IPv4
```

Создайте `src/mobile/.env.example`:

```bash
EXPO_PUBLIC_API_URL=http://10.0.2.2:5000
```

Скопируйте в `.env`:

```bash
cp .env.example .env
```

`.env` уже в `.gitignore` (правило `.env.*` со страницы 01).

> **Замечание:** переменные Expo читаются только с префиксом `EXPO_PUBLIC_`
> и **попадают в бандл в открытом виде**. Строка подключения к базе и JWT-секрет
> сюда не пишутся никогда.

# 4. HTTP-клиент с токеном (45–60 мин)

`src/mobile/src/api/types.ts` — типы совпадают с web-версией:

```typescript
export type TaskStatus = 'new' | 'in_progress' | 'done' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high';

export interface User {
  id: number;
  email: string;
  fullName: string;
}

export interface Task {
  id: number;
  userId: number;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  dueDate: string | null;
  completedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface TaskSummary {
  total: number;
  done: number;
  notDone: number;
  overdue: number;
  byPriority: Record<string, number>;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  message: string;
  error_code: string | null;
}

export interface LoginResponse {
  token: string;
  tokenType: string;
  expiresIn: number;
  user: User;
}
```

`src/mobile/src/api/tokenStorage.ts`:

```typescript
import * as SecureStore from 'expo-secure-store';

const TOKEN_KEY = 'taskplanner.token';
const USER_KEY = 'taskplanner.user';

/**
 * SecureStore шифрует данные системным хранилищем (Keychain на iOS,
 * EncryptedSharedPreferences на Android). Обычный AsyncStorage на Android
 * хранит всё в открытом файле — для токена это не годится.
 */
export const tokenStorage = {
  async getToken(): Promise<string | null> {
    return SecureStore.getItemAsync(TOKEN_KEY);
  },

  async setToken(token: string): Promise<void> {
    await SecureStore.setItemAsync(TOKEN_KEY, token);
  },

  async getUser(): Promise<User | null> {
    const raw = await SecureStore.getItemAsync(USER_KEY);

    if (!raw) return null;

    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  },

  async setUser(user: User): Promise<void> {
    await SecureStore.setItemAsync(USER_KEY, JSON.stringify(user));
  },

  async clear(): Promise<void> {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(USER_KEY);
  },
};

import type { User } from './types';
```

> **Замечание:** `import type { User }` в конце файла — не ошибка, но
> неаккуратно. Перенесите его в начало файла, вместе с остальными импортами.

`src/mobile/src/api/client.ts`:

```typescript
import { Platform } from 'react-native';
import { tokenStorage } from './tokenStorage';
import type {
  ApiResponse,
  LoginResponse,
  Task,
  TaskPriority,
  TaskStatus,
  TaskSummary,
  User,
} from './types';

const DEFAULT_URL = Platform.OS === 'android' ? 'http://10.0.2.2:5000' : 'http://localhost:5000';

export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? DEFAULT_URL;

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly errorCode: string | null,
  ) {
    super(message);
  }
}

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; auth?: boolean } = {},
): Promise<T> {
  const { method = 'GET', body, auth = true } = options;

  const headers: Record<string, string> = { 'Content-Type': 'application/json' };

  if (auth) {
    const token = await tokenStorage.getToken();

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      `Нет связи с сервером (${API_BASE_URL}). Проверьте, что API запущен.`,
      0,
      null,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const payload = (await response.json()) as ApiResponse<T>;

  if (!response.ok || !payload.success || payload.data === null) {
    throw new ApiError(
      payload.message?.split(' (traceId:')[0] ?? `Ошибка ${response.status}`,
      response.status,
      payload.error_code,
    );
  }

  return payload.data;
}

export const authApi = {
  register: (body: { email: string; password: string; fullName: string }) =>
    request<{ user: User }>('/api/auth/register', { method: 'POST', body, auth: false }).then(
      (r) => r.user,
    ),

  login: (body: { email: string; password: string }) =>
    request<LoginResponse>('/api/auth/login', { method: 'POST', body, auth: false }),
};

export const tasksApi = {
  list: (status?: TaskStatus) =>
    request<{ items: Task[]; total: number; page: number; pageSize: number }>(
      `/api/tasks?page=1&pageSize=50${status ? `&status=${status}` : ''}`,
    ),

  create: (body: Partial<Task>) =>
    request<Task>('/api/tasks', { method: 'POST', body }),

  update: (id: number, body: Partial<Task>) =>
    request<Task>(`/api/tasks/${id}`, { method: 'PUT', body }),

  remove: (id: number) => request<void>(`/api/tasks/${id}`, { method: 'DELETE' }),

  toggleCompleted: (id: number) =>
    request<Task>(`/api/tasks/${id}/complete`, { method: 'PATCH' }),

  summary: () => request<TaskSummary>('/api/tasks/summary'),
};
```

> **Замечание:** на Android нужно разрешить **незашифрованный HTTP**.
> В `app.json` добавьте:

```json
{
  "expo": {
    "android": {
      "usesCleartextTraffic": true
    },
    "ios": {
      "infoPlist": {
        "NSAppTransportSecurity": {
          "NSAllowsArbitraryLoads": true
        }
      }
    }
  }
}
```

> **Замечание:** `usesCleartextTraffic: true` ослабляет безопасность. Он
> нужен только для разработки против локального `http://localhost`. На
> финальном этапе API должен быть на `https`, и тогда настройку убирают.

# 5. Контекст авторизации (60–75 мин)

`src/mobile/src/auth/AuthContext.tsx`:

```tsx
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { ApiError, authApi } from '../api/client';
import { tokenStorage } from '../api/tokenStorage';
import type { User } from '../api/types';

interface AuthContextValue {
  user: User | null;
  isInitializing: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    let cancelled = false;

    tokenStorage
      .getToken()
      .then(async (token) => {
        const stored = await tokenStorage.getUser();

        if (!cancelled && token && stored) {
          setUser(stored);
        } else if (!token) {
          await tokenStorage.clear();
        }
      })
      .finally(() => {
        if (!cancelled) setIsInitializing(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const session = await authApi.login({ email: email.trim(), password });

    await tokenStorage.setToken(session.token);
    await tokenStorage.setUser(session.user);

    setUser(session.user);
  }, []);

  const register = useCallback(async (email: string, password: string, fullName: string) => {
    await authApi.register({ email: email.trim(), password, fullName: fullName.trim() });

    // Регистрация токена не возвращает — сразу входим
    await login(email, password);
  }, [login]);

  const logout = useCallback(async () => {
    await tokenStorage.clear();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isInitializing, login, register, logout }),
    [user, isInitializing, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) return { user: null, isInitializing: true, login: async () => {}, register: async () => {}, logout: async () => {} };

  return context;
}
```

# Проверка

1. `npx expo start` → приложение запускается на устройстве или эмуляторе.
2. На эмуляторе адрес API — `http://10.0.2.2:5000`, на реальном телефоне —
   ваш IP. Проверьте `EXPO_PUBLIC_API_URL` в `.env`.
3. Страница входа подключена к `authApi.login` и показывает текст ошибки.
4. Войдите → `SecureStore` содержит `taskplanner.token`:

```bash
# Android: данные приложения в файловой системе эмулятора
adb shell run-as ru.college.taskplanner ls shared_prefs
```

5. Закройте приложение и откройте снова → вы вошли, на экране не форма входа.
6. Покажите, что `AsyncStorage` не используется: в коде есть только
   `expo-secure-store`.

# Коммит

```bash
git add src/mobile
git commit -m "Mobile-клиент: проект Expo, API-клиент, SecureStore, контекст авторизации"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| `Network request failed` на эмуляторе | адрес должен быть `http://10.0.2.2:5000`, а не `localhost` |
| `Network request failed` на реальном телефоне | телефон и компьютер в одной сети; проверьте адрес `ip addr` и `usesCleartextTraffic` |
| `Could not connect to development server` | проверьте, что порт 8081 не занят; `npx expo start --tunnel` помогает при сложных сетях |
| Токен не сохраняется | `SecureStore` на web не работает; проверяйте на устройстве или эмуляторе |
| `process.env.EXPO_PUBLIC_API_URL` — `undefined` | файл должен называться `.env`, переменная — с префиксом `EXPO_PUBLIC_` |
| Метка `blank-typescript` не найдена | `npx create-expo-app@latest` требует Node 18+ |

## Иллюстрации

![[images/mob22-explorer.png]]
*Структура мобильного проекта в VS Code*

![[images/mob22-app.png]]
*Экраны на API React Native: View, Text, Pressable, FlatList*

![[images/mob22-api.png]]
*Слой API мобильного клиента — тот же конверт ответа*

![[images/mob22-vite-rnw.png]]
*Запуск RN-кода в браузере: react-native подменяется на react-native-web*

![[images/mob22-login.png]]
*Экран входа на 390 px*

---

Дальше: [23-Mobile-React-Native-экраны](23-Mobile-React-Native-экраны)
