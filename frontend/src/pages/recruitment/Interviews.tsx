import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Video, Plus, Pencil, Trash2 } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input, Select } from '@/components/ui/Input'
import { DateTimePicker } from '@/components/ui/DatePicker'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import api from '@/lib/api'

interface Interview {
  id: string
  application: string
  application_display: string
  interview_type: string
  status: string
  scheduled_at: string
  location_or_link: string
  round_number: number
  panel_display: string
  notes?: string
}

interface Application { id: string; applicant_display?: string; job_title?: string }
interface ApiList<T> { count: number; results: T[] }

const PAGE_SIZE = 15
const INTERVIEW_TYPES = ['VIDEO', 'PHONE', 'IN_PERSON', 'PANEL']
const INTERVIEW_STATUSES = ['SCHEDULED', 'COMPLETED', 'CANCELLED', 'NO_SHOW']

const emptyForm = {
  application: '',
  interview_type: 'VIDEO',
  status: 'SCHEDULED',
  scheduled_at: '',
  location_or_link: '',
  round_number: '1',
  notes: '',
}

export default function Interviews() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Interview | null>(null)
  const [form, setForm] = useState(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['interviews', page, typeFilter, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (typeFilter) params.set('interview_type', typeFilter)
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/recruitment/interviews/?${params}`).then(r => r.data)
    },
  })

  const { data: applications } = useQuery<ApiList<Application>>({
    queryKey: ['applications-all'],
    queryFn: () => api.get('/recruitment/applications/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: (body: typeof emptyForm) => api.post('/recruitment/interviews/', body),
    onSuccess: () => { toast.success('Interview scheduled'); qc.invalidateQueries({ queryKey: ['interviews'] }); closeModal() },
    onError: () => toast.error('Failed to schedule interview'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) => api.patch(`/recruitment/interviews/${id}/`, body),
    onSuccess: () => { toast.success('Interview updated'); qc.invalidateQueries({ queryKey: ['interviews'] }); closeModal() },
    onError: () => toast.error('Failed to update interview'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/recruitment/interviews/${id}/`),
    onSuccess: () => { toast.success('Interview deleted'); qc.invalidateQueries({ queryKey: ['interviews'] }) },
    onError: () => toast.error('Cannot delete interview'),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }
  function openEdit(iv: Interview) {
    setEditing(iv)
    setForm({
      application: iv.application,
      interview_type: iv.interview_type,
      status: iv.status,
      scheduled_at: iv.scheduled_at ? iv.scheduled_at.slice(0, 16) : '',
      location_or_link: iv.location_or_link ?? '',
      round_number: String(iv.round_number),
      notes: iv.notes ?? '',
    })
    setModalOpen(true)
  }
  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = { ...form, round_number: Number(form.round_number) }
    if (editing) update.mutate({ id: editing.id, ...payload } as typeof emptyForm & { id: string })
    else create.mutate(payload as typeof emptyForm)
  }

  function handleDelete(iv: Interview) {
    if (!window.confirm(`Delete this interview? This cannot be undone.`)) return
    remove.mutate(iv.id)
  }

  const set = (k: keyof typeof emptyForm) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [k]: e.target.value }))

  function fmtDatetime(dt: string) {
    if (!dt) return '—'
    try { return new Date(dt).toLocaleString('en-MY', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) }
    catch { return dt }
  }

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Interviews">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex gap-3">
            <Select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className="w-40">
              <option value="">All Types</option>
              {INTERVIEW_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </Select>
            <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-44">
              <option value="">All Statuses</option>
              {INTERVIEW_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <Button onClick={openCreate}><Plus size={16} />Schedule Interview</Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Video} title="No interviews scheduled" description="Interviews appear here once applications are shortlisted." action={<Button onClick={openCreate}><Plus size={16} />Schedule Interview</Button>} />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr><Th>Application</Th><Th>Type</Th><Th>Round</Th><Th>Scheduled</Th><Th>Location / Link</Th><Th>Status</Th><Th></Th></tr>
                </Thead>
                <Tbody>
                  {data.results.map((iv: Interview) => (
                    <Tr key={iv.id}>
                      <Td className="font-medium text-gray-900">{iv.application_display || '—'}</Td>
                      <Td><Badge status={iv.interview_type} /></Td>
                      <Td className="text-center font-semibold text-gray-600">R{iv.round_number}</Td>
                      <Td className="text-sm text-gray-700">{fmtDatetime(iv.scheduled_at)}</Td>
                      <Td className="text-sm text-blue-600 max-w-xs truncate">{iv.location_or_link || '—'}</Td>
                      <Td><Badge status={iv.status} /></Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(iv)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit"><Pencil size={15} /></button>
                          <button onClick={() => handleDelete(iv)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete"><Trash2 size={15} /></button>
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

      <Modal open={modalOpen} onClose={closeModal} title={editing ? 'Edit Interview' : 'Schedule Interview'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select label="Application" required value={form.application} onChange={set('application')} disabled={!!editing}>
            <option value="">— Select Application —</option>
            {applications?.results.map(a => <option key={a.id} value={a.id}>{a.applicant_display ?? a.id}</option>)}
          </Select>
          <div className="grid grid-cols-2 gap-4">
            <Select label="Interview Type" value={form.interview_type} onChange={set('interview_type')}>
              {INTERVIEW_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </Select>
            <Select label="Status" value={form.status} onChange={set('status')}>
              {INTERVIEW_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <DateTimePicker label="Scheduled At" required value={form.scheduled_at} onChange={v => setForm(prev => ({ ...prev, scheduled_at: v }))} />
            <Input label="Round Number" type="number" min={1} value={form.round_number} onChange={set('round_number')} />
          </div>
          <Input label="Location / Link" value={form.location_or_link} onChange={set('location_or_link')} placeholder="e.g. Zoom link or Room 101" />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} rows={2} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Schedule'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
