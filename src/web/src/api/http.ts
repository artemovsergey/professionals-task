/* ===========================================================================
   ТОиР-Проф — HTTP-клиент.
   Все запросы идут на относительный путь /api/... — их перехватывает прокси
   Vite из vite.config.ts. Так клиент одинаково работает и при `npm run dev`
   (5173), и при раздаче статики с любого адреса: абсолютный хост прописан
   только один раз, в прокси.
   =========================================================================== */

/** Ответ API в единой обёртке `{ success, data, message, error_code }`. */
interface Envelope<T> {
  success: boolean
  data: T | null
  message: string
  errorCode: string | null
}

/**
 * Секрет для сессии лежит в localStorage: после перезагрузки вкладки
 * пользователь остаётся внутри приложения, а не возвращается на форму входа.
 * Имя ключа совпадает с desktop-клиентом — оба клиента независимы, но
 * полезно открывать один профиль в двух приложениях.
 */
const TOKEN_KEY = 'toirprof.token'
const USER_KEY = 'toirprof.user'

/** Ошибка с кодом ответа нужна страницам: 401 разлогинивает, 403 показывает баннер. */
export class HttpError extends Error {
  readonly status: number
  readonly code: string

  constructor(message: string, status: number, code: string) {
    super(message)
    this.name = 'HttpError'
    this.status = status
    this.code = code
  }

  /** 401 — токен протух или неверен, пора слать на форму входа. */
  get isUnauthorized(): boolean {
    return this.status === 401
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string, userJson: string): void {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, userJson)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

/** Пользователь для отображения в шапке до первого запроса /api/auth/me. */
export function getCachedUser(): { username: string; fullName: string; role: string } | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as { username: string; fullName: string; role: string }
  } catch {
    // Повреждённая запись в localStorage не должна ронять приложение:
    // просто забываем её и показываем форму входа.
    clearToken()
    return null
  }
}

export function buildQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    search.append(key, String(value))
  }
  const text = search.toString()
  return text ? `?${text}` : ''
}

async function request<T>(method: string, path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let response: Response
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers,
      signal,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch (cause) {
    // Сеть недоступна или запрос отменён. Отмена — не ошибка приложения,
    // поэтому её пробрасываем как есть, а обрыв связи помечаем кодом 0.
    if (cause instanceof DOMException && cause.name === 'AbortError') throw cause
    throw new HttpError('Нет связи с сервером. Проверьте, запущен ли API.', 0, 'NETWORK')
  }

  if (response.status === 204) return undefined as T

  let payload: Envelope<T> | null = null
  try {
    payload = (await response.json()) as Envelope<T>
  } catch {
    // Тело не JSON — сервер вернул 500 с пустым ответом или прокси срезал.
    if (!response.ok) throw new HttpError(`Ошибка ${response.status}`, response.status, 'INTERNAL_ERROR')
    return undefined as T
  }

  if (!response.ok || payload?.success === false) {
    throw new HttpError(
      payload?.message || `Ошибка ${response.status}`,
      response.status,
      payload?.errorCode || 'INTERNAL_ERROR',
    )
  }

  return payload?.data as T
}

export const http = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>('GET', path, undefined, signal),
  post: <T>(path: string, body: unknown, signal?: AbortSignal) => request<T>('POST', path, body, signal),
  put: <T>(path: string, body: unknown, signal?: AbortSignal) => request<T>('PUT', path, body, signal),
  patch: <T>(path: string, body: unknown, signal?: AbortSignal) => request<T>('PATCH', path, body, signal),
  delete: <T>(path: string, signal?: AbortSignal) => request<T>('DELETE', path, undefined, signal),
}
