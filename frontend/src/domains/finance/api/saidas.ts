import { api } from '../../../lib/api'
import type { Saida, SaidaPayload } from '../types/finance'

const BASE = '/v1/finance/saidas/'

export async function listSaidas(): Promise<Saida[]> {
  const { data } = await api.get<Saida[]>(BASE)
  return data
}

export async function createSaida(payload: SaidaPayload): Promise<Saida> {
  const { data } = await api.post<Saida>(BASE, payload)
  return data
}

export async function updateSaida(
  id: string,
  payload: SaidaPayload,
): Promise<Saida> {
  const { data } = await api.put<Saida>(`${BASE}${id}/`, payload)
  return data
}

export async function deleteSaida(id: string): Promise<void> {
  await api.delete(`${BASE}${id}/`)
}
