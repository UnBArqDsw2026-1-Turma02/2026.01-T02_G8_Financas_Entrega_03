import { useMemo } from 'react'
import { CalendarIcon } from '../atoms/Icon'
import type { DiaProgresso, Progresso } from '../../domains/finance/api/progresso'
import './streak-calendar.css'

interface Props {
  data: Progresso | null
  isLoading: boolean
}

type Status = 'dentro' | 'reserva' | 'extra' | 'futuro'

function classify(dia: DiaProgresso, hoje: Date): Status {
  const d = new Date(dia.data)
  if (Number.isNaN(d.getTime())) return 'futuro'
  if (
    d.getFullYear() > hoje.getFullYear() ||
    (d.getFullYear() === hoje.getFullYear() &&
      (d.getMonth() > hoje.getMonth() ||
        (d.getMonth() === hoje.getMonth() && d.getDate() > hoje.getDate())))
  ) {
    return 'futuro'
  }
  if (dia.usou_extra) return 'extra'
  if (dia.usou_reserva) return 'reserva'
  if (dia.dentro_limite) return 'dentro'
  return 'futuro'
}

export function StreakCalendar({ data, isLoading }: Props) {
  const hoje = useMemo(() => new Date(), [])

  const dias = data?.calendario ?? []

  if (isLoading && !data) {
    return (
      <section className="streak-calendar">
        <div className="streak-calendar__head">
          <CalendarIcon size={16} />
          <span className="streak-calendar__title">Calendário de Progresso</span>
        </div>
        <p className="streak-calendar__empty">Carregando…</p>
      </section>
    )
  }

  return (
    <section className="streak-calendar">
      <div className="streak-calendar__head">
        <CalendarIcon size={16} />
        <span className="streak-calendar__title">Calendário de Progresso</span>
      </div>

      <div className="streak-calendar__grid" role="list">
        {dias.map((dia) => {
          const status = classify(dia, hoje)
          const num = Number(dia.data.slice(-2))
          const isFuturo = status === 'futuro'
          return (
            <div
              key={dia.data}
              role="listitem"
              className={`streak-calendar__day streak-calendar__day--${status}`}
              aria-label={`${dia.data}: ${labelStatus(status)}`}
            >
              {num}
              {!isFuturo && (
                <span className="streak-calendar__tooltip" role="tooltip">
                  <span className="streak-calendar__tooltip-date">
                    {formatDate(dia.data)}
                  </span>
                  <span className="streak-calendar__tooltip-row">
                    Gasto: <strong>{formatBRL(dia.gasto)}</strong>
                  </span>
                  <span className="streak-calendar__tooltip-row">
                    Limite: <strong>{formatBRL(dia.limite)}</strong>
                  </span>
                  <span className="streak-calendar__tooltip-status">
                    {labelStatus(status)}
                  </span>
                </span>
              )}
            </div>
          )
        })}
      </div>

      <ul className="streak-calendar__legend">
        <li>
          <span className="streak-calendar__swatch streak-calendar__swatch--dentro" />
          Dentro do limite
        </li>
        <li>
          <span className="streak-calendar__swatch streak-calendar__swatch--reserva" />
          Na reserva
        </li>
        <li>
          <span className="streak-calendar__swatch streak-calendar__swatch--extra" />
          Usou extra
        </li>
      </ul>
    </section>
  )
}

function formatBRL(value: string | number): string {
  const n = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(n)) return 'R$ 0,00'
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatDate(iso: string): string {
  const [y, m, d] = iso.split('-')
  if (!y || !m || !d) return iso
  return `${d}/${m}/${y}`
}

function labelStatus(status: Status): string {
  switch (status) {
    case 'dentro':
      return 'Dentro do limite'
    case 'reserva':
      return 'Na reserva'
    case 'extra':
      return 'Usou extra'
    case 'futuro':
    default:
      return 'Sem dados'
  }
}
