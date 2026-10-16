/* ===========================================================================
   ТОиР-Проф — хук загрузки данных.
   Снимает три задачи, повторяющиеся на каждом экране: отменять прежний
   запрос, показывать индикатор и превращать ошибку в текст для баннера.
   =========================================================================== */

import { useCallback, useEffect, useRef, useState } from 'react'
import { HttpError } from '../api/http'

export interface LoadState<T> {
  data: T | null
  loading: boolean
  error: string | null
  /** Перезагрузить принудительно — кнопка «Повторить» в баннере. */
  reload: () => void
  /** Обновить данные из уже пришедшего ответа потока событий. */
  set: (value: T) => void
}

export function useLoad<T>(load: (signal: AbortSignal) => Promise<T>, deps: readonly unknown[]): LoadState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  // Запрос хранится в ref: useEffect зависит только от deps и tick,
  // а не от самой функции load, которую страница пересоздаёт каждый рендер.
  const loadRef = useRef(load)
  loadRef.current = load

  useEffect(() => {
    const controller = new AbortController()
    let active = true

    setLoading(true)
    setError(null)

    loadRef
      .current(controller.signal)
      .then((value) => {
        if (!active) return
        setData(value)
      })
      .catch((cause: unknown) => {
        if (!active || controller.signal.aborted) return
        if (cause instanceof DOMException && cause.name === 'AbortError') return
        setError(cause instanceof HttpError ? cause.message : 'Не удалось загрузить данные.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
      controller.abort()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick])

  const reload = useCallback(() => setTick((value) => value + 1), [])
  const set = useCallback((value: T) => setData(value), [])

  return { data, loading, error, reload, set }
}

/**
 * Хук для действий с кнопки: одна кнопка не должна нажиматься дважды,
 * пока предыдущий запрос ещё идёт.
 */
export function useAction() {
  const [busy, setBusy] = useState(false)
  const busyRef = useRef(false)

  const run = useCallback(async <T,>(action: () => Promise<T>): Promise<T | null> => {
    if (busyRef.current) return null
    busyRef.current = true
    setBusy(true)
    try {
      return await action()
    } finally {
      busyRef.current = false
      setBusy(false)
    }
  }, [])

  return { busy, run }
}
