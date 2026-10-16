/* ===========================================================================
   ТОиР-Проф — реестр заявок на ремонт и ТО.

   Требование листа: список с фильтрами, поиском, сортировкой и пагинацией,
   а также действия жизненного цикла — создать заявку, назначить бригаду,
   начать работу, завершить со списанием материалов. Руководитель смотрит
   реестр, мастер в нём же работает, поэтому кнопки показываются по роли
   и по текущему статусу заявки.
   =========================================================================== */

import { useState } from 'react'
import { crewsApi, materialsApi, workOrdersApi } from '../api/endpoints'
import type { CrewShortDto, MaterialDto, WorkOrderDto, WorkOrderShortDto, WorkOrderStatus } from '../api/types'
import { WORK_ORDER_PRIORITIES, WORK_ORDER_STATUSES } from '../api/types'
import { DataTable } from '../components/DataTable'
import type { Column } from '../components/DataTable'
import { useToast } from '../components/ToastProvider'
import { Badge, Card, EmptyState, ErrorBanner, LoadingBar } from '../components/Ui'
import { useAuth } from '../auth/AuthContext'
import { useAction, useLoad } from '../hooks/useLoad'
import { formatDate, formatDateTime, formatHours, formatMoney, formatNumber, formatQuantity } from '../utils/format'

const SORTABLE = ['createdAt', 'number', 'status', 'priority', 'plannedStart', 'downtime'] as const

const columns: Column<WorkOrderShortDto>[] = [
  { key: 'number', title: 'Номер', sortable: true, render: (row) => <span className="mono nowrap">{row.number}</span> },
  { key: 'equipment', title: 'Оборудование', render: (row) => row.equipmentName },
  { key: 'inventory', title: 'Инв. номер', render: (row) => <span className="mono">{row.inventoryNumber}</span> },
  { key: 'priority', title: 'Приоритет', sortable: true, render: (row) => <Badge text={row.priority} /> },
  { key: 'status', title: 'Статус', sortable: true, render: (row) => <Badge text={row.status} /> },
  { key: 'plannedStart', title: 'План', sortable: true, numeric: true, render: (row) => formatDate(row.plannedStart) },
  {
    key: 'downtime',
    title: 'Простой, ч',
    sortable: true,
    numeric: true,
    render: (row) => (row.downtimeHours == null ? '—' : formatHours(row.downtimeHours)),
  },
  { key: 'crew', title: 'Бригада', render: (row) => row.crewName ?? '—' },
]

