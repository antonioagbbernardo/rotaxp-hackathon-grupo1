interface UserMessageProps {
  children: string
}

export function UserMessage({ children }: UserMessageProps) {
  return (
    <p className="ml-auto max-w-[85%] rounded-xl bg-surface-raised px-4 py-3.5 text-xs leading-relaxed">
      {children}
    </p>
  )
}
