import ReactDatePicker from 'react-datepicker'
import { cn } from '@/lib/utils'

// Shared input class to match the existing Input component styling
const inputClass = (error?: string, className?: string) =>
  cn(
    'w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors bg-white',
    error ? 'border-red-300 bg-red-50' : 'border-gray-300',
    className
  )

function parseDate(value: string): Date | null {
  if (!value) return null
  const d = new Date(value)
  return isNaN(d.getTime()) ? null : d
}

function toDateStr(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function toDateTimeStr(d: Date): string {
  return `${toDateStr(d)}T${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

interface DatePickerProps {
  label?: string
  value: string
  onChange: (value: string) => void
  required?: boolean
  disabled?: boolean
  placeholder?: string
  error?: string
  className?: string
  minDate?: string
  maxDate?: string
}

export function DatePicker({
  label, value, onChange, required, disabled, placeholder, error, className, minDate, maxDate,
}: DatePickerProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="text-sm font-medium text-gray-700">
          {label}{required && <span className="text-red-500 ml-0.5">*</span>}
        </label>
      )}
      <ReactDatePicker
        selected={parseDate(value)}
        onChange={(d) => d ? onChange(toDateStr(d)) : onChange('')}
        dateFormat="dd/MM/yyyy"
        placeholderText={placeholder ?? 'dd/mm/yyyy'}
        disabled={disabled}
        minDate={minDate ? parseDate(minDate) ?? undefined : undefined}
        maxDate={maxDate ? parseDate(maxDate) ?? undefined : undefined}
        className={inputClass(error, className)}
        wrapperClassName="w-full"
        autoComplete="off"
        showPopperArrow={false}
        popperPlacement="bottom-start"
      />
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  )
}

interface DateTimePickerProps {
  label?: string
  value: string
  onChange: (value: string) => void
  required?: boolean
  disabled?: boolean
  placeholder?: string
  error?: string
  className?: string
}

export function DateTimePicker({
  label, value, onChange, required, disabled, placeholder, error, className,
}: DateTimePickerProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="text-sm font-medium text-gray-700">
          {label}{required && <span className="text-red-500 ml-0.5">*</span>}
        </label>
      )}
      <ReactDatePicker
        selected={parseDate(value)}
        onChange={(d) => d ? onChange(toDateTimeStr(d)) : onChange('')}
        showTimeSelect
        timeFormat="HH:mm"
        timeIntervals={15}
        dateFormat="dd/MM/yyyy HH:mm"
        placeholderText={placeholder ?? 'dd/mm/yyyy HH:mm'}
        disabled={disabled}
        className={inputClass(error, className)}
        wrapperClassName="w-full"
        autoComplete="off"
        showPopperArrow={false}
        popperPlacement="bottom-start"
      />
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  )
}
