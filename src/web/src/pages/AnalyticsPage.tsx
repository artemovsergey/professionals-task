/* ===========================================================================
   ТОиР-Проф — аналитика руководителя.

   Требование листа: панель фильтров и пять блоков — сводка по заявкам,
   анализ простоев, анализ материалов, выполнение графика ТО и
   эффективность бригад с рейтингом. Каждый блок выгружается в PNG, CSV
   и PDF, вся страница печатается.

   Данные приходят одним запросом /api/analytics: пять отдельных запросов
   дали бы пять разных моментов времени, и цифры в блоках разошлись бы
   между собой — на демонстрации это выглядит как ошибка.
   =========================================================================== */

import { useRef, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { dashboardApi } from '../api/endpoints'
import type {
  CrewEfficiency,
  DowntimeSlice,
  MaterialUsage,
  OrdersSummary,
  PlanExecutionSlice,
} from '../api/types'
import { DataTable } from '../components/DataTable'
import type { Column } from '../components/DataTable'
import { ExportMenu } from '../components/ExportMenu'
import { Badge, Card, EmptyState, ErrorBanner, Loading, LoadingBar, MetricCard } from '../components/Ui'
import { PlanDonut, TopDowntimeBar } from '../components/charts/Charts'
import { printPage } from '../hooks/useExport'
import type { ExportColumn } from '../hooks/useExport'
import { useLoad } from '../hooks/useLoad'
import { formatHours, formatMoney, formatNumber, formatPercent, isoDaysAgo, periodLabel } from '../utils/format'

/* ----------------------------- колонки таблиц ----------------------------- */

const ordersColumns: Column<OrdersSummary>[] = [
  { key: 'total', title: 'Заявок всего', numeric: true, render: (row) => formatNumber(row.total) },
  { key: 'completed', title: 'Завершено', numeric: true, render: (row) => formatNumber(row.completed) },
  { key: 'inProgress', title: 'В работе', numeric: true, render: (row) => formatNumber(row.inProgress) },
  { key: 'cancelled', title: 'Отменено', numeric: true, render: (row) => formatNumber(row.cancelled) },
  {
    key: 'completionShare',
    title: 'Доля завершённых',
    numeric: true,
    render: (row) => formatPercent(row.completionShare),
  },
  {
    key: 'emergencyShare',
    title: 'Доля аварийных',
    numeric: true,
    render: (row) => formatPercent(row.emergencyShare),
  },
  {
    key: 'averageDowntimeHours',
    title: 'Средний простой',
    numeric: true,
    render: (row) => formatHours(row.averageDowntimeHours),
  },
]

const ordersCsv: ExportColumn<OrdersSummary>[] = [
  { title: 'Заявок всего', value: (row) => row.total },
  { title: 'Завершено', value: (row) => row.completed },
  { title: 'В работе', value: (row) => row.inProgress },
  { title: 'Отменено', value: (row) => row.cancelled },
  { title: 'Доля завершённых, %', value: (row) => row.completionShare },
  { title: 'Доля аварийных, %', value: (row) => row.emergencyShare },
  { title: 'Средний простой, ч', value: (row) => row.averageDowntimeHours },
]

const downtimeColumns: Column<DowntimeSlice>[] = [
  { key: 'inventoryNumber', title: 'Инв. номер', render: (row) => <span className="mono">{row.inventoryNumber}</span> },
  { key: 'name', title: 'Оборудование', render: (row) => row.name },
  { key: 'workshopName', title: 'Цех', render: (row) => row.workshopName },
  { key: 'ordersCount', title: 'Заявок', numeric: true, render: (row) => formatNumber(row.ordersCount) },
  { key: 'totalDowntimeHours', title: 'Простой, ч', numeric: true, render: (row) => formatHours(row.totalDowntimeHours) },
  { key: 'sharePercent', title: 'Доля, %', numeric: true, render: (row) => formatPercent(row.sharePercent) },
]

const downtimeCsv: ExportColumn<DowntimeSlice>[] = [
  { title: 'Инв. номер', value: (row) => row.inventoryNumber },
  { title: 'Оборудование', value: (row) => row.name },
  { title: 'Цех', value: (row) => row.workshopName },
  { title: 'Заявок', value: (row) => row.ordersCount },
  { title: 'Простой, ч', value: (row) => row.totalDowntimeHours },
  { title: 'Доля, %', value: (row) => row.sharePercent },
]

const materialColumns: Column<MaterialUsage>[] = [
  { key: 'sku', title: 'Артикул', render: (row) => <span className="mono">{row.sku}</span> },
  { key: 'name', title: 'Материал', render: (row) => row.name },
  { key: 'quantity', title: 'Списано', numeric: true, render: (row) => `${row.quantity} ${row.unit}` },
  { key: 'cost', title: 'Стоимость', numeric: true, render: (row) => formatMoney(row.cost) },
  { key: 'ordersCount', title: 'Заявок', numeric: true, render: (row) => formatNumber(row.ordersCount) },
]

const materialCsv: ExportColumn<MaterialUsage>[] = [
  { title: 'Артикул', value: (row) => row.sku },
  { title: 'Материал', value: (row) => row.name },
  { title: 'Списано', value: (row) => row.quantity },
  { title: 'Единица', value: (row) => row.unit },
  { title: 'Стоимость', value: (row) => row.cost },
  { title: 'Заявок', value: (row) => row.ordersCount },
]

const planColumns: Column<PlanExecutionSlice>[] = [
  { key: 'status', title: 'Статус', render: (row) => <Badge text={row.status} /> },
  { key: 'count', title: 'Количество', numeric: true, render: (row) => formatNumber(row.count) },
  { key: 'percent', title: 'Доля, %', numeric: true, render: (row) => formatPercent(row.percent) },
]

const planCsv: ExportColumn<PlanExecutionSlice>[] = [
  { title: 'Статус', value: (row) => row.status },
  { title: 'Количество', value: (row) => row.count },
  { title: 'Доля, %', value: (row) => row.percent },
]

const crewColumns: Column<CrewEfficiency>[] = [
  { key: 'code', title: 'Код', render: (row) => <span className="mono">{row.code}</span> },
  { key: 'name', title: 'Бригада', render: (row) => row.name },
  { key: 'assigned', title: 'Назначено', numeric: true, render: (row) => formatNumber(row.assigned) },
  { key: 'completed', title: 'Завершено', numeric: true, render: (row) => formatNumber(row.completed) },
  { key: 'inTime', title: 'В срок', numeric: true, render: (row) => formatNumber(row.inTime) },
  {
    key: 'averageDowntimeHours',
    title: 'Средний простой',
    numeric: true,
    render: (row) => formatHours(row.averageDowntimeHours),
  },
  {
    key: 'totalMaterialCost',
    title: 'Материалы',
    numeric: true,
    render: (row) => formatMoney(row.totalMaterialCost),
  },
  {
    key: 'rating',
    title: 'Рейтинг',
    numeric: true,
    render: (row) => (
      <Badge
        text={formatPercent(row.rating)}
        tone={row.rating >= 80 ? 'ok' : row.rating >= 50 ? 'wait' : 'bad'}
      />
    ),
  },
]

const crewCsv: ExportColumn<CrewEfficiency>[] = [
  { title: 'Код', value: (row) => row.code },
  { title: 'Бригада', value: (row) => row.name },
  { title: 'Назначено', value: (row) => row.assigned },
  { title: 'Завершено', value: (row) => row.completed },
  { title: 'В срок', value: (row) => row.inTime },
  { title: 'Средний простой, ч', value: (row) => row.averageDowntimeHours },
  { title: 'Материалы', value: (row) => row.totalMaterialCost },
  { title: 'Рейтинг, %', value: (row) => row.rating },
]

/* -------------------------------- страница -------------------------------- */

export function AnalyticsPage() {
  const { can } = useAuth()

  const [from, setFrom] = useState(() => isoDaysAgo(-90))
  const [to, setTo] = useState(() => isoDaysAgo(0))
  const [workshop, setWorkshop] = useState('')

  const load = useLoad(
    (signal) => dashboardApi.analytics(from, to, workshop === '' ? undefined : workshop, signal),
    [from, to, workshop],
  )

  // У каждого блока свой ref: html2canvas снимает ровно тот узел,
  // который передан в ExportMenu.
  const ordersRef = useRef<HTMLDivElement | null>(null)
  const downtimeRef = useRef<HTMLDivElement | null>(null)
  const materialsRef = useRef<HTMLDivElement | null>(null)
  const planRef = useRef<HTMLDivElement | null>(null)
  const crewsRef = useRef<HTMLDivElement | null>(null)

  const report = load.data
  const allowed = can('ADMIN', 'MANAGER')

  // Справочника цехов в API нет, поэтому список для фильтра собирается из
  // названий, которые пришли в срезе простоев.
  const workshops = [...new Set((report?.downtime ?? []).map((item) => item.workshopName))].sort()
  const materialCost = (report?.materials ?? []).reduce((sum, item) => sum + item.cost, 0)

  return (
    <div className="grid">
      <div className="section-title no-print">
        <h1>Аналитика</h1>
        <span className="muted">{periodLabel(from, to)}</span>
        <button type="button" className="btn btn--sm" onClick={printPage}>
          Печать страницы
        </button>
        <button type="button" className="btn btn--ghost btn--sm" onClick={load.reload} disabled={load.loading}>
          Обновить
        </button>
      </div>

      <LoadingBar visible={load.loading} />

      {!allowed ? <ErrorBanner message="Раздел доступен руководителю и администратору." /> : null}
      {load.error ? <ErrorBanner message={load.error} onRetry={load.reload} /> : null}

      <Card title="Панель фильтров" className="no-print">
        <div className="form-grid">
          <label className="field">
            Период с
            <input
              className="input"
              type="date"
              value={from}
              max={to}
              onChange={(event) => setFrom(event.target.value)}
            />
          </label>
          <label className="field">
            по
            <input
              className="input"
              type="date"
              value={to}
              min={from}
              onChange={(event) => setTo(event.target.value)}
            />
          </label>
          <label className="field">
            Цех
            <select className="select" value={workshop} onChange={(event) => setWorkshop(event.target.value)}>
              <option value="">Все цеха</option>
              {workshops.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <span className="muted">
          Цех в списке появляется, когда за выбранный период есть заявки с простоем. Пустой список означает, что фильтр
          нечего уточнять.
        </span>
      </Card>

      {load.loading && !report ? <Loading caption="Считаю показатели…" /> : null}

      {report ? (
        <>
          <div className="kpi-row">
            <MetricCard title="Заявок за период" value={formatNumber(report.orders.total)} hint={periodLabel(from, to)} />
            <MetricCard
              title="Завершено"
              value={formatPercent(report.orders.completionShare)}
              hint={`${report.orders.completed} из ${report.orders.total}`}
              tone={report.orders.completionShare >= 70 ? 'ok' : 'wait'}
            />
            <MetricCard
              title="Доля аварийных"
              value={formatPercent(report.orders.emergencyShare)}
              tone={report.orders.emergencyShare > 15 ? 'bad' : 'ok'}
              hint="от всех заявок периода"
            />
            <MetricCard
              title="Средний простой"
              value={formatHours(report.orders.averageDowntimeHours)}
              tone="wait"
              hint="на завершённую заявку"
            />
            <MetricCard title="Списано материалов" value={formatMoney(materialCost)} />
            <MetricCard title="Бригад в рейтинге" value={formatNumber(report.crews.length)} />
          </div>

          <Card
            title="Блок 1. Сводка по заявкам"
            hint="сколько пришло, сколько закрыто"
            actions={
              <ExportMenu
                name="аналитика-сводка"
                target={ordersRef}
                columns={ordersCsv}
                rows={[report.orders]}
                disabled={load.loading}
              />
            }
          >
            <div ref={ordersRef}>
              <DataTable columns={ordersColumns} rows={[report.orders]} rowKey={() => 'orders'} />
            </div>
          </Card>

          <Card
            title="Блок 2. Анализ простоев"
            hint="топ единиц оборудования"
            actions={
              <ExportMenu
                name="аналитика-простои"
                target={downtimeRef}
                columns={downtimeCsv}
                rows={report.downtime}
                disabled={load.loading}
              />
            }
          >
            <div ref={downtimeRef}>
              <TopDowntimeBar data={report.downtime} />
              <DataTable
                columns={downtimeColumns}
                rows={report.downtime}
                rowKey={(row) => row.equipmentId}
                empty="Простоев за период нет"
              />
            </div>
          </Card>

          <Card
            title="Блок 3. Расход материалов"
            hint="что списали и на сколько"
            actions={
              <ExportMenu
                name="аналитика-материалы"
                target={materialsRef}
                columns={materialCsv}
                rows={report.materials}
                disabled={load.loading}
              />
            }
          >
            <div ref={materialsRef}>
              <DataTable
                columns={materialColumns}
                rows={report.materials}
                rowKey={(row) => row.materialId}
                empty="Списаний за период нет"
              />
            </div>
          </Card>

          <Card
            title="Блок 4. Выполнение графика ТО"
            hint="плановые работы по статусам"
            actions={
              <ExportMenu
                name="аналитика-план"
                target={planRef}
                columns={planCsv}
                rows={report.plan}
                disabled={load.loading}
              />
            }
          >
            <div ref={planRef}>
              <PlanDonut data={report.plan} />
              <DataTable columns={planColumns} rows={report.plan} rowKey={(row) => row.status} empty="Плановых работ нет" />
            </div>
          </Card>

          <Card
            title="Блок 5. Эффективность бригад"
            hint="рейтинг по завершённым заявкам"
            actions={
              <ExportMenu
                name="аналитика-бригады"
                target={crewsRef}
                columns={crewCsv}
                rows={report.crews}
                disabled={load.loading}
              />
            }
          >
            <div ref={crewsRef}>
              <DataTable
                columns={crewColumns}
                rows={report.crews}
                rowKey={(row) => row.crewId}
                empty="За период бригады не работали"
              />
            </div>
          </Card>
        </>
      ) : !load.loading && !load.error ? (
        <EmptyState caption="Показателей за выбранный период нет" />
      ) : null}
    </div>
  )
}