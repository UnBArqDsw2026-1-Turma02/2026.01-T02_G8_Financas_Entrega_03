import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Badge } from '../../../components/atoms/Badge'
import { Select } from '../../../components/atoms/Select'
import {
  CartIcon,
  FilterIcon,
  LockIcon,
  PiggyBankIcon,
  ReceiptIcon,
  SearchIcon,
} from '../../../components/atoms/Icon'
import { CategoriaTag } from '../../../components/molecules/CategoriaTag'
import { DataTable } from '../../../components/organisms/DataTable'
import { useCategorias } from '../hooks/useCategorias'
import { useExtrato } from '../hooks/useExtrato'
import {
  PAGAMENTO_OPTIONS,
  TIPO_GASTO_OPTIONS,
  type Categoria,
  type ExtratoFiltros,
  type Pagamento,
  type TipoGasto,
  type TransacaoExtrato,
  type TransacaoTipo,
} from '../types/finance'
import './extrato-page.css'

const TIPO_OPTIONS: { value: TransacaoTipo; label: string }[] = [
  { value: 'entrada', label: 'Entrada' },
  { value: 'saida', label: 'Saída' },
  { value: 'parcelamento', label: 'Parcelamento' },
]

const MES_OPTIONS = [
  { value: '1', label: 'Janeiro' },
  { value: '2', label: 'Fevereiro' },
  { value: '3', label: 'Março' },
  { value: '4', label: 'Abril' },
  { value: '5', label: 'Maio' },
  { value: '6', label: 'Junho' },
  { value: '7', label: 'Julho' },
  { value: '8', label: 'Agosto' },
  { value: '9', label: 'Setembro' },
  { value: '10', label: 'Outubro' },
  { value: '11', label: 'Novembro' },
  { value: '12', label: 'Dezembro' },
]

function anoOptions(): { value: string; label: string }[] {
  const ano = new Date().getFullYear()
  return Array.from({ length: 6 }, (_, i) => {
    const v = String(ano - i)
    return { value: v, label: v }
  })
}

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

function labelPagamento(value: string): string {
  return PAGAMENTO_OPTIONS.find((o) => o.value === value)?.label ?? value
}

function useDebouncedValue<T>(value: T, delay = 350): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delay)
    return () => window.clearTimeout(id)
  }, [value, delay])
  return debounced
}

interface SummaryCardProps {
  icon: ReactNode
  label: string
  value: string
}

function SummaryCard({ icon, label, value }: SummaryCardProps) {
  return (
    <div className="extrato-summary-card">
      <div className="extrato-summary-card__head">
        <span className="extrato-summary-card__icon">{icon}</span>
        <span className="extrato-summary-card__label">{label}</span>
      </div>
      <span className="extrato-summary-card__value">{value}</span>
    </div>
  )
}

function tipoBadge(tipo: TransacaoTipo) {
  const labels: Record<TransacaoTipo, string> = {
    entrada: 'Entrada',
    saida: 'Saída',
    parcelamento: 'Parcelamento',
  }
  return (
    <span className={`extrato-tipo-badge extrato-tipo-badge--${tipo}`}>
      {labels[tipo]}
    </span>
  )
}

function categoriaIdOf(t: TransacaoExtrato): string | null {
  if (t.tipo === 'entrada') return null
  return t.detalhes.categoria.id
}

function pagamentoOf(t: TransacaoExtrato): Pagamento | null {
  if (t.tipo === 'entrada') return null
  return t.detalhes.pagamento
}

function tipoGastoOf(t: TransacaoExtrato): TipoGasto | 'PARCELAMENTO' | null {
  if (t.tipo === 'saida') return t.detalhes.tipo_gasto
  if (t.tipo === 'parcelamento') return 'PARCELAMENTO'
  return null
}