export function WorkOrdersPage() {
  const { session, can } = useAuth()
  const toast = useToast()
  const action = useAction()

  const [search, setSearch] = useState('')
  const [applied, setApplied] = useState('')
  const [status, setStatus] = useState('')
  const [priority, setPriority] = useState('')
  const [crew, setCrew] = useState('')
  const [sort, setSort] = useState<string>('createdAt')
  const [order, setOrder] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  const [selected, setSelected] = useState<WorkOrderDto | null>(null)
  const [assignCrew, setAssignCrew] = useState('')
  const [failureReason, setFailureReason] = useState('')
  const [material, setMaterial] = useState('')
  const [quantity, setQuantity] = useState('')

  const list = useLoad(
    (signal) =>
      workOrdersApi.list(
        {
          query: applied === '' ? undefined : applied,
          status: status === '' ? undefined : (status as WorkOrderStatus),
          priority: priority === '' ? undefined : priority,
          crewId: crew === '' ? undefined : crew,
          sort,
          order,
          page,
          pageSize,
        },
        signal,
      ),
    [applied, status, priority, crew, sort, order, page, pageSize],
  )

  const crews = useLoad<CrewShortDto[]>((signal) => crewsApi.forSelect(signal), [])
  const materials = useLoad<MaterialDto[]>((signal) => materialsApi.forSelect(signal), [])

  const open = async (id: string) => {
    await action.run(async () => {
      const order = await workOrdersApi.byId(id)
      setSelected(order)
      setAssignCrew(order.crewId ?? '')
      setFailureReason(order.failureReason ?? '')
    })
  }

  const apply = () => {
    setPage(1)
    setApplied(search.trim())
  }

  const onSort = (field: string) => {
    if (sort === field) setOrder(order === 'asc' ? 'desc' : 'asc')
    else {
      setSort(field)
      setOrder('asc')
    }
    setPage(1)
  }

  const doAssign = async () => {
    if (!selected || assignCrew === '') return
    await action.run(async () => {
      const updated = await workOrdersApi.assignCrew(selected.id, { crewId: assignCrew })
      setSelected(updated)
      toast.success(`Бригада ${updated.crewName ?? ''} назначена на ${updated.number}`)
      list.reload()
    })
  }

  const doStart = async () => {
    if (!selected) return
    await action.run(async () => {
      const updated = await workOrdersApi.start(selected.id, new Date().toISOString())
      setSelected(updated)
      toast.success(`${updated.number}: работа начата`)
      list.reload()
    })
  }

  const doComplete = async () => {
    if (!selected) return
    if (failureReason.trim() === '') {
      toast.warning('Укажите причину неисправности — без неё заявку завершить нельзя')
      return
    }
    await action.run(async () => {
      const updated = await workOrdersApi.complete(selected.id, {
        actualEnd: new Date().toISOString(),
        failureReason: failureReason.trim(),
      })
      setSelected(updated)
      toast.success(`${updated.number}: заявка завершена`)
      list.reload()
    })
  }

  const doWriteOff = async () => {
    if (!selected || material === '' || quantity.trim() === '') {
      toast.warning('Выберите материал и укажите количество')
      return
    }
    await action.run(async () => {
      const updated = await workOrdersApi.writeOff(selected.id, {
        materialId: material,
        quantity: Number(quantity.replace(',', '.')),
      })
      setSelected(updated)
      setQuantity('')
      toast.success(`Списано. Стоимость по заявке — ${formatMoney(updated.totalMaterialCost)}`)
      list.reload()
    })
  }

  const rows = list.data?.items ?? []
  const mayEdit = can('ADMIN', 'MANAGER', 'MASTER')

  return (
    <div className="grid">
      <div className="section-title no-print">
        <h1>Заявки</h1>
        <span className="muted">{list.data ? `всего ${formatNumber(list.data.total)}` : 'загружаю…'}</span>
        <button type="button" className="btn btn--ghost btn--sm" onClick={list.reload} disabled={list.loading}>
          Обновить
        </button>
      </div>

      <LoadingBar visible={list.loading || action.busy} />

      <Card title="Фильтры" className="no-print">
        <div className="form-grid">
          <label className="field">
            Поиск
            <input
              className="input"
              value={search}
              placeholder="номер, название, оборудование"
              onChange={(event) => setSearch(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') apply()
              }}
            />
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
              {WORK_ORDER_STATUSES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Приоритет
            <select
              className="select"
              value={priority}
              onChange={(event) => {
                setPriority(event.target.value)
                setPage(1)
              }}
            >
              <option value="">Любой</option>
              {WORK_ORDER_PRIORITIES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Бригада
            <select
              className="select"
              value={crew}
              onChange={(event) => {
                setCrew(event.target.value)
                setPage(1)
              }}
            >
              <option value="">Любые</option>
              {(crews.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.code} · {item.name}
                </option>
              ))}
            </select>
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
              setStatus('')
              setPriority('')
              setCrew('')
              setPage(1)
            }}
          >
            Сбросить
          </button>
        </div>
      </Card>

      {list.error ? <ErrorBanner message={list.error} onRetry={list.reload} /> : null}

      <Card title="Реестр заявок">
        <DataTable
          columns={columns}
          rows={rows}
          rowKey={(row) => row.id}
          loading={list.loading}
          empty="Заявок по заданным условиям нет"
          selectedId={selected?.id ?? null}
          onSelect={(row) => void open(row.id)}
          sortField={sort}
          sortOrder={order}
          onSort={(field) => onSort(field)}
          pager={list.data ? { page: list.data.page, pageSize: list.data.pageSize, total: list.data.total } : undefined}
          onPage={(value) => setPage(value)}
          onPageSize={(value) => {
            setPageSize(value)
            setPage(1)
          }}
        />
        <span className="muted">
          Доступные сортировки: {SORTABLE.join(', ')}. Сортировка выполняется на сервере.
        </span>
      </Card>

      <Card title="Карточка заявки" hint={selected ? selected.number : 'выберите строку реестра'}>
        {!selected ? (
          <EmptyState caption="Заявка не выбрана" />
        ) : (
          <div className="grid">
            <div className="btn-row">
              <Badge text={selected.status} />
              <Badge text={selected.priority} />
              {selected.crewName ? <Badge text={`Бригада ${selected.crewName}`} tone="info" /> : null}
            </div>
            <div>
              <strong>{selected.title}</strong>
              <p className="muted">{selected.description}</p>
            </div>
            <div className="muted">
              {selected.equipmentName} ({selected.inventoryNumber}) · план {formatDate(selected.plannedStart)} —{' '}
              {formatDate(selected.plannedEnd)}
              {selected.actualStart ? ` · начало ${formatDateTime(selected.actualStart)}` : ''}
              {selected.actualEnd ? ` · окончание ${formatDateTime(selected.actualEnd)}` : ''}
              {selected.downtimeHours != null ? ` · простой ${formatHours(selected.downtimeHours)}` : ''}
            </div>

            {selected.materials.length > 0 ? (
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Артикул</th>
                      <th>Материал</th>
                      <th className="table__num">Количество</th>
                      <th className="table__num">Цена</th>
                      <th className="table__num">Стоимость</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.materials.map((line) => (
                      <tr key={line.materialId}>
                        <td className="mono">{line.sku}</td>
                        <td>{line.name}</td>
                        <td className="table__num mono">
                          {formatQuantity(line.quantity)} {line.unit}
                        </td>
                        <td className="table__num mono">{formatMoney(line.unitPrice)}</td>
                        <td className="table__num mono">{formatMoney(line.cost)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <span className="muted">Итого по заявке: {formatMoney(selected.totalMaterialCost)}</span>
              </div>
            ) : null}

            {selected.history.length > 0 ? (
              <div>
                <div className="section-title">История изменений</div>
                <ul className="muted">
                  {selected.history.slice(0, 8).map((item, index) => (
                    <li key={`${item.changedAt}-${index}`}>
                      {formatDateTime(item.changedAt)} · {item.action} · {item.summary}
                      {item.changedByName ? ` (${item.changedByName})` : ''}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {mayEdit && selected.status !== 'Завершена' && selected.status !== 'Отменена' ? (
              <div className="grid">
                <div className="btn-row">
                  <label className="field">
                    Бригада
                    <select className="select" value={assignCrew} onChange={(event) => setAssignCrew(event.target.value)}>
                      <option value="">не назначена</option>
                      {(crews.data ?? []).map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.code} · {item.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button type="button" className="btn btn--sm" disabled={action.busy || assignCrew === ''} onClick={() => void doAssign()}>
                    Назначить
                  </button>
                  <button
                    type="button"
                    className="btn btn--primary btn--sm"
                    disabled={action.busy || selected.status === 'В работе'}
                    onClick={() => void doStart()}
                  >
                    Начать работу
                  </button>
                </div>

                <label className="field">
                  Причина неисправности
                  <textarea
                    className="input"
                    rows={2}
                    value={failureReason}
                    onChange={(event) => setFailureReason(event.target.value)}
                  />
                </label>
                <div className="btn-row">
                  <button type="button" className="btn btn--primary btn--sm" disabled={action.busy} onClick={() => void doComplete()}>
                    Завершить заявку
                  </button>
                </div>

                <div className="btn-row">
                  <label className="field">
                    Материал
                    <select className="select" value={material} onChange={(event) => setMaterial(event.target.value)}>
                      <option value="">выберите материал</option>
                      {(materials.data ?? [])
                        .filter((item) => item.isActive)
                        .map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.sku} · {item.name} (остаток {formatQuantity(item.stock)} {item.unit})
                          </option>
                        ))}
                    </select>
                  </label>
                  <label className="field">
                    Количество
                    <input
                      className="input"
                      type="text"
                      inputMode="decimal"
                      value={quantity}
                      onChange={(event) => setQuantity(event.target.value)}
                    />
                  </label>
                  <button type="button" className="btn btn--sm" disabled={action.busy} onClick={() => void doWriteOff()}>
                    Списать
                  </button>
                </div>
              </div>
            ) : null}

            <span className="muted">
              Автор заявки: {session?.user.fullName ?? '—'} · простой считает база, поле вручную не меняется.
            </span>
          </div>
        )}
      </Card>
    </div>
  )
}