import { useEffect, useRef, useState, type ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import {
  ChevronDownIcon,
  HomeIcon,
  ArrowDownIcon,
  ArrowUpIcon,
  CardIcon,
  ListIcon,
  PlugIcon,
  TagIcon,
  UserIcon,
} from '../atoms/Icon'
import { useAuth } from '../../domains/auth/hooks/useAuth'
import './app-shell.css'

interface NavItem {
  to: string
  label: string
  icon: ReactNode
  end?: boolean
}

const NAV: NavItem[] = [
  { to: '/', label: 'Home', icon: <HomeIcon />, end: true },
  { to: '/categorias', label: 'Categorias', icon: <TagIcon /> },
  { to: '/entradas', label: 'Entradas', icon: <ArrowDownIcon /> },
  { to: '/saidas', label: 'Saídas', icon: <ArrowUpIcon /> },
  { to: '/parcelamentos', label: 'Parcelamentos', icon: <CardIcon /> },
  { to: '/extrato', label: 'Extrato', icon: <ListIcon /> },
  { to: '/integracoes', label: 'Integrações', icon: <PlugIcon /> },
]

function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    window.addEventListener('mousedown', onClick)
    return () => window.removeEventListener('mousedown', onClick)
  }, [open])

  return (
    <div className="user-menu" ref={ref}>
      <button
        type="button"
        className="user-menu__trigger"
        onClick={() => setOpen((v) => !v)}
      >
        <UserIcon />
        <span>{user?.username ?? 'usuário'}</span>
        <ChevronDownIcon />
      </button>
      {open && (
        <div className="user-menu__dropdown">
          <button type="button" onClick={logout} className="user-menu__item">
            Sair
          </button>
        </div>
      )}
    </div>
  )
}

export interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <aside className="app-shell__sidebar">
        <div className="app-shell__brand">
          <span className="app-shell__brand-logo" />
          <span className="app-shell__brand-name">Finanças</span>
        </div>
        <nav className="app-shell__nav">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `app-shell__nav-item${isActive ? ' app-shell__nav-item--active' : ''}`
              }
            >
              <span className="app-shell__nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="app-shell__main">
        <header className="app-shell__topbar">
          <UserMenu />
        </header>
        <div className="app-shell__content">{children}</div>
      </div>
    </div>
  )
}
