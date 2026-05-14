import { useMemo, useState, type ReactNode } from 'react'
import { Select } from '../../../components/atoms/Select'
import {
  CalendarIcon,
  CartIcon,
  LockIcon,
  PiggyBankIcon,
  PieChartIcon,
  ReceiptIcon,
  SlidersIcon,
  TargetIcon,
  TrendingUpIcon,
} from '../../../components/atoms/Icon'
import { DonutChart } from '../../../components/molecules/DonutChart'
import { LineChart } from '../../../components/molecules/LineChart'
import { CarteiraCard } from '../../../components/organisms/CarteiraCard'
import { StreakCalendar } from '../../../components/organisms/StreakCalendar'
import { ResumoCiclo } from '../../../components/organisms/ResumoCiclo'
import { useDashboard } from '../hooks/useDashboard'
import { useCarteira } from '../hooks/useCarteira'
import { useProgresso } from '../hooks/useProgresso'
import { useAlertas } from '../hooks/useAlertas'
import './dashboard-page.css'

const MES_OPTIONS = [
  { value: '1', label: 'Janeiro' },
  { value: '2', label: 'Fevereiro' },
  { value: '3', label: 'Março' },
  { value: '4', label: 'Abril' },
  { value: '5', label: 'Maio' },
  { value: '6', label: 'Junho' },
  { value: '7', label: 'Julho' },
  { value: '8', label: 'Agosto' },
  { value: '9', label: 'Setembro' },
  { value: '10', label: 'Outubro' },
  { value: '11', label: 'Novembro' },
  { value: '12', label: 'Dezembro' },
]

function anoOptions(): { value: string; label: string }[] {
  const ano = new Date().getFullYear()
  return Array.from({ length: 6 }, (_, i) => {
    const v = String(ano - i)
    return { value: v, label: v }
  })
}

function formatCurrency(value: string | number): string {
  const n = typeof value === 'number' ? value : Number(value)
  if (Number.isNaN(n)) return String(value)
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function shortDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  return `${dd}/${mm}`
}

interface SummaryCardProps {
  icon: ReactNode
  label: string
  value: string
}

function SummaryCard({ icon, label, value }: SummaryCardProps) {
  return (
    <div className="dashboard-summary">
      <div className="dashboard-summary__head">
        <span className="dashboard-summary__icon">{icon}</span>
        <span className="dashboard-summary__label">{label}</span>
      </div>
      <span className="dashboard-summary__value">{value}</span>
    </div>
  )
}

