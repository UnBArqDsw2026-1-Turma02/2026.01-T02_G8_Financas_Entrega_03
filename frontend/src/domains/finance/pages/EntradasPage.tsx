import { useMemo, useState } from 'react'
import { Badge } from '../../../components/atoms/Badge'
import { ConfirmDialog } from '../../../components/organisms/ConfirmDialog'
import { DataTable } from '../../../components/organisms/DataTable'
import { EntradaForm } from '../../../components/organisms/EntradaForm'
import { Modal } from '../../../components/organisms/Modal'
import { CrudPageTemplate } from '../../../components/templates/CrudPageTemplate'
import { useEntradas } from '../hooks/useEntradas'
import type { Entrada } from '../types/finance'

function formatCurrency(value: string): string {
  const n = Number(value)
  if (Number.isNaN(n)) return value
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatDate(value: string): string {
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleDateString('pt-BR')
}

export default function EntradasPage() {
  const { items, isLoading, error, create, update, remove } = useEntradas()
  const [editing, setEditing] = useState<Entrada | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [toDelete, setToDelete] = useState<Entrada | null>(null)
  const [deleting, setDeleting] = useState(false)

  const sorted = useMemo(
    () =>
      [...items].sort(
        (a, b) => new Date(b.data).getTime() - new Date(a.data).getTime(),
      ),
    [items],
  )

  async function handleDelete() {
    if (!toDelete) return
    setDeleting(true)
    try {
      await remove(toDelete.id)
      setToDelete(null)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <>
      <CrudPageTemplate
        title="Entradas"
        isLoading={isLoading}
        error={error}
        onCreate={() => setShowCreate(true)}
        createLabel="Nova Entrada"
      >
        <DataTable
          items={sorted}
          getKey={(e) => e.id}
          onEdit={(e) => setEditing(e)}
          onDelete={(e) => setToDelete(e)}
          emptyMessage="Nenhuma entrada cadastrada ainda."
          columns={[
            { key: 'nome', header: 'Nome', render: (e) => e.nome },
            {
              key: 'valor',
              header: 'Valor',
              render: (e) => (
                <span className="data-table__money data-table__money--in">
                  + {formatCurrency(e.valor)}
                </span>
              ),
            },
            {
              key: 'data',
              header: 'Data',
              render: (e) => formatDate(e.data),
            },
            {
              key: 'recorrencia',
              header: 'Recorrência',
              render: (e) => (
                <Badge tone="purple" variant="outline">
                  {e.recorrencia ? 'Recorrente' : 'Não Recorrente'}
                </Badge>
              ),
            },
          ]}
        />
      </CrudPageTemplate>

      <Modal open={showCreate} title="Nova entrada" onClose={() => setShowCreate(false)}>
        <EntradaForm
          onSubmit={async (p) => {
            await create(p)
            setShowCreate(false)
          }}
          onCancel={() => setShowCreate(false)}
        />
      </Modal>

      <Modal open={!!editing} title="Editar entrada" onClose={() => setEditing(null)}>
        {editing && (
          <EntradaForm
            initial={editing}
            onSubmit={async (p) => {
              await update(editing.id, p)
              setEditing(null)
            }}
            onCancel={() => setEditing(null)}
          />
        )}
      </Modal>

      <ConfirmDialog
        open={!!toDelete}
        title="Excluir entrada"
        message={toDelete ? `Excluir a entrada "${toDelete.nome}"?` : ''}
        confirmLabel="Excluir"
        busy={deleting}
        onConfirm={handleDelete}
        onCancel={() => setToDelete(null)}
      />
    </>
  )
}
