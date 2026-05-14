import { useEffect, useState } from 'react'
import {
  getDashboardCategorias,
  getDashboardTendencia,
  getDashboardVisaoGeral,
  type DashboardCategoriasResponse,
  type DashboardFiltros,
  type DashboardTendenciaResponse,
  type DashboardVisaoGeral,
} from '../api/dashboard'

export interface DashboardData {
  visao: DashboardVisaoGeral | null
  categorias: DashboardCategoriasResponse | null
  tendencia: DashboardTendenciaResponse | null
}

export function useDashboard(filtros: DashboardFiltros) {
  const [data, setData] = useState<DashboardData>({
    visao: null,
    categorias: null,
    tendencia: null,
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const key = JSON.stringify(filtros)

  useEffect(() => {
    let cancelled = false
    const fetchAll = async () => {
      try {
        const [visao, categorias, tendencia] = await Promise.all([
          getDashboardVisaoGeral(filtros),
          getDashboardCategorias(filtros),
          getDashboardTendencia(filtros),
        ])
        if (cancelled) return
        setData({ visao, categorias, tendencia })
        setError(null)
      } catch {
        if (!cancelled) setError('Não foi possível carregar o dashboard.')
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsLoading(true)
    void fetchAll()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  return { data, isLoading, error }
}