export default function DashboardPage() {
  const now = new Date()
  const [ano, setAno] = useState<string>(String(now.getFullYear()))
  const [mes, setMes] = useState<string>(String(now.getMonth() + 1))

  const filtros = useMemo(
    () => ({ ano: Number(ano), mes: Number(mes) }),
    [ano, mes],
  )

  const { data, isLoading, error } = useDashboard(filtros)
  const { data: carteira, isLoading: carteiraLoading } = useCarteira()
  const { data: progresso, isLoading: progressoLoading } = useProgresso()
  const { alertas } = useAlertas()

  const cicloRange = useMemo(() => {
    const a = Number(ano)
    const m = Number(mes)
    const lastDay = new Date(a, m, 0).getDate()
    const fmt = (d: number) =>
      `${String(d).padStart(2, '0')}/${String(m).padStart(2, '0')}`
    return `${fmt(1)} → ${fmt(lastDay)}`
  }, [ano, mes])

  const totaisVisao = data.visao
  const orcamentoMensal = useMemo(() => {
    if (!totaisVisao) return 0
    return (
      Number(totaisVisao.total_entradas) -
      Number(totaisVisao.total_saidas_fixas)
    )
  }, [totaisVisao])

  const donutData = useMemo(() => {
    if (!data.categorias) return []
    return data.categorias.categorias.map((c) => ({
      label: c.nome,
      value: Number(c.total),
      color: c.cor,
    }))
  }, [data.categorias])

  const lineData = useMemo(() => {
    if (!data.tendencia) return []
    return data.tendencia.dias.map((d) => ({
      label: shortDate(d.data),
      value: Number(d.total_gasto),
    }))
  }, [data.tendencia])

  return (
    <section className="dashboard-page">
      <div className="dashboard-ciclo">
        <div className="dashboard-ciclo__info">
          <span className="dashboard-ciclo__label">
            <CalendarIcon size={16} />
            Ciclo Atual
          </span>
          <span className="dashboard-ciclo__range">{cicloRange}</span>
        </div>
        <div className="dashboard-ciclo__actions">
          <div className="dashboard-selector">
            <span className="dashboard-selector__group">
              <label htmlFor="dashboard-mes">Mês</label>
              <Select
                id="dashboard-mes"
                value={mes}
                onChange={(e) => setMes(e.target.value)}
                options={MES_OPTIONS}
              />
            </span>
            <span className="dashboard-selector__group">
              <label htmlFor="dashboard-ano">Ano</label>
              <Select
                id="dashboard-ano"
                value={ano}
                onChange={(e) => setAno(e.target.value)}
                options={anoOptions()}
              />
            </span>
          </div>
        </div>
      </div>

      {error && <div className="dashboard-page__error">{error}</div>}

      <div className="dashboard-cards">
        <SummaryCard
          icon={<ReceiptIcon size={16} />}
          label="Entradas"
          value={formatCurrency(totaisVisao?.total_entradas ?? 0)}
        />
        <SummaryCard
          icon={<LockIcon size={16} />}
          label="Despesas Fixas"
          value={formatCurrency(totaisVisao?.total_saidas_fixas ?? 0)}
        />
        <SummaryCard
          icon={<CartIcon size={16} />}
          label="Despesas Variáveis"
          value={formatCurrency(totaisVisao?.total_saidas_variaveis ?? 0)}
        />
        <SummaryCard
          icon={<TargetIcon size={16} />}
          label="Orçamento Mensal"
          value={formatCurrency(orcamentoMensal)}
        />
      </div>

      <CarteiraCard
        estado={carteira}
        alertas={alertas}
        isLoading={carteiraLoading}
      />

      <div className="dashboard-cards">
        <SummaryCard
          icon={<PiggyBankIcon size={16} />}
          label="Saldo Disponível"
          value={formatCurrency(totaisVisao?.saldo_disponivel ?? 0)}
        />
        <SummaryCard
          icon={<SlidersIcon size={16} />}
          label="Total Gasto"
          value={formatCurrency(
            (Number(totaisVisao?.total_saidas_fixas ?? 0) +
              Number(totaisVisao?.total_saidas_variaveis ?? 0)) || 0,
          )}
        />
      </div>

      <div className="dashboard-charts">
        <div className="dashboard-card">
          <div className="dashboard-card__head">
            <PieChartIcon size={16} />
            <span className="dashboard-card__title">Gastos por Categoria</span>
          </div>
          {isLoading ? (
            <div className="dashboard-empty">Carregando…</div>
          ) : (
            <div className="dashboard-donut">
              <div className="dashboard-donut__chart">
                <DonutChart data={donutData} size={200} thickness={32} />
              </div>
              <ul className="dashboard-donut__legend">
                {donutData.length === 0 && (
                  <li className="dashboard-empty">Sem gastos no período.</li>
                )}
                {donutData.map((d) => (
                  <li key={d.label} className="dashboard-donut__legend-item">
                    <span
                      className="dashboard-donut__swatch"
                      style={{ background: d.color }}
                    />
                    <span>{d.label}</span>
                    <span className="dashboard-donut__value">
                      {formatCurrency(d.value)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="dashboard-card">
          <div className="dashboard-card__head">
            <TrendingUpIcon size={16} />
            <span className="dashboard-card__title">Tendência de Gastos</span>
          </div>
          {isLoading ? (
            <div className="dashboard-empty">Carregando…</div>
          ) : (
            <div className="dashboard-line">
              <LineChart
                data={lineData}
                width={560}
                height={240}
                color="#4F378A"
              />
            </div>
          )}
        </div>
      </div>

      <div className="dashboard-progresso">
        <StreakCalendar data={progresso} isLoading={progressoLoading} />
        <ResumoCiclo data={progresso} isLoading={progressoLoading} />
      </div>
    </section>
  )
}
