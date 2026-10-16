/* ===========================================================================
   ТОиР-Проф — приём данных в реальном времени.

   Требование листа: WebSocket или SSE, при этом должен быть резервный опрос,
   автоматическое переподключение с экспоненциальной задержкой и индикатор
   состояния соединения. Реализация:

   1. Пытаемся открыть Server-Sent Events на /api/dashboard/events.
   2. Если поток молчит дольше заданного окна (сервер мог не поддерживать SSE,
      соединение могло зависнуть) — переходим на опрос раз в 60 секунд.
   3. При обрыве переподключаемся с задержкой 1с, 2с, 4с… до 30с.
   4. Отдаём странице статус соединения, чтобы показать индикатор.
   =========================================================================== */

import { useEffect, useRef, useState } from 'react'
import { DASHBOARD_EVENTS_PATH, dashboardApi } from '../api/endpoints'
import { getToken } from '../api/http'
import type { DashboardSummary } from '../api/types'

export type StreamStatus = 'live' | 'polling' | 'offline'

export interface DashboardStream {
  data: DashboardSummary | null
  status: StreamStatus
  /** Подпись для индикатора: «в реальном времени», «опрос 60 с», «нет связи». */
  caption: string
  lastUpdate: Date | null
  from: string
  to: string
}

/** Задержка переподключения: 1с, 2с, 4с, 8с, 16с, 30с и далее 30с. */
function backoffDelay(attempt: number): number {
  return Math.min(30_000, 1000 * 2 ** Math.max(0, attempt - 1))
}

const POLL_INTERVAL_MS = 60_000
const SILENCE_TIMEOUT_MS = 12_000
const POLL_AFTER_ATTEMPTS = 3

/**
 * refreshToken — счётчик ручных перезапросов. Страница увеличивает его
 * кнопкой «Повторить», и хук переоткрывает поток: иначе после обрыва
 * соединения единственным способом получить данные был бы перезагруз
 * страницы целиком.
 */
export function useDashboardStream(from: string, to: string, refreshToken = 0): DashboardStream {
  const [data, setData] = useState<DashboardSummary | null>(null)
  const [status, setStatus] = useState<StreamStatus>('live')
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const sourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    let disposed = false
    let attempts = 0
    let reconnectTimer: number | undefined
    let pollTimer: number | undefined
    let silenceTimer: number | undefined
    let failures = 0

    const applySummary = (summary: DashboardSummary) => {
      if (disposed) return
      setData(summary)
      setLastUpdate(new Date())
      failures = 0
      attempts = 0
    }

    const poll = async () => {
      try {
        applySummary(await dashboardApi.summary(from, to))
        setStatus('polling')
      } catch {
        // Сеть легла: показываем «нет связи» и пробуем опрос позже.
        setStatus('offline')
      }
    }

    const scheduleReconnect = () => {
      if (disposed) return
      attempts += 1
      const delay = backoffDelay(attempts)
      reconnectTimer = window.setTimeout(() => {
        void connect()
      }, delay)
    }

    const connect = async () => {
      if (disposed) return

      const token = getToken()
      if (!token) return

      // EventSource не умеет задавать заголовки, поэтому токен передаётся
      // параметром запроса. Сервер его читает через query.
      const url = `${DASHBOARD_EVENTS_PATH}?access_token=${encodeURIComponent(token)}`
      const source = new EventSource(url)
      sourceRef.current = source

      let received = false
      const markReceived = () => {
        received = true
        setStatus('live')
        window.clearTimeout(silenceTimer)
        silenceTimer = window.setTimeout(() => {
          // Поток открыт, но данных нет. На старте это нормально (изменений
          // могло не быть), после нескольких попыток переходим на опрос.
          if (!received && attempts >= POLL_AFTER_ATTEMPTS) void startPolling()
        }, SILENCE_TIMEOUT_MS)
      }

      source.addEventListener('open', markReceived)
      source.addEventListener('dashboard.updated', (event) => {
        try {
          applySummary(JSON.parse((event as MessageEvent<string>).data) as DashboardSummary)
        } catch {
          // Повреждённое событие игнорируем: следующее придёт через минуту.
        }
      })
      source.addEventListener('dashboard.ping', markReceived)
      source.onerror = () => {
        source.close()
        sourceRef.current = null
        if (disposed) return
        failures += 1
        if (failures >= POLL_AFTER_ATTEMPTS) {
          void startPolling()
          return
        }
        scheduleReconnect()
      }
    }

    const startPolling = async () => {
      if (disposed) return
      window.clearInterval(pollTimer)
      await poll()
      pollTimer = window.setInterval(() => void poll(), POLL_INTERVAL_MS)
    }

    void connect()

    return () => {
      disposed = true
      window.clearTimeout(reconnectTimer)
      window.clearInterval(pollTimer)
      window.clearTimeout(silenceTimer)
      sourceRef.current?.close()
      sourceRef.current = null
    }
  }, [from, to, refreshToken])

  const caption =
    status === 'live'
      ? 'Обновление в реальном времени'
      : status === 'polling'
        ? `Резервный опрос раз в ${POLL_INTERVAL_MS / 1000} с`
        : 'Нет связи с сервером'

  return { data, status, caption, lastUpdate, from, to }
}
