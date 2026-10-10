import type { ComponentPropsWithoutRef } from 'react'
import { cn } from '@/lib/cn'

type PanelProps = ComponentPropsWithoutRef<'section'>

export function Panel({ className, ...props }: PanelProps) {
  return (
    <section
      className={cn('rounded-2xl border border-line bg-surface', className)}
      {...props}
    />
  )
}
