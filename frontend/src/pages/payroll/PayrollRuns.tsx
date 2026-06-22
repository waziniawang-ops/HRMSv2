import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { Input, Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Plus, Search, DollarSign } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type PayrollRun = {
  id: string; calendar: string; calendar_display: string
  period_start: string; period_end: string; status: string
  pay_date: string | null; total_gross: string | null
  total_deductions: string | null; total_net: string | null
  employee_count: number
}

const emptyForm = { calendar: '', period_start: '', period_end: '', pay_date: '' }

export default function PayrollRuns() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [calendars, setCalendars] = useState<{ id: string; name: string }[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['payroll-runs', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/payroll/payroll-runs/?${params}`).then(r => r.data)
    },
  })

  function openCreate() {
    setForm(emptyForm)
    api.get('/payroll/payroll-calendars/?page_size=100').then(r => setCalendars(r.data.results || []))
    setModalOpen(true)
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/payroll/payroll-runs/', body),
    onSuccess: () => { toast.success('Payroll run created'); qc.invalidateQueries({ queryKey: ['payroll-runs'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to create payroll run'),
  })

  const doAction = useMutation({
    mutationFn: ({ id, action }: { id: string; action: string }) => api.post(`/payroll/payroll-runs/${id}/${action}/`, {}),
    onSuccess: () => { toast.success('Action completed'); qc.invalidateQueries({ queryKey: ['payroll-runs'] }) },
    onError: () => toast.error('Action failed'),
  })

  const filtered = search
    ? data?.results?.filter((r: PayrollRun) => r.calendar_display?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="Payroll Runs">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-1">
            <div className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search calendar..." value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-40">
              <option value="">All Statuses</option>
              {['DRAFT','PROCESSING','LOCKED','APPROVED','PAID'].map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <Button onClick={openCreate}><Plus size={16} /> New Run</Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={DollarSign} title="No payroll runs" action={<Button onClick={openCreate}><Plus size={16} />New Run</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Calendar</Th><Th>Period Start</Th><Th>Period End</Th><Th>Pay Date</Th><Th>Employees</Th><Th>Gross</Th><Th>Net</Th><Th>Status</Th><Th></Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: PayrollRun) => (
                    <Tr key={r.id}>
                      <Td className="font-medium">{r.calendar_display}</Td>
                      <Td>{fmt(r.period_start)}</Td>
                      <Td>{fmt(r.period_end)}</Td>
                      <Td>{r.pay_date ? fmt(r.pay_date) : '—'}</Td>
                      <Td>{r.employee_count}</Td>
                      <Td>{r.total_gross ? Number(r.total_gross).toLocaleString() : '—'}</Td>
                      <Td className="font-semibold">{r.total_net ? Number(r.total_net).toLocaleString() : '—'}</Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td>
                        <div className="flex items-center gap-1 justify-end">
                          {r.status === 'DRAFT' && <button onClick={() => doAction.mutate({ id: r.id, action: 'lock_run' })} className="text-xs px-2 py-1 bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200">Lock</button>}
                          {r.status === 'LOCKED' && <button onClick={() => doAction.mutate({ id: r.id, action: 'submit_for_approval' })} className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200">Submit</button>}
                          {r.status === 'SUBMITTED' && <button onClick={() => doAction.mutate({ id: r.id, action: 'approve' })} className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200">Approve</button>}
                        </div>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              {!search && <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />}
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Payroll Run">
        <form onSubmit={e => { e.preventDefault(); create.mutate(form) }} className="space-y-4">
          <Select label="Pay Calendar *" value={form.calendar} onChange={e => setForm(f => ({ ...f, calendar: e.target.value }))} required>
            <option value="">Select calendar…</option>
            {calendars.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </Select>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Period Start *" type="date" value={form.period_start} onChange={e => setForm(f => ({ ...f, period_start: e.target.value }))} required />
            <Input label="Period End *" type="date" value={form.period_end} onChange={e => setForm(f => ({ ...f, period_end: e.target.value }))} required />
          </div>
          <Input label="Pay Date" type="date" value={form.pay_date} onChange={e => setForm(f => ({ ...f, pay_date: e.target.value }))} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Create Run</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
