import { useEffect, useState, type FormEvent } from 'react'
import { isAxiosError } from 'axios'
import { changePassword, updateProfile } from '../api/auth'
import { useAuth } from '../hooks/useAuth'
import './configuracoes.css'

function extractApiError(err: unknown, fallback: string): string {
  if (isAxiosError(err) && err.response?.data) {
    const data = err.response.data as Record<string, string[] | string>
    const first = Object.values(data)[0]
    return Array.isArray(first) ? first[0] : String(first)
  }
  return fallback
}

export default function ConfiguracoesPage() {
  const { user, setUser } = useAuth()
  const [username, setUsername] = useState(user?.username ?? '')
  const [email, setEmail] = useState(user?.email ?? '')
  const [profileSubmitting, setProfileSubmitting] = useState(false)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordSubmitting, setPasswordSubmitting] = useState(false)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null)

  useEffect(() => {
    if (user) {
      setUsername(user.username)
      setEmail(user.email)
    }
  }, [user])

  async function onSubmitProfile(event: FormEvent) {
    event.preventDefault()
    setProfileError(null)
    setProfileSuccess(null)
    setProfileSubmitting(true)
    try {
      const updated = await updateProfile({
        username: username.trim(),
        email: email.trim(),
      })
      setUser(updated)
      setProfileSuccess('Dados atualizados com sucesso.')
    } catch (err) {
      setProfileError(extractApiError(err, 'Não foi possível atualizar seus dados.'))
    } finally {
      setProfileSubmitting(false)
    }
  }

  async function onSubmitPassword(event: FormEvent) {
    event.preventDefault()
    setPasswordError(null)
    setPasswordSuccess(null)
    if (newPassword !== confirmPassword) {
      setPasswordError('A confirmação não corresponde à nova senha.')
      return
    }
    setPasswordSubmitting(true)
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      setPasswordSuccess('Senha alterada com sucesso.')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      setPasswordError(extractApiError(err, 'Não foi possível alterar a senha.'))
    } finally {
      setPasswordSubmitting(false)
    }
  }

  return (
    <section className="configuracoes-page">
      <h1>Configurações</h1>
      <p className="configuracoes-page__subtitle">
        Gerencie os dados da sua conta.
      </p>

      <article className="config-card">
        <h2 className="config-card__title">Dados da conta</h2>
        <p className="config-card__subtitle">
          Atualize seu nome de usuário e e-mail.
        </p>
        <form className="config-form" onSubmit={onSubmitProfile}>
          <label className="config-field">
            Usuário
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label className="config-field">
            E-mail
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </label>
          {profileError && (
            <p className="config-message config-message--error">{profileError}</p>
          )}
          {profileSuccess && (
            <p className="config-message config-message--success">{profileSuccess}</p>
          )}
          <div className="config-form__actions">
            <button
              type="submit"
              className="config-button"
              disabled={profileSubmitting}
            >
              {profileSubmitting ? 'Salvando…' : 'Salvar alterações'}
            </button>
          </div>
        </form>
      </article>

      <article className="config-card">
        <h2 className="config-card__title">Alterar senha</h2>
        <p className="config-card__subtitle">
          Para alterar sua senha, informe a senha atual e a nova senha.
        </p>
        <form className="config-form" onSubmit={onSubmitPassword}>
          <label className="config-field">
            Senha atual
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          <label className="config-field">
            Nova senha
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              autoComplete="new-password"
              required
            />
          </label>
          <label className="config-field">
            Confirmar nova senha
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              autoComplete="new-password"
              required
            />
          </label>
          {passwordError && (
            <p className="config-message config-message--error">{passwordError}</p>
          )}
          {passwordSuccess && (
            <p className="config-message config-message--success">{passwordSuccess}</p>
          )}
          <div className="config-form__actions">
            <button
              type="submit"
              className="config-button"
              disabled={passwordSubmitting}
            >
              {passwordSubmitting ? 'Alterando…' : 'Alterar senha'}
            </button>
          </div>
        </form>
      </article>
    </section>
  )
}
