/* ===========================================================================
   ТОиР-Проф — всплывающие сообщения (toast).
   Провайдер раздаёт функцию сообщения всем страницам через useToast(),
   а список сам удаляет сообщения по таймеру.
   =========================================================================== */

import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'

export type ToastKind = 'info' | 'success' | 'warning' | 'error'

interface ToastItem {
  id: number
  kind: ToastKind
  message: string
}

interface ToastValue {
  show: (message: string, kind?: ToastKind) => void
  success: (message: string) => void
  error: (message: string) => void
  warning: (message: string) => void
}

const ToastContext = createContext<ToastValue | null>(null)

const GLYPH: Record<ToastKind, string> = {
  info: 'i',
  success: '✓',
  warning: '!',
  error: '✕',
}

/** Сообщение живёт 4 секунды; ошибки — вдвое дольше, чтобы их успели прочитать. */
const LIFETIME_MS = 4000
const ERROR_LIFETIME_MS = 8000

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])
  const nextId = useRef(1)

  const dismiss = useCallback((id: number) => {
    setItems((current) => current.filter((item) => item.id !== id))
  }, [])

  const show = useCallback(
    (message: string, kind: ToastKind = 'info') => {
      const id = nextId.current++
      setItems((current) => [...current.slice(-4), { id, kind, message }])
      window.setTimeout(() => dismiss(id), kind === 'error' ? ERROR_LIFETIME_MS : LIFETIME_MS)
    },
    [dismiss],
  )

  const value = useMemo<ToastValue>(
    () => ({
      show,
      success: (message: string) => show(message, 'success'),
      warning: (message: string) => show(message, 'warning'),
      error: (message: string) => show(message, 'error'),
    }),
    [show],
  )

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toasts no-print" aria-live="polite">
        {items.map((item) => (
          <div key={item.id} className={`toast toast--${item.kind}`}>
            <span className="toast__glyph" aria-hidden="true">
              {GLYPH[item.kind]}
            </span>
            <span className="toast__text">{item.message}</span>
            <button type="button" className="toast__close" onClick={() => dismiss(item.id)} aria-label="Закрыть">
              ✕
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast(): ToastValue {
  const value = useContext(ToastContext)
  if (!value) throw new Error('useToast вызван вне ToastProvider')
  return value
}
