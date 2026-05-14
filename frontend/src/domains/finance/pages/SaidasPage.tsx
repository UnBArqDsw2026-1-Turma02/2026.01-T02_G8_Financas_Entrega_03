import { useMemo, useState } from 'react'
import { Badge } from '../../../components/atoms/Badge'
import { CategoriaTag } from '../../../components/molecules/CategoriaTag'
import { ConfirmDialog } from '../../../components/organisms/ConfirmDialog'
import { DataTable } from '../../../components/organisms/DataTable'
import { Modal } from '../../../components/organisms/Modal'
import { SaidaForm } from '../../../components/organisms/SaidaForm'
import { SimularGastoFlow } from '../../../components/organisms/SimularGastoFlow'
import { CrudPageTemplate } from '../../../components/templates/CrudPageTemplate'
import { useCategorias } from '../hooks/useCategorias'
import { useSaidas } from '../hooks/useSaidas'
import { PAGAMENTO_OPTIONS, type Categoria, type Saida } from '../types/finance'

function labelPagamento(value: string): string {
  return PAGAMENTO_OPTIONS.find((o) => o.value === value)?.label ?? value
}

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

export default function SaidasPage() {
  const { items, isLoading, error, create, update, remove } = useSaidas()
  const { items: categorias, isLoading: loadingCats } = useCategorias()
  const categoriasById = useMemo(() => {
    const map = new Map<string, Categoria>()
    categorias.forEach((c) => map.set(c.id, c))
    return map
  }, [categorias])

  const [editing, setEditing] = useState<Saida | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [toDelete, setToDelete] = useState<Saida | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [simular, setSimular] = useState<{ valor: string; nome: string } | null>(
    null,
  )

  function openSimular(valor: string, nome: string) {
    setShowCreate(false)
    setEditing(null)
    setSimular({ valor, nome })
  }

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
        title="Saídas"
        isLoading={isLoading || loadingCats}
        error={error}
        onCreate={() => setShowCreate(true)}
        createLabel="Nova Saída"
      >
        <DataTable
          items={sorted}
          getKey={(s) => s.id}
          onEdit={(s) => setEditing(s)}
          onDelete={(s) => setToDelete(s)}
          emptyMessage="Nenhuma saída cadastrada ainda."
          columns={[
            { key: 'nome', header: 'Nome', render: (s) => s.nome },
            {
              key: 'valor',
              header: 'Valor',
              render: (s) => (
                <span className="data-table__money data-table__money--out">
                  - {formatCurrency(s.valor)}
                </span>
              ),
            },
            {
              key: 'data',
              header: 'Data',
              render: (s) => formatDate(s.data),
            },
            {
              key: 'categoria',
              header: 'Categoria',
              render: (s) => {
                const cat = categoriasById.get(s.categoria)
                return cat ? (
                  <CategoriaTag categoria={cat} />
                ) : (
                  <span style={{ color: '#a1a1aa' }}>—</span>
                )
              },
            },
            {
              key: 'status',
              header: 'Status',
              render: (s) => (
                <Badge
                  tone={s.tipo_gasto === 'FIXO' ? 'info' : 'warning'}
                  variant="outline"
                >
                  {s.tipo_gasto === 'FIXO' ? 'Fixo' : 'Variável'}
                </Badge>
              ),
            },
            {
              key: 'pagamento',
              header: 'Pagamento',
              render: (s) => (
                <Badge tone="purple" variant="outline">
                  {labelPagamento(s.pagamento)}
                </Badge>
              ),
            },
          ]}
        />
      </CrudPageTemplate>

      <Modal open={showCreate} title="Nova saída" onClose={() => setShowCreate(false)}>
        <SaidaForm
          categorias={categorias}
          onSubmit={async (p) => {
            await create(p)
            setShowCreate(false)
          }}
          onCancel={() => setShowCreate(false)}
          onRequestSimular={openSimular}
        />
      </Modal>

      <Modal open={!!editing} title="Editar saída" onClose={() => setEditing(null)}>
        {editing && (
          <SaidaForm
            initial={editing}
            categorias={categorias}
            onSubmit={async (p) => {
              await update(editing.id, p)
              setEditing(null)
            }}
            onCancel={() => setEditing(null)}
            onRequestSimular={openSimular}
          />
        )}
      </Modal>

      {simular && (
        <SimularGastoFlow
          open
          initialValor={simular.valor}
          initialNome={simular.nome}
          onClose={() => setSimular(null)}
        />
      )}

      <ConfirmDialog
        open={!!toDelete}
        title="Excluir saída"
        message={toDelete ? `Excluir a saída "${toDelete.nome}"?` : ''}
        confirmLabel="Excluir"
        busy={deleting}
        onConfirm={handleDelete}
        onCancel={() => setToDelete(null)}
      />
    </>
  )
}
