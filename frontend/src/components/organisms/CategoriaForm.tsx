import { useState, type FormEvent } from 'react'
import { isAxiosError } from 'axios'
import { ColorPicker } from '../atoms/ColorPicker'
import { PlusIcon } from '../atoms/Icon'
import { Input } from '../atoms/Input'
import { Textarea } from '../atoms/Textarea'
import { FormField } from '../molecules/FormField'
import type {
  Categoria,
  CategoriaPayload,
} from '../../domains/finance/types/finance'
import './organisms.css'

export interface CategoriaFormProps {
  initial?: Categoria
  onSubmit: (payload: CategoriaPayload) => Promise<void>
  onCancel: () => void
}

export function CategoriaForm({ initial, onSubmit }: CategoriaFormProps) {
  const [nome, setNome] = useState(initial?.nome ?? '')
  const [descricao, setDescricao] = useState(initial?.descricao ?? '')
  const [cor, setCor] = useState(initial?.cor ?? '#FFA500')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handle(e: FormEvent) {
    e.preventDefault()
    if (!nome.trim()) return setError('Nome é obrigatório.')
    if (!descricao.trim()) return setError('Descrição é obrigatória.')
    if (!cor.trim()) return setError('Cor é obrigatória.')
    setError(null)
    setSubmitting(true)
    try {
      await onSubmit({ nome: nome.trim(), descricao: descricao.trim(), cor })
    } catch (err) {
      if (isAxiosError(err) && err.response?.data) {
        const data = err.response.data as Record<string, unknown>
        const messages = Object.values(data).flat().filter(Boolean)
        setError(messages.length ? String(messages[0]) : 'Erro ao salvar.')
      } else {
        setError('Erro ao salvar categoria.')
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
      <FormField label="Descrição">
        <Textarea
          value={descricao}
          onChange={(e) => setDescricao(e.target.value)}
          placeholder="Placeholder"
          required
        />
      </FormField>
      <FormField label="Cor">
        <ColorPicker value={cor} onChange={setCor} required />
      </FormField>
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
