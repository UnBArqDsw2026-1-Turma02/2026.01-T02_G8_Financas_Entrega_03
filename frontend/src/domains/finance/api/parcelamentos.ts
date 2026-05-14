import { api } from '../../../lib/api'
import type { Parcelamento, ParcelamentoPayload } from '../types/finance'

const BASE = '/v1/finance/parcelamentos/'

export async function listParcelamentos(): Promise<Parcelamento[]> {
  const { data } = await api.get<Parcelamento[]>(BASE)
  return data
}

export async function createParcelamento(
  payload: ParcelamentoPayload,
): Promise<Parcelamento> {
  const { data } = await api.post<Parcelamento>(BASE, payload)
  return data
}

export async function updateParcelamento(
  id: string,
  payload: ParcelamentoPayload,
): Promise<Parcelamento> {
  const { data } = await api.put<Parcelamento>(`${BASE}${id}/`, payload)
  return data
}

export async function deleteParcelamento(id: string): Promise<void> {
  await api.delete(`${BASE}${id}/`)
}

export async function anteciparParcelamento(id: string): Promise<Parcelamento> {
  const { data } = await api.post<Parcelamento>(`${BASE}${id}/antecipar/`)
  return data
}
