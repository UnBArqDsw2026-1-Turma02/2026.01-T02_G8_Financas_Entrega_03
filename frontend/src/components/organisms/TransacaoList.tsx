import type { ReactNode } from 'react'
import './organisms.css'

export interface TransacaoListProps<T> {
  items: T[]
  renderItem: (item: T) => ReactNode
  emptyMessage?: string
}

export function TransacaoList<T extends { id: string }>({
  items,
  renderItem,
  emptyMessage = 'Nenhum item cadastrado.',
}: TransacaoListProps<T>) {
  if (items.length === 0) {
    return <div className="organism-list__empty">{emptyMessage}</div>
  }
  return (
    <div className="organism-list">
      {items.map((item) => (
        <div key={item.id}>{renderItem(item)}</div>
      ))}
    </div>
  )
}
