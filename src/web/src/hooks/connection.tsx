/* ===========================================================================
   ТОиР-Проф — контекст состояния соединения.

   Поток событий живёт на странице дашборда, а индикатор соединения должен
   быть виден на любой странице — в шапке. Поэтому статус хранится в
   контексте: дашборд его записывает, шапка читает.
   =========================================================================== */

import { createContext, useContext, useMemo, useState } from 'react'
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

  const value = useMemo<ConnectionValue>(
    () => ({
      status: state.status,
      caption: state.caption,
      setConnection: (status, caption) => setState({ status, caption }),
    }),
    [state],
  )

  return <ConnectionContext.Provider value={value}>{children}</ConnectionContext.Provider>
}

export function useConnection(): ConnectionValue {
  const value = useContext(ConnectionContext)
  if (!value) throw new Error('useConnection вызван вне ConnectionProvider')
  return value
}
