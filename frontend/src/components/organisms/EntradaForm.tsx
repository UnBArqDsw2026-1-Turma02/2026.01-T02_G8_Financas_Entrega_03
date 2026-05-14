import { useState, type FormEvent } from 'react'
import { isAxiosError } from 'axios'
import { PlusIcon } from '../atoms/Icon'
import { Input } from '../atoms/Input'
import { Select } from '../atoms/Select'
import { FormField } from '../molecules/FormField'
import type {
  Entrada,
  EntradaPayload,
} from '../../domains/finance/types/finance'
import './organisms.css'

export interface EntradaFormProps {
  initial?: Entrada
  onSubmit: (payload: EntradaPayload) => Promise<void>
  onCancel: () => void
}

const RECORRENCIA_OPTIONS = [
  { value: 'nao', label: 'Não Recorrente' },
  { value: 'sim', label: 'Recorrente' },
]

function todayISO(): string {
  return new Date().toISOString().slice(0, 10)
}

export function EntradaForm({ initial, onSubmit }: EntradaFormProps) {
  const [nome, setNome] = useState(initial?.nome ?? '')
  const [valor, setValor] = useState(initial?.valor ?? '')
  const [fonte, setFonte] = useState(initial?.fonte ?? '')
  const [recorrencia, setRecorrencia] = useState(initial?.recorrencia ?? false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const dataDisplay = initial?.data
    ? new Date(initial.data).toISOString().slice(0, 10)
    : todayISO()

  async function handle(e: FormEvent) {
    e.preventDefault()
    if (!nome.trim()) return setError('Nome é obrigatório.')
    const valorNum = Number(valor)
    if (!Number.isFinite(valorNum) || valorNum <= 0)
      return setError('Valor deve ser maior que zero.')
    if (!fonte.trim()) return setError('Fonte é obrigatória.')
    setError(null)
    setSubmitting(true)
    try {
      await onSubmit({
        nome: nome.trim(),
        valor: valorNum.toFixed(2),
        fonte: fonte.trim(),
        recorrencia,
      })
    } catch (err) {
      if (isAxiosError(err) && err.response?.data) {
        const data = err.response.data as Record<string, unknown>
        const messages = Object.values(data).flat().filter(Boolean)
        setError(messages.length ? String(messages[0]) : 'Erro ao salvar.')
      } else {
        setError('Erro ao salvar entrada.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="organism-form" onSubmit={handle}>
      <FormField label="Nome">
        <Input
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          placeholder="Placeholder"
          required
        />
      </FormField>
      <div className="organism-form__row">
        <FormField label="Valor">
          <Input
            type="number"
            step="0.01"
            min="0.01"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            placeholder="Placeholder"
            required
          />
        </FormField>
        <FormField label="Data">
          <Input type="date" value={dataDisplay} readOnly disabled />
        </FormField>
      </div>
      <div className="organism-form__row">
        <FormField label="Fonte">
          <Input
            value={fonte}
            onChange={(e) => setFonte(e.target.value)}
            placeholder="Placeholder"
            required
          />
        </FormField>
        <FormField label="Recorrência">
          <Select
            value={recorrencia ? 'sim' : 'nao'}
            onChange={(e) => setRecorrencia(e.target.value === 'sim')}
            options={RECORRENCIA_OPTIONS}
          />
        </FormField>
      </div>
      {error && <p className="organism-form__error">{error}</p>}
      <div className="organism-form__actions">
        <button type="submit" className="organism-form__submit" disabled={submitting}>
          <PlusIcon />
          <span>{submitting ? 'Salvando…' : initial ? 'Salvar' : 'Criar'}</span>
        </button>
      </div>
    </form>
  )
}
