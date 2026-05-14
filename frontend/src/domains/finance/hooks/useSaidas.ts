import { useCallback, useEffect, useState } from 'react'
import {
  createSaida,
  deleteSaida,
  listSaidas,
  updateSaida,
} from '../api/saidas'
import type { Saida, SaidaPayload } from '../types/finance'

export function useSaidas() {
  const [items, setItems] = useState<Saida[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    try {
      const data = await listSaidas()
      setItems(data)
      setError(null)
    } catch {
      setError('Não foi possível carregar as saídas.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    listSaidas()
      .then((data) => {
        if (!cancelled) {
          setItems(data)
          setError(null)
        }
      })
      .catch(() => {
        if (!cancelled) setError('Não foi possível carregar as saídas.')
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const create = useCallback(
    async (payload: SaidaPayload) => {
      await createSaida(payload)
      await reload()
    },
    [reload],
  )

  const update = useCallback(
    async (id: string, payload: SaidaPayload) => {
      await updateSaida(id, payload)
      await reload()
    },
    [reload],
  )

  const remove = useCallback(
    async (id: string) => {
      await deleteSaida(id)
      await reload()
    },
    [reload],
  )

  return { items, isLoading, error, reload, create, update, remove }
}
