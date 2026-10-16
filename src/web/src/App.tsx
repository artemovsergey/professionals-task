/* ===========================================================================
   ТОиР-Проф — точка входа веб-клиента.

   Провайдеры стоят в таком порядке:
     AuthProvider   — токен и профиль;
     ToastProvider  — всплывающие сообщения;
     ConnectionProvider — статус соединения, который пишет дашборд
                          и который показывает индикатор в верхней панели.
   =========================================================================== */

import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { ConnectionProvider, useConnection } from './hooks/connection'
import { ConnectionBadge } from './components/Ui'
import { ToastProvider } from './components/ToastProvider'
import { AppShell } from './layout/AppShell'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { CrewsPage } from './pages/CrewsPage'
import { DashboardPage } from './pages/DashboardPage'
import { EquipmentPage } from './pages/EquipmentPage'
import { LoginPage } from './pages/LoginPage'
import { MaterialsPage } from './pages/MaterialsPage'
import { SchedulePage } from './pages/SchedulePage'
import { UsersPage } from './pages/UsersPage'
import { WorkOrdersPage } from './pages/WorkOrdersPage'

/**
 * Индикатор соединения в верхней панели. Отдельный компонент, потому что
 * useConnection() можно вызвать только внутри провайдера, а шапка
 * отрисовывается вложенным маршрутом уже после него.
 */
function TopBarConnection() {
  const { status, caption } = useConnection()
  return <ConnectionBadge status={status} caption={caption} />
}

/** Пока пользователь не проверил токен, нельзя ни пускать дальше, ни ругать на 401. */
function RequireAuth({ children }: { children: ReactNode }) {
  const { session, ready } = useAuth()

  if (!ready) {
    return (
      <div className="state" style={{ minHeight: '60vh' }}>
        <div className="spinner" />
        <span>Проверяю сеанс…</span>
      </div>
    )
  }

  if (!session) return <Navigate to="/login" replace />

  return <>{children}</>
}

function ProtectedLayout() {
  return (
    <RequireAuth>
      <AppShell connection={<TopBarConnection />} />
    </RequireAuth>
  )
}

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <ConnectionProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />

              <Route element={<ProtectedLayout />}>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/analytics" element={<AnalyticsPage />} />
                <Route path="/equipment" element={<EquipmentPage />} />
                <Route path="/schedule" element={<SchedulePage />} />
                <Route path="/work-orders" element={<WorkOrdersPage />} />
                <Route path="/crews" element={<CrewsPage />} />
                <Route path="/materials" element={<MaterialsPage />} />
                <Route path="/users" element={<UsersPage />} />
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ConnectionProvider>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App