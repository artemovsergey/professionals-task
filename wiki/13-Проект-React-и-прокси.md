Сессия 5. Web-клиент: каркас · 0–40 мин

# 1. Создание проекта (0–10 мин)

```bash
cd src
npm create vite@latest web -- --template react-ts
cd web
npm install
```

Проверьте версии — контракт требует React 19 и Node 20+:

```bash
node -v
npm ls react react-dom
```

Удалите то, что не пригодится:

```bash
rm -f src/App.css src/index.css src/assets/react.svg public/vite.svg
rmdir src/assets 2>/dev/null
```

# 2. Зависимости (10–18 мин)

```bash
npm install react-router-dom
npm install axios
npm install -D prettier
```

| Пакет | Зачем |
|---|---|
| `react-router-dom` | маршруты и защита страниц |
| `axios` | HTTP-клиент, интерцепторы для токена |
| `prettier` | единый формат кода |

# 3. API-клиент с интерцептором (18–30 мин)

`src/api/types.ts` — типы строго по контракту:

```typescript
export type TaskStatus = 'new' | 'in_progress' | 'done' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high';

export type SortField = 'createdAt' | 'dueDate' | 'priority' | 'title';
export type SortOrder = 'asc' | 'desc';

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
  categoryId: number | null;
}

export interface PagedResult<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface TaskSummary {
  total: number;
  done: number;
  notDone: number;
  overdue: number;
  byPriority: Record<string, number>;
}

export interface LoginResponse {
  token: string;
  tokenType: string;
  expiresIn: number;
  user: User;
}

/** Единая обёртка ответа API. */
export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  message: string;
  error_code: string | null;
}
```

`src/api/tokenStorage.ts` — токен в `localStorage`, чтобы он пережил
перезагрузку:

```typescript
const TOKEN_KEY = 'taskplanner.token';
const USER_KEY = 'taskplanner.user';

export const tokenStorage = {
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  },

  getUser(): User | null {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;

    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  },

  setUser(user: User): void {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },

  clear(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};
```

> **Замечание:** `localStorage` читается **синхронно**, поэтому его удобно
> положить в отдельный модуль, а не размазывать по компонентам. Реактивность
> для него не нужна — компоненты узнают о входе через состояние на
> [15-Токен-и-защита-маршрутов](15-Токен-и-защита-маршрутов).

`src/api/client.ts`:

```typescript
import axios from 'axios';
import type {
  ApiResponse,
  LoginResponse,
  PagedResult,
  Task,
  TaskPriority,
  TaskStatus,
  SortField,
  SortOrder,
  TaskSummary,
} from './types';
import { tokenStorage } from './tokenStorage';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// Каждый запрос уходит с токеном
api.interceptors.request.use((config) => {
  const token = tokenStorage.getToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// Токен протух или его нет — выходим и возвращаем на страницу входа
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      tokenStorage.clear();
      window.location.assign('/login');
    }

    return Promise.reject(error);
  },
);

/** Достаёт message из обёртки API, чтобы показать его пользователю. */
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const body = error.response?.data as ApiResponse<unknown> | undefined;

    if (body?.message) {
      // Убираем технический хвост с traceId — он нужен в логах, не в интерфейсе.
      return body.message.split(' (traceId:')[0];
    }

    if (error.code === 'ECONNABORTED') {
      return 'Сервер не отвечает. Проверьте, что API запущен.';
    }

    if (!error.response) {
      return 'Нет связи с сервером. Проверьте, что API запущен на порту 5000.';
    }
  }

  return 'Что-то пошло не так. Попробуйте ещё раз.';
}

export interface AuthApi {
  register: (body: { email: string; password: string; fullName: string }) =>
    Promise<User>;
  login: (body: { email: string; password: string }) => Promise<LoginResponse>;
}

export const authApi: AuthApi = {
  async register(body) {
    const response = await api.post<ApiResponse<{ user: import('./types').User }>>(
      '/auth/register',
      body,
    );

    return response.data.data!.user;
  },

  async login(body) {
    const response = await api.post<ApiResponse<LoginResponse>>('/auth/login', body);

    return response.data.data!;
  },
};

export interface TaskQueryParams {
  status?: TaskStatus;
  priority?: TaskPriority;
  dueDate?: string;
  q?: string;
  sort?: SortField;
  order?: SortOrder;
  page?: number;
  pageSize?: number;
}

export const tasksApi = {
  async list(params: TaskQueryParams = {}): Promise<PagedResult<Task>> {
    const response = await api.get<ApiResponse<PagedResult<Task>>>('/tasks', { params });

    return response.data.data!;
  },

  async getById(id: number): Promise<Task> {
    const response = await api.get<ApiResponse<Task>>(`/tasks/${id}`);

    return response.data.data!;
  },

  async create(body: Partial<Task>): Promise<Task> {
    const response = await api.post<ApiResponse<Task>>('/tasks', body);

    return response.data.data!;
  },

  async update(id: number, body: Partial<Task>): Promise<Task> {
    const response = await api.put<ApiResponse<Task>>(`/tasks/${id}`, body);

    return response.data.data!;
  },

  async remove(id: number): Promise<void> {
    await api.delete(`/tasks/${id}`);
  },

  async toggleCompleted(id: number): Promise<Task> {
    const response = await api.patch<ApiResponse<Task>>(`/tasks/${id}/complete`);

    return response.data.data!;
  },

  async summary(): Promise<TaskSummary> {
    const response = await api.get<ApiResponse<TaskSummary>>('/tasks/summary');

    return response.data.data!;
  },
};
```

