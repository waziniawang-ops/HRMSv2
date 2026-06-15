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
import { Plus, Timer, Pencil, Trash2 } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type OT = { id: string; employee: string; employee_name: string; date: string; hours_requested: string; hours_approved: string; reason: string; status: string }

const emptyForm = { employee: '', date: '', hours_requested: '', reason: '', status: 'PENDING' }

export default function Overtime() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<OT | null>(null)
  const [employees, setEmployees] = useState<{ id: string; person_display: string; employee_number: string }[]>([])
  const [form, setForm] = useState(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['overtime', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/workforce/overtime/?${params}`).then(r => r.data)
    },
  })

  function loadEmployees() {
    return api.get('/core/employees/?page_size=100').then(r => setEmployees(r.data.results))
  }

  function openCreate() {
    setEditing(null)
    setForm(emptyForm)
    loadEmployees().then(() => setModalOpen(true))
  }

  function openEdit(ot: OT) {
    setEditing(ot)
    setForm({
      employee: ot.employee,
      date: ot.date ?? '',
      hours_requested: String(ot.hours_requested),
      reason: ot.reason ?? '',
      status: ot.status,
    })
    loadEmployees().then(() => setModalOpen(true))
  }

  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/workforce/overtime/', body),
    onSuccess: () => { toast.success('OT request submitted'); qc.invalidateQueries({ queryKey: ['overtime'] }); closeModal() },
    onError: () => toast.error('Failed to submit'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) => api.patch(`/workforce/overtime/${id}/`, body),
    onSuccess: () => { toast.success('OT request updated'); qc.invalidateQueries({ queryKey: ['overtime'] }); closeModal() },
    onError: () => toast.error('Failed to update'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/workforce/overtime/${id}/`),
    onSuccess: () => { toast.success('OT request deleted'); qc.invalidateQueries({ queryKey: ['overtime'] }) },
    onError: () => toast.error('Cannot delete OT request'),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = { ...form, hours_requested: Number(form.hours_requested) }
    if (editing) update.mutate({ id: editing.id, ...payload } as typeof emptyForm & { id: string })
    else create.mutate(payload)
  }

  function handleDelete(ot: OT) {
    if (!window.confirm(`Delete OT request for "${ot.employee_name}"? This cannot be undone.`)) return
    remove.mutate(ot.id)
  }

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Overtime Requests">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-44">
            <option value="">All Statuses</option>
            {['PENDING','APPROVED','REJECTED','CANCELLED'].map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
          <Button onClick={openCreate}><Plus size={16} /> New OT Request</Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Timer} title="No overtime requests" action={<Button onClick={openCreate}><Plus size={16} />New Request</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Date</Th><Th>Requested (h)</Th><Th>Approved (h)</Th><Th>Status</Th><Th>Reason</Th><Th></Th></tr></Thead>
                <Tbody>
                  {data.results.map((ot: OT) => (
                    <Tr key={ot.id}>
                      <Td className="font-medium text-gray-900">{ot.employee_name || '—'}</Td>
                      <Td>{fmt(ot.date)}</Td>
                      <Td className="font-semibold">{ot.hours_requested}h</Td>
                      <Td className="font-semibold text-green-700">{ot.hours_approved ? `${ot.hours_approved}h` : '—'}</Td>
                      <Td><Badge status={ot.status} /></Td>
                      <Td className="text-gray-500 max-w-xs truncate">{ot.reason || '—'}</Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(ot)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit"><Pencil size={15} /></button>
                          <button onClick={() => handleDelete(ot)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete"><Trash2 size={15} /></button>
                        </div>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={closeModal} title={editing ? 'Edit OT Request' : 'New Overtime Request'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select label="Employee *" value={form.employee} onChange={e => setForm(f => ({ ...f, employee: e.target.value }))} required disabled={!!editing}>
            <option value="">Select employee…</option>
            {employees.map(e => <option key={e.id} value={e.id}>{e.person_display || e.employee_number}</option>)}
          </Select>
          <div className="grid grid-cols-2 gap-4">
            <DatePicker label="Date" required value={form.date} onChange={v => setForm(f => ({ ...f, date: v }))} />
            <Input label="Hours Requested *" type="number" step="0.5" value={form.hours_requested} onChange={e => setForm(f => ({ ...f, hours_requested: e.target.value }))} required />
          </div>
          {editing && (
            <Select label="Status" value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
              {['PENDING', 'APPROVED', 'REJECTED', 'CANCELLED'].map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          )}
          <Textarea label="Reason *" value={form.reason} onChange={e => setForm(f => ({ ...f, reason: e.target.value }))} required />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Submit'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
