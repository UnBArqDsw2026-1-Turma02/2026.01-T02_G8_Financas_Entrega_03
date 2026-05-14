import { api } from '../../../lib/api'
import type { Categoria, CategoriaPayload } from '../types/finance'

const BASE = '/v1/finance/categorias/'

export async function listCategorias(): Promise<Categoria[]> {
  const { data } = await api.get<Categoria[]>(BASE)
  return data
}

export async function createCategoria(payload: CategoriaPayload): Promise<Categoria> {
  const { data } = await api.post<Categoria>(BASE, payload)
  return data
}

export async function updateCategoria(
  id: string,
  payload: CategoriaPayload,
): Promise<Categoria> {
  const { data } = await api.put<Categoria>(`${BASE}${id}/`, payload)
  return data
}

export async function deleteCategoria(id: string): Promise<void> {
  await api.delete(`${BASE}${id}/`)
}
