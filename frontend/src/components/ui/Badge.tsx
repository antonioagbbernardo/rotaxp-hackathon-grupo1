import type { ReactNode } from 'react'
import { cn } from '@/lib/cn'

export type BadgeTone = 'neutral' | 'positive' | 'negative' | 'brand'

interface BadgeProps {
  tone?: BadgeTone
  withDot?: boolean
  uppercase?: boolean
  className?: string
  children: ReactNode
}

const toneClasses: Record<BadgeTone, string> = {
  neutral: 'bg-surface-raised text-ink',
  positive: 'bg-positive-soft text-positive',
  negative: 'bg-negative-soft text-negative',
  brand: 'bg-brand-soft text-brand',
}

export function Badge({
  tone = 'neutral',
  withDot = false,
  uppercase = false,
  className,
  children,
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium',
        uppercase && 'tracking-wide uppercase',
        toneClasses[tone],
        className,
      )}
    >
      {withDot && <span aria-hidden className="size-1.5 rounded-full bg-current" />}
      {children}
    </span>
  )
}
