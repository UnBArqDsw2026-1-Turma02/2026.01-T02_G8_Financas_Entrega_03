import { api } from '../../../lib/api'

export interface TelegramVinculo {
  telegram_id: string | null
}

export async function getTelegram(): Promise<TelegramVinculo> {
  const { data } = await api.get<TelegramVinculo>('/v1/auth/me/telegram/')
  return data
}

export async function linkTelegram(telegramId: string): Promise<TelegramVinculo> {
  const { data } = await api.post<TelegramVinculo>('/v1/auth/me/telegram/', {
    telegram_id: telegramId,
  })
  return data
}

export async function unlinkTelegram(): Promise<void> {
  await api.delete('/v1/auth/me/telegram/')
}
