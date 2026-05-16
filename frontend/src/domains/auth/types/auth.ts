export interface Usuario {
  id: number
  username: string
  email: string
  telegram_id: string | null
  date_joined: string
}

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
  telegram_id?: string | null
}

export interface TokenPair {
  access: string
  refresh: string
}

export interface AuthState {
  user: Usuario | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (payload: LoginPayload) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => void
  setUser: (user: Usuario) => void
}
