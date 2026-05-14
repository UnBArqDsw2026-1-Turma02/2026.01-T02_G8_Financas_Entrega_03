import { api } from '../../../lib/api'

export interface DiaProgresso {
  data: string
  dentro_limite: boolean
  usou_reserva: boolean
  usou_extra: boolean
  gasto: string
  limite: string
}

export interface Progresso {
  ano: number
  mes: number
  streak: number
  calendario: DiaProgresso[]
}

export async function getProgresso(): Promise<Progresso> {
  const { data } = await api.get<Progresso>('/v1/finance/progresso/')
  return data
}
