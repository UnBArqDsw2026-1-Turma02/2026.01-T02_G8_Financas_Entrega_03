import { useState, type FormEvent } from 'react'
import { isAxiosError } from 'axios'
import { ArrowRightIcon, PiggyBankIcon, PlusIcon } from '../atoms/Icon'
import { Input } from '../atoms/Input'
import { FormField } from '../molecules/FormField'
import { api } from '../../lib/api'
import { Modal } from './Modal'
import './simular-gasto.css'

interface SimulacaoResponse {
  impacta_30_porcento: boolean
  dentro_orcamento: boolean
  orcamento_mensal_atual: string
  novo_orcamento: string
  limite_diario_atual: string
  novo_limite_diario: string
  simulacao_parcelamento?: {
    valor_parcela: string
    impacto_mensal: string
  }
}

interface FormState {
  nome: string
  valor: string
  parcelas: string
}

export interface SimularGastoFlowProps {
  open: boolean
  onClose: () => void
  initialValor?: string
  initialNome?: string
}

function toNumber(value: string): number {
  const n = Number(value)
  return Number.isFinite(n) ? n : 0
}

function formatBRL(value: string | number): string {
  const n = typeof value === 'string' ? Number(value) : value
  if (!Number.isFinite(n)) return String(value)
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function SimularGastoFlow({
  open,
  onClose,
  initialValor,
  initialNome,
}: SimularGastoFlowProps) {
  const [form, setForm] = useState<FormState>({
    nome: initialNome ?? '',
    valor: initialValor ?? '',
    parcelas: '1',
  })
  const [result, setResult] = useState<SimulacaoResponse | null>(null)
  const [parcelasResult, setParcelasResult] = useState<number>(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const valorNum = toNumber(form.valor)
    if (valorNum <= 0) {
      setError('Informe um valor maior que zero.')
      return
    }
    const parcelasNum = Math.max(1, Number.parseInt(form.parcelas, 10) || 1)
    setError(null)
    setLoading(true)
    try {
      const { data } = await api.post<SimulacaoResponse>(
        '/v1/finance/simular-gasto/',
        {
          valor: valorNum.toFixed(2),
          parcelado: parcelasNum > 1,
          num_parcelas: parcelasNum,
        },
      )
      setResult(data)
      setParcelasResult(parcelasNum)
    } catch (err) {
      if (isAxiosError(err) && err.response?.data) {
        const data = err.response.data as Record<string, unknown>
        const messages = Object.values(data).flat().filter(Boolean)
        setError(messages.length ? String(messages[0]) : 'Erro ao simular.')
      } else {
        setError('Não foi possível simular o gasto.')
      }
    } finally {
      setLoading(false)
    }
  }

  if (!open) return null

  if (result) {
    return (
      <ResultadoCard
        result={result}
        parcelas={parcelasResult}
        onClose={onClose}
        onNova={() => setResult(null)}
      />
    )
  }

  return (
    <Modal open title="Simular Gasto" onClose={onClose}>
      <form className="organism-form" onSubmit={handleSubmit}>
        <FormField label="Nome (opcional)">
          <Input
            value={form.nome}
            onChange={(e) => setForm({ ...form, nome: e.target.value })}
            placeholder="Placeholder"
          />
        </FormField>
        <div className="organism-form__row">
          <FormField label="Valor">
            <Input
              type="number"
              step="0.01"
              min="0.01"
              value={form.valor}
              onChange={(e) => setForm({ ...form, valor: e.target.value })}
              placeholder="Placeholder"
              required
            />
          </FormField>
          <FormField label="Parcelas">
            <Input
              type="number"
              min="1"
              step="1"
              value={form.parcelas}
              onChange={(e) => setForm({ ...form, parcelas: e.target.value })}
              placeholder="1 = a vista"
            />
          </FormField>
        </div>
        {error && <p className="organism-form__error">{error}</p>}
        <div className="organism-form__actions">
          <button
            type="submit"
            className="organism-form__submit"
            disabled={loading}
          >
            <PlusIcon />
            <span>{loading ? 'Simulando…' : 'Criar'}</span>
          </button>
        </div>
      </form>
    </Modal>
  )
}

interface ResultadoCardProps {
  result: SimulacaoResponse
  parcelas: number
  onClose: () => void
  onNova: () => void
}

function ResultadoCard({ result, parcelas, onClose, onNova }: ResultadoCardProps) {
  const orcamentoAtual = toNumber(result.orcamento_mensal_atual)
  const orcamentoNovo = toNumber(result.novo_orcamento)
  const limiteNovo = toNumber(result.novo_limite_diario)
  const limiteAtual = toNumber(result.limite_diario_atual)
  const impactoLimite = Math.max(0, limiteAtual - limiteNovo)
  const impactoMensal = result.simulacao_parcelamento
    ? toNumber(result.simulacao_parcelamento.impacto_mensal)
    : orcamentoAtual - orcamentoNovo
  const orcamentoEstourado = orcamentoAtual <= 0 || orcamentoNovo < 0
  const comprometimento = orcamentoEstourado
    ? 100
    : (impactoMensal / orcamentoAtual) * 100
  const comprometimentoLabel = comprometimento.toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  const barWidth = Math.min(100, Math.max(0, comprometimento))

  return (
    <Modal open title="Simular Gasto" onClose={onClose}>
      <div className="simular-resultado">
        <div className="simular-resultado__impacto">
          <span className="simular-resultado__impacto-label">Impacto Mensal</span>
          <span className="simular-resultado__impacto-value">
            {formatBRL(impactoMensal)}
          </span>
          {parcelas > 1 && result.simulacao_parcelamento && (
            <span className="simular-resultado__impacto-sub">
              {parcelas}x de {formatBRL(result.simulacao_parcelamento.valor_parcela)}
            </span>
          )}
        </div>

        <div className="simular-resultado__grid">
          <DeltaCard
            label="Orçamento Mensal"
            antes={formatBRL(orcamentoAtual)}
            depois={formatBRL(orcamentoNovo)}
            tone="down"
          />
          <DeltaCard
            label="Limite diário"
            antes={formatBRL(limiteAtual)}
            depois={formatBRL(limiteNovo)}
            tone="down"
          />
        </div>

        <div className="simular-resultado__card">
          <div className="simular-resultado__card-header">
            <PiggyBankIcon />
            <span>Impacto no limite diário</span>
          </div>
          <span className="simular-resultado__delta-positive">
            {formatBRL(impactoLimite)}
          </span>
        </div>

        <div className="simular-resultado__card">
          <div className="simular-resultado__card-header">
            <span style={{ display: 'inline-flex', gap: 8, alignItems: 'center' }}>
              <PiggyBankIcon />
              <span>Comprometimento da renda</span>
            </span>
            <span className="simular-resultado__pct">{comprometimentoLabel}%</span>
          </div>
          <div className="simular-resultado__bar">
            <div
              className="simular-resultado__bar-fill"
              style={{
                width: `${barWidth}%`,
                background:
                  comprometimento >= 40 ? '#dc2626' : '#16a34a',
              }}
            />
            <div className="simular-resultado__bar-marker" />
          </div>
          <div className="simular-resultado__bar-labels">
            <span>0%</span>
            <span>40% - Limite</span>
            <span>100%</span>
          </div>
        </div>

        <div className="organism-form__actions">
          <button type="button" className="organism-form__simular" onClick={onNova}>
            <PlusIcon />
            <span>Nova Simulação</span>
          </button>
        </div>
      </div>
    </Modal>
  )
}

function DeltaCard({
  label,
  antes,
  depois,
}: {
  label: string
  antes: string
  depois: string
  tone: 'up' | 'down'
}) {
  return (
    <div className="simular-resultado__card simular-resultado__card--center">
      <div className="simular-resultado__card-header">
        <PiggyBankIcon />
        <span>{label}</span>
      </div>
      <div className="simular-resultado__delta-row">
        <span>{antes}</span>
        <ArrowRightIcon />
      </div>
      <span className="simular-resultado__delta-new">{depois}</span>
    </div>
  )
}
