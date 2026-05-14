import { useMemo } from 'react'
import { PiggyBankIcon, WalletIcon } from '../atoms/Icon'
import type { CarteiraEstado } from '../../domains/finance/api/carteira'
import type { Alerta } from '../../domains/finance/api/alertas'
import './carteira-card.css'

interface Props {
  estado: CarteiraEstado | null
  alertas: Alerta[]
  isLoading: boolean
}

function toNumber(value: string | number | null | undefined): number {
  if (value === null || value === undefined) return 0
  const n = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(n) ? n : 0
}

function formatCurrency(value: number): string {
  return value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
}

function ExtraIcon({ size = 16 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 2v6" />
      <path d="M5 9h14" />
      <path d="M6 9l1 11h10l1-11" />
      <path d="M9 13l6 4" />
      <path d="M15 13l-6 4" />
    </svg>
  )
}

function SunIcon({ size = 16 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 3v2" />
      <path d="M12 19v2" />
      <path d="M3 12h2" />
      <path d="M19 12h2" />
      <path d="M5.6 5.6l1.4 1.4" />
      <path d="M17 17l1.4 1.4" />
      <path d="M5.6 18.4l1.4-1.4" />
      <path d="M17 7l1.4-1.4" />
    </svg>
  )
}

export function CarteiraCard({ estado, alertas, isLoading }: Props) {
  const gasto = toNumber(estado?.gasto_dia)
  const limite = toNumber(estado?.limite_diario)
  const reserva = toNumber(estado?.saldo_reserva)
  const extra = toNumber(estado?.saldo_extra)
  const falta = toNumber(estado?.falta_limite)

  const totalDisponivel = useMemo(
    () => limite + reserva - extra - gasto,
    [limite, reserva, extra, gasto],
  )

  const segments = useMemo(() => {
    const excessoDiario = Math.max(gasto - limite, 0)
    const diario = Math.max(limite - gasto, 0)
    const reservaSeg = Math.max(reserva - excessoDiario, 0)
    const extraSeg = Math.max(extra, 0)
    const ultrapassagem = Math.max(excessoDiario - reserva, 0)
    const total = diario + reservaSeg + extraSeg + ultrapassagem || 1
    return {
      diarioPct: (diario / total) * 100,
      reservaPct: (reservaSeg / total) * 100,
      extraPct: (extraSeg / total) * 100,
      ultrapassagemPct: (ultrapassagem / total) * 100,
      diario,
      reservaSeg,
      extraSeg,
      ultrapassagem,
    }
  }, [limite, reserva, extra, gasto])

  const principalAlerta = alertas[0] ?? null

  return (
    <section className="carteira-card">
      <div className="carteira-card__header">
        <WalletIcon size={18} />
        <span className="carteira-card__title">Carteira</span>
      </div>

      <div
        className={`carteira-card__valor${
          totalDisponivel < 0 ? ' carteira-card__valor--negativo' : ''
        }`}
        aria-live="polite"
      >
        {isLoading && !estado ? '—' : formatCurrency(totalDisponivel)}
      </div>

      <div
        className="carteira-card__bar"
        role="img"
        aria-label="Distribuição entre limite diário, reserva e extra"
      >
        {segments.diario > 0 && (
          <div
            className="carteira-card__seg carteira-card__seg--diario"
            style={{ width: `${segments.diarioPct}%` }}
          >
            <SunIcon size={14} />
            <span>Diário: {formatCurrency(segments.diario)}</span>
          </div>
        )}
        {segments.reservaSeg > 0 && (
          <div
            className="carteira-card__seg carteira-card__seg--reserva"
            style={{ width: `${segments.reservaPct}%` }}
          >
            <PiggyBankIcon size={14} />
            <span>Reserva: {formatCurrency(segments.reservaSeg)}</span>
          </div>
        )}
        {segments.extraSeg > 0 && (
          <div
            className="carteira-card__seg carteira-card__seg--extra"
            style={{ width: `${segments.extraPct}%` }}
          >
            <ExtraIcon size={14} />
            <span>Extra: -{formatCurrency(segments.extraSeg)}</span>
          </div>
        )}
        {segments.ultrapassagem > 0 && (
          <div
            className="carteira-card__seg carteira-card__seg--ultrapassagem"
            style={{ width: `${segments.ultrapassagemPct}%` }}
            title={`Ultrapassou em ${formatCurrency(segments.ultrapassagem)}`}
          >
            <ExtraIcon size={14} />
            <span>Ultrapassou: +{formatCurrency(segments.ultrapassagem)}</span>
          </div>
        )}
      </div>

      <div className="carteira-card__info">
        <span className="carteira-card__info-item">
          <SunIcon size={14} />
          Limite Diário: {formatCurrency(limite)}
        </span>
        <span className="carteira-card__info-item">
          <PiggyBankIcon size={14} />
          Reserva acumulada: {formatCurrency(reserva)}
        </span>
        {falta > 0 && (
          <span className="carteira-card__info-item">
            Falta para limite: {formatCurrency(falta)}
          </span>
        )}
      </div>

      {principalAlerta && (
        <div
          className={`carteira-alert carteira-alert--${alertaSeverity(
            principalAlerta.gatilho,
          )}`}
          role="alert"
        >
          <span className="carteira-alert__icon" aria-hidden="true">
            !
          </span>
          <div className="carteira-alert__body">
            <strong className="carteira-alert__title">
              {alertaTitulo(principalAlerta.gatilho)}
            </strong>
            <span className="carteira-alert__msg">
              {principalAlerta.mensagem}
            </span>
          </div>
        </div>
      )}
    </section>
  )
}

function alertaSeverity(gatilho: string): 'info' | 'warn' | 'danger' {
  if (gatilho === 'limite_100' || gatilho === 'reserva_esgotada') return 'danger'
  if (gatilho === 'limite_70' || gatilho === 'reserva_80') return 'warn'
  return 'info'
}

function alertaTitulo(gatilho: string): string {
  switch (gatilho) {
    case 'limite_100':
      return 'Limite diário atingido!'
    case 'limite_70':
      return 'Atenção com o limite!'
    case 'reserva_esgotada':
      return 'Revise seus gastos!'
    case 'reserva_80':
      return 'Reserva quase no fim'
    case 'reserva_50':
      return 'Metade da reserva já foi'
    default:
      return 'Alerta'
  }
}
