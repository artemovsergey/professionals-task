/* ===========================================================================
   ТОиР-Проф — оболочка приложения: боковое меню, верхняя панель,
   область содержимого. Меню и права ролей описаны здесь, а не размазаны
   по страницам: при добавлении раздела достаточно одной строки.
   =========================================================================== */

import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import type { RoleCode } from '../api/types'

interface NavEntry {
  to: string
  label: string
  glyph: string
  group: string
  roles: RoleCode[]
}

/**
 * Права по разделам. Администратор видит всё, руководитель — сводку и
 * справочники, мастер — только свою работу с оборудованием и заявками.
 * Сервер проверяет права повторно, но скрывать недоступное нужно и в меню:
 * иначе руководитель увидит кнопку, которая вернёт 403.
 */
const MENU: NavEntry[] = [
  { to: '/', label: 'Дашборд руководителя', glyph: 'Д', group: 'Сводка', roles: ['ADMIN', 'MANAGER', 'MASTER'] },
  { to: '/analytics', label: 'Аналитика', glyph: 'А', group: 'Сводка', roles: ['ADMIN', 'MANAGER'] },
  { to: '/equipment', label: 'Оборудование', glyph: 'О', group: 'Учёт', roles: ['ADMIN', 'MANAGER', 'MASTER'] },
  { to: '/schedule', label: 'График ТО', glyph: 'Г', group: 'Учёт', roles: ['ADMIN', 'MANAGER', 'MASTER'] },
  { to: '/work-orders', label: 'Заявки', glyph: 'З', group: 'Учёт', roles: ['ADMIN', 'MANAGER', 'MASTER'] },
  { to: '/crews', label: 'Бригады', glyph: 'Б', group: 'Справочники', roles: ['ADMIN', 'MANAGER'] },
  { to: '/materials', label: 'Материалы и ЗИП', glyph: 'М', group: 'Справочники', roles: ['ADMIN', 'MANAGER'] },
  { to: '/users', label: 'Пользователи', glyph: 'П', group: 'Справочники', roles: ['ADMIN'] },
]

const ROLE_TITLE: Record<RoleCode, string> = {
  ADMIN: 'Администратор',
  MANAGER: 'Руководитель',
  MASTER: 'Мастер',
}

export function AppShell({ connection }: { connection?: React.ReactNode }) {
  const { session, logout, can } = useAuth()

  const groups: string[] = []
  for (const entry of MENU) {
    if (!groups.includes(entry.group)) groups.push(entry.group)
  }

  return (
    <div className="shell">
      <div className="brand">
        <span className="brand__mark">ТП</span>
        <span className="brand__title">
          ТОиР-Проф
          <span className="brand__sub">учёт обслуживания</span>
        </span>
      </div>

      <header className="topbar">
        {connection}
        {session ? (
          <>
            <span className="topbar__user">
              {session.user.fullName} · {ROLE_TITLE[session.role]}
            </span>
            <button type="button" className="btn btn--sm" onClick={logout}>
              Выйти
            </button>
          </>
        ) : null}
      </header>

      <nav className="sidebar">
        {groups.map((group) => (
          <div key={group}>
            <div className="sidebar__group">{group}</div>
            {MENU.filter((entry) => entry.group === group && can(...entry.roles)).map((entry) => (
              <NavLink
                key={entry.to}
                to={entry.to}
                end={entry.to === '/'}
                className={({ isActive }) => (isActive ? 'menu-item menu-item--active' : 'menu-item')}
                title={entry.label}
              >
                <span className="menu-item__glyph" aria-hidden="true">
                  {entry.glyph}
                </span>
                <span className="menu-item__label">{entry.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}

export { MENU, ROLE_TITLE }
export type { NavEntry }
