import { cn } from '@/lib/utils'
import type { ReactNode } from 'react'

export function Table({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="w-full text-sm">{children}</table>
    </div>
  )
}

export function Thead({ children }: { children: ReactNode }) {
  return <thead className="bg-gray-50 border-b border-gray-200">{children}</thead>
}

export function Tbody({ children }: { children: ReactNode }) {
  return <tbody className="divide-y divide-gray-100">{children}</tbody>
}

export function Th({ children, className }: { children?: ReactNode; className?: string }) {
  return (
    <th className={cn('px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide', className)}>
      {children}
    </th>
  )
}

export function Td({ children, className, onClick }: { children: ReactNode; className?: string; onClick?: (e: React.MouseEvent) => void }) {
  return <td onClick={onClick} className={cn('px-4 py-3 text-gray-700', className)}>{children}</td>
}

export function Tr({ children, className, onClick }: { children: ReactNode; className?: string; onClick?: () => void }) {
  return (
    <tr
      onClick={onClick}
      className={cn('hover:bg-gray-50 transition-colors', onClick && 'cursor-pointer', className)}
    >
      {children}
    </tr>
  )
}
