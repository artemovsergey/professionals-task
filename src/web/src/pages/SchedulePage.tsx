/* ===========================================================================
   ТОиР-Проф — график планового ТО.

   Требование листа: реестр графика с фильтрами и поиском. Плановые записи
   приходят списком без постраничности — их на год вперёд немного, поэтому
   здесь показываем всё и добавляем поиск по оборудованию и виду ТО.
   =========================================================================== */

import { useMemo, useState } from 'react'
import { equipmentApi, scheduleApi } from '../api/endpoints'
import type { MaintenanceScheduleDto, ScheduleStatus } from '../api/types'
import { SCHEDULE_STATUSES } from '../api/types'
import { DataTable } from '../components/DataTable'
import type { Column } from '../components/DataTable'
import { useToast } from '../components/ToastProvider'
import { Badge, Card, EmptyState, ErrorBanner, LoadingBar } from '../components/Ui'
import { useAction, useLoad } from '../hooks/useLoad'
import { formatDate, formatMoney, formatNumber, isoDaysAgo, periodLabel } from '../utils/format'

const columns: Column<MaintenanceScheduleDto>[] = [
  {
    key: 'inventoryNumber',
    title: 'Инв. номер',
    render: (row) => <span className="mono nowrap">{row.inventoryNumber}</span>,
  },
  { key: 'equipmentName', title: 'Оборудование', render: (row) => row.equipmentName },
  { key: 'maintenanceTypeName', title: 'Вид ТО', render: (row) => row.maintenanceTypeName },
  { key: 'plannedDate', title: 'План', numeric: true, render: (row) => formatDate(row.plannedDate) },
  { key: 'completedDate', title: 'Выполнено', numeric: true, render: (row) => formatDate(row.completedDate) },
  { key: 'nextPlannedDate', title: 'Следующая', numeric: true, render: (row) => formatDate(row.nextPlannedDate) },
  { key: 'status', title: 'Статус', render: (row) => <Badge text={row.status} /> },
]

