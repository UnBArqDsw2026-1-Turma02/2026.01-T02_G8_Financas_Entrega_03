import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { isAxiosError } from 'axios'
import { useAuth } from '../hooks/useAuth'
import './auth.css'

interface LocationState {
  from?: { pathname: string }
}

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login({ username, password })
      const target = (location.state as LocationState | null)?.from?.pathname ?? '/'
      navigate(target, { replace: true })
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 401) {
        setError('Usuário ou senha inválidos.')
      } else {
        setError('Não foi possível entrar. Tente novamente.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Entrar</h1>
        <label className="auth-field">
          Usuário
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </label>
        <label className="auth-field">
          Senha
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        {error && <p className="auth-error">{error}</p>}
        <button className="auth-button" type="submit" disabled={submitting}>
          {submitting ? 'Entrando…' : 'Entrar'}
        </button>
        <p className="auth-footer">
          Sem conta? <Link to="/register">Cadastre-se</Link>
        </p>
      </form>
    </main>
  )
}
