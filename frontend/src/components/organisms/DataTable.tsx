import type { ReactNode } from 'react'
import { PencilIcon, TrashIcon } from '../atoms/Icon'
import './data-table.css'

export interface Column<T> {
  key: string
  header: string
  render: (item: T) => ReactNode
  align?: 'left' | 'right' | 'center'
  width?: string
}

export interface DataTableProps<T> {
  items: T[]
  columns: Column<T>[]
  onEdit?: (item: T) => void
  onDelete?: (item: T) => void
  renderExtraActions?: (item: T) => ReactNode
  emptyMessage?: string
  getKey: (item: T) => string
}

export function DataTable<T>({
  items,
  columns,
  onEdit,
  onDelete,
  renderExtraActions,
  emptyMessage = 'Nenhum item cadastrado.',
  getKey,
}: DataTableProps<T>) {
  if (items.length === 0) {
    return <div className="data-table__empty">{emptyMessage}</div>
  }
  const hasActions = !!onEdit || !!onDelete || !!renderExtraActions
  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                style={{ width: c.width, textAlign: c.align ?? 'left' }}
              >
                {c.header}
              </th>
            ))}
            {hasActions && <th className="data-table__actions-h">Ações</th>}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={getKey(item)}>
              {columns.map((c) => (
                <td key={c.key} style={{ textAlign: c.align ?? 'left' }}>
                  {c.render(item)}
                </td>
              ))}
              {hasActions && (
                <td className="data-table__actions">
                  {renderExtraActions?.(item)}
                  {onEdit && (
                    <button
                      type="button"
                      className="data-table__icon-btn"
                      aria-label="Editar"
                      onClick={() => onEdit(item)}
                    >
                      <PencilIcon />
                    </button>
                  )}
                  {onDelete && (
                    <button
                      type="button"
                      className="data-table__icon-btn data-table__icon-btn--danger"
                      aria-label="Excluir"
                      onClick={() => onDelete(item)}
                    >
                      <TrashIcon />
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
