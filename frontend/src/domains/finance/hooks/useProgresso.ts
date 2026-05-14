import { useEffect, useState } from 'react'
import { getProgresso, type Progresso } from '../api/progresso'

export function useProgresso(refreshKey?: number | string) {
  const [data, setData] = useState<Progresso | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsLoading(true)
    getProgresso()
      .then((value) => {
        if (cancelled) return
        setData(value)
        setError(null)
      })
      .catch(() => {
        if (!cancelled) setError('Não foi possível carregar o progresso.')
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [refreshKey])

  return { data, isLoading, error }
}
