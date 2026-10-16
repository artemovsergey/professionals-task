/* ===========================================================================
   ТОиР-Проф — экспорт блоков аналитики.

   Требование листа: каждый блок аналитики выгружается в PNG, CSV и PDF,
   плюс печать страницы целиком. Здесь три независимых механизма:

   * CSV — вручную, чтобы файл открывался в Excel без танцев с кодировкой.
   * PNG — html2canvas снимает DOM-узел блока.
   * PDF — jsPDF собирает страницу из снятого изображения: векторный текст
     не нужен, а шрифты не приходится встраивать вручную.
   =========================================================================== */

import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'

export interface ExportColumn<T> {
  title: string
  value: (row: T) => string | number | null
}

/** Знак разделителя — запятая; Excel в русской локали примет файл и так. */
const CSV_SEPARATOR = ','
/** Перевод строки CRLF: LibreOffice и Excel ждут именно его в CSV. */
const CSV_EOL = '\r\n'

/**
 * Скачивание файла. object URL освобождается сразу: если этого не сделать,
 * вкладка держит в памяти копию каждого выгруженного отчёта.
 */
function download(blobUrl: string, filename: string): void {
  const anchor = document.createElement('a')
  anchor.href = blobUrl
  anchor.download = filename
  document.body.append(anchor)
  anchor.click()
  anchor.remove()
}

export function exportCsv<T>(filename: string, columns: ExportColumn<T>[], rows: T[]): void {
  const escape = (value: string): string => {
    // Кавычки внутри значения удваиваются по RFC 4180, иначе поле разъедется.
    const cleaned = value.replaceAll('"', '""')
    return /["\n\r]/.test(cleaned) ? `"${cleaned}"` : cleaned
  }

  const lines = [
    columns.map((column) => escape(column.title)).join(CSV_SEPARATOR),
    ...rows.map((row) =>
      columns
        .map((column) => {
          const raw = column.value(row)
          return escape(raw === null || raw === undefined ? '' : String(raw))
        })
        .join(CSV_SEPARATOR),
    ),
  ]

  // BOM обязателен: без него Excel откроет кириллицу как «Ð¡Ð¸ÑÐ¾Ð½»,
  // потому что угадывает кодировку как windows-1251.
  const blob = new Blob(['﻿', lines.join(CSV_EOL)], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  download(url, `${filename}.csv`)
  URL.revokeObjectURL(url)
}

/** Снятие блока в картинку. `background` задаётся явно: html2canvas иначе делает прозрачный фон. */
async function capture(element: HTMLElement): Promise<HTMLCanvasElement> {
  return html2canvas(element, {
    backgroundColor: '#242a31',
    scale: 2,
    logging: false,
    useCORS: true,
  })
}

export async function exportPng(element: HTMLElement, filename: string): Promise<void> {
  const canvas = await capture(element)
  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png'))
  if (!blob) throw new Error('Не удалось сформировать изображение')
  const url = URL.createObjectURL(blob)
  download(url, `${filename}.png`)
  URL.revokeObjectURL(url)
}

export async function exportPdf(element: HTMLElement, filename: string): Promise<void> {
  const canvas = await capture(element)

  // Страница альбомная A4: в блоках аналитики до восьми колонок,
  // в книжной ориентации они не помещаются.
  const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' })
  const pageWidth = pdf.internal.pageSize.getWidth()
  const pageHeight = pdf.internal.pageSize.getHeight()
  const margin = 8
  const fit = Math.min((pageWidth - margin * 2) / canvas.width, (pageHeight - margin * 2) / canvas.height)

  const width = canvas.width * fit
  const height = canvas.height * fit
  const image = canvas.toDataURL('image/png')
  pdf.addImage(image, 'PNG', (pageWidth - width) / 2, (pageHeight - height) / 2, width, height)
  pdf.save(`${filename}.pdf`)
}

/**
 * Печать страницы. Правило @media print в components.css прячет меню,
 * шапку и кнопки, поэтому в PDF попадает только содержимое.
 */
export function printPage(): void {
  window.print()
}

/** Подпись файла: отчёт-простои-2026-03-31. */
export function stamp(prefix: string, date: Date = new Date()): string {
  const iso = date.toISOString().slice(0, 10)
  return `${prefix}-${iso}`
}
