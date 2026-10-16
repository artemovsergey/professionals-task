/* ===========================================================================
   ТОиР-Проф — экран входа.
   =========================================================================== */

import { useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { HttpError } from '../api/http'

export function LoginPage() {
  const { session, ready, login } = useAuth()
  const [username, setUsername] = useState('master')
  const [password, setPassword] = useState('Master123!')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (ready && session) return <Navigate to="/" replace />

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      await login({ username: username.trim(), password })
      // Навигацию делает AuthContext: как только появилась сессия,
      // защищённый маршрут пропускает пользователя на дашборд.
    } catch (cause) {
      setError(
        cause instanceof HttpError
          ? cause.message
          : 'Не удалось войти. Проверьте логин, пароль и доступность сервера.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login">
      <form className="login__card" onSubmit={submit}>
        <div className="login__brand">
          <span className="brand__mark">ТП</span>
          <div>
            <h1>ТОиР-Проф</h1>
            <span className="muted">Система управления техническим обслуживанием</span>
          </div>
        </div>

        <div className="field">
          <label className="field__label" htmlFor="login-user">
            Логин
          </label>
          <input
            id="login-user"
            className="input"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
            required
          />
        </div>

        <div className="field" style={{ marginTop: 12 }}>
          <label className="field__label" htmlFor="login-pass">
            Пароль
          </label>
          <input
            id="login-pass"
            className="input"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </div>

        {error ? (
          <div className="banner" style={{ marginTop: 14 }} role="alert">
            <span className="banner__text">{error}</span>
          </div>
        ) : null}

        <button type="submit" className="btn btn--primary" style={{ width: '100%', marginTop: 16 }} disabled={busy}>
          {busy ? 'Вход…' : 'Войти'}
        </button>

        <div className="login__hint">
          Демонстрационные учётные записи: <code>master / Master123!</code>,{' '}
          <code>manager / Manager123!</code>, <code>admin / Admin123!</code>.
        </div>
      </form>
    </div>
  )
}
