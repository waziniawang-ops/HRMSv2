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
import { Plus, ArrowRightLeft, Pencil, Trash2 } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type Transfer = {
  id: string; employee: string; employee_name: string; movement_type: string
  from_position: string | null; to_position: string
  from_grade: string | null; to_grade: string | null
  from_position_title: string; to_position_title: string
  effective_date: string; status: string; reason: string
}

const emptyForm = {
  employee: '', from_position: '', to_position: '', from_grade: '', to_grade: '',
  movement_type: 'TRANSFER', effective_date: '', reason: '', status: 'PENDING',
}

export default function Transfers() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Transfer | null>(null)
  const [employees, setEmployees] = useState<{ id: string; person_display: string; employee_number: string }[]>([])
  const [positions, setPositions] = useState<{ id: string; title: string; position_code: string }[]>([])
  const [grades, setGrades] = useState<{ id: string; grade_code: string; grade_name: string }[]>([])
  const [form, setForm] = useState(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['transfers', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/workforce/transfers/?${params}`).then(r => r.data)
    },
  })

  function loadDropdowns() {
    return Promise.all([
      api.get('/core/employees/?page_size=200').then(r => r.data.results),
      api.get('/core/positions/?page_size=200').then(r => r.data.results),
      api.get('/core/grades/?page_size=50').then(r => r.data.results),
    ]).then(([emps, pos, grd]) => { setEmployees(emps); setPositions(pos); setGrades(grd) })
  }

  function openCreate() {
    setEditing(null)
    setForm(emptyForm)
    loadDropdowns().then(() => setModalOpen(true))
  }

  function openEdit(t: Transfer) {
    setEditing(t)
    setForm({
      employee: t.employee,
      from_position: t.from_position ?? '',
      to_position: t.to_position,
      from_grade: t.from_grade ?? '',
      to_grade: t.to_grade ?? '',
      movement_type: t.movement_type,
      effective_date: t.effective_date ?? '',
      reason: t.reason ?? '',
      status: t.status,
    })
    loadDropdowns().then(() => setModalOpen(true))
  }

  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/workforce/transfers/', body),
    onSuccess: () => { toast.success('Transfer initiated'); qc.invalidateQueries({ queryKey: ['transfers'] }); closeModal() },
    onError: () => toast.error('Failed to create transfer'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) => api.patch(`/workforce/transfers/${id}/`, body),
    onSuccess: () => { toast.success('Transfer updated'); qc.invalidateQueries({ queryKey: ['transfers'] }); closeModal() },
    onError: () => toast.error('Failed to update transfer'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/workforce/transfers/${id}/`),
    onSuccess: () => { toast.success('Transfer deleted'); qc.invalidateQueries({ queryKey: ['transfers'] }) },
    onError: () => toast.error('Cannot delete transfer'),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = {
      ...form,
      from_position: form.from_position || null,
      from_grade: form.from_grade || null,
      to_grade: form.to_grade || null,
    }
    if (editing) update.mutate({ id: editing.id, ...payload } as unknown as typeof emptyForm & { id: string })
    else create.mutate(payload)
  }

  function handleDelete(t: Transfer) {
    if (!window.confirm(`Delete transfer for "${t.employee_name}"? This cannot be undone.`)) return
    remove.mutate(t.id)
  }

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Transfers & Movements">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-44">
            <option value="">All Statuses</option>
            {['PENDING','APPROVED','REJECTED','CANCELLED'].map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
          <Button onClick={openCreate}><Plus size={16} /> Initiate Transfer</Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={ArrowRightLeft} title="No transfers" description="Transfers, promotions and lateral movements appear here" action={<Button onClick={openCreate}><Plus size={16} />Initiate</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Type</Th><Th>From</Th><Th>To</Th><Th>Effective</Th><Th>Status</Th><Th></Th></tr></Thead>
                <Tbody>
                  {data.results.map((t: Transfer) => (
                    <Tr key={t.id}>
                      <Td className="font-medium text-gray-900">{t.employee_name || '—'}</Td>
                      <Td><Badge status={t.movement_type} /></Td>
                      <Td className="text-gray-600">{t.from_position_title || '—'}</Td>
                      <Td className="text-gray-900 font-medium">{t.to_position_title || '—'}</Td>
                      <Td>{fmt(t.effective_date)}</Td>
                      <Td><Badge status={t.status} /></Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(t)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit"><Pencil size={15} /></button>
                          <button onClick={() => handleDelete(t)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete"><Trash2 size={15} /></button>
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

      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit Transfer — ${editing.employee_name}` : 'Initiate Transfer'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Select label="Employee *" value={form.employee} onChange={e => setForm(f => ({ ...f, employee: e.target.value }))} required disabled={!!editing}>
              <option value="">Select employee…</option>
              {employees.map(e => <option key={e.id} value={e.id}>{e.person_display || e.employee_number}</option>)}
            </Select>
            <Select label="Movement Type *" value={form.movement_type} onChange={e => setForm(f => ({ ...f, movement_type: e.target.value }))}>
              {['TRANSFER','PROMOTION','DEMOTION','LATERAL','SECONDMENT'].map(m => <option key={m} value={m}>{m}</option>)}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Select label="From Position" value={form.from_position} onChange={e => setForm(f => ({ ...f, from_position: e.target.value }))}>
              <option value="">Select position…</option>
              {positions.map(p => <option key={p.id} value={p.id}>{p.title} ({p.position_code})</option>)}
            </Select>
            <Select label="To Position *" value={form.to_position} onChange={e => setForm(f => ({ ...f, to_position: e.target.value }))} required>
              <option value="">Select position…</option>
              {positions.map(p => <option key={p.id} value={p.id}>{p.title} ({p.position_code})</option>)}
            </Select>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <Select label="From Grade" value={form.from_grade} onChange={e => setForm(f => ({ ...f, from_grade: e.target.value }))}>
              <option value="">Select…</option>
              {grades.map(g => <option key={g.id} value={g.id}>{g.grade_code} – {g.grade_name}</option>)}
            </Select>
            <Select label="To Grade" value={form.to_grade} onChange={e => setForm(f => ({ ...f, to_grade: e.target.value }))}>
              <option value="">Select…</option>
              {grades.map(g => <option key={g.id} value={g.id}>{g.grade_code} – {g.grade_name}</option>)}
            </Select>
            <DatePicker label="Effective Date" required value={form.effective_date} onChange={v => setForm(f => ({ ...f, effective_date: v }))} />
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
