import type { ReactNode } from 'react'
import { cn } from '@/lib/cn'

interface DotLabelProps {
  className?: string
  children: ReactNode
}

/** Texto precedido por um marcador circular que herda a cor do texto. */
export function DotLabel({ className, children }: DotLabelProps) {
  return (
    <span className={cn('inline-flex items-center gap-1.5', className)}>
      <span aria-hidden className="size-1 shrink-0 rounded-full bg-current" />
      {children}
    </span>
  )
}
