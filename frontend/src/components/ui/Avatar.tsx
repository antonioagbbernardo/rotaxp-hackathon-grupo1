import { useState } from 'react'
import { cn } from '@/lib/cn'
import { getInitials } from '@/lib/format'

type AvatarSize = 'sm' | 'md' | 'lg'

interface AvatarProps {
  name: string
  src?: string
  size?: AvatarSize
  className?: string
}

const sizeClasses: Record<AvatarSize, string> = {
  sm: 'size-7 text-[10px]',
  md: 'size-9 text-xs',
  lg: 'size-14 text-base',
}

export function Avatar({ name, src, size = 'md', className }: AvatarProps) {
  const [failed, setFailed] = useState(false)
  if (src && !failed) return <img src={src} alt={name} onError={() => setFailed(true)} className={cn('shrink-0 rounded-full object-cover', sizeClasses[size], className)} />
  return (
    <span
      aria-hidden
      className={cn(
        'inline-flex shrink-0 items-center justify-center rounded-full bg-[#34342f] font-medium text-ink',
        sizeClasses[size],
        className,
      )}
    >
      {getInitials(name)}
    </span>
  )
}
