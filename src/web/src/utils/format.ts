/* ===========================================================================
   ТОиР-Проф — форматирование значений для интерфейса.

   Русская локаль требует запятой в качестве десятичного разделителя и
   неразрывного пробела перед единицами измерения. Если это делать в
   каждом экране, к концу проекта разделители разъедутся, поэтому все
   правила собраны здесь.
   =========================================================================== */

/** Неразрывный пробел: «24,5 ч» не должно разрываться переносом строки. */
const NBSP = ' '

function decimal(value: number, digits: number): string {
  return value.toFixed(digits).replace('.', ',')
}

export function formatNumber(value: number): string {
  return Math.round(value).toLocaleString('ru-RU')
}

export function formatMoney(value: number): string {
  return `${value.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}${NBSP}₽`
}

export function formatHours(value: number): string {
  return `${decimal(value, 1)}${NBSP}ч`
}

export function formatPercent(value: number): string {
  return `${decimal(value, 1)}${NBSP}%`
}

export function formatQuantity(value: number): string {
  return decimal(value, 2).replace(/,?0+$/, '')
}

/** Дата из API приходит строкой «2026-03-20», её и показываем без часов. */
export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(`${value.slice(0, 10)}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('ru-RU')
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' })
}

/** Смещение в днях от сегодняшней даты. Отрицательное — в прошлом. */
export function isoDaysAgo(days: number): string {
  const date = new Date()
  date.setDate(date.getDate() + days)
  return date.toISOString().slice(0, 10)
}

/** Подпись периода для панели фильтров. */
export function periodLabel(from: string, to: string): string {
  return `${formatDate(from)} — ${formatDate(to)}`
}

export function today(): string {
  return isoDaysAgo(0)
}
