import { useEffect, useState, type FormEvent } from 'react'
import { isAxiosError } from 'axios'
import { getTelegram, linkTelegram, unlinkTelegram } from '../api/telegram'
import { PlugIcon } from '../../../components/atoms/Icon'
import './integracoes.css'

export default function IntegracoesPage() {
  const [telegramId, setTelegramId] = useState<string | null>(null)
  const [inputId, setInputId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let cancelled = false
    getTelegram()
      .then((v) => {
        if (!cancelled) setTelegramId(v.telegram_id)
      })
      .catch(() => {
        if (!cancelled) setError('Não foi possível carregar suas integrações.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function handleLink(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const { telegram_id } = await linkTelegram(inputId.trim())
      setTelegramId(telegram_id)
      setInputId('')
    } catch (err) {
      if (isAxiosError(err) && err.response?.data?.telegram_id) {
        setError(String(err.response.data.telegram_id[0]))
      } else {
        setError('Não foi possível vincular. Tente novamente.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  async function handleUnlink() {
    setError(null)
    setSubmitting(true)
    try {
      await unlinkTelegram()
      setTelegramId(null)
    } catch {
      setError('Não foi possível desvincular. Tente novamente.')
    } finally {
      setSubmitting(false)
    }
  }

  const isLinked = telegramId !== null

  return (
    <section className="integracoes-page">
      <h1>Integrações</h1>
      <p className="integracoes-page__subtitle">
        Gerencie suas integrações com serviços de mensageria.
      </p>

      <div className="integracoes-grid">
        <article className="integracao-card">
          <span
            className={`integracao-card__status ${
              isLinked
                ? 'integracao-card__status--linked'
                : 'integracao-card__status--unlinked'
            }`}
          >
            <PlugIcon size={14} />
            {isLinked ? 'Vinculado' : 'Não Vinculado'}
          </span>
          <h2 className="integracao-card__title">Telegram</h2>

          {loading ? (
            <p className="integracao-card__meta">Carregando…</p>
          ) : isLinked ? (
            <>
              <p className="integracao-card__meta">
                <strong>ID externo:</strong> {telegramId}
              </p>
              {error && <p className="integracao-card__error">{error}</p>}
              <button
                type="button"
                className="integracao-card__button integracao-card__button--danger"
                onClick={handleUnlink}
                disabled={submitting}
              >
                {submitting ? 'Desvinculando…' : 'Desvincular'}
              </button>
            </>
          ) : (
            <form onSubmit={handleLink} style={{ display: 'contents' }}>
              <input
                className="integracao-card__input"
                type="text"
                inputMode="numeric"
                pattern="\d{5,20}"
                placeholder="Seu ID numérico do Telegram"
                value={inputId}
                onChange={(e) => setInputId(e.target.value)}
                required
              />
              <p className="integracao-card__hint">
                Descubra seu ID enviando uma mensagem para{' '}
                <a
                  href="https://t.me/userinfobot"
                  target="_blank"
                  rel="noreferrer"
                >
                  @userinfobot
                </a>
                .
              </p>
              {error && <p className="integracao-card__error">{error}</p>}
              <button
                type="submit"
                className="integracao-card__button"
                disabled={submitting}
              >
                {submitting ? 'Vinculando…' : 'Vincular'}
              </button>
            </form>
          )}
        </article>

        <article className="integracao-card integracao-card--disabled">
          <span className="integracao-card__status integracao-card__status--unlinked">
            <PlugIcon size={14} />
            Não Vinculado
          </span>
          <h2 className="integracao-card__title">Whatsapp</h2>
          <p className="integracao-card__hint">Integração ainda não disponível.</p>
          <button type="button" className="integracao-card__button" disabled>
            Vincular
          </button>
        </article>
      </div>
    </section>
  )
}
