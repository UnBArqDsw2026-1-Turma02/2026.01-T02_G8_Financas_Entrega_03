import { useMemo, useState, type FormEvent } from 'react'
import { isAxiosError } from 'axios'
import { PlusIcon } from '../atoms/Icon'
import { Input } from '../atoms/Input'
import { Select } from '../atoms/Select'
import { FormField } from '../molecules/FormField'
import {
  PAGAMENTO_OPTIONS,
  TIPO_GASTO_OPTIONS,
  type Categoria,
  type Pagamento,
  type Saida,
  type SaidaPayload,
  type TipoGasto,
} from '../../domains/finance/types/finance'
import './organisms.css'

export interface SaidaFormProps {
  initial?: Saida
  categorias: Categoria[]
  onSubmit: (payload: SaidaPayload) => Promise<void>
  onCancel: () => void
  onRequestSimular?: (valor: string, nome: string) => void
}

function todayISO(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function buildDataISO(dateStr: string): string {
  const [y, m, d] = dateStr.split('-').map(Number)
  const now = new Date()
  const dt = new Date(
    y,
    m - 1,
    d,
    now.getHours(),
    now.getMinutes(),
    now.getSeconds(),
  )
  return dt.toISOString()
}

function CalendarIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 10h18" />
      <path d="M8 3v4" />
      <path d="M16 3v4" />
    </svg>
  )
}

export function SaidaForm({
  initial,
  categorias,
  onSubmit,
  onRequestSimular,
}: SaidaFormProps) {
  const [nome, setNome] = useState(initial?.nome ?? '')
  const [valor, setValor] = useState(initial?.valor ?? '')
  const [categoria, setCategoria] = useState(initial?.categoria ?? '')
  const [pagamento, setPagamento] = useState<Pagamento | ''>(initial?.pagamento ?? '')
  const [tipoGasto, setTipoGasto] = useState<TipoGasto | ''>(
    initial?.tipo_gasto ?? '',
  )
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [data, setData] = useState(
    initial?.data ? new Date(initial.data).toISOString().slice(0, 10) : todayISO(),
  )

  const categoriaSelecionada = useMemo(
    () => categorias.find((c) => c.id === categoria),
    [categorias, categoria],
  )

  async function handle(e: FormEvent) {
    e.preventDefault()
    if (!nome.trim()) return setError('Nome é obrigatório.')
    const valorNum = Number(valor)
    if (!Number.isFinite(valorNum) || valorNum <= 0)
      return setError('Valor deve ser maior que zero.')
    if (!categoria) return setError('Selecione uma categoria.')
    if (!pagamento) return setError('Selecione a forma de pagamento.')
    if (!tipoGasto) return setError('Selecione o tipo de gasto.')
    if (!data) return setError('Data é obrigatória.')
    setError(null)
    setSubmitting(true)
    try {
      await onSubmit({
        nome: nome.trim(),
        valor: valorNum.toFixed(2),
        categoria,
        pagamento,
        tipo_gasto: tipoGasto,
        data: buildDataISO(data),
      })
    } catch (err) {
      if (isAxiosError(err) && err.response?.data) {
        const data = err.response.data as Record<string, unknown>
        const messages = Object.values(data).flat().filter(Boolean)
        setError(messages.length ? String(messages[0]) : 'Erro ao salvar.')
      } else {
        setError('Erro ao salvar saída.')
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
        <FormField
          label="Categoria"
          hint={categorias.length === 0 ? 'Cadastre uma categoria primeiro.' : undefined}
        >
          <div className="categoria-select">
            <span
              className="categoria-select__dot"
              style={{ background: categoriaSelecionada?.cor || '#FFA500' }}
            />
            <select
              className="categoria-select__native"
              value={categoria}
              onChange={(e) => setCategoria(e.target.value)}
              required
            >
              <option value="" disabled>
                Selecione uma categoria...
              </option>
              {categorias.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </div>
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
            <Input
              type="date"
              value={data}
              onChange={(e) => setData(e.target.value)}
              required
            />
          </FormField>
        </div>
        <div className="organism-form__row">
          <FormField label="Tipo de Gasto">
            <Select
              value={tipoGasto}
              onChange={(e) => setTipoGasto(e.target.value as TipoGasto)}
              options={TIPO_GASTO_OPTIONS}
              placeholder="Placeholder"
              required
            />
          </FormField>
          <FormField label="Meio de Pagamento">
            <Select
              value={pagamento}
              onChange={(e) => setPagamento(e.target.value as Pagamento)}
              options={PAGAMENTO_OPTIONS}
              placeholder="Placeholder"
              required
            />
          </FormField>
        </div>
        {error && <p className="organism-form__error">{error}</p>}
      <div className="organism-form__actions">
        {onRequestSimular && (
          <button
            type="button"
            className="organism-form__simular"
            onClick={() => onRequestSimular(valor, nome)}
          >
            <CalendarIcon />
            <span>Simular Gasto</span>
          </button>
        )}
        <button
          type="submit"
          className="organism-form__submit"
          disabled={submitting || categorias.length === 0}
        >
          <PlusIcon />
          <span>{submitting ? 'Salvando…' : initial ? 'Salvar' : 'Criar'}</span>
        </button>
      </div>
    </form>
  )
}
