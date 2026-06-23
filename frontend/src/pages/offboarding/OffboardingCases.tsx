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
import { Plus, Search, LogOut } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type OffboardingCase = {
  id: string; employee_name: string; employee_number: string
  status: string; last_working_date: string | null; created_at: string
}

const emptyForm = { employee: '', status: 'INITIATED', notice_period_days: '30', last_working_date: '' }

export default function OffboardingCases() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [employees, setEmployees] = useState<{ id: string; employee_number: string; full_name: string }[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['offboarding-cases', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/offboarding/cases/?${params}`).then(r => r.data)
    },
  })

  function openCreate() {
    setForm(emptyForm)
    api.get('/core/employees/?page_size=200').then(r => setEmployees(r.data.results || []))
    setModalOpen(true)
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/offboarding/cases/', body),
    onSuccess: () => { toast.success('Offboarding case created'); qc.invalidateQueries({ queryKey: ['offboarding-cases'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to create case'),
  })

  const filtered = search
    ? data?.results?.filter((r: OffboardingCase) =>
        r.employee_name?.toLowerCase().includes(search.toLowerCase()) ||
        r.employee_number?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="Offboarding Cases">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-1">
            <div className="relative flex-1 max-w-sm">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search employee..." value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-44">
              <option value="">All Statuses</option>
              {['INITIATED','IN_PROGRESS','PENDING_CLEARANCE','COMPLETED','CANCELLED'].map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
            </Select>
          </div>
          <Button onClick={openCreate}><Plus size={16} /> New Case</Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={LogOut} title="No offboarding cases" action={<Button onClick={openCreate}><Plus size={16} />New Case</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Last Working Date</Th><Th>Status</Th><Th>Initiated</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: OffboardingCase) => (
                    <Tr key={r.id}>
                      <Td className="font-medium">{r.employee_name} <span className="text-gray-400 text-xs">#{r.employee_number}</span></Td>
                      <Td>{r.last_working_date ? fmt(r.last_working_date) : '—'}</Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td className="text-gray-500">{fmt(r.created_at)}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              {!search && <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />}
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Offboarding Case">
        <form onSubmit={e => {
          e.preventDefault()
          const payload: Record<string, unknown> = { ...form, notice_period_days: Number(form.notice_period_days) }
          if (!payload.last_working_date) delete payload.last_working_date
          create.mutate(payload)
        }} className="space-y-4">
          <Select label="Employee *" value={form.employee} onChange={e => setForm(f => ({ ...f, employee: e.target.value }))} required>
            <option value="">Select employee…</option>
            {employees.map(e => <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>)}
          </Select>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Notice Period (days)" type="number" value={form.notice_period_days} onChange={e => setForm(f => ({ ...f, notice_period_days: e.target.value }))} />
            <Input label="Last Working Date" type="date" value={form.last_working_date} onChange={e => setForm(f => ({ ...f, last_working_date: e.target.value }))} />
          </div>
          <Select label="Status" value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
            {['INITIATED','IN_PROGRESS'].map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Create Case</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
