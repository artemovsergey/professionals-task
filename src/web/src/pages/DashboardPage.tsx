/* ===========================================================================
   ТОиР-Проф — главный дашборд руководителя.

   Из листа задания: шесть KPI-карточек, круговая, столбчатая и линейная
   диаграммы, топ-5 единиц по простою и таблица последних заявок.

   Сводка приходит потоком событий (SSE), а если он недоступен — резервным
   опросом раз в минуту; см. useDashboardStream. Топ-5 простоев в сводке
   нет: он считается в аналитике, поэтому эта страница дополнительно
   запрашивает /api/analytics. Повод для второго запроса — требование
   листа: дашборд показывает и аналитический срез.
   =========================================================================== */

import { useEffect, useMemo, useState } from 'react'
import { dashboardApi, workOrdersApi } from '../api/endpoints'
import type { DashboardSummary, WorkOrderShortDto } from '../api/types'
import { DataTable } from '../components/DataTable'
import { Badge, Card, ConnectionBadge, EmptyState, ErrorBanner, Loading, LoadingBar, MetricCard } from '../components/Ui'
import { MonthlyLine, PlanDonut, StatusPie, TopDowntimeBar, WorkshopBar } from '../components/charts/Charts'
import { useConnection } from '../hooks/connection'
import { useDashboardStream } from '../hooks/useDashboardStream'
import { useLoad } from '../hooks/useLoad'
import { formatHours, formatMoney, formatPercent, isoDaysAgo, periodLabel } from '../utils/format'

/** Шесть карточек из листа задания. Порядок повторяет отчёт руководителю. */
function buildCards(summary: DashboardSummary) {
  const workshops = summary.byWorkshop.map((item) => `${item.name}: ${item.total}`).join(' · ')

  return [
    {
      title: 'Заявок за период',
      value: String(summary.totalOrders),
      hint: `завершено ${summary.completed} · в работе ${summary.inProgress}`,
      tone: 'info' as const,
    },
    {
      title: 'Средний простой',
      value: formatHours(summary.averageDowntimeHours),
      hint: 'на одну завершённую заявку',
      tone: 'wait' as const,
    },
    {
      title: 'Доля аварийных',
      value: formatPercent(summary.emergencyShare),
      hint: summary.emergencyShare > 15 ? 'выше нормы — разберитесь с причинами' : 'в пределах нормы',
      tone: summary.emergencyShare > 15 ? ('bad' as const) : ('ok' as const),
    },
    {
      title: 'Выполнение плана ТО',
      value: formatPercent(summary.maintenancePlanShare),
      hint: 'доля выполненных плановых работ',
      tone: summary.maintenancePlanShare >= 80 ? ('ok' as const) : ('wait' as const),
    },
    {
      title: 'Списано материалов',
      value: formatMoney(summary.totalMaterialCost),
      hint: 'по всем завершённым работам',
      tone: 'info' as const,
    },
    {
      title: 'Цехов в работе',
      value: String(summary.byWorkshop.length),
      hint: workshops || 'нет данных',
      tone: 'info' as const,
    },
  ]
}

const recentColumns = [
  {
    key: 'number',
    title: 'Номер',
    render: (row: WorkOrderShortDto) => <span className="mono nowrap">{row.number}</span>,
  },
  { key: 'equipment', title: 'Оборудование', render: (row: WorkOrderShortDto) => row.equipmentName },
  {
    key: 'inventory',
    title: 'Инв. номер',
    render: (row: WorkOrderShortDto) => <span className="mono">{row.inventoryNumber}</span>,
  },
  { key: 'priority', title: 'Приоритет', render: (row: WorkOrderShortDto) => <Badge text={row.priority} /> },
  { key: 'status', title: 'Статус', render: (row: WorkOrderShortDto) => <Badge text={row.status} /> },
  {
    key: 'downtime',
    title: 'Простой, ч',
    numeric: true,
    render: (row: WorkOrderShortDto) => (row.downtimeHours == null ? '—' : formatHours(row.downtimeHours)),
  },
  { key: 'crew', title: 'Бригада', render: (row: WorkOrderShortDto) => row.crewName ?? '—' },
]

