/* ===========================================================================
   ТОиР-Проф — материалы и запас ЗИП.

   Требование листа: реестр справочника с фильтрами и поиском, дефицитные
   позиции отдельным блоком и приход на склад. Принимает приход только
   администратор и руководитель; недостаток остатка при списании
   блокирует сервер и возвращает NOT_ENOUGH_STOCK.
   =========================================================================== */

import { useState } from 'react'
import { materialsApi } from '../api/endpoints'
import type { MaterialDto, MaterialShortageDto } from '../api/types'
import { DataTable } from '../components/DataTable'
import type { Column } from '../components/DataTable'
import { useToast } from '../components/ToastProvider'
import { Badge, Card, EmptyState, ErrorBanner, LoadingBar, MetricCard } from '../components/Ui'
import { useAuth } from '../auth/AuthContext'
import { useAction, useLoad } from '../hooks/useLoad'
import { formatMoney, formatNumber, formatQuantity } from '../utils/format'

const columns: Column<MaterialDto>[] = [
  { key: 'sku', title: 'Артикул', render: (row) => <span className="mono">{row.sku}</span> },
  { key: 'name', title: 'Материал', render: (row) => row.name },
  { key: 'unit', title: 'Ед.', render: (row) => row.unit },
  { key: 'price', title: 'Цена', numeric: true, render: (row) => formatMoney(row.price) },
  { key: 'stock', title: 'Остаток', numeric: true, render: (row) => `${formatQuantity(row.stock)} ${row.unit}` },
  { key: 'minStock', title: 'Минимум', numeric: true, render: (row) => formatQuantity(row.minStock) },
  {
    key: 'totalWrittenOff',
    title: 'Списано',
    numeric: true,
    render: (row) => (row.totalWrittenOff == null ? '—' : formatQuantity(row.totalWrittenOff)),
  },
  {
    key: 'state',
    title: 'Состояние',
    render: (row) => <Badge text={row.isShortage ? 'Дефицит' : 'В наличии'} tone={row.isShortage ? 'bad' : 'ok'} />,
  },
  { key: 'isActive', title: 'Активен', render: (row) => (row.isActive ? 'да' : 'нет') },
]

const shortageColumns: Column<MaterialShortageDto>[] = [
  { key: 'sku', title: 'Артикул', render: (row) => <span className="mono">{row.sku}</span> },
  { key: 'name', title: 'Материал', render: (row) => row.name },
  { key: 'stock', title: 'Остаток', numeric: true, render: (row) => `${formatQuantity(row.stock)} ${row.unit}` },
  { key: 'minStock', title: 'Минимум', numeric: true, render: (row) => `${formatQuantity(row.minStock)} ${row.unit}` },
  {
    key: 'gap',
    title: 'Не хватает',
    numeric: true,
    render: (row) => `${formatQuantity(row.minStock - row.stock)} ${row.unit}`,
  },
]

