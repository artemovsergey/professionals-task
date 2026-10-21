/* ===========================================================================
   ТОиР-Проф — контекст состояния соединения.

   Поток событий живёт на странице дашборда, а индикатор соединения должен
   быть виден на любой странице — в шапке. Поэтому статус хранится в
   контексте: дашборд его записывает, шапка читает.
   =========================================================================== */

import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type { StreamStatus } from './useDashboardStream'

interface ConnectionValue {
  status: StreamStatus
  caption: string
  setConnection: (status: StreamStatus, caption: string) => void
}

const INITIAL: StreamStatus = 'live'

const ConnectionContext = createContext<ConnectionValue | null>(null)

export function ConnectionProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState({ status: INITIAL as StreamStatus, caption: 'Ожидание обновлений' })

  // Функция записи обязана быть неизменной по ссылке. Дашборд пишет статус
  // в контекст из useEffect, и если бы setConnection пересоздавался при
  // каждом обновлении состояния, эффект запускался бы снова и снова —
  // React останавливал это ошибкой «Maximum update depth exceeded».
  // Заодно отсекаем запись тех же значений: setState с новым объектом при
  // равных полях тоже меняет ссылку и зацикливает обновление.
  const setConnection = useCallback((status: StreamStatus, caption: string) => {
    setState((current) =>
      current.status === status && current.caption === caption ? current : { status, caption },
    )
  }, [])

  const value = useMemo<ConnectionValue>(
    () => ({ status: state.status, caption: state.caption, setConnection }),
    [state.status, state.caption, setConnection],
  )

  return <ConnectionContext.Provider value={value}>{children}</ConnectionContext.Provider>
}

export function useConnection(): ConnectionValue {
  const value = useContext(ConnectionContext)
  if (!value) throw new Error('useConnection вызван вне ConnectionProvider')
  return value
}
