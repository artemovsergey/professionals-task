/* ===========================================================================
   ТОиР-Проф — справочник бригад.

   Реестр с фильтрами, пагинацией и карточкой бригады: состав, загрузка,
   завершённые заявки, суммарный простой и рейтинг. Рейтинг считает сервер
   как долю завершённых заявок от назначенных.
   =========================================================================== */

import { useState } from 'react'
import { crewsApi } from '../api/endpoints'
import type { CrewDto } from '../api/types'
import { DataTable } from '../components/DataTable'
import type { Column } from '../components/DataTable'
import { useToast } from '../components/ToastProvider'
import { Badge, Card, EmptyState, ErrorBanner, LoadingBar, MetricCard } from '../components/Ui'
import { useAction, useLoad } from '../hooks/useLoad'
import { formatDate, formatHours, formatNumber, formatPercent } from '../utils/format'

const columns: Column<CrewDto>[] = [
  { key: 'code', title: 'Код', render: (row) => <span className="mono">{row.code}</span> },
  { key: 'name', title: 'Бригада', render: (row) => row.name },
  { key: 'specialty', title: 'Специализация', render: (row) => row.specialty ?? '—' },
  { key: 'memberCount', title: 'Членов', numeric: true, render: (row) => formatNumber(row.members.length) },
  { key: 'activeOrders', title: 'В работе', numeric: true, render: (row) => formatNumber(row.activeOrders) },
  { key: 'completedOrders', title: 'Завершено', numeric: true, render: (row) => formatNumber(row.completedOrders) },
  {
    key: 'totalDowntimeHours',
    title: 'Простой, ч',
    numeric: true,
    render: (row) => formatHours(row.totalDowntimeHours),
  },
  {
    key: 'rating',
    title: 'Рейтинг',
    numeric: true,
    render: (row) => (
      <Badge text={formatPercent(row.rating)} tone={row.rating >= 80 ? 'ok' : row.rating >= 50 ? 'wait' : 'bad'} />
    ),
  },
  { key: 'isActive', title: 'Состояние', render: (row) => <Badge text={row.isActive ? 'Активна' : 'Отключена'} /> },
]

export function CrewsPage() {
  const toast = useToast()
  const action = useAction()

  const [search, setSearch] = useState('')
  const [applied, setApplied] = useState('')
  const [includeInactive, setIncludeInactive] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [selected, setSelected] = useState<CrewDto | null>(null)

  const list = useLoad(
    (signal) => crewsApi.list({ search: applied === '' ? undefined : applied, includeInactive, page, pageSize }, signal),
    [applied, includeInactive, page, pageSize],
  )

  const open = async (id: string) => {
    await action.run(async () => {
      setSelected(await crewsApi.byId(id))
    })
  }

  const apply = () => {
    setPage(1)
    setApplied(search.trim())
  }

  return (
    <div className="grid">
      <div className="section-title no-print">
        <h1>Бригады</h1>
        <span className="muted">{list.data ? `всего ${formatNumber(list.data.total)}` : 'загружаю…'}</span>
        <button type="button" className="btn btn--ghost btn--sm" onClick={list.reload} disabled={list.loading}>
          Обновить
        </button>
      </div>

      <LoadingBar visible={list.loading || action.busy} />

      <Card title="Фильтры" className="no-print">
        <div className="form-grid">
          <label className="field">
            Поиск по названию или коду
            <input
              className="input"
              value={search}
              placeholder="БР-1 или токарн"
              onChange={(event) => setSearch(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') apply()
              }}
            />
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(event) => {
                setIncludeInactive(event.target.checked)
                setPage(1)
              }}
            />
            показывать отключённые
          </label>
        </div>
        <div className="btn-row">
          <button type="button" className="btn btn--primary btn--sm" onClick={apply}>
            Найти
          </button>
          <button
            type="button"
            className="btn btn--ghost btn--sm"
            onClick={() => {
              setSearch('')
              setApplied('')
              setPage(1)
              toast.show('Фильтры сброшены')
            }}
          >
            Сбросить
          </button>
        </div>
      </Card>

      {list.error ? <ErrorBanner message={list.error} onRetry={list.reload} /> : null}

      <Card title="Реестр бригад">
        <DataTable
          columns={columns}
          rows={list.data?.items ?? []}
          rowKey={(row) => row.id}
          loading={list.loading}
          empty="Бригад по заданным условиям нет"
          selectedId={selected?.id ?? null}
          onSelect={(row) => void open(row.id)}
          pager={list.data ? { page: list.data.page, pageSize: list.data.pageSize, total: list.data.total } : undefined}
          onPage={(value) => setPage(value)}
          onPageSize={(value) => {
            setPageSize(value)
            setPage(1)
          }}
        />
      </Card>

      <Card title="Карточка бригады" hint={selected ? `${selected.code} · ${selected.name}` : 'выберите строку реестра'}>
        {!selected ? (
          <EmptyState caption="Бригада не выбрана" />
        ) : (
          <div className="grid">
            <div className="kpi-row">
              <MetricCard title="Членов бригады" value={formatNumber(selected.members.length)} />
              <MetricCard title="Заявок в работе" value={formatNumber(selected.activeOrders)} tone="wait" />
              <MetricCard title="Заявок завершено" value={formatNumber(selected.completedOrders)} tone="ok" />
              <MetricCard title="Рейтинг" value={formatPercent(selected.rating)} tone={selected.rating >= 80 ? 'ok' : 'wait'} />
              <MetricCard title="Суммарный простой" value={formatHours(selected.totalDowntimeHours)} />
            </div>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Логин</th>
                    <th>Сотрудник</th>
                    <th>В бригаде с</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.members.map((member) => (
                    <tr key={member.userId}>
                      <td className="mono">{member.username}</td>
                      <td>{member.fullName}</td>
                      <td className="mono">{formatDate(member.joinedAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <span className="muted">
              Специализация: {selected.specialty ?? 'не указана'}. Бригада не может вести вторую заявку «В работе»
              одновременно — это проверяет сервер и возвращает код CREW_BUSY.
            </span>
          </div>
        )}
      </Card>
    </div>
  )
}