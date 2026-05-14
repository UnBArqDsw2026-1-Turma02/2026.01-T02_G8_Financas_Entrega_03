import { api } from '../../../lib/api'
import type { ExtratoFiltros, ExtratoResponse } from '../types/finance'

const BASE = '/v1/finance/extrato/'

export async function getExtrato(filtros: ExtratoFiltros = {}): Promise<ExtratoResponse> {
  const params: Record<string, string> = {}
  if (filtros.tipo) params.tipo = filtros.tipo
  if (filtros.ano !== undefined) params.ano = String(filtros.ano)
  if (filtros.mes !== undefined) params.mes = String(filtros.mes)
  if (filtros.categoria) params.categoria = filtros.categoria
  if (filtros.pagamento) params.pagamento = filtros.pagamento
  if (filtros.tipo_gasto) params.tipo_gasto = filtros.tipo_gasto
  if (filtros.nome && filtros.nome.trim() !== '') params.nome = filtros.nome.trim()

  const { data } = await api.get<ExtratoResponse>(BASE, { params })
  return data
}
