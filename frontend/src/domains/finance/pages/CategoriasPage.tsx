import { useMemo, useState } from 'react'
import { ConfirmDialog } from '../../../components/organisms/ConfirmDialog'
import { DataTable } from '../../../components/organisms/DataTable'
import { Modal } from '../../../components/organisms/Modal'
import { CategoriaForm } from '../../../components/organisms/CategoriaForm'
import { CrudPageTemplate } from '../../../components/templates/CrudPageTemplate'
import { useCategorias } from '../hooks/useCategorias'
import type { Categoria } from '../types/finance'

export default function CategoriasPage() {
  const { items, isLoading, error, create, update, remove } = useCategorias()
  const [editing, setEditing] = useState<Categoria | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [toDelete, setToDelete] = useState<Categoria | null>(null)
  const [deleting, setDeleting] = useState(false)

  const sorted = useMemo(
    () => [...items].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR')),
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
        title="Categorias"
        isLoading={isLoading}
        error={error}
        onCreate={() => setShowCreate(true)}
        createLabel="Nova tag"
      >
        <DataTable
          items={sorted}
          getKey={(c) => c.id}
          onEdit={(c) => setEditing(c)}
          onDelete={(c) => setToDelete(c)}
          emptyMessage="Você ainda não cadastrou categorias."
          columns={[
            {
              key: 'nome',
              header: 'Nome',
              render: (c) => c.nome,
            },
            {
              key: 'descricao',
              header: 'Descrição',
              render: (c) => (
                <span
                  style={{
                    display: 'inline-block',
                    maxWidth: 360,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    verticalAlign: 'middle',
                  }}
                  title={c.descricao}
                >
                  {c.descricao}
                </span>
              ),
            },
            {
              key: 'cor',
              header: 'Cor',
              render: (c) => (
                <span className="data-table__hex">
                  <span
                    className="molecule-categoria-tag__dot"
                    style={{ background: c.cor || '#71717a' }}
                  />
                  {c.cor.toUpperCase()}
                </span>
              ),
            },
          ]}
        />
      </CrudPageTemplate>

      <Modal
        open={showCreate}
        title="Nova categoria"
        onClose={() => setShowCreate(false)}
      >
        <CategoriaForm
          onSubmit={async (p) => {
            await create(p)
            setShowCreate(false)
          }}
          onCancel={() => setShowCreate(false)}
        />
      </Modal>

      <Modal
        open={!!editing}
        title="Editar categoria"
        onClose={() => setEditing(null)}
      >
        {editing && (
          <CategoriaForm
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
        title="Excluir categoria"
        message={
          toDelete
            ? `Tem certeza que deseja excluir "${toDelete.nome}"? Esta ação não pode ser desfeita.`
            : ''
        }
        confirmLabel="Excluir"
        busy={deleting}
        onConfirm={handleDelete}
        onCancel={() => setToDelete(null)}
      />
    </>
  )
}
