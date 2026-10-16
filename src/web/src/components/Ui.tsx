/* ===========================================================================
   ТОиР-Проф — мелкие переиспользуемые элементы: бейджи, состояния,
   карточка KPI, индикатор соединения.
   =========================================================================== */

import type { ReactNode } from 'react'
import type { StreamStatus } from '../hooks/useDashboardStream'

type Tone = 'info' | 'ok' | 'wait' | 'bad' | 'plain'

/* -------------------------------- Бейдж ---------------------------------- */

/**
 * Тон бейджа выводится из текста, а не задаётся на каждом вызове: иначе
 * на одном экране «Завершена» будет зелёной, а на другом — синей, и
 * руководитель будет читать одну и ту же заявку по-разному.
 */
function toneOf(text: string): Tone {
  if (/выведен|отмен|просрочен|отказ/i.test(text)) return 'bad'
  if (/заверш|выполн|работает/i.test(text)) return 'ok'
  if (/работе|ремонт|назнач|запланирован|просрочен/i.test(text)) return 'wait'
  if (/черновик|аварийн/i.test(text)) return 'info'
  return 'plain'
}

export function Badge({ text, tone }: { text: string; tone?: Tone }) {
  const resolved = tone ?? toneOf(text)
  const className = resolved === 'plain' ? 'badge' : `badge badge--${resolved}`
  return <span className={className}>{text}</span>
}

/* ------------------------------- Состояния -------------------------------- */

export function Loading({ caption = 'Загрузка данных…' }: { caption?: string }) {
  return (
    <div className="state" role="status" aria-live="polite">
      <div className="spinner" />
      <span>{caption}</span>
    </div>
  )
}

export function LoadingBar({ visible }: { visible: boolean }) {
  return visible ? <div className="loading-bar" role="progressbar" aria-label="Идёт загрузка" /> : null
}

export function ErrorBanner({ message, onRetry, busy }: { message: string; onRetry?: () => void; busy?: boolean }) {
  return (
    <div className="banner" role="alert">
      <span className="banner__text">{message}</span>
      {onRetry ? (
        <button type="button" className="btn btn--sm" onClick={onRetry} disabled={busy}>
          Повторить
        </button>
      ) : null}
    </div>
  )
}

export function InfoBanner({ children }: { children: ReactNode }) {
  return (
    <div className="banner banner--info">
      <span className="banner__text">{children}</span>
    </div>
  )
}

export function EmptyState({ caption = 'Данных нет' }: { caption?: string }) {
  return (
    <div className="state">
      <span>{caption}</span>
    </div>
  )
}

/* -------------------------------- KPI ------------------------------------ */

export type KpiTone = 'info' | 'ok' | 'wait' | 'bad'

export function MetricCard({ title, value, hint, tone = 'info' }: { title: string; value: string; hint?: string; tone?: KpiTone }) {
  const className = tone === 'info' ? 'kpi' : `kpi kpi--${tone}`
  return (
    <div className={className}>
      <span className="kpi__title">{title}</span>
      <span className="kpi__value">{value}</span>
      {hint ? <span className="kpi__hint">{hint}</span> : null}
    </div>
  )
}

/* --------------------- Индикатор соединения с сервером -------------------- */

const STATUS_LABEL: Record<StreamStatus, string> = {
  live: 'SSE',
  polling: 'Опрос',
  offline: 'Нет связи',
}

const STATUS_DOT: Record<StreamStatus, string> = {
  live: 'dot dot--live',
  polling: 'dot dot--poll',
  offline: 'dot dot--off',
}

export function ConnectionBadge({ status, caption }: { status: StreamStatus; caption: string }) {
  return (
    <span className="badge" title={caption}>
      <span className={STATUS_DOT[status]} />
      {STATUS_LABEL[status]}
    </span>
  )
}

/* ------------------------------ Разделитель ------------------------------- */

export function Card({ title, hint, actions, children, className = '' }: { title?: string; hint?: string; actions?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`card ${className}`.trim()}>
      {title ? (
        <header className="card__head">
          <h2>{title}</h2>
          {hint ? <span className="card__hint">{hint}</span> : null}
          {actions}
        </header>
      ) : null}
      {children}
    </section>
  )
}
