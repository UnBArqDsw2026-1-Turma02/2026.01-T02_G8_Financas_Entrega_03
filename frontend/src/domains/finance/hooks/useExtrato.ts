import { useEffect, useState } from 'react'
import { getExtrato } from '../api/extrato'
import type { ExtratoFiltros, ExtratoResponse } from '../types/finance'

export function useExtrato(filtros: ExtratoFiltros) {
  const [data, setData] = useState<ExtratoResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const key = JSON.stringify(filtros)

  useEffect(() => {
    let cancelled = false
    const fetchData = async () => {
      try {
        const res = await getExtrato(filtros)
        if (cancelled) return
        setData(res)
        setError(null)
      } catch {
        if (!cancelled) setError('Não foi possível carregar o extrato.')
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsLoading(true)
    void fetchData()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  return { data, isLoading, error }
}
