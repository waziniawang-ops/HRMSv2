import { cn, statusColor } from '@/lib/utils'

interface BadgeProps {
  status: string
  label?: string
  className?: string
}

export function Badge({ status, label, className }: BadgeProps) {
  return (
    <span className={cn(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
      statusColor(status),
      className
    )}>
      {label ?? status.replace(/_/g, ' ')}
    </span>
  )
}
