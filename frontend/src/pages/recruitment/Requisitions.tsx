import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { ClipboardList, Plus, Pencil, Trash2 } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input, Select, Textarea } from '@/components/ui/Input'
import { DatePicker } from '@/components/ui/DatePicker'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

interface Requisition {
  id: string
  requisition_number: string
  position: string | null
  position_display?: string
  hiring_reason: string
  status: string
  headcount: number
  target_start_date: string | null
  requested_by: string | null
  requested_by_display?: string
  justification?: string
}

interface Position { id: string; position_code: string; title: string }
interface ApiList<T> { count: number; results: T[] }

const PAGE_SIZE = 15
const HIRING_REASONS = ['REPLACEMENT', 'EXPANSION', 'SUCCESSION_GAP', 'NEW_ROLE']
const REQ_STATUSES = ['DRAFT', 'SUBMITTED', 'CHECKED', 'APPROVED', 'REJECTED', 'CANCELLED']

const emptyForm = {
  position: '',
  hiring_reason: 'NEW_ROLE',
  headcount: '1',
  justification: '',
  target_start_date: '',
  status: 'DRAFT',
}

export default function Requisitions() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Requisition | null>(null)
  const [form, setForm] = useState(emptyForm)

  const params = {
    page, page_size: PAGE_SIZE,
    ...(search ? { search } : {}),
    ...(statusFilter ? { status: statusFilter } : {}),
  }

  const { data, isLoading } = useQuery<ApiList<Requisition>>({
    queryKey: ['requisitions', params],
    queryFn: () => api.get('/recruitment/requisitions/', { params }).then(r => r.data),
  })

  const { data: positions } = useQuery<ApiList<Position>>({
    queryKey: ['positions-all'],
    queryFn: () => api.get('/core/positions/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: (body: typeof emptyForm) => api.post('/recruitment/requisitions/', body),
    onSuccess: () => { toast.success('Requisition created'); qc.invalidateQueries({ queryKey: ['requisitions'] }); closeModal() },
    onError: () => toast.error('Failed to create requisition'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) => api.patch(`/recruitment/requisitions/${id}/`, body),
    onSuccess: () => { toast.success('Requisition updated'); qc.invalidateQueries({ queryKey: ['requisitions'] }); closeModal() },
    onError: () => toast.error('Failed to update requisition'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/recruitment/requisitions/${id}/`),
    onSuccess: () => { toast.success('Requisition deleted'); qc.invalidateQueries({ queryKey: ['requisitions'] }) },
    onError: () => toast.error('Cannot delete — requisition may have linked postings'),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }
  function openEdit(r: Requisition) {
    setEditing(r)
    setForm({
      position: r.position ?? '',
      hiring_reason: r.hiring_reason,
      headcount: String(r.headcount),
      justification: r.justification ?? '',
      target_start_date: r.target_start_date ?? '',
      status: r.status,
    })
    setModalOpen(true)
  }
  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = {
      ...form,
      position: form.position || null,
      headcount: Number(form.headcount),
      target_start_date: form.target_start_date || null,
    }
    if (editing) update.mutate({ id: editing.id, ...payload } as unknown as typeof emptyForm & { id: string })
    else create.mutate(payload as unknown as typeof emptyForm)
  }

  function handleDelete(r: Requisition) {
    if (!window.confirm(`Delete requisition "${r.requisition_number}"? This cannot be undone.`)) return
    remove.mutate(r.id)
  }

  const set = (k: keyof typeof emptyForm) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [k]: e.target.value }))

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Recruitment Requisitions">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recruitment Requisitions</CardTitle>
              <Button onClick={openCreate}><Plus size={16} />New Requisition</Button>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <div className="flex gap-3">
              <Input placeholder="Search requisitions…" value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} className="max-w-sm" />
              <Select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1) }} className="w-48">
                <option value="">All Statuses</option>
                {REQ_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </Select>
            </div>
          </CardContent>

          {isLoading ? <PageSpinner /> : !data?.results.length ? (
            <EmptyState icon={ClipboardList} title="No requisitions found" description="Create a hiring requisition to start the recruitment process." action={<Button onClick={openCreate}><Plus size={16} />New Requisition</Button>} />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Number</Th><Th>Position</Th><Th>Reason</Th><Th>Status</Th>
                    <Th>Headcount</Th><Th>Target Start</Th><Th>Requested By</Th><Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map(r => (
                    <Tr key={r.id}>
                      <Td className="font-mono text-xs">{r.requisition_number}</Td>
                      <Td className="text-gray-500">{r.position_display ?? '—'}</Td>
                      <Td><Badge status={r.hiring_reason} /></Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td>{r.headcount}</Td>
                      <Td className="text-gray-500">{fmt(r.target_start_date)}</Td>
                      <Td className="text-gray-500">{r.requested_by_display ?? '—'}</Td>
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
              <Pagination count={data.count} page={page} pageSize={PAGE_SIZE} onPage={setPage} />
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit — ${editing.requisition_number}` : 'New Requisition'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select label="Position" value={form.position} onChange={set('position')}>
            <option value="">— Select Position —</option>
            {positions?.results.map(p => <option key={p.id} value={p.id}>{p.title} ({p.position_code})</option>)}
          </Select>
          <div className="grid grid-cols-2 gap-4">
            <Select label="Hiring Reason" value={form.hiring_reason} onChange={set('hiring_reason')}>
              {HIRING_REASONS.map(r => <option key={r} value={r}>{r.replace(/_/g, ' ')}</option>)}
            </Select>
            <Input label="Headcount" type="number" min="1" required value={form.headcount} onChange={set('headcount')} />
          </div>
          <Textarea label="Justification" required value={form.justification} onChange={set('justification')} placeholder="Provide business justification for this hire…" rows={3} />
          <div className="grid grid-cols-2 gap-4">
            <DatePicker label="Target Start Date" value={form.target_start_date} onChange={v => setForm(prev => ({ ...prev, target_start_date: v }))} />
            <Select label="Status" value={form.status} onChange={set('status')}>
              {REQ_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Create'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
