import { api } from '../../../lib/api'

export type AlertaGatilho =
  | 'limite_70'
  | 'limite_100'
  | 'reserva_50'
  | 'reserva_80'
  | 'reserva_esgotada'

export interface Alerta {
  gatilho: AlertaGatilho | string
  mensagem: string
}

export interface AlertasResponse {
  alertas: Alerta[]
}

export async function getAlertas(): Promise<AlertasResponse> {
  const { data } = await api.get<AlertasResponse>('/v1/finance/alertas/')
  return data
}
