import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { AxiosError } from 'axios'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input, Select } from '@/components/ui/Input'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Plus, Trash2, Receipt } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type PayrollRun = { id: string; calendar_display: string; period_start: string; period_end: string; status: string }
type Employee = { id: string; employee_number: string; full_name: string }
type PayrollElement = { id: string; code: string; name: string; category: string }
type Line = {
  id: string; payroll_run: string; employee: string; employee_name: string
  element: string; element_display: string; element_category: string
  amount: string; taxable_amount: string; is_deduction: boolean
}

const emptyForm = { employee: '', element: '', amount: '', taxable_amount: '', is_deduction: false }

export default function PayslipLines() {
  const qc = useQueryClient()
  const [runId, setRunId] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)

  const { data: runsData } = useQuery({
    queryKey: ['payroll-runs-for-lines'],
    queryFn: () => api.get('/payroll/payroll-runs/?page_size=100').then(r => r.data),
  })
  const runs: PayrollRun[] = runsData?.results || []
  const effectiveRunId = runId || runs[0]?.id || ''

  const { data: employeesData } = useQuery({
    queryKey: ['employees-for-lines'],
    queryFn: () => api.get('/core/employees/?page_size=500').then(r => r.data),
  })
  const employees: Employee[] = employeesData?.results || []

  const { data: elementsData } = useQuery({
    queryKey: ['elements-for-lines'],
    queryFn: () => api.get('/payroll/payroll-elements/?page_size=200').then(r => r.data),
  })
  const elements: PayrollElement[] = elementsData?.results || []

  const { data: linesData, isLoading } = useQuery({
    queryKey: ['payslip-lines', effectiveRunId],
    queryFn: () => api.get(`/payroll/payslip-lines/?payroll_run=${effectiveRunId}&page_size=500`).then(r => r.data),
    enabled: !!effectiveRunId,
  })
  const lines: Line[] = linesData?.results || []

  function openCreate() {
    setForm(emptyForm)
    setModalOpen(true)
  }

  function errorDetail(e: unknown, fallback: string) {
    const data = (e as AxiosError<Record<string, unknown>>)?.response?.data
    if (!data) return fallback
    const detail = data.detail
    if (typeof detail === 'string') return detail
    const firstField = Object.values(data)[0]
    if (Array.isArray(firstField) && typeof firstField[0] === 'string') return firstField[0]
    return fallback
  }

  const create = useMutation({
    mutationFn: (body: typeof emptyForm) => api.post('/payroll/payslip-lines/', {
      ...body,
      payroll_run: effectiveRunId,
      taxable_amount: body.taxable_amount || 0,
    }),
    onSuccess: () => { toast.success('Line added'); qc.invalidateQueries({ queryKey: ['payslip-lines', effectiveRunId] }); setModalOpen(false) },
    onError: (e: unknown) => toast.error(errorDetail(e, 'Failed to add line')),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/payroll/payslip-lines/${id}/`),
    onSuccess: () => { toast.success('Deleted'); qc.invalidateQueries({ queryKey: ['payslip-lines', effectiveRunId] }) },
    onError: () => toast.error('Cannot delete line'),
  })

  const selectedElement = elements.find(e => e.id === form.element)
  const totalGross = lines.filter(l => ['BASIC', 'ALLOWANCE'].includes(l.element_category)).reduce((s, l) => s + Number(l.amount), 0)
  const totalDeductions = lines.filter(l => l.is_deduction).reduce((s, l) => s + Number(l.amount), 0)

  return (
    <AppLayout title="Payslip Lines">
      <div className="space-y-4">
        <Card>
          <div className="p-4 flex flex-wrap items-center gap-3 justify-between">
            <Select value={effectiveRunId} onChange={e => setRunId(e.target.value)} className="w-80">
              {runs.map(r => (
                <option key={r.id} value={r.id}>
                  {r.calendar_display} — {fmt(r.period_start)} to {fmt(r.period_end)} [{r.status}]
                </option>
              ))}
            </Select>
            <Button onClick={openCreate} disabled={!effectiveRunId}><Plus size={16} /> Add Line</Button>
          </div>
        </Card>

        {lines.length > 0 && (
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <div className="p-4">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Gross (Basic + Allowances)</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{totalGross.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
              </div>
            </Card>
            <Card>
              <div className="p-4">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Total Deductions</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{totalDeductions.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
              </div>
            </Card>
          </div>
        )}

        <Card>
          {isLoading ? <PageSpinner /> : !lines.length ? (
            <EmptyState
              icon={Receipt}
              title="No payslip lines for this run"
              description="Add a line per employee per pay element (basic, allowance, deduction, tax, contribution) before generating payslips."
              action={<Button onClick={openCreate} disabled={!effectiveRunId}><Plus size={16} />Add Line</Button>}
            />
          ) : (
            <Table>
              <Thead><tr><Th>Employee</Th><Th>Element</Th><Th>Category</Th><Th>Amount</Th><Th>Deduction</Th><Th></Th></tr></Thead>
              <Tbody>
                {lines.map(l => (
                  <Tr key={l.id}>
                    <Td className="font-medium">{l.employee_name}</Td>
                    <Td>{l.element_display}</Td>
                    <Td><span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{l.element_category}</span></Td>
                    <Td className="font-semibold">{Number(l.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</Td>
                    <Td>{l.is_deduction ? '✓' : '—'}</Td>
                    <Td>
                      <button onClick={() => window.confirm('Delete this line?') && remove.mutate(l.id)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg">
                        <Trash2 size={15} />
                      </button>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Add Payslip Line">
        <form onSubmit={e => { e.preventDefault(); create.mutate(form) }} className="space-y-4">
          <Select label="Employee *" value={form.employee} onChange={e => setForm(f => ({ ...f, employee: e.target.value }))} required>
            <option value="">Select employee…</option>
            {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.employee_number} — {emp.full_name}</option>)}
          </Select>
          <Select
            label="Element *"
            value={form.element}
            onChange={e => {
              const el = elements.find(x => x.id === e.target.value)
              setForm(f => ({ ...f, element: e.target.value, is_deduction: el?.category === 'DEDUCTION' }))
            }}
            required
          >
            <option value="">Select element…</option>
            {elements.map(el => <option key={el.id} value={el.id}>{el.code} — {el.name} ({el.category})</option>)}
          </Select>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Amount *" type="number" step="0.01" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))} required />
            <Input label="Taxable Amount" type="number" step="0.01" placeholder="defaults to 0" value={form.taxable_amount} onChange={e => setForm(f => ({ ...f, taxable_amount: e.target.value }))} />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_deduction} onChange={e => setForm(f => ({ ...f, is_deduction: e.target.checked }))} /> Is Deduction
          </label>
          {selectedElement && (selectedElement.category === 'TAX' || selectedElement.category === 'CONTRIBUTION') && (
            <p className="text-xs text-gray-500">Tax and contribution amounts are aggregated by category automatically for payslips and GL postings — "Is Deduction" only affects the net pay deduction total.</p>
          )}
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Add Line</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
