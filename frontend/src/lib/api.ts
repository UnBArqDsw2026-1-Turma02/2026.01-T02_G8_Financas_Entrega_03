import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'

const baseURL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

export const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean }

let refreshing: Promise<string | null> | null = null
let onAuthFailure: (() => void) | null = null

export function setAuthFailureHandler(handler: (() => void) | null) {
  onAuthFailure = handler
}

async function performRefresh(): Promise<string | null> {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) return null
  try {
    const { data } = await axios.post<{ access: string }>(
      `${baseURL}/v1/auth/refresh/`,
      { refresh: refreshToken },
      { headers: { 'Content-Type': 'application/json' } },
    )
    localStorage.setItem('access_token', data.access)
    return data.access
  } catch {
    return null
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined
    const isAuthEndpoint = original?.url?.includes('/v1/auth/login/') ||
      original?.url?.includes('/v1/auth/refresh/') ||
      original?.url?.includes('/v1/auth/register/')

    if (error.response?.status !== 401 || !original || original._retry || isAuthEndpoint) {
      return Promise.reject(error)
    }

    original._retry = true
    refreshing ??= performRefresh().finally(() => {
      refreshing = null
    })
    const newAccess = await refreshing

    if (!newAccess) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      onAuthFailure?.()
      return Promise.reject(error)
    }

    original.headers.Authorization = `Bearer ${newAccess}`
    return api.request(original)
  },
)
