import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from './Button'

interface PaginationProps {
  count: number
  page: number
  pageSize: number
  onPage: (p: number) => void
}

export function Pagination({ count, page, pageSize, onPage }: PaginationProps) {
  const totalPages = Math.ceil(count / pageSize)
  if (totalPages <= 1) return null
  const from = (page - 1) * pageSize + 1
  const to = Math.min(page * pageSize, count)

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
      <p className="text-sm text-gray-500">
        Showing <span className="font-medium text-gray-900">{from}–{to}</span> of{' '}
        <span className="font-medium text-gray-900">{count}</span> results
      </p>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" onClick={() => onPage(page - 1)} disabled={page === 1}>
          <ChevronLeft size={16} />
        </Button>
        {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
          let p: number
          if (totalPages <= 7) p = i + 1
          else if (page <= 4) p = i + 1
          else if (page >= totalPages - 3) p = totalPages - 6 + i
          else p = page - 3 + i
          return (
            <button
              key={p}
              onClick={() => onPage(p)}
              className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
                p === page ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {p}
            </button>
          )
        })}
        <Button variant="ghost" size="sm" onClick={() => onPage(page + 1)} disabled={page === totalPages}>
          <ChevronRight size={16} />
        </Button>
      </div>
    </div>
  )
}
