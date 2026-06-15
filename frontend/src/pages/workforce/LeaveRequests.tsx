import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { Input, Select, Textarea } from '@/components/ui/Input'
import { DatePicker } from '@/components/ui/DatePicker'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Plus, Search, Calendar, Pencil, Trash2 } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type LeaveRequest = {
  id: string; employee: string; leave_type: string
  employee_name: string; leave_type_name: string
  start_date: string; end_date: string; days_requested: string; status: string; reason: string
}

const emptyForm = { employee: '', leave_type: '', start_date: '', end_date: '', days_requested: '', reason: '', status: 'PENDING' }

export default function LeaveRequests() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<LeaveRequest | null>(null)
  const [employees, setEmployees] = useState<{ id: string; employee_number: string; person_display: string }[]>([])
  const [leaveTypes, setLeaveTypes] = useState<{ id: string; name: string }[]>([])
  const [form, setForm] = useState(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['leave-requests', page, search, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/workforce/leave-requests/?${params}`).then(r => r.data)
    },
  })

  function loadDropdowns() {
    return Promise.all([
      api.get('/core/employees/?page_size=100').then(r => r.data.results),
      api.get('/workforce/leave-types/?page_size=100').then(r => r.data.results),
    ]).then(([emps, lts]) => { setEmployees(emps); setLeaveTypes(lts) })
  }

  function openCreate() {
    setEditing(null)
    setForm(emptyForm)
    loadDropdowns().then(() => setModalOpen(true))
  }

  function openEdit(r: LeaveRequest) {
    setEditing(r)
    setForm({
      employee: r.employee,
      leave_type: r.leave_type,
      start_date: r.start_date ?? '',
      end_date: r.end_date ?? '',
      days_requested: String(r.days_requested),
      reason: r.reason ?? '',
      status: r.status,
    })
    loadDropdowns().then(() => setModalOpen(true))
  }

  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/workforce/leave-requests/', body),
    onSuccess: () => { toast.success('Leave request created'); qc.invalidateQueries({ queryKey: ['leave-requests'] }); closeModal() },
    onError: () => toast.error('Failed to create request'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) => api.patch(`/workforce/leave-requests/${id}/`, body),
    onSuccess: () => { toast.success('Request updated'); qc.invalidateQueries({ queryKey: ['leave-requests'] }); closeModal() },
    onError: () => toast.error('Failed to update request'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/workforce/leave-requests/${id}/`),
    onSuccess: () => { toast.success('Request deleted'); qc.invalidateQueries({ queryKey: ['leave-requests'] }) },
    onError: () => toast.error('Cannot delete request'),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = { ...form, days_requested: Number(form.days_requested) }
    if (editing) update.mutate({ id: editing.id, ...payload } as unknown as typeof emptyForm & { id: string })
    else create.mutate(payload)
  }

  function handleDelete(r: LeaveRequest) {
    if (!window.confirm(`Delete leave request for "${r.employee_name}"? This cannot be undone.`)) return
    remove.mutate(r.id)
  }

  const filtered = search
    ? data?.results?.filter((r: LeaveRequest) => r.employee_name?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Leave Requests">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-1">
            <div className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search employee..." value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-40">
              <option value="">All Statuses</option>
              {['PENDING','APPROVED','REJECTED','CANCELLED'].map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <Button onClick={openCreate}><Plus size={16} /> New Request</Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={Calendar} title="No leave requests" action={<Button onClick={openCreate}><Plus size={16} />New Request</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Leave Type</Th><Th>From</Th><Th>To</Th><Th>Days</Th><Th>Status</Th><Th>Reason</Th><Th></Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: LeaveRequest) => (
                    <Tr key={r.id}>
                      <Td className="font-medium text-gray-900">{r.employee_name || '—'}</Td>
                      <Td>{r.leave_type_name || '—'}</Td>
                      <Td>{fmt(r.start_date)}</Td>
                      <Td>{fmt(r.end_date)}</Td>
                      <Td className="font-semibold">{r.days_requested}d</Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td className="text-gray-500 max-w-xs truncate">{r.reason || '—'}</Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(r)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit"><Pencil size={15} /></button>
                          <button onClick={() => handleDelete(r)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete"><Trash2 size={15} /></button>
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

      <Modal open={modalOpen} onClose={closeModal} title={editing ? 'Edit Leave Request' : 'New Leave Request'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select label="Employee *" value={form.employee} onChange={e => setForm(f => ({ ...f, employee: e.target.value }))} required disabled={!!editing}>
            <option value="">Select employee…</option>
            {employees.map(e => <option key={e.id} value={e.id}>{e.person_display || e.employee_number}</option>)}
          </Select>
          <Select label="Leave Type *" value={form.leave_type} onChange={e => setForm(f => ({ ...f, leave_type: e.target.value }))} required disabled={!!editing}>
            <option value="">Select leave type…</option>
            {leaveTypes.map(lt => <option key={lt.id} value={lt.id}>{lt.name}</option>)}
          </Select>
          <div className="grid grid-cols-3 gap-3">
            <DatePicker label="Start Date" required value={form.start_date} onChange={v => setForm(f => ({ ...f, start_date: v }))} />
            <DatePicker label="End Date" required value={form.end_date} onChange={v => setForm(f => ({ ...f, end_date: v }))} />
            <Input label="Days *" type="number" step="0.5" value={form.days_requested} onChange={e => setForm(f => ({ ...f, days_requested: e.target.value }))} required />
          </div>
          {editing && (
            <Select label="Status" value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
              {['PENDING', 'APPROVED', 'REJECTED', 'CANCELLED'].map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          )}
          <Textarea label="Reason" value={form.reason} onChange={e => setForm(f => ({ ...f, reason: e.target.value }))} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Submit Request'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