export function MaterialsPage() {
  const { can } = useAuth()
  const toast = useToast()
  const action = useAction()

  const [search, setSearch] = useState('')
  const [applied, setApplied] = useState('')
  const [includeInactive, setIncludeInactive] = useState(false)
  const [onlyShortage, setOnlyShortage] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [selected, setSelected] = useState<MaterialDto | null>(null)
  const [receipt, setReceipt] = useState('')

  const list = useLoad(
    (signal) =>
      materialsApi.list(
        { search: applied === '' ? undefined : applied, includeInactive, onlyShortage, page, pageSize },
        signal,
      ),
    [applied, includeInactive, onlyShortage, page, pageSize],
  )

  const shortages = useLoad<MaterialShortageDto[]>((signal) => materialsApi.shortages(signal), [])

  const apply = () => {
    setPage(1)
    setApplied(search.trim())
  }

  const pick = (row: MaterialDto) => {
    setSelected(row)
    setReceipt('')
  }

  const doReceipt = async () => {
    if (!selected || receipt.trim() === '') {
      toast.warning('Укажите количество прихода')
      return
    }
    await action.run(async () => {
      const updated = await materialsApi.receive(selected.id, Number(receipt.replace(',', '.')))
      setSelected(updated)
      setReceipt('')
      toast.success(`${updated.name}: остаток ${formatQuantity(updated.stock)} ${updated.unit}`)
      list.reload()
      shortages.reload()
    })
  }

  const mayReceive = can('ADMIN', 'MANAGER')

  return (
    <div className="grid">
      <div className="section-title no-print">
        <h1>Материалы и ЗИП</h1>
        <span className="muted">{list.data ? `позиций ${formatNumber(list.data.total)}` : 'загружаю…'}</span>
        <button type="button" className="btn btn--ghost btn--sm" onClick={list.reload} disabled={list.loading}>
          Обновить
        </button>
      </div>

      <LoadingBar visible={list.loading || action.busy} />

      <Card title="Фильтры" className="no-print">
        <div className="form-grid">
          <label className="field">
            Поиск по артикулу или названию
            <input
              className="input"
              value={search}
              placeholder="SK-6205 или подшипник"
              onChange={(event) => setSearch(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') apply()
              }}
            />
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={onlyShortage}
              onChange={(event) => {
                setOnlyShortage(event.target.checked)
                setPage(1)
              }}
            />
            только дефицитные
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
              setOnlyShortage(false)
              setIncludeInactive(false)
              setPage(1)
            }}
          >
            Сбросить
          </button>
        </div>
      </Card>

      {list.error ? <ErrorBanner message={list.error} onRetry={list.reload} /> : null}

      <div className="grid grid--2">
        <Card title="Справочник материалов">
          <DataTable
            columns={columns}
            rows={list.data?.items ?? []}
            rowKey={(row) => row.id}
            loading={list.loading}
            empty="Материалы по заданным условиям не найдены"
            selectedId={selected?.id ?? null}
            onSelect={pick}
            pager={
              list.data ? { page: list.data.page, pageSize: list.data.pageSize, total: list.data.total } : undefined
            }
            onPage={(value) => setPage(value)}
            onPageSize={(value) => {
              setPageSize(value)
              setPage(1)
            }}
          />
        </Card>

        <Card title="Дефицит" hint="остаток ниже минимума">
          {shortages.error ? <ErrorBanner message={shortages.error} onRetry={shortages.reload} /> : null}
          <DataTable
            columns={shortageColumns}
            rows={shortages.data ?? []}
            rowKey={(row) => row.id}
            loading={shortages.loading}
            empty="Всех материалов достаточно"
          />
          <span className="muted">
            Здесь важен порядок: сервер сортирует дефицит по глубине нехватки, чтобы в первую очередь закупали
            самое критичное.
          </span>
        </Card>
      </div>

      <Card title="Приход на склад" hint={selected ? `${selected.sku} · ${selected.name}` : 'выберите материал'}>
        {!selected ? (
          <EmptyState caption="Материал не выбран" />
        ) : (
          <div className="grid">
            <div className="kpi-row">
              <MetricCard title="Остаток" value={`${formatQuantity(selected.stock)} ${selected.unit}`} tone={selected.isShortage ? 'bad' : 'ok'} />
              <MetricCard title="Минимум" value={`${formatQuantity(selected.minStock)} ${selected.unit}`} tone="wait" />
              <MetricCard title="Цена" value={formatMoney(selected.price)} />
              <MetricCard
                title="Списано всего"
                value={selected.totalWrittenOff == null ? '—' : `${formatQuantity(selected.totalWrittenOff)} ${selected.unit}`}
              />
            </div>
            {mayReceive ? (
              <div className="btn-row">
                <label className="field">
                  Количество прихода
                  <input
                    className="input"
                    type="text"
                    inputMode="decimal"
                    value={receipt}
                    placeholder="например, 10"
                    onChange={(event) => setReceipt(event.target.value)}
                  />
                </label>
                <button type="button" className="btn btn--primary btn--sm" disabled={action.busy} onClick={() => void doReceipt()}>
                  Принять
                </button>
              </div>
            ) : (
              <ErrorBanner message="Приход на склад доступен руководителю и администратору." />
            )}
            <span className="muted">
              Место хранения: {selected.location ?? 'не указано'}. Остаток меняется только приходом и списанием в
              заявку — вручную в форме он не правится.
            </span>
          </div>
        )}
      </Card>
    </div>
  )
}