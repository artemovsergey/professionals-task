/* ===========================================================================
   ТОиР-Проф — пользователи и состав бригад.

   Отдельного эндпоинта пользователей в API нет: он не требовался листом
   задания, а данные о людях есть в составе бригад. Поэтому страница
   показывает профиль текущего пользователя и сводный список сотрудников
   по бригадам — это ровно то, что нужно администратору на демонстрации.
   =========================================================================== */

import { useMemo, useState } from 'react'
import { crewsApi } from '../api/endpoints'
import type { CrewDto } from '../api/types'
import { DataTable } from '../components/DataTable'
import type { Column } from '../components/DataTable'
import { Badge, Card, EmptyState, ErrorBanner, LoadingBar, MetricCard } from '../components/Ui'
import { useAuth } from '../auth/AuthContext'
import { ROLE_TITLE } from '../layout/AppShell'
import { useLoad } from '../hooks/useLoad'
import { formatDate } from '../utils/format'

interface MemberRow {
  userId: string
  username: string
  fullName: string
  joinedAt: string
  crewCode: string
  crewName: string
}

const columns: Column<MemberRow>[] = [
  { key: 'username', title: 'Логин', render: (row) => <span className="mono">{row.username}</span> },
  { key: 'fullName', title: 'Сотрудник', render: (row) => row.fullName },
  { key: 'crewCode', title: 'Бригада', render: (row) => <span className="mono">{row.crewCode}</span> },
  { key: 'crewName', title: 'Название бригады', render: (row) => row.crewName },
  { key: 'joinedAt', title: 'В бригаде с', numeric: true, render: (row) => formatDate(row.joinedAt) },
]

export function UsersPage() {
  const { session, can } = useAuth()

  const [search, setSearch] = useState('')

  // Состав бригад лежит в карточке бригады, а не в списке, поэтому после
  // выборки списка идёт запрос по каждой бригаде. Бригад в системе единицы,
  // поэтому N+1 здесь не превращается в проблему.
  const crews = useLoad<CrewDto[]>(
    async (signal) => {
      const page = await crewsApi.list({ includeInactive: true, pageSize: 100 }, signal)
      return Promise.all(page.items.map((row) => crewsApi.byId(row.id, signal)))
    },
    [],
  )

  const members = useMemo(() => {
    const result: MemberRow[] = []
    for (const crew of crews.data ?? []) {
      for (const member of crew.members) {
        result.push({
          userId: member.userId,
          username: member.username,
          fullName: member.fullName,
          joinedAt: member.joinedAt,
          crewCode: crew.code,
          crewName: crew.name,
        })
      }
    }
    const needle = search.trim().toLowerCase()
    const filtered =
      needle === ''
        ? result
        : result.filter((row) => `${row.username} ${row.fullName}`.toLowerCase().includes(needle))
    return filtered.sort((left, right) => left.fullName.localeCompare(right.fullName, 'ru'))
  }, [crews.data, search])

  const allowed = can('ADMIN')

  return (
    <div className="grid">
      <div className="section-title no-print">
        <h1>Пользователи</h1>
        <span className="muted">сотрудников в бригадах: {members.length}</span>
        <button
          type="button"
          className="btn btn--ghost btn--sm"
          disabled={crews.loading}
          onClick={crews.reload}
        >
          Обновить состав
        </button>
      </div>

      <LoadingBar visible={crews.loading} />

      {!allowed ? <ErrorBanner message="Раздел доступен администратору." /> : null}

      <Card title="Текущий пользователь">
        {session ? (
          <div className="kpi-row">
            <MetricCard title="Логин" value={session.user.username} />
            <MetricCard title="Сотрудник" value={session.user.fullName} />
            <MetricCard title="Роль" value={ROLE_TITLE[session.role]} tone="info" />
            <MetricCard title="Учётная запись" value={session.user.isActive ? 'активна' : 'отключена'} tone={session.user.isActive ? 'ok' : 'bad'} />
            <MetricCard title="В системе с" value={formatDate(session.user.createdAt)} />
          </div>
        ) : (
          <EmptyState caption="Профиль недоступен" />
        )}
        <span className="muted">
          Роль определяется на сервере и попадает в токен. Разделы меню фильтруются по этой роли, а сервер проверяет
          права повторно и отвечает 403 при попытке обойти меню.
        </span>
      </Card>

      <Card title="Сотрудники по бригадам" className="no-print">
        <label className="field">
          Поиск по логину или фамилии
          <input className="input" value={search} placeholder="master, Иванов" onChange={(event) => setSearch(event.target.value)} />
        </label>
      </Card>

      {crews.error ? <ErrorBanner message={crews.error} onRetry={crews.reload} /> : null}

      <Card title="Сводный список">
        <DataTable
          columns={columns}
          rows={members}
          rowKey={(row) => row.userId}
          loading={crews.loading}
          empty="Сотрудников не найдено"
        />
        <span className="muted">
          Сотрудник без бригады в этот список не попадает: API отдаёт состав по бригадам, отдельного реестра
          пользователей в листе задания нет.
        </span>
      </Card>

      <Card title="Роли">
        <div className="btn-row">
          <Badge text="ADMIN — администратор" tone="bad" />
          <Badge text="MANAGER — руководитель" tone="info" />
          <Badge text="MASTER — мастер" tone="ok" />
        </div>
      </Card>
    </div>
  )
}