import { cn } from '@/lib/utils'
import type { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export function Input({ label, error, className, ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm font-medium text-slate-700">{label}</label>}
      <input
        {...props}
        className={cn(
          'w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors',
          error ? 'border-danger-300 bg-danger-50' : 'border-slate-300 bg-white',
          className
        )}
      />
      {error && <span className="text-xs text-danger-600">{error}</span>}
    </div>
  )
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
}

export function Select({ label, error, className, children, ...props }: SelectProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm font-medium text-slate-700">{label}</label>}
      <select
        {...props}
        className={cn(
          'w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white transition-colors',
          error ? 'border-danger-300' : 'border-slate-300',
          className
        )}
      >
        {children}
      </select>
      {error && <span className="text-xs text-danger-600">{error}</span>}
    </div>
  )
}

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
}

export function Textarea({ label, error, className, ...props }: TextareaProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm font-medium text-slate-700">{label}</label>}
      <textarea
        {...props}
        rows={props.rows ?? 3}
        className={cn(
          'w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none transition-colors',
          error ? 'border-danger-300 bg-danger-50' : 'border-slate-300 bg-white',
          className
        )}
      />
      {error && <span className="text-xs text-danger-600">{error}</span>}
    </div>
  )
}
