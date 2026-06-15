import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, parseISO } from 'date-fns'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function fmt(date: string | null | undefined, pattern = 'dd MMM yyyy') {
  if (!date) return '—'
  try { return format(parseISO(date), pattern) } catch { return date }
}

export function currency(val: string | number | null | undefined, sym = 'BND$') {
  if (val == null || val === '') return '—'
  return `${sym} ${Number(val).toLocaleString('en-MY', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    ACTIVE: 'bg-green-100 text-green-800',
    APPROVED: 'bg-green-100 text-green-800',
    COMPLETED: 'bg-green-100 text-green-800',
    ACCEPTED: 'bg-green-100 text-green-800',
    PUBLISHED: 'bg-green-100 text-green-800',
    OCCUPIED: 'bg-blue-100 text-blue-800',
    POSTED: 'bg-blue-100 text-blue-800',
    IN_PROGRESS: 'bg-blue-100 text-blue-800',
    PENDING: 'bg-yellow-100 text-yellow-800',
    DRAFT: 'bg-gray-100 text-gray-700',
    VACANT: 'bg-orange-100 text-orange-800',
    INTERVIEW: 'bg-purple-100 text-purple-800',
    SCREENING: 'bg-indigo-100 text-indigo-800',
    OFFER: 'bg-teal-100 text-teal-800',
    REJECTED: 'bg-red-100 text-red-800',
    FAILED: 'bg-red-100 text-red-800',
    CANCELLED: 'bg-red-100 text-red-800',
    PROBATION: 'bg-yellow-100 text-yellow-800',
    SUBMITTED: 'bg-blue-100 text-blue-800',
    YEAR_END: 'bg-purple-100 text-purple-800',
    EXCEEDS: 'bg-green-100 text-green-800',
    MEETS: 'bg-blue-100 text-blue-800',
    LATERAL: 'bg-blue-100 text-blue-800',
    ASSIGNED: 'bg-yellow-100 text-yellow-800',
  }
  return map[status] ?? 'bg-gray-100 text-gray-600'
}
