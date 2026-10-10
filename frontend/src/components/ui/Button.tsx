import type { ComponentPropsWithoutRef } from 'react'
import { cn } from '@/lib/cn'

type ButtonVariant = 'primary' | 'secondary'

interface ButtonProps extends ComponentPropsWithoutRef<'button'> {
  variant?: ButtonVariant
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'border-brand bg-brand text-black hover:bg-[#ffdf33]',
  secondary: 'border-line bg-transparent text-ink hover:bg-surface-raised',
}

export function Button({ variant = 'secondary', className, type = 'button', ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        'h-9 rounded-lg border px-3.5 text-left text-xs font-medium transition-colors',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand',
        variantClasses[variant],
        className,
      )}
      {...props}
    />
  )
}
