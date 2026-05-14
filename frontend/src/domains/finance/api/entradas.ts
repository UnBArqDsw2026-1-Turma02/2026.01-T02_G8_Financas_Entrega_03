import { api } from '../../../lib/api'
import type { Entrada, EntradaPayload } from '../types/finance'

const BASE = '/v1/finance/entradas/'

export async function listEntradas(): Promise<Entrada[]> {
  const { data } = await api.get<Entrada[]>(BASE)
  return data
}

export async function createEntrada(payload: EntradaPayload): Promise<Entrada> {
  const { data } = await api.post<Entrada>(BASE, payload)
  return data
}

export async function updateEntrada(
  id: string,
  payload: EntradaPayload,
): Promise<Entrada> {
  const { data } = await api.put<Entrada>(`${BASE}${id}/`, payload)
  return data
}

export async function deleteEntrada(id: string): Promise<void> {
  await api.delete(`${BASE}${id}/`)
}
