import { api } from '../../../lib/api'

export interface DashboardVisaoGeral {
  total_entradas: string
  total_saidas_fixas: string
  total_saidas_variaveis: string
  saldo_disponivel: string
}

export interface DashboardCategoria {
  id: string
  nome: string
  cor: string
  total: string
  percentual: string
}

export interface DashboardCategoriasResponse {
  categorias: DashboardCategoria[]
}

export interface DashboardDia {
  data: string
  total_gasto: string
}

export interface DashboardTendenciaResponse {
  dias: DashboardDia[]
}

export interface DashboardFiltros {
  ano?: number
  mes?: number
}

const BASE = '/v1/finance/dashboard/'

function buildParams(filtros: DashboardFiltros): Record<string, string> {
  const params: Record<string, string> = {}
  if (filtros.ano !== undefined && filtros.mes !== undefined) {
    params.ano = String(filtros.ano)
    params.mes = String(filtros.mes)
  }
  return params
}

export async function getDashboardVisaoGeral(
  filtros: DashboardFiltros = {},
): Promise<DashboardVisaoGeral> {
  const { data } = await api.get<DashboardVisaoGeral>(BASE, {
    params: buildParams(filtros),
  })
  return data
}

export async function getDashboardCategorias(
  filtros: DashboardFiltros = {},
): Promise<DashboardCategoriasResponse> {
  const { data } = await api.get<DashboardCategoriasResponse>(
    `${BASE}categorias/`,
    { params: buildParams(filtros) },
  )
  return data
}

export async function getDashboardTendencia(
  filtros: DashboardFiltros = {},
): Promise<DashboardTendenciaResponse> {
  const { data } = await api.get<DashboardTendenciaResponse>(
    `${BASE}tendencia/`,
    { params: buildParams(filtros) },
  )
  return data
}
