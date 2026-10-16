/* ===========================================================================
   ТОиР-Проф — контекст авторизации.
   Держит профиль пользователя и токен, умеет входить и выходить. Страницы
   получают профиль через useAuth(), а RequireAuth не пускает без токена.
   =========================================================================== */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { HttpError, clearToken, getCachedUser, getToken, http, setToken } from '../api/http'
import type { LoginDto, RoleCode, TokenResponse, UserDto } from '../api/types'

export interface Session {
  user: UserDto
  role: RoleCode
}

interface AuthValue {
  session: Session | null
  ready: boolean
  login: (dto: LoginDto) => Promise<void>
  logout: () => void
  /** Есть ли у роли право на раздел. Меню и кнопки спрашивают здесь. */
  can: (...roles: RoleCode[]) => boolean
}

const AuthContext = createContext<AuthValue | null>(null)

function toRole(code: string): RoleCode {
  const upper = code.toUpperCase()
  return upper === 'ADMIN' || upper === 'MANAGER' || upper === 'MASTER' ? upper : 'MASTER'
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  // Если токена или сохранённого профиля нет, проверять нечего — сразу готовы.
  const [ready, setReady] = useState(() => !getToken() || !getCachedUser())

  // Токен лежит в localStorage, но профиль после перезагрузки надо заново
  // получить: он мог измениться (роль, активность учётной записи).
  useEffect(() => {
    if (ready) return

    const controller = new AbortController()
    http
      .get<UserDto>('/auth/me', controller.signal)
      .then((user) => setSession({ user, role: toRole(user.role) }))
      // 401 после перезагрузки — обычное дело: токен истёк за время перерыва.
      .catch((error: unknown) => {
        if (error instanceof HttpError && error.isUnauthorized) clearToken()
      })
      .finally(() => setReady(true))

    return () => controller.abort()
  }, [ready])

  const login = useCallback(async (dto: LoginDto) => {
    const response = await http.post<TokenResponse>('/auth/login', dto)
    setToken(response.token, JSON.stringify(response.user))
    setSession({ user: response.user, role: toRole(response.user.role) })
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setSession(null)
  }, [])

  const can = useCallback(
    (...roles: RoleCode[]) => (session ? roles.includes(session.role) : false),
    [session],
  )

  const value = useMemo<AuthValue>(
    () => ({ session, ready, login, logout, can }),
    [session, ready, login, logout, can],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth вызван вне AuthProvider')
  return value
}
