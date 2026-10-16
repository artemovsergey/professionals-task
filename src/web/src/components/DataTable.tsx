/* ===========================================================================
   ТОиР-Проф — таблица со сортировкой, выбором строки и постраничностью.

   Общая таблица для всех реестров. Сортировка и постраничность живут в
   состоянии страницы, а таблица только сообщает о намерении через колбэки:
   так один и тот же компонент работает и на серверной пагинации
   (реестры), и на клиентской (аналитика).
   =========================================================================== */

import type { ReactNode } from 'react'
import { EmptyState } from './Ui'

export interface Column<T> {
  key: string
  title: string
  render: (row: T) => ReactNode
  /** Числовая колонка выравнивается вправо и сортируется иначе, чем текст. */
  numeric?: boolean
  sortable?: boolean
}

export interface PagerState {
  page: number
  pageSize: number
  total: number
}

interface DataTableProps<T> {
  columns: Column<T>[]
  rows: T[]
  rowKey: (row: T) => string
  loading?: boolean
  empty?: string
  /** Подсветка выбранной строки и обработчик клика. */
  selectedId?: string | null
  onSelect?: (row: T) => void
  sortField?: string
  sortOrder?: 'asc' | 'desc'
  onSort?: (field: string) => void
  pager?: PagerState
  onPage?: (page: number) => void
  onPageSize?: (size: number) => void
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  loading = false,
  empty = 'Ничего не найдено',
  selectedId,
  onSelect,
  sortField,
  sortOrder = 'desc',
  onSort,
  pager,
  onPage,
  onPageSize,
}: DataTableProps<T>) {
  if (loading) {
    return (
      <div className="state">
        <div className="spinner" />
        <span>Загрузка…</span>
      </div>
    )
  }

  if (rows.length === 0) return <EmptyState caption={empty} />

  const totalPages = pager ? Math.max(1, Math.ceil(pager.total / Math.max(1, pager.pageSize))) : 1

  return (
    <>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column.key} className={column.numeric ? 'table__num' : undefined}>
                  {column.sortable && onSort ? (
                    <button type="button" onClick={() => onSort(column.key)}>
                      {column.title}
                      {sortField === column.key ? <span className="table__sort">{sortOrder === 'asc' ? '▲' : '▼'}</span> : null}
                    </button>
                  ) : (
                    column.title
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const id = rowKey(row)
              const isSelected = selectedId != null && selectedId === id
              return (
                <tr
                  key={id}
                  className={isSelected ? 'table__row table__row--selected' : 'table__row'}
                  onClick={onSelect ? () => onSelect(row) : undefined}
                  style={onSelect ? { cursor: 'pointer' } : undefined}
                >
                  {columns.map((column) => (
                    <td key={column.key} className={column.numeric ? 'table__num mono' : undefined}>
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {pager && onPage ? (
        <div className="pager">
          <button type="button" className="btn btn--sm" onClick={() => onPage(1)} disabled={pager.page <= 1}>
            В начало
          </button>
          <button
            type="button"
            className="btn btn--sm"
            onClick={() => onPage(pager.page - 1)}
            disabled={pager.page <= 1}
          >
            Назад
          </button>
          <span className="mono">
            стр. {pager.page} из {totalPages} · всего {pager.total}
          </span>
          <button
            type="button"
            className="btn btn--sm"
            onClick={() => onPage(pager.page + 1)}
            disabled={pager.page >= totalPages}
          >
            Вперёд
          </button>

          {onPageSize ? (
            <>
              <span className="pager__spacer" />
              <label className="check">
                на странице
                <select
                  className="select"
                  style={{ width: 76 }}
                  value={pager.pageSize}
                  onChange={(event) => onPageSize(Number(event.target.value))}
                >
                  {[10, 20, 50, 100].map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </select>
              </label>
            </>
          ) : null}
        </div>
      ) : null}
    </>
  )
}
