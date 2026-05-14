import { useEffect, useState } from 'react'
import { getAlertas, type Alerta } from '../api/alertas'

export function useAlertas(refreshKey?: number | string) {
  const [alertas, setAlertas] = useState<Alerta[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsLoading(true)
    getAlertas()
      .then(({ alertas: lista }) => {
        if (cancelled) return
        setAlertas(lista)
        setError(null)
      })
      .catch(() => {
        if (!cancelled) setError('Não foi possível carregar os alertas.')
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [refreshKey])

  return { alertas, isLoading, error }
}
