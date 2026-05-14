import { useCallback, useEffect, useState } from 'react'
import {
  anteciparParcelamento,
  createParcelamento,
  deleteParcelamento,
  listParcelamentos,
  updateParcelamento,
} from '../api/parcelamentos'
import type { Parcelamento, ParcelamentoPayload } from '../types/finance'

export function useParcelamentos() {
  const [items, setItems] = useState<Parcelamento[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    try {
      const data = await listParcelamentos()
      setItems(data)
      setError(null)
    } catch {
      setError('Não foi possível carregar os parcelamentos.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    listParcelamentos()
      .then((data) => {
        if (!cancelled) {
          setItems(data)
          setError(null)
        }
      })
      .catch(() => {
        if (!cancelled) setError('Não foi possível carregar os parcelamentos.')
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const create = useCallback(
    async (payload: ParcelamentoPayload) => {
      await createParcelamento(payload)
      await reload()
    },
    [reload],
  )

  const update = useCallback(
    async (id: string, payload: ParcelamentoPayload) => {
      await updateParcelamento(id, payload)
      await reload()
    },
    [reload],
  )

  const remove = useCallback(
    async (id: string) => {
      await deleteParcelamento(id)
      await reload()
    },
    [reload],
  )

  const antecipar = useCallback(
    async (id: string) => {
      await anteciparParcelamento(id)
      await reload()
    },
    [reload],
  )

  return { items, isLoading, error, reload, create, update, remove, antecipar }
}
