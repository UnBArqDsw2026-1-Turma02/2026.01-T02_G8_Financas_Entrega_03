import { api } from '../../../lib/api'

export interface CarteiraEstado {
  gasto_dia: string
  falta_limite: string
  limite_diario: string
  saldo_reserva: string
  saldo_extra: string
}

export async function getCarteira(): Promise<CarteiraEstado> {
  const { data } = await api.get<CarteiraEstado>('/v1/finance/carteira/')
  return data
}
