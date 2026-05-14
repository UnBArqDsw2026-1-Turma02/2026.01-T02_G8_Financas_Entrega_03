import { useMemo, useState } from 'react'
import { Badge } from '../../../components/atoms/Badge'
import { ChevronsRightIcon } from '../../../components/atoms/Icon'
import { CategoriaTag } from '../../../components/molecules/CategoriaTag'
import { ConfirmDialog } from '../../../components/organisms/ConfirmDialog'
import { DataTable } from '../../../components/organisms/DataTable'
import { Modal } from '../../../components/organisms/Modal'
import { ParcelamentoForm } from '../../../components/organisms/ParcelamentoForm'
import { SimularGastoFlow } from '../../../components/organisms/SimularGastoFlow'
import { CrudPageTemplate } from '../../../components/templates/CrudPageTemplate'
import { useCategorias } from '../hooks/useCategorias'
import { useParcelamentos } from '../hooks/useParcelamentos'
import { type Categoria, type Parcelamento } from '../types/finance'

function formatCurrency(value: string | number): string {
  const n = typeof value === 'number' ? value : Number(value)
  if (Number.isNaN(n)) return String(value)
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatDate(value: string): string {
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleDateString('pt-BR')
}

function aPagar(p: Parcelamento): number {
  if (p.parcela_atual > p.num_parcelas) return 0
  const parcela = Number(p.valor_parcela)
  if (Number.isNaN(parcela)) return 0
  return parcela * (1 + (p.antecipadas_no_ciclo ?? 0))
}

export default function ParcelamentosPage() {
  const { items, isLoading, error, create, update, remove, antecipar } =
    useParcelamentos()
  const { items: categorias, isLoading: loadingCats } = useCategorias()
  const categoriasById = useMemo(() => {
    const map = new Map<string, Categoria>()
    categorias.forEach((c) => map.set(c.id, c))
    return map
  }, [categorias])

  const [editing, setEditing] = useState<Parcelamento | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [toDelete, setToDelete] = useState<Parcelamento | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [toAntecipar, setToAntecipar] = useState<Parcelamento | null>(null)
  const [antecipando, setAntecipando] = useState(false)
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

  async function handleAntecipar() {
    if (!toAntecipar) return
    setAntecipando(true)
    try {
      await antecipar(toAntecipar.id)
      setToAntecipar(null)
    } finally {
      setAntecipando(false)
    }
  }

  return (
    <>
      <CrudPageTemplate
        title="Parcelamentos"
        isLoading={isLoading || loadingCats}
        error={error}
        onCreate={() => setShowCreate(true)}
        createLabel="Novo Parcelamento"
      >
        <DataTable
          items={sorted}
          getKey={(p) => p.id}
          onEdit={(p) => setEditing(p)}
          onDelete={(p) => setToDelete(p)}
          renderExtraActions={(p) => {
            const quitado = p.parcela_atual >= p.num_parcelas
            return (
              <button
                type="button"
                className="data-table__icon-btn data-table__icon-btn--accent"
                aria-label="Antecipar parcela"
                title={
                  quitado
                    ? 'Parcelamento já quitado'
                    : 'Antecipar próxima parcela'
                }
                disabled={quitado}
                onClick={() => setToAntecipar(p)}
              >
                <ChevronsRightIcon />
              </button>
            )
          }}
          emptyMessage="Nenhum parcelamento cadastrado ainda."
          columns={[
            { key: 'nome', header: 'Nome', render: (p) => p.nome },
            {
              key: 'valor',
              header: 'Valor Total',
              render: (p) => (
                <span className="data-table__money data-table__money--info">
                  {formatCurrency(p.valor)}
                </span>
              ),
            },
            {
              key: 'valor_parcela',
              header: 'Valor Parcela',
              render: (p) => formatCurrency(p.valor_parcela),
            },
            {
              key: 'a_pagar',
              header: 'À Pagar',
              render: (p) => formatCurrency(aPagar(p)),
            },
            {
              key: 'parcelas',
              header: 'Parcelas',
              render: (p) => (
                <Badge tone="purple" variant="outline">
                  {String(p.parcela_atual).padStart(2, '0')}/
                  {String(p.num_parcelas).padStart(2, '0')}
                </Badge>
              ),
            },
            {
              key: 'data',
              header: 'Data',
              render: (p) => formatDate(p.data),
            },
            {
              key: 'categoria',
              header: 'Categoria',
              render: (p) => {
                const cat = categoriasById.get(p.categoria)
                return cat ? (
                  <CategoriaTag categoria={cat} />
                ) : (
                  <span style={{ color: '#a1a1aa' }}>—</span>
                )
              },
            },
          ]}
        />
      </CrudPageTemplate>

      <Modal
        open={showCreate}
        title="Novo parcelamento"
        onClose={() => setShowCreate(false)}
      >
        <ParcelamentoForm
          categorias={categorias}
          onSubmit={async (p) => {
            await create(p)
            setShowCreate(false)
          }}
          onCancel={() => setShowCreate(false)}
          onRequestSimular={openSimular}
        />
      </Modal>

      <Modal
        open={!!editing}
        title="Editar parcelamento"
        onClose={() => setEditing(null)}
      >
        {editing && (
          <ParcelamentoForm
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
        title="Excluir parcelamento"
        message={toDelete ? `Excluir o parcelamento "${toDelete.nome}"?` : ''}
        confirmLabel="Excluir"
        busy={deleting}
        onConfirm={handleDelete}
        onCancel={() => setToDelete(null)}
      />

      <ConfirmDialog
        open={!!toAntecipar}
        title="Antecipar parcela"
        message={
          toAntecipar
            ? `Confirmar pagamento da parcela ${toAntecipar.parcela_atual}/${toAntecipar.num_parcelas} de "${toAntecipar.nome}"?`
            : ''
        }
        confirmLabel="Antecipar"
        busy={antecipando}
        onConfirm={handleAntecipar}
        onCancel={() => setToAntecipar(null)}
      />
    </>
  )
}
