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

type Package = { id: string; employee: string; employee_name: string; employee_number: string; effective_date: string; valid_to: string | null; total_ctc: string; currency: string; status: string }

const emptyForm = { employee: '', effective_date: '', total_ctc: '', currency: 'BND' }

export default function Packages() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [employees, setEmployees] = useState<{ id: string; employee_number: string; full_name: string }[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['comp-packages', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/compensation/employee-packages/?${params}`).then(r => r.data)
    },
  })

  function openCreate() {
    setForm(emptyForm)
    api.get('/core/employees/?page_size=200').then(r => setEmployees(r.data.results || []))
    setModalOpen(true)
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/compensation/employee-packages/', body),
    onSuccess: () => { toast.success('Package created'); qc.invalidateQueries({ queryKey: ['comp-packages'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to create package'),
  })

  const approve = useMutation({
    mutationFn: (id: string) => api.post(`/compensation/employee-packages/${id}/approve/`, {}),
    onSuccess: () => { toast.success('Package approved'); qc.invalidateQueries({ queryKey: ['comp-packages'] }) },
    onError: () => toast.error('Approval failed'),
  })

  const filtered = search ? data?.results?.filter((r: Package) => r.employee_name?.toLowerCase().includes(search.toLowerCase())) : data?.results

  return (
    <AppLayout title="Compensation Packages">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-1">
            <div className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search employee..." value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-36">
              <option value="">All Statuses</option>
              {['DRAFT','ACTIVE','SUPERSEDED'].map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <Button onClick={openCreate}><Plus size={16} /> New Package</Button>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={DollarSign} title="No packages" action={<Button onClick={openCreate}><Plus size={16} />New Package</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Effective Date</Th><Th>Valid To</Th><Th>Total CTC</Th><Th>Currency</Th><Th>Status</Th><Th></Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: Package) => (
                    <Tr key={r.id}>
                      <Td><div className="font-medium">{r.employee_name}</div><div className="text-xs text-gray-400">{r.employee_number}</div></Td>
                      <Td>{fmt(r.effective_date)}</Td>
                      <Td>{r.valid_to ? fmt(r.valid_to) : '—'}</Td>
                      <Td className="font-semibold">{Number(r.total_ctc).toLocaleString()}</Td>
                      <Td>{r.currency}</Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td>{r.status === 'DRAFT' && <button onClick={() => approve.mutate(r.id)} className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200">Approve</button>}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              {!search && <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />}
            </>
          )}
        </Card>
      </div>
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Compensation Package">
        <form onSubmit={e => { e.preventDefault(); create.mutate({ ...form, total_ctc: Number(form.total_ctc) }) }} className="space-y-4">
          <Select label="Employee *" value={form.employee} onChange={e => setForm(f => ({ ...f, employee: e.target.value }))} required>
            <option value="">Select employee…</option>
            {employees.map(e => <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>)}
          </Select>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Effective Date *" type="date" value={form.effective_date} onChange={e => setForm(f => ({ ...f, effective_date: e.target.value }))} required />
            <Select label="Currency" value={form.currency} onChange={e => setForm(f => ({ ...f, currency: e.target.value }))}>
              {['BND','USD','SGD','MYR'].map(c => <option key={c} value={c}>{c}</option>)}
            </Select>
          </div>
          <Input label="Total CTC *" type="number" step="0.01" value={form.total_ctc} onChange={e => setForm(f => ({ ...f, total_ctc: e.target.value }))} required />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Create Package</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