export function DashboardPage() {
  const [from, setFrom] = useState(() => isoDaysAgo(-30))
  const [to, setTo] = useState(() => isoDaysAgo(0))
  const [retry, setRetry] = useState(0)

  const { setConnection } = useConnection()
  const stream = useDashboardStream(from, to, retry)

  const recent = useLoad((signal) => workOrdersApi.recent(8, signal), [])
  const analytics = useLoad((signal) => dashboardApi.analytics(from, to, undefined, signal), [from, to])

  // Индикатор в верхней панели должен видеть статус потока с любой страницы,
  // а поток живёт только здесь — поэтому статус дублируется в контекст.
  useEffect(() => {
    setConnection(stream.status, stream.caption)
  }, [setConnection, stream.status, stream.caption])

  const summary = stream.data
  const cards = useMemo(() => (summary ? buildCards(summary) : []), [summary])
  const downtime = analytics.data?.downtime ?? []
  const plan = analytics.data?.plan ?? []

  const reload = () => {
    setRetry((value) => value + 1)
    analytics.reload()
    recent.reload()
  }

  return (
    <div className="grid">
      <div className="section-title no-print">
        <h1>Дашборд руководителя</h1>
        <label className="check">
          с
          <input
            className="input"
            type="date"
            style={{ width: 140 }}
            value={from}
            max={to}
            onChange={(event) => setFrom(event.target.value)}
          />
        </label>
        <label className="check">
          по
          <input
            className="input"
            type="date"
            style={{ width: 140 }}
            value={to}
            min={from}
            onChange={(event) => setTo(event.target.value)}
          />
        </label>
        <button type="button" className="btn btn--sm" onClick={() => setFrom(isoDaysAgo(-30))}>
          30 дней
        </button>
        <button type="button" className="btn btn--sm" onClick={() => setFrom(isoDaysAgo(-90))}>
          90 дней
        </button>
        <ConnectionBadge status={stream.status} caption={stream.caption} />
        <span className="muted">
          {periodLabel(from, to)}
          {stream.lastUpdate ? ` · обновлено в ${stream.lastUpdate.toLocaleTimeString('ru-RU')}` : ''}
        </span>
      </div>

      <LoadingBar visible={!summary && stream.status !== 'offline'} />

      {stream.status === 'offline' ? (
        <ErrorBanner message="Нет связи с сервером. Показаны последние загруженные данные." onRetry={reload} />
      ) : null}

      {summary ? (
        <>
          <div className="kpi-row">
            {cards.map((card) => (
              <MetricCard key={card.title} title={card.title} value={card.value} hint={card.hint} tone={card.tone} />
            ))}
          </div>

          <div className="grid grid--2">
            <Card title="Статусы заявок" hint="круговая диаграмма">
              <StatusPie data={summary.byStatus} />
            </Card>
            <Card title="Заявки по цехам" hint="столбчатая диаграмма">
              <WorkshopBar data={summary.byWorkshop} />
            </Card>
          </div>

          <div className="grid grid--2">
            <Card title="Динамика по месяцам" hint="линейная диаграмма">
              <MonthlyLine data={summary.byMonth} />
            </Card>
            <Card title="Топ-5 единиц по простою" hint="красным — худшая">
              {analytics.error ? <ErrorBanner message={analytics.error} onRetry={analytics.reload} /> : null}
              <TopDowntimeBar data={downtime} />
            </Card>
          </div>

          <div className="grid grid--2">
            <Card title="Выполнение графика ТО" hint="доли по статусам">
              <PlanDonut data={plan} />
            </Card>
            <Card title="Простой по цехам" hint="часы за период">
              <WorkshopBar data={summary.byWorkshop} metric="downtime" />
            </Card>
          </div>

          <Card title="Последние заявки" hint="сортировка по дате создания">
            {recent.error ? <ErrorBanner message={recent.error} onRetry={recent.reload} /> : null}
            <DataTable
              columns={recentColumns}
              rows={recent.data?.items ?? []}
              rowKey={(row) => row.id}
              loading={recent.loading}
              empty="Заявок пока нет"
            />
          </Card>
        </>
      ) : stream.status === 'offline' ? (
        <EmptyState caption="Сводка недоступна: нет связи с сервером" />
      ) : (
        <Loading caption="Загружаю сводку…" />
      )}
    </div>
  )
}
