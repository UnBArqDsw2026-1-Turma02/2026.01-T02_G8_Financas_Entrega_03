import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { isAxiosError } from 'axios'
import { useAuth } from '../hooks/useAuth'
import './auth.css'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [telegramId, setTelegramId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await register({
        username,
        email,
        password,
        telegram_id: telegramId.trim() ? telegramId.trim() : null,
      })
      navigate('/', { replace: true })
    } catch (err) {
      if (isAxiosError(err) && err.response?.data) {
        const data = err.response.data as Record<string, string[] | string>
        const first = Object.values(data)[0]
        setError(Array.isArray(first) ? first[0] : String(first))
      } else {
        setError('Não foi possível concluir o cadastro.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Criar conta</h1>
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
          E-mail
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </label>
        <label className="auth-field">
          Senha
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            required
          />
        </label>
        <label className="auth-field">
          Telegram ID (opcional)
          <input
            type="text"
            value={telegramId}
            onChange={(e) => setTelegramId(e.target.value)}
          />
        </label>
        {error && <p className="auth-error">{error}</p>}
        <button className="auth-button" type="submit" disabled={submitting}>
          {submitting ? 'Criando…' : 'Cadastrar'}
        </button>
        <p className="auth-footer">
          Já tem conta? <Link to="/login">Entrar</Link>
        </p>
      </form>
    </main>
  )
}
