import { useEffect, useState } from 'react'
import { getCarteira, type CarteiraEstado } from '../api/carteira'

export function useCarteira(refreshKey?: number | string) {
  const [data, setData] = useState<CarteiraEstado | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsLoading(true)
    getCarteira()
      .then((value) => {
        if (cancelled) return
        setData(value)
        setError(null)
      })
      .catch(() => {
        if (!cancelled) setError('Não foi possível carregar a carteira.')
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
