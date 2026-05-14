import { useCallback, useEffect, useState } from 'react'
import {
  createCategoria,
  deleteCategoria,
  listCategorias,
  updateCategoria,
} from '../api/categorias'
import type { Categoria, CategoriaPayload } from '../types/finance'

export function useCategorias() {
  const [items, setItems] = useState<Categoria[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    try {
      const data = await listCategorias()
      setItems(data)
      setError(null)
    } catch {
      setError('Não foi possível carregar as categorias.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    listCategorias()
      .then((data) => {
        if (!cancelled) {
          setItems(data)
          setError(null)
        }
      })
      .catch(() => {
        if (!cancelled) setError('Não foi possível carregar as categorias.')
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const create = useCallback(
    async (payload: CategoriaPayload) => {
      await createCategoria(payload)
      await reload()
    },
    [reload],
  )

  const update = useCallback(
    async (id: string, payload: CategoriaPayload) => {
      await updateCategoria(id, payload)
      await reload()
    },
    [reload],
  )

  const remove = useCallback(
    async (id: string) => {
      await deleteCategoria(id)
      await reload()
    },
    [reload],
  )

  return { items, isLoading, error, reload, create, update, remove }
}