export function SchedulePage() {
  const toast = useToast()
  const action = useAction()

  const [from, setFrom] = useState(() => isoDaysAgo(-60))
  const [to, setTo] = useState(() => isoDaysAgo(90))
  const [status, setStatus] = useState('')
  const [equipment, setEquipment] = useState('')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<MaintenanceScheduleDto | null>(null)
  const [completedDate, setCompletedDate] = useState(() => isoDaysAgo(0))
  const [actualCost, setActualCost] = useState('')

  const load = useLoad(
    (signal) =>
      scheduleApi.list(
        {
          from,
          to,
          status: status === '' ? undefined : (status as ScheduleStatus),
          equipmentId: equipment === '' ? undefined : equipment,
        },
        signal,
      ),
    [from, to, status, equipment],
  )

  const catalog = useLoad((signal) => equipmentApi.forSelect(signal), [])

  const rows = useMemo(() => {
    const needle = search.trim().toLowerCase()
    const items = load.data ?? []
    if (needle === '') return items
    return items.filter(
      (row) =>
        row.equipmentName.toLowerCase().includes(needle) ||
        row.inventoryNumber.toLowerCase().includes(needle) ||
        row.maintenanceTypeName.toLowerCase().includes(needle),
    )
  }, [load.data, search])

  const pick = (row: MaintenanceScheduleDto) => {
    setSelected(row)
    setCompletedDate(row.completedDate ?? isoDaysAgo(0))
    setActualCost(row.actualCost == null ? '' : String(row.actualCost))
  }

  const complete = async () => {
    if (!selected) return
    await action.run(async () => {
      const updated = await scheduleApi.complete(selected.id, {
        completedDate,
        actualCost: actualCost.trim() === '' ? null : Number(actualCost.replace(',', '.')),
      })
      setSelected(updated)
      toast.success(`${updated.equipmentName}: ТО ${formatDate(updated.completedDate)} отмечено выполненным`)
      load.reload()
    })
  }

  const backToPlan = async () => {
    if (!selected) return
    await action.run(async () => {
      const updated = await scheduleApi.returnToPlan(selected.id)
      setSelected(updated)
      toast.show(`${updated.equipmentName}: запись возвращена в план`)
      load.reload()
    })
  }

  return (
    <div className="grid">
      <div className="section-title no-print">
        <h1>График ТО</h1>
        <span className="muted">
          {periodLabel(from, to)} · записей {formatNumber(rows.length)}
        </span>
        <button type="button" className="btn btn--ghost btn--sm" onClick={load.reload} disabled={load.loading}>
          Обновить
        </button>
      </div>

      <LoadingBar visible={load.loading} />

      <Card title="Фильтры" className="no-print">
        <div className="form-grid">
          <label className="field">
            Период с
            <input className="input" type="date" value={from} max={to} onChange={(event) => setFrom(event.target.value)} />
          </label>
          <label className="field">
            по
            <input className="input" type="date" value={to} min={from} onChange={(event) => setTo(event.target.value)} />
          </label>
          <label className="field">
            Статус
            <select className="select" value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="">Любой</option>
              {SCHEDULE_STATUSES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Оборудование
            <select className="select" value={equipment} onChange={(event) => setEquipment(event.target.value)}>
              <option value="">Всё оборудование</option>
              {(catalog.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.inventoryNumber} · {item.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Поиск
            <input className="input" value={search} placeholder="название, инв. номер, вид ТО" onChange={(event) => setSearch(event.target.value)} />
          </label>
        </div>
      </Card>

      {load.error ? <ErrorBanner message={load.error} onRetry={load.reload} /> : null}

      <div className="grid grid--2">
        <Card title="График">
          <DataTable
            columns={columns}
            rows={rows}
            rowKey={(row) => row.id}
            loading={load.loading}
            empty="За выбранный период плановых работ нет"
            selectedId={selected?.id ?? null}
            onSelect={pick}
          />
          {!load.loading && rows.length === 0 ? <EmptyState caption="Измените период или сбросьте фильтры" /> : null}
        </Card>

        <Card title="Выполнение ТО" hint={selected ? selected.equipmentName : 'выберите запись в графике'}>
          {selected ? (
            <div className="grid">
              <div>
                <span className="muted">
                  {selected.maintenanceTypeName} · план {formatDate(selected.plannedDate)} · периодичность{' '}
                  {selected.intervalDays} дн.
                </span>
              </div>
              <label className="field">
                Дата выполнения
                <input className="input" type="date" value={completedDate} onChange={(event) => setCompletedDate(event.target.value)} />
              </label>
              <label className="field">
                Фактическая стоимость, ₽
                <input
                  className="input"
                  type="text"
                  inputMode="decimal"
                  value={actualCost}
                  placeholder="например, 12500"
                  onChange={(event) => setActualCost(event.target.value)}
                />
              </label>
              <div className="btn-row">
                <button
                  type="button"
                  className="btn btn--primary btn--sm"
                  disabled={action.busy || selected.status === 'Выполнено'}
                  onClick={() => void complete()}
                >
                  Отметить выполненным
                </button>
                <button
                  type="button"
                  className="btn btn--ghost btn--sm"
                  disabled={action.busy || selected.status === 'Запланировано'}
                  onClick={() => void backToPlan()}
                >
                  Вернуть в план
                </button>
              </div>
              <span className="muted">
                Следующая плановая дата рассчитывает база функцией fn_next_maintenance_date:{' '}
                {formatDate(selected.nextPlannedDate)}.{' '}
                {selected.actualCost != null ? `Стоимость прошлого выполнения — ${formatMoney(selected.actualCost)}.` : ''}
              </span>
            </div>
          ) : (
            <EmptyState caption="Выберите плановую запись слева" />
          )}
        </Card>
      </div>
    </div>
  )
}