export default function ExtratoPage() {
  const [nome, setNome] = useState('')
  const nomeDebounced = useDebouncedValue(nome, 350)

  const [tipo, setTipo] = useState<'' | TransacaoTipo>('')
  const [ano, setAno] = useState<string>('')
  const [mes, setMes] = useState<string>('')
  const [categoria, setCategoria] = useState<string>('')
  const [pagamento, setPagamento] = useState<'' | Pagamento>('')
  const [tipoGasto, setTipoGasto] = useState<'' | TipoGasto>('')
  const [showFiltros, setShowFiltros] = useState(false)

  const { items: categorias } = useCategorias()
  const categoriasById = useMemo(() => {
    const m = new Map<string, Categoria>()
    categorias.forEach((c) => m.set(c.id, c))
    return m
  }, [categorias])

  const filtros = useMemo<ExtratoFiltros>(() => {
    const f: ExtratoFiltros = {}
    if (tipo) f.tipo = tipo
    if (ano && mes) {
      f.ano = Number(ano)
      f.mes = Number(mes)
    }
    if (categoria) f.categoria = categoria
    if (pagamento) f.pagamento = pagamento
    if (tipoGasto) f.tipo_gasto = tipoGasto
    if (nomeDebounced.trim()) f.nome = nomeDebounced.trim()
    return f
  }, [tipo, ano, mes, categoria, pagamento, tipoGasto, nomeDebounced])

  const { data, isLoading, error } = useExtrato(filtros)

  const totais = useMemo(() => {
    const t = { entradas: 0, despesasFixas: 0, despesasVariaveis: 0 }
    data?.transacoes.forEach((tr) => {
      const v = Number(tr.valor)
      if (Number.isNaN(v)) return
      if (tr.tipo === 'entrada') t.entradas += v
      else if (tr.tipo === 'saida') {
        if (tr.detalhes.tipo_gasto === 'FIXO') t.despesasFixas += v
        else t.despesasVariaveis += v
      } else if (tr.tipo === 'parcelamento') {
        t.despesasFixas += Number(tr.detalhes.valor_parcela) || 0
      }
    })
    return t
  }, [data])

  const filtersActive =
    !!tipo || !!ano || !!mes || !!categoria || !!pagamento || !!tipoGasto

  function clearFiltros() {
    setTipo('')
    setAno('')
    setMes('')
    setCategoria('')
    setPagamento('')
    setTipoGasto('')
  }

  return (
    <section className="extrato-page">
      <h1 className="extrato-page__title">Extrato</h1>

      <div className="extrato-page__searchbar">
        <label className="extrato-page__search">
          <SearchIcon />
          <input
            type="search"
            placeholder="Pesquisar por nome…"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
          />
        </label>
        <button
          type="button"
          className={`extrato-page__filter-btn${
            filtersActive || showFiltros ? ' extrato-page__filter-btn--active' : ''
          }`}
          aria-label="Filtros"
          aria-expanded={showFiltros}
          onClick={() => setShowFiltros((v) => !v)}
        >
          <FilterIcon />
        </button>
      </div>

      {showFiltros && (
        <div className="extrato-page__filters-panel">
          <div className="extrato-page__filters-field">
            <label htmlFor="filtro-tipo">Tipo</label>
            <Select
              id="filtro-tipo"
              value={tipo}
              onChange={(e) => setTipo(e.target.value as TransacaoTipo | '')}
              options={[{ value: '', label: 'Todos' }, ...TIPO_OPTIONS]}
            />
          </div>
          <div className="extrato-page__filters-field">
            <label htmlFor="filtro-ano">Ano</label>
            <Select
              id="filtro-ano"
              value={ano}
              onChange={(e) => setAno(e.target.value)}
              options={[{ value: '', label: 'Todos' }, ...anoOptions()]}
            />
          </div>
          <div className="extrato-page__filters-field">
            <label htmlFor="filtro-mes">Mês</label>
            <Select
              id="filtro-mes"
              value={mes}
              onChange={(e) => setMes(e.target.value)}
              options={[{ value: '', label: 'Todos' }, ...MES_OPTIONS]}
            />
          </div>
          <div className="extrato-page__filters-field">
            <label htmlFor="filtro-categoria">Categoria</label>
            <Select
              id="filtro-categoria"
              value={categoria}
              onChange={(e) => setCategoria(e.target.value)}
              options={[
                { value: '', label: 'Todas' },
                ...categorias.map((c) => ({ value: c.id, label: c.nome })),
              ]}
            />
          </div>
          <div className="extrato-page__filters-field">
            <label htmlFor="filtro-pagamento">Pagamento</label>
            <Select
              id="filtro-pagamento"
              value={pagamento}
              onChange={(e) => setPagamento(e.target.value as Pagamento | '')}
              options={[{ value: '', label: 'Todos' }, ...PAGAMENTO_OPTIONS]}
            />
          </div>
          <div className="extrato-page__filters-field">
            <label htmlFor="filtro-tipo-gasto">Tipo de gasto</label>
            <Select
              id="filtro-tipo-gasto"
              value={tipoGasto}
              onChange={(e) => setTipoGasto(e.target.value as TipoGasto | '')}
              options={[{ value: '', label: 'Todos' }, ...TIPO_GASTO_OPTIONS]}
            />
          </div>
          <div className="extrato-page__filters-actions">
            <button
              type="button"
              className="extrato-page__filters-clear"
              onClick={clearFiltros}
              disabled={!filtersActive}
            >
              Limpar filtros
            </button>
          </div>
        </div>
      )}

      <div className="extrato-page__cards">
        <SummaryCard
          icon={<ReceiptIcon size={16} />}
          label="Entradas"
          value={formatCurrency(totais.entradas)}
        />
        <SummaryCard
          icon={<LockIcon size={16} />}
          label="Despesas Fixas"
          value={formatCurrency(totais.despesasFixas)}
        />
        <SummaryCard
          icon={<CartIcon size={16} />}
          label="Despesas Variáveis"
          value={formatCurrency(totais.despesasVariaveis)}
        />
        <SummaryCard
          icon={<PiggyBankIcon size={16} />}
          label="Saldo Atual"
          value={formatCurrency(
            totais.entradas - totais.despesasFixas - totais.despesasVariaveis,
          )}
        />
      </div>

      {error && <div className="extrato-page__error">{error}</div>}

      <div className="extrato-page__table-card">
        {isLoading ? (
          <div className="data-table__empty">Carregando…</div>
        ) : (
          <DataTable
            items={data?.transacoes ?? []}
            getKey={(t) => t.id}
            emptyMessage="Nenhuma transação encontrada para os filtros aplicados."
            columns={[
              {
                key: 'tipo',
                header: 'Tipo',
                render: (t) => tipoBadge(t.tipo),
              },
              { key: 'nome', header: 'Nome', render: (t) => t.nome },
              {
                key: 'valor',
                header: 'Valor',
                render: (t) => {
                  if (t.tipo === 'entrada')
                    return (
                      <span className="data-table__money data-table__money--in">
                        + {formatCurrency(t.valor)}
                      </span>
                    )
                  if (t.tipo === 'parcelamento')
                    return (
                      <span className="data-table__money data-table__money--info">
                        - {formatCurrency(t.detalhes.valor_parcela)}
                      </span>
                    )
                  return (
                    <span className="data-table__money data-table__money--out">
                      - {formatCurrency(t.valor)}
                    </span>
                  )
                },
              },
              {
                key: 'data',
                header: 'Data',
                render: (t) => formatDate(t.data),
              },
              {
                key: 'categoria',
                header: 'Categoria',
                render: (t) => {
                  const id = categoriaIdOf(t)
                  if (!id) return <span className="extrato-empty-cell">----</span>
                  const cat = categoriasById.get(id)
                  return cat ? (
                    <CategoriaTag categoria={cat} />
                  ) : (
                    <span className="extrato-empty-cell">----</span>
                  )
                },
              },
              {
                key: 'status',
                header: 'Status',
                render: (t) => {
                  const g = tipoGastoOf(t)
                  if (g === 'FIXO')
                    return (
                      <Badge tone="info" variant="outline">
                        Fixo
                      </Badge>
                    )
                  if (g === 'VARIAVEL')
                    return (
                      <Badge tone="warning" variant="outline">
                        Variável
                      </Badge>
                    )
                  if (g === 'PARCELAMENTO')
                    return (
                      <Badge tone="info" variant="outline">
                        Fixo
                      </Badge>
                    )
                  return <span className="extrato-empty-cell">----</span>
                },
              },
              {
                key: 'pagamento',
                header: 'Pagamento',
                render: (t) => {
                  const p = pagamentoOf(t)
                  return p ? (
                    labelPagamento(p)
                  ) : (
                    <span className="extrato-empty-cell">----</span>
                  )
                },
              },
            ]}
          />
        )}
      </div>
    </section>
  )
}
