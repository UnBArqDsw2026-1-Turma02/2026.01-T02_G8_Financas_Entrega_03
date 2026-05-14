import type { Categoria } from '../../domains/finance/types/finance'
import './molecules.css'

export interface CategoriaTagProps {
  categoria: Pick<Categoria, 'nome' | 'cor'>
}

export function CategoriaTag({ categoria }: CategoriaTagProps) {
  return (
    <span className="molecule-categoria-tag">
      <span
        className="molecule-categoria-tag__dot"
        style={{ background: categoria.cor || '#71717a' }}
      />
      {categoria.nome}
    </span>
  )
}
