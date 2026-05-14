import { useCallback, useEffect, useState } from 'react'
import {
  createEntrada,
  deleteEntrada,
  listEntradas,
  updateEntrada,
} from '../api/entradas'
import type { Entrada, EntradaPayload } from '../types/finance'

export function useEntradas() {
  const [items, setItems] = useState<Entrada[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    try {
      const data = await listEntradas()
      setItems(data)
      setError(null)
    } catch {
      setError('Não foi possível carregar as entradas.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    listEntradas()
      .then((data) => {
        if (!cancelled) {
          setItems(data)
          setError(null)
        }
      })
      .catch(() => {
        if (!cancelled) setError('Não foi possível carregar as entradas.')
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const create = useCallback(
    async (payload: EntradaPayload) => {
      await createEntrada(payload)
      await reload()
    },
    [reload],
  )

  const update = useCallback(
    async (id: string, payload: EntradaPayload) => {
      await updateEntrada(id, payload)
      await reload()
    },
    [reload],
  )

  const remove = useCallback(
    async (id: string) => {
      await deleteEntrada(id)
      await reload()
    },
    [reload],
  )

  return { items, isLoading, error, reload, create, update, remove }
}
