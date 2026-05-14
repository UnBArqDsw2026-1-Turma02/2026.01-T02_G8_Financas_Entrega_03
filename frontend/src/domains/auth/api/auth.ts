import { api } from '../../../lib/api'
import type { LoginPayload, RegisterPayload, TokenPair, Usuario } from '../types/auth'

export async function login(payload: LoginPayload): Promise<TokenPair> {
  const { data } = await api.post<TokenPair>('/v1/auth/login/', payload)
  return data
}

export async function register(payload: RegisterPayload): Promise<Usuario> {
  const { data } = await api.post<Usuario>('/v1/auth/register/', payload)
  return data
}

export async function refresh(refreshToken: string): Promise<{ access: string }> {
  const { data } = await api.post<{ access: string }>('/v1/auth/refresh/', {
    refresh: refreshToken,
  })
  return data
}

export async function me(): Promise<Usuario> {
  const { data } = await api.get<Usuario>('/v1/auth/me/')
  return data
}
