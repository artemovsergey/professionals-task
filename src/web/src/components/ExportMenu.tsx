/* ===========================================================================
   ТОиР-Проф — кнопки экспорта блока.

   Требование листа: каждый блок аналитики выгружается в PNG, CSV и PDF,
   а вся страница печатается. Меню вынесено отдельным компонентом, потому
   что одинаково повторяется в пяти блоках, а отличается только тем, на
   какой узел страницы смотрит html2canvas.
   =========================================================================== */

import { useState } from 'react'
import type { RefObject } from 'react'
import type { ExportColumn } from '../hooks/useExport'
import { exportCsv, exportPdf, exportPng, stamp } from '../hooks/useExport'

interface ExportMenuProps<T> {
  /** Имя блока в подписи файла: «аналитика-простои». */
  name: string
  /** ref на корневой узел блока — его и снимает html2canvas. */
  target: RefObject<HTMLElement | null>
  /** Колонки для CSV. */
  columns: ExportColumn<T>[]
  rows: T[]
  /** Снимать блок, пока идёт обновление, смысла нет. */
  disabled?: boolean
}

export function ExportMenu<T>({ name, target, columns, rows, disabled = false }: ExportMenuProps<T>) {
  const [busy, setBusy] = useState<'png' | 'pdf' | null>(null)
  const file = stamp(name)

  const run = async (kind: 'png' | 'pdf') => {
    const element = target.current
    if (!element) return
    setBusy(kind)
    try {
      if (kind === 'png') await exportPng(element, file)
      else await exportPdf(element, file)
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="btn-row no-print">
      <button
        type="button"
        className="btn btn--ghost btn--sm"
        disabled={disabled || rows.length === 0}
        onClick={() => exportCsv(file, columns, rows)}
      >
        CSV
      </button>
      <button type="button" className="btn btn--ghost btn--sm" disabled={disabled || busy !== null} onClick={() => void run('png')}>
        {busy === 'png' ? 'Снимаю…' : 'PNG'}
      </button>
      <button type="button" className="btn btn--ghost btn--sm" disabled={disabled || busy !== null} onClick={() => void run('pdf')}>
        {busy === 'pdf' ? 'Готовлю…' : 'PDF'}
      </button>
    </div>
  )
}