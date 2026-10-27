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

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    PENDING: 'bg-warning-50 text-warning-700',
    ACTIVE: 'bg-success-50 text-success-700',
    SUSPENDED: 'bg-danger-50 text-danger-700',
    OFFBOARDED: 'bg-slate-100 text-slate-600',
    PROVISIONING: 'bg-primary-50 text-primary-700',
    FAILED: 'bg-danger-50 text-danger-700',
    NOT_PROVISIONED: 'bg-slate-100 text-slate-500',
    DEPROVISIONING: 'bg-warning-50 text-warning-700',
    DEPROVISION_FAILED: 'bg-danger-50 text-danger-700',
    CORE: 'bg-primary-50 text-primary-700',
    TALENT: 'bg-success-50 text-success-700',
    FINANCE: 'bg-warning-50 text-warning-700',
    OPERATIONS: 'bg-slate-200 text-slate-700',
  }
  return map[status] ?? 'bg-slate-100 text-slate-600'
}

export function apiErrorMessage(error: unknown, fallback: string): string {
  const data = (error as { response?: { data?: unknown } })?.response?.data
  if (!data || typeof data !== 'object') return fallback
  const obj = data as Record<string, unknown>
  if (typeof obj.detail === 'string') return obj.detail
  const parts = Object.entries(obj).map(([field, msgs]) => {
    const text = Array.isArray(msgs) ? msgs.join(' ') : String(msgs)
    return field === 'non_field_errors' ? text : `${field}: ${text}`
  })
  return parts.length ? parts.join(' | ') : fallback
}
