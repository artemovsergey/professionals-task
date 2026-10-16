/* ===========================================================================
   ТОиР-Проф — реестр оборудования.

   Требование листа: реестр со списком, фильтрами, поиском, сортировкой и
   пагинацией. Сортировку по инвентарному номеру делает сервер, поэтому
   здесь она включается только там, где сервер её поддерживает.
   =========================================================================== */

import { useState } from 'react'
import { equipmentApi, workshopsApi } from '../api/endpoints'
import type { EquipmentShortDto } from '../api/types'
import { EQUIPMENT_STATUSES } from '../api/types'
import { DataTable } from '../components/DataTable'
import type { Column } from '../components/DataTable'
import { useToast } from '../components/ToastProvider'
import { Badge, Card, EmptyState, ErrorBanner, LoadingBar } from '../components/Ui'
import { useLoad } from '../hooks/useLoad'
import { formatNumber } from '../utils/format'

const columns: Column<EquipmentShortDto>[] = [
  {
    key: 'inventoryNumber',
    title: 'Инв. номер',
    render: (row) => <span className="mono nowrap">{row.inventoryNumber}</span>,
  },
  { key: 'name', title: 'Оборудование', render: (row) => row.name },
  { key: 'workshopName', title: 'Цех', render: (row) => row.workshopName },
  { key: 'status', title: 'Статус', render: (row) => <Badge text={row.status} /> },
  { key: 'criticality', title: 'Критичность', numeric: true, render: (row) => `${row.criticality} / 5` },
]

export function EquipmentPage() {
  const toast = useToast()

  const [search, setSearch] = useState('')
  const [applied, setApplied] = useState('')
  const [workshop, setWorkshop] = useState('')
  const [status, setStatus] = useState('')
  const [criticality, setCriticality] = useState('0')
  const [includeRetired, setIncludeRetired] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  const load = useLoad(
    (signal) =>
      equipmentApi.list(
        {
          workshopId: workshop === '' ? undefined : workshop,
          search: applied === '' ? undefined : applied,
          status: status === '' ? undefined : status,
          criticality: Number(criticality),
          includeRetired,
          page,
          pageSize,
        },
        signal,
      ),
    [applied, workshop, status, criticality, includeRetired, page, pageSize],
  )

  // Справочника цехов в API нет: список собирается из первых страниц
  // оборудования, этого достаточно для фильтра «цех».
  const catalog = useLoad((signal) => equipmentApi.forSelect(signal), [])
  const workshops = workshopsApi.fromEquipment(catalog.data ?? [])
  const rows = load.data?.items ?? []

  const apply = () => {
    setPage(1)
    setApplied(search.trim())
  }

  const reset = () => {
    setSearch('')
    setApplied('')
    setWorkshop('')
    setStatus('')
    setCriticality('0')
    setIncludeRetired(false)
    setPage(1)
    toast.show('Фильтры сброшены')
  }

  return (
    <div className="grid">
      <div className="section-title no-print">
        <h1>Оборудование</h1>
        <span className="muted">
          {load.data ? `найдено ${formatNumber(load.data.total)}` : 'загружаю…'}
        </span>
        <button type="button" className="btn btn--ghost btn--sm" onClick={load.reload}>
          Обновить
        </button>
      </div>

      <LoadingBar visible={load.loading} />

      <Card title="Фильтры" className="no-print">
        <div className="form-grid">
          <label className="field">
            Поиск по названию или инв. номеру
            <input
              className="input"
              value={search}
              placeholder="ПР-2 или пресс"
              onChange={(event) => setSearch(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') apply()
              }}
            />
          </label>
          <label className="field">
            Цех
            <select
              className="select"
              value={workshop}
              onChange={(event) => {
                setWorkshop(event.target.value)
                setPage(1)
              }}
            >
              <option value="">Все цеха</option>
              {workshops.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Статус
            <select
              className="select"
              value={status}
              onChange={(event) => {
                setStatus(event.target.value)
                setPage(1)
              }}
            >
              <option value="">Любой</option>
              {EQUIPMENT_STATUSES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Критичность от
            <select
              className="select"
              value={criticality}
              onChange={(event) => {
                setCriticality(event.target.value)
                setPage(1)
              }}
            >
              {[0, 1, 2, 3, 4, 5].map((value) => (
                <option key={value} value={String(value)}>
                  {value === 0 ? 'любая' : `от ${value}`}
                </option>
              ))}
            </select>
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={includeRetired}
              onChange={(event) => {
                setIncludeRetired(event.target.checked)
                setPage(1)
              }}
            />
            показывать выведенное из эксплуатации
          </label>
        </div>
        <div className="btn-row">
          <button type="button" className="btn btn--primary btn--sm" onClick={apply}>
            Найти
          </button>
          <button type="button" className="btn btn--ghost btn--sm" onClick={reset}>
            Сбросить
          </button>
        </div>
      </Card>

      {load.error ? <ErrorBanner message={load.error} onRetry={load.reload} /> : null}

      {load.data && rows.length === 0 ? (
        <EmptyState caption="По заданным условиям ничего не найдено" />
      ) : (
        <Card title="Реестр">
          <DataTable
            columns={columns}
            rows={rows}
            rowKey={(row) => row.id}
            loading={load.loading}
            empty="Оборудование не найдено"
            pager={
              load.data
                ? { page: load.data.page, pageSize: load.data.pageSize, total: load.data.total }
                : undefined
            }
            onPage={(value) => setPage(value)}
            onPageSize={(value) => {
              setPageSize(value)
              setPage(1)
            }}
          />
          <span className="muted">
            Сортировка и пагинация выполняются на сервере: при большом числе единиц это быстрее, чем разбирать всю
            выборку в браузере. Выведенное из эксплуатации оборудование по умолчанию скрыто.
          </span>
        </Card>
      )}
    </div>
  )
}