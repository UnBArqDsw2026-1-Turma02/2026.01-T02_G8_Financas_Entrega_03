import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import * as authApi from '../api/auth'
import { setAuthFailureHandler } from '../../../lib/api'
import { tokenStorage } from '../storage'
import type { AuthState, LoginPayload, RegisterPayload, Usuario } from '../types/auth'
import { AuthContext } from './context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Usuario | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(!!tokenStorage.getAccess())

  const logout = useCallback(() => {
    tokenStorage.clear()
    setUser(null)
  }, [])

  useEffect(() => {
    setAuthFailureHandler(() => {
      setUser(null)
    })
    return () => setAuthFailureHandler(null)
  }, [])

  useEffect(() => {
    if (!tokenStorage.getAccess()) return
    let cancelled = false
    authApi
      .me()
      .then((u) => {
        if (!cancelled) setUser(u)
      })
      .catch(() => {
        if (!cancelled) tokenStorage.clear()
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (payload: LoginPayload) => {
    const tokens = await authApi.login(payload)
    tokenStorage.set(tokens)
    const me = await authApi.me()
    setUser(me)
  }, [])

  const register = useCallback(async (payload: RegisterPayload) => {
    await authApi.register(payload)
    await login({ username: payload.username, password: payload.password })
  }, [login])

  const value = useMemo<AuthState>(
    () => ({
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      register,
      logout,
      setUser,
    }),
    [user, isLoading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
