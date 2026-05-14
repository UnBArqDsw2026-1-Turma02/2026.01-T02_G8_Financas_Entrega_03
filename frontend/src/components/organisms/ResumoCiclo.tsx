import { useMemo } from 'react'
import type { Progresso } from '../../domains/finance/api/progresso'
import './resumo-ciclo.css'

interface Props {
  data: Progresso | null
  isLoading: boolean
}

function TrophyIcon({ size = 16 }: { size?: number }) {
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
      <path d="M8 4h8v4a4 4 0 0 1-8 0z" />
      <path d="M8 6H5a3 3 0 0 0 3 4" />
      <path d="M16 6h3a3 3 0 0 1-3 4" />
      <path d="M10 14h4" />
      <path d="M9 18h6" />
      <path d="M12 14v4" />
    </svg>
  )
}

function TargetIcon({ size = 16 }: { size?: number }) {
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
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" />
    </svg>
  )
}

function FlameIcon({ size = 16 }: { size?: number }) {
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
      <path d="M12 3c1 4 4 5 4 9a4 4 0 1 1-8 0c0-2 1-3 2-4-.5 2 .5 3 2-1 0 2 0 3-0-4z" />
    </svg>
  )
}

function AlertCircleIcon({ size = 16 }: { size?: number }) {
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
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v5" />
      <path d="M12 16h0" />
    </svg>
  )
}

interface Stats {
  totalDias: number
  diasNoLimite: number
  diasAcimaLimite: number
  sequenciaAtual: number
  melhorSequencia: number
  percentualSucesso: number
}

function computeStats(data: Progresso | null): Stats {
  if (!data) {
    return {
      totalDias: 0,
      diasNoLimite: 0,
      diasAcimaLimite: 0,
      sequenciaAtual: 0,
      melhorSequencia: 0,
      percentualSucesso: 0,
    }
  }
  const hoje = new Date()
  const fechados = data.calendario.filter((d) => {
    const dt = new Date(d.data)
    return dt <= hoje
  })

  let diasNoLimite = 0
  let diasAcimaLimite = 0
  let melhor = 0
  let atual = 0
  for (const d of fechados) {
    if (d.usou_extra) {
      diasAcimaLimite += 1
      atual = 0
    } else if (d.dentro_limite || d.usou_reserva) {
      diasNoLimite += 1
      atual += 1
      if (atual > melhor) melhor = atual
    }
  }

  const total = fechados.length || 1
  const percentual = Math.round((diasNoLimite / total) * 100)

  return {
    totalDias: fechados.length,
    diasNoLimite,
    diasAcimaLimite,
    sequenciaAtual: data.streak,
    melhorSequencia: Math.max(melhor, data.streak),
    percentualSucesso: percentual,
  }
}

export function ResumoCiclo({ data, isLoading }: Props) {
  const stats = useMemo(() => computeStats(data), [data])

  const radius = 38
  const circumference = 2 * Math.PI * radius
  const offset =
    circumference - (Math.min(Math.max(stats.percentualSucesso, 0), 100) / 100) * circumference

  return (
    <section className="resumo-ciclo">
      <div className="resumo-ciclo__head">
        <TrophyIcon size={16} />
        <span className="resumo-ciclo__title">Resumo do Ciclo</span>
      </div>

      <div className="resumo-ciclo__body">
        <div className="resumo-ciclo__progress">
          <svg width={120} height={120} viewBox="0 0 100 100">
            <circle
              cx={50}
              cy={50}
              r={radius}
              stroke="#ececf2"
              strokeWidth={8}
              fill="none"
            />
            <circle
              cx={50}
              cy={50}
              r={radius}
              stroke="#6dbe64"
              strokeWidth={8}
              fill="none"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              transform="rotate(-90 50 50)"
            />
          </svg>
          <div className="resumo-ciclo__progress-label">
            <span className="resumo-ciclo__pct">
              {isLoading && !data ? '—' : `${stats.percentualSucesso}%`}
            </span>
            <span className="resumo-ciclo__pct-sub">sucesso</span>
          </div>
        </div>

        <div className="resumo-ciclo__stats">
          <div className="resumo-ciclo__stat">
            <span className="resumo-ciclo__stat-icon resumo-ciclo__stat-icon--green">
              <TargetIcon size={14} />
            </span>
            <div>
              <span className="resumo-ciclo__stat-label">Dias no limite</span>
              <span className="resumo-ciclo__stat-value">
                {stats.diasNoLimite}/{stats.totalDias}
              </span>
            </div>
          </div>
          <div className="resumo-ciclo__stat">
            <span className="resumo-ciclo__stat-icon resumo-ciclo__stat-icon--orange">
              <FlameIcon size={14} />
            </span>
            <div>
              <span className="resumo-ciclo__stat-label">Sequência atual</span>
              <span className="resumo-ciclo__stat-value">
                {stats.sequenciaAtual}
              </span>
            </div>
          </div>
          <div className="resumo-ciclo__stat">
            <span className="resumo-ciclo__stat-icon resumo-ciclo__stat-icon--red">
              <AlertCircleIcon size={14} />
            </span>
            <div>
              <span className="resumo-ciclo__stat-label">Dias acima do limite</span>
              <span className="resumo-ciclo__stat-value">
                {stats.diasAcimaLimite}
              </span>
            </div>
          </div>
          <div className="resumo-ciclo__stat">
            <span className="resumo-ciclo__stat-icon resumo-ciclo__stat-icon--purple">
              <TrophyIcon size={14} />
            </span>
            <div>
              <span className="resumo-ciclo__stat-label">Melhor Sequência</span>
              <span className="resumo-ciclo__stat-value">
                {stats.melhorSequencia}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