> **Замечание:** `response.data.data!` — «непустое утверждение» в TypeScript.
> Оно оправдано: контракт API гарантирует `data` при `success: true`. Если
> сервер вернул `success: false` с кодом 2xx, это уже нарушение контракта и
> такой случай стоит обработать. Альтернатива — маленький хелпер
> `unwrap<T>(response): T`, который бросает исключение при `!success`.

# 4. Прокси Vite (30–35 мин)

Без прокси запросы уходили бы на `http://localhost:5173/api/...` и падали с
CORS. С прокси они уходят на API **с того же origin** — CORS не возникает.

`src/web/vite.config.ts`:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      // Клиент ходит на /api — Vite пересылает запрос на API.
      // Токен остаётся в одном origin, CORS не нужен.
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
});
```

`src/web/.env.example`:

```bash
VITE_API_BASE_URL=/api
```

Создайте `.env.local` (в `.gitignore` он уже есть):

```bash
cp .env.example .env.local
```

> **Замечание:** переменные Vite читаются только из файлов, имена которых
> начинаются с `VITE_`. Всё, что попало в `import.meta.env`, попадает в
> итоговый бандл **в открытом виде** — секреты туда класть нельзя.

# 5. Точка входа и стили (35–40 мин)

`src/web/index.html`:

```html
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Планировщик задач</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

`meta viewport` обязателен: без него адаптивность на телефоне не работает,
а по критериям нужен корректный вид от 360 px.

`src/web/src/main.tsx`:

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import './styles/global.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

`src/web/src/styles/global.css`:

```css
:root {
  --green: #0f9346;
  --green-lite: #4ecc0a;
  --yellow: #fcee73;
  --dark: #364046;
  --grey: #6d797f;
  --light: #f1f6f2;
  --white: #ffffff;
  --red: #d13c3c;
  --radius: 12px;
  --space: 8px;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: 'Segoe UI', Roboto, system-ui, Arial, sans-serif;
  color: var(--dark);
  background: var(--light);
  -webkit-font-smoothing: antialiased;
}

h1,
h2,
h3 {
  margin: 0;
}

button {
  font: inherit;
  cursor: pointer;
  border: none;
  border-radius: var(--radius);
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-primary {
  background: var(--green);
  color: var(--white);
  padding: 12px 20px;
}

.btn-primary:hover:not(:disabled) {
  background: var(--green-lite);
}

.btn-secondary {
  background: var(--white);
  color: var(--dark);
  padding: 12px 20px;
  border: 1px solid #dde3e0;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: calc(var(--space) * 2);
}

.field label {
  font-size: 14px;
  color: var(--grey);
}

.field input,
.field select,
.field textarea {
  font: inherit;
  padding: 10px 12px;
  border: 1px solid #dde3e0;
  border-radius: var(--radius);
  background: var(--white);
  color: var(--dark);
}

.field input:focus,
.field select:focus,
.field textarea:focus {
  outline: 2px solid var(--green-lite);
  outline-offset: 1px;
}

.error {
  background: #fdecec;
  border: 1px solid var(--red);
  color: var(--red);
  padding: 10px 14px;
  border-radius: var(--radius);
  margin-bottom: calc(var(--space) * 2);
}

.success {
  background: #eaf7ee;
  border: 1px solid var(--green);
  color: var(--green);
  padding: 10px 14px;
  border-radius: var(--radius);
}
```

# Проверка

```bash
cd src/web
npm run dev
```

В консоли: `Local: http://localhost:5173/`.

Страница пока пустая — маршруты будут на
[14-Регистрация-и-вход](14-Регистрация-и-вход), но проверьте, что прокси
работает. Откройте DevTools → Console и введите:

```javascript
await fetch('/api/health').then((r) => r.json())
```

Должно вернуть `{success: true, data: {status: 'ok', ...}}`. Если пришло
`404` или ошибка CORS — прокси не настроен или API не запущен.

Проверка, что бандл не содержит секретов:

```bash
grep -ri "password.*=.*'" dist/ 2>/dev/null | head
# пусто
```

# Коммит

```bash
git add src/web
git commit -m "Web-клиент: React-проект, типы API, клиент с интерцептором, прокси Vite"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| `fetch('/api/health')` вернул `404` | API не запущен, либо в `vite.config.ts` нет блока `proxy` |
| `changeOrigin` ругается в редакторе | правильное имя опции — `changeOrigin: true` |
| `import.meta.env.VITE_API_BASE_URL` — `undefined` | переименуйте файл в `.env.local` и перезапустите `npm run dev` |
| `Node 20+ требуется` | обновите Node, см. [00-Подготовка-окружения](00-Подготовка-окружения) |
| Типы не совпадают с API | сверьтесь с `api/openapi.yaml`; не выдумывайте поля |
| В консоли ошибка про `import.meta.env` | в `tsconfig.json` должен быть `"types": ["vite/client"]` |

# Что должно быть в репозитории к концу сессии 5, блок 1

- [ ] Vite-проект React + TypeScript
- [ ] `src/api/types.ts` — типы по контракту
- [ ] `src/api/tokenStorage.ts`
- [ ] `src/api/client.ts` с интерцепторами токена и 401
- [ ] `vite.config.ts` с прокси `/api` → `http://localhost:5000`
- [ ] `index.html` с `viewport`, глобальные стили

## Иллюстрации

![[images/web13-explorer.png]]
*Структура веб-клиента в VS Code*

![[images/web13-api-client.png]]
*Слой API: токен в localStorage и разбор конверта*

![[images/web13-vite-proxy.png]]
*Прокси `/api` на сервер в `vite.config.js`*
