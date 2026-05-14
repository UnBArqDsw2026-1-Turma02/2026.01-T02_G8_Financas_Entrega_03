import type { SVGProps } from 'react'

type IconProps = SVGProps<SVGSVGElement> & { size?: number }

function base(size: number, rest: SVGProps<SVGSVGElement>) {
  return {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    ...rest,
  }
}

export function HomeIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M3 11l9-8 9 8" />
      <path d="M5 10v10h14V10" />
    </svg>
  )
}

export function TagIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M20 12l-8 8-9-9V3h8z" />
      <circle cx="7.5" cy="7.5" r="1.2" fill="currentColor" />
    </svg>
  )
}

export function ArrowDownIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M12 5v14" />
      <path d="M6 13l6 6 6-6" />
    </svg>
  )
}

export function ArrowUpIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M12 19V5" />
      <path d="M6 11l6-6 6 6" />
    </svg>
  )
}

export function CardIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <rect x="3" y="6" width="18" height="13" rx="2" />
      <path d="M3 10h18" />
    </svg>
  )
}

export function ListIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M8 6h12" />
      <path d="M8 12h12" />
      <path d="M8 18h12" />
      <circle cx="4" cy="6" r="0.8" fill="currentColor" />
      <circle cx="4" cy="12" r="0.8" fill="currentColor" />
      <circle cx="4" cy="18" r="0.8" fill="currentColor" />
    </svg>
  )
}

export function PlugIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M9 3v4" />
      <path d="M15 3v4" />
      <path d="M6 7h12v4a6 6 0 0 1-12 0z" />
      <path d="M12 17v4" />
    </svg>
  )
}

export function PencilIcon({ size = 16, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M4 20h4l10-10-4-4L4 16z" />
      <path d="M13 7l4 4" />
    </svg>
  )
}

export function TrashIcon({ size = 16, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M4 7h16" />
      <path d="M9 7V4h6v3" />
      <path d="M6 7l1 13h10l1-13" />
      <path d="M10 11v6" />
      <path d="M14 11v6" />
    </svg>
  )
}

export function PlusIcon({ size = 16, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M12 5v14" />
      <path d="M5 12h14" />
    </svg>
  )
}

export function UserIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </svg>
  )
}

export function ChevronDownIcon({ size = 16, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M6 9l6 6 6-6" />
    </svg>
  )
}

export function PiggyBankIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M16 4v3.8a6 6 0 0 1 2.66 3.2H20a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1h-1.34a6 6 0 0 1-1.66 2.47V19.5a1.5 1.5 0 0 1-3 0v-.58a6 6 0 0 1-1 .08h-4a6 6 0 0 1-1-.08v.58a1.5 1.5 0 0 1-3 0v-2.03A6 6 0 0 1 9 7h2.5z" />
      <path d="M5.17 8.38a3 3 0 1 1 4.66-1.38" />
      <circle cx="15" cy="11" r="0.8" fill="currentColor" stroke="none" />
    </svg>
  )
}

export function ArrowRightIcon({ size = 14, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M5 12h14" />
      <path d="M13 6l6 6-6 6" />
    </svg>
  )
}

export function ChevronsRightIcon({ size = 16, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M6 6l6 6-6 6" />
      <path d="M13 6l6 6-6 6" />
    </svg>
  )
}

export function SearchIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <circle cx="11" cy="11" r="7" />
      <path d="M20 20l-3.5-3.5" />
    </svg>
  )
}

export function FilterIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M3 5h18" />
      <path d="M6 12h12" />
      <path d="M10 19h4" />
    </svg>
  )
}

export function LockIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </svg>
  )
}

export function CartIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M3 4h2l2 12h11l2-8H6" />
      <circle cx="9" cy="20" r="1.4" fill="currentColor" stroke="none" />
      <circle cx="17" cy="20" r="1.4" fill="currentColor" stroke="none" />
    </svg>
  )
}

export function ReceiptIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M5 3h14v18l-3-2-2 2-2-2-2 2-2-2-3 2z" />
      <path d="M8 8h8" />
      <path d="M8 12h8" />
      <path d="M8 16h5" />
    </svg>
  )
}

export function PieChartIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M12 3a9 9 0 1 0 9 9h-9z" />
      <path d="M12 3v9h9a9 9 0 0 0-9-9z" />
    </svg>
  )
}

export function TrendingUpIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M3 17l6-6 4 4 8-8" />
      <path d="M14 7h7v7" />
    </svg>
  )
}

export function TargetIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" />
    </svg>
  )
}

export function CalendarIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 9h18" />
      <path d="M8 3v4" />
      <path d="M16 3v4" />
    </svg>
  )
}

export function SlidersIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M4 6h10" />
      <path d="M18 6h2" />
      <path d="M4 12h2" />
      <path d="M10 12h10" />
      <path d="M4 18h12" />
      <path d="M20 18h0" />
      <circle cx="16" cy="6" r="2" />
      <circle cx="8" cy="12" r="2" />
      <circle cx="18" cy="18" r="2" />
    </svg>
  )
}

export function WalletIcon({ size = 18, ...rest }: IconProps) {
  return (
    <svg {...base(size, rest)}>
      <path d="M3 7a2 2 0 0 1 2-2h12v4" />
      <rect x="3" y="7" width="18" height="13" rx="2" />
      <path d="M17 13h3" />
    </svg>
  )
}
