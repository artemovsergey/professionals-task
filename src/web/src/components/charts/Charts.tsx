/* ===========================================================================
   ТОиР-Проф — диаграммы дашборда.
   Три типа из задания: круговая (статусы заявок), столбчатая (цеха и топ
   простоев) и линейная (динамика по месяцам). Палитра совпадает с токенами
   темы, поэтому графики не выбиваются из тёмного интерфейса.
   =========================================================================== */

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { DowntimeSlice, MonthSlice, StatusSlice, WorkshopSlice } from '../../api/types'

const AXIS = '#9aa6b2'
const GRID = '#3a424c'
const TOOLTIP_BG = '#2c333b'
const TOOLTIP_BORDER = '#3a424c'

const PALETTE = ['#3d7dd6', '#3fa66b', '#c79a2e', '#d0553f', '#8b6fd0', '#4aa3a8', '#b06fd0', '#6b7f8f']

/** Палитра статусов заявок задана явно, иначе recharts перемешает цвета. */
const STATUS_COLORS: Record<string, string> = {
  Завершена: '#3fa66b',
  'В работе': '#3d7dd6',
  Назначена: '#c79a2e',
  Черновик: '#6b7f8f',
  Отменена: '#d0553f',
}

const tooltipStyle = {
  background: TOOLTIP_BG,
  border: `1px solid ${TOOLTIP_BORDER}`,
  borderRadius: 8,
  color: '#e8edf2',
  fontSize: 12,
}

function Empty({ caption }: { caption: string }) {
  return (
    <div className="state" style={{ height: 220 }}>
      <span>{caption}</span>
    </div>
  )
}

/* ------------------------- Круговая: статусы заявок ----------------------- */

export function StatusPie({ data }: { data: StatusSlice[] }) {
  if (data.length === 0) return <Empty caption="Заявок за период нет" />

  return (
    <>
      <div className="chart chart--sm">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="count"
              nameKey="status"
              innerRadius={52}
              outerRadius={86}
              paddingAngle={2}
              stroke="none"
            >
              {data.map((item) => (
                <Cell key={item.status} fill={STATUS_COLORS[item.status] ?? PALETTE[0]} />
              ))}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="chart-legend">
        {data.map((item) => (
          <span key={item.status} className="chart-legend__item">
            <span className="chart-legend__swatch" style={{ background: STATUS_COLORS[item.status] ?? PALETTE[0] }} />
            {item.status} — {item.count}
          </span>
        ))}
      </div>
    </>
  )
}

/* ---------------------- Столбчатая: заявки по цехам ------------------------ */

export function WorkshopBar({ data, metric = 'total' }: { data: WorkshopSlice[]; metric?: 'total' | 'downtime' }) {
  if (data.length === 0) return <Empty caption="Данных по цехам нет" />

  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -16 }}>
          <CartesianGrid stroke={GRID} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" stroke={AXIS} tick={{ fontSize: 12 }} />
          <YAxis stroke={AXIS} tick={{ fontSize: 12 }} allowDecimals={metric === 'downtime'} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
          {metric === 'total' ? (
            <>
              <Bar dataKey="total" name="Заявок" fill="#3d7dd6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="completed" name="Завершено" fill="#3fa66b" radius={[4, 4, 0, 0]} />
            </>
          ) : (
            <Bar dataKey="totalDowntimeHours" name="Простой, ч" fill="#c79a2e" radius={[4, 4, 0, 0]} />
          )}
          <Legend wrapperStyle={{ fontSize: 12 }} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/* ----------------------- Линейная: динамика по месяцам -------------------- */

export function MonthlyLine({ data }: { data: MonthSlice[] }) {
  if (data.length === 0) return <Empty caption="Динамика за период отсутствует" />

  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -16 }}>
          <CartesianGrid stroke={GRID} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="label" stroke={AXIS} tick={{ fontSize: 12 }} />
          <YAxis stroke={AXIS} tick={{ fontSize: 12 }} />
          <Tooltip contentStyle={tooltipStyle} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line
            type="monotone"
            dataKey="count"
            name="Заявок"
            stroke="#3d7dd6"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
          <Line
            type="monotone"
            dataKey="downtimeHours"
            name="Простой, ч"
            stroke="#c79a2e"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

/* --------------------- Столбчатая: топ-5 единиц по простою ----------------- */

export function TopDowntimeBar({ data }: { data: DowntimeSlice[] }) {
  if (data.length === 0) return <Empty caption="Простоев за период нет" />

  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
          <CartesianGrid stroke={GRID} strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" stroke={AXIS} tick={{ fontSize: 12 }} />
          <YAxis type="category" dataKey="inventoryNumber" stroke={AXIS} tick={{ fontSize: 12 }} width={70} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
          <Bar dataKey="totalDowntimeHours" name="Простой, ч" radius={[0, 4, 4, 0]}>
            {data.map((item, index) => (
              <Cell key={item.equipmentId} fill={index === 0 ? '#d0553f' : PALETTE[index % PALETTE.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/* ------------------------------ План ТО ---------------------------------- */

const PLAN_COLORS: Record<string, string> = {
  Выполнено: '#3fa66b',
  Запланировано: '#3d7dd6',
  Просрочено: '#d0553f',
}

export function PlanDonut({ data }: { data: { status: string; count: number }[] }) {
  if (data.length === 0) return <Empty caption="Плановых работ нет" />
  return (
    <>
      <div className="chart chart--sm">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="count" nameKey="status" outerRadius={86} stroke="none">
              {data.map((item) => (
                <Cell key={item.status} fill={PLAN_COLORS[item.status] ?? PALETTE[0]} />
              ))}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="chart-legend">
        {data.map((item) => (
          <span key={item.status} className="chart-legend__item">
            <span className="chart-legend__swatch" style={{ background: PLAN_COLORS[item.status] ?? PALETTE[0] }} />
            {item.status} — {item.count}
          </span>
        ))}
      </div>
    </>
  )
}

export { PALETTE, STATUS_COLORS, PLAN_COLORS }
