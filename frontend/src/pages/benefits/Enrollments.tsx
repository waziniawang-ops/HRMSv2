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
import { Plus, Search, Heart } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type Enrollment = { id: string; employee: string; employee_name: string; plan: string; plan_name: string; enrollment_date: string; status: string; employee_contribution: string; employer_contribution: string }
const emptyForm = { employee: '', plan: '', enrollment_date: '', employee_contribution: '0', employer_contribution: '0' }

export default function Enrollments() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [employees, setEmployees] = useState<{ id: string; employee_number: string; full_name: string }[]>([])
  const [plans, setPlans] = useState<{ id: string; name: string }[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['benefit-enrollments', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/benefits/benefit-enrollments/?${params}`).then(r => r.data)
    },
  })

  function openCreate() {
    setForm(emptyForm)
    Promise.all([
      api.get('/core/employees/?page_size=200').then(r => setEmployees(r.data.results || [])),
      api.get('/benefits/benefit-plans/?page_size=100&is_active=true').then(r => setPlans(r.data.results || [])),
    ]).then(() => setModalOpen(true))
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/benefits/benefit-enrollments/', body),
    onSuccess: () => { toast.success('Enrollment created'); qc.invalidateQueries({ queryKey: ['benefit-enrollments'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to create enrollment'),
  })

  const filtered = search ? data?.results?.filter((r: Enrollment) => r.employee_name?.toLowerCase().includes(search.toLowerCase())) : data?.results

  return (
    <AppLayout title="Benefit Enrollments">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-1">
            <div className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search employee..." value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-36">
              <option value="">All Statuses</option>
              {['ACTIVE','SUSPENDED','ENDED'].map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <Button onClick={openCreate}><Plus size={16} /> New Enrollment</Button>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={Heart} title="No enrollments" action={<Button onClick={openCreate}><Plus size={16} />New Enrollment</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Plan</Th><Th>Enrolled</Th><Th>Emp. Contribution</Th><Th>Employer Contribution</Th><Th>Status</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: Enrollment) => (
                    <Tr key={r.id}>
                      <Td className="font-medium">{r.employee_name}</Td>
                      <Td>{r.plan_name}</Td>
                      <Td>{fmt(r.enrollment_date)}</Td>
                      <Td>{Number(r.employee_contribution).toLocaleString()}</Td>
                      <Td>{Number(r.employer_contribution).toLocaleString()}</Td>
                      <Td><Badge status={r.status} /></Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              {!search && <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />}
            </>
          )}
        </Card>
      </div>
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Benefit Enrollment">
        <form onSubmit={e => { e.preventDefault(); create.mutate({ ...form, employee_contribution: Number(form.employee_contribution), employer_contribution: Number(form.employer_contribution) }) }} className="space-y-4">
          <Select label="Employee *" value={form.employee} onChange={e => setForm(f => ({ ...f, employee: e.target.value }))} required>
            <option value="">Select employee…</option>
            {employees.map(e => <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>)}
          </Select>
          <Select label="Benefit Plan *" value={form.plan} onChange={e => setForm(f => ({ ...f, plan: e.target.value }))} required>
            <option value="">Select plan…</option>
            {plans.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </Select>
          <Input label="Enrollment Date *" type="date" value={form.enrollment_date} onChange={e => setForm(f => ({ ...f, enrollment_date: e.target.value }))} required />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Employee Contribution" type="number" step="0.01" value={form.employee_contribution} onChange={e => setForm(f => ({ ...f, employee_contribution: e.target.value }))} />
            <Input label="Employer Contribution" type="number" step="0.01" value={form.employer_contribution} onChange={e => setForm(f => ({ ...f, employer_contribution: e.target.value }))} />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Enroll</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
