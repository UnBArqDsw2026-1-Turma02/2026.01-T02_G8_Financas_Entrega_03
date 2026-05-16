export type Pagamento = 'PIX' | 'CREDITO' | 'DEBITO' | 'DINHEIRO'
export type TipoGasto = 'FIXO' | 'VARIAVEL'

export const PAGAMENTO_OPTIONS: { value: Pagamento; label: string }[] = [
  { value: 'PIX', label: 'PIX' },
  { value: 'CREDITO', label: 'Crédito' },
  { value: 'DEBITO', label: 'Débito' },
  { value: 'DINHEIRO', label: 'Dinheiro' },
]

export const TIPO_GASTO_OPTIONS: { value: TipoGasto; label: string }[] = [
  { value: 'FIXO', label: 'Fixo' },
  { value: 'VARIAVEL', label: 'Variável' },
]

export interface Categoria {
  id: string
  nome: string
  descricao: string
  cor: string
}

export interface CategoriaPayload {
  nome: string
  descricao: string
  cor: string
}

export interface Entrada {
  id: string
  nome: string
  valor: string
  fonte: string
  recorrencia: boolean
  data: string
}

export interface EntradaPayload {
  nome: string
  valor: string
  fonte: string
  recorrencia: boolean
  data?: string
}

export interface Saida {
  id: string
  nome: string
  valor: string
  categoria: string
  pagamento: Pagamento
  tipo_gasto: TipoGasto
  data: string
}

export interface SaidaPayload {
  nome: string
  valor: string
  categoria: string
  pagamento: Pagamento
  tipo_gasto: TipoGasto
  data?: string
}

export interface Parcelamento {
  id: string
  nome: string
  valor: string
  categoria: string
  pagamento: Pagamento
  num_parcelas: number
  parcela_atual: number
  valor_parcela: string
  antecipadas_no_ciclo: number
  data: string
}

export interface ParcelamentoPayload {
  nome: string
  valor: string
  categoria: string
  pagamento: Pagamento
  num_parcelas: number
  data?: string
}

export type TransacaoTipo = 'entrada' | 'saida' | 'parcelamento'

export interface TransacaoExtratoBase {
  id: string
  nome: string
  valor: string
  data: string
}

export interface TransacaoExtratoEntrada extends TransacaoExtratoBase {
  tipo: 'entrada'
  detalhes: {
    fonte: string
    recorrencia: boolean
  }
}

export interface TransacaoExtratoSaida extends TransacaoExtratoBase {
  tipo: 'saida'
  detalhes: {
    categoria: { id: string; nome: string }
    pagamento: Pagamento
    tipo_gasto: TipoGasto
  }
}

export interface TransacaoExtratoParcelamento extends TransacaoExtratoBase {
  tipo: 'parcelamento'
  detalhes: {
    categoria: { id: string; nome: string }
    pagamento: Pagamento
    num_parcelas: number
    parcela_atual: number
    valor_parcela: string
  }
}

export type TransacaoExtrato =
  | TransacaoExtratoEntrada
  | TransacaoExtratoSaida
  | TransacaoExtratoParcelamento

export interface ExtratoResponse {
  transacoes: TransacaoExtrato[]
  saldo_atual: string
  filtros_aplicados: Record<string, unknown>
}

export interface ExtratoFiltros {
  tipo?: TransacaoTipo
  ano?: number
  mes?: number
  categoria?: string
  pagamento?: Pagamento
  tipo_gasto?: TipoGasto
  nome?: string
}
