import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { FileText, Plus, Pencil, Trash2 } from 'lucide-react'
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

interface Posting {
  id: string
  title: string
  description: string
  requirements: string
  visibility: string
  status: string
  requisition: string | null
  requisition_display?: string
  opening_date: string | null
  closing_date: string | null
}

interface Requisition { id: string; requisition_number: string }
interface ApiList<T> { count: number; results: T[] }

const PAGE_SIZE = 15
const VISIBILITY_OPTIONS = ['INTERNAL', 'EXTERNAL', 'BOTH']
const POSTING_STATUSES = ['DRAFT', 'POSTED', 'CLOSED', 'CANCELLED']

const emptyForm = {
  title: '',
  description: '',
  requirements: '',
  visibility: 'EXTERNAL',
  status: 'DRAFT',
  requisition: '',
  opening_date: '',
  closing_date: '',
}

export default function Postings() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Posting | null>(null)
  const [form, setForm] = useState(emptyForm)

  const params = {
    page, page_size: PAGE_SIZE,
    ...(search ? { search } : {}),
    ...(statusFilter ? { status: statusFilter } : {}),
  }

  const { data, isLoading } = useQuery<ApiList<Posting>>({
    queryKey: ['postings', params],
    queryFn: () => api.get('/recruitment/postings/', { params }).then(r => r.data),
  })

  const { data: requisitions } = useQuery<ApiList<Requisition>>({
    queryKey: ['requisitions-all'],
    queryFn: () => api.get('/recruitment/requisitions/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: (body: typeof emptyForm) => api.post('/recruitment/postings/', body),
    onSuccess: () => { toast.success('Posting created'); qc.invalidateQueries({ queryKey: ['postings'] }); closeModal() },
    onError: () => toast.error('Failed to create posting'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) => api.patch(`/recruitment/postings/${id}/`, body),
    onSuccess: () => { toast.success('Posting updated'); qc.invalidateQueries({ queryKey: ['postings'] }); closeModal() },
    onError: () => toast.error('Failed to update posting'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/recruitment/postings/${id}/`),
    onSuccess: () => { toast.success('Posting deleted'); qc.invalidateQueries({ queryKey: ['postings'] }) },
    onError: () => toast.error('Cannot delete posting'),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }
  function openEdit(p: Posting) {
    setEditing(p)
    setForm({
      title: p.title,
      description: p.description ?? '',
      requirements: p.requirements ?? '',
      visibility: p.visibility,
      status: p.status,
      requisition: p.requisition ?? '',
      opening_date: p.opening_date ?? '',
      closing_date: p.closing_date ?? '',
    })
    setModalOpen(true)
  }
  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = {
      ...form,
      requisition: form.requisition || null,
      opening_date: form.opening_date || null,
      closing_date: form.closing_date || null,
    }
    if (editing) update.mutate({ id: editing.id, ...payload } as typeof emptyForm & { id: string })
    else create.mutate(payload as typeof emptyForm)
  }

  function handleDelete(p: Posting) {
    if (!window.confirm(`Delete posting "${p.title}"? This cannot be undone.`)) return
    remove.mutate(p.id)
  }

  const set = (k: keyof typeof emptyForm) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [k]: e.target.value }))

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Job Postings">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Job Postings</CardTitle>
              <Button onClick={openCreate}><Plus size={16} />New Posting</Button>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <div className="flex gap-3">
              <Input placeholder="Search postings…" value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} className="max-w-sm" />
              <Select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1) }} className="w-48">
                <option value="">All Statuses</option>
                {POSTING_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </Select>
            </div>
          </CardContent>

          {isLoading ? <PageSpinner /> : !data?.results.length ? (
            <EmptyState icon={FileText} title="No postings found" description="Create a job posting to attract candidates." action={<Button onClick={openCreate}><Plus size={16} />New Posting</Button>} />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Title</Th><Th>Visibility</Th><Th>Status</Th><Th>Requisition</Th>
                    <Th>Opening Date</Th><Th>Closing Date</Th><Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map(p => (
                    <Tr key={p.id}>
                      <Td className="font-medium">{p.title}</Td>
                      <Td><Badge status={p.visibility} /></Td>
                      <Td><Badge status={p.status} /></Td>
                      <Td className="text-gray-500 font-mono text-xs">{p.requisition_display ?? '—'}</Td>
                      <Td className="text-gray-500">{fmt(p.opening_date)}</Td>
                      <Td className="text-gray-500">{fmt(p.closing_date)}</Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(p)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit"><Pencil size={15} /></button>
                          <button onClick={() => handleDelete(p)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete"><Trash2 size={15} /></button>
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

      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit — ${editing.title}` : 'New Job Posting'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Title" required value={form.title} onChange={set('title')} placeholder="e.g. Senior Software Engineer" />
          <Textarea label="Description" rows={4} value={form.description} onChange={set('description')} placeholder="Describe the role and responsibilities…" />
          <Textarea label="Requirements" rows={3} value={form.requirements} onChange={set('requirements')} placeholder="List required skills and qualifications…" />
          <div className="grid grid-cols-2 gap-4">
            <Select label="Visibility" value={form.visibility} onChange={set('visibility')}>
              {VISIBILITY_OPTIONS.map(v => <option key={v} value={v}>{v}</option>)}
            </Select>
            <Select label="Status" value={form.status} onChange={set('status')}>
              {POSTING_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <Select label="Requisition" value={form.requisition} onChange={set('requisition')}>
            <option value="">— None —</option>
            {requisitions?.results.map(r => <option key={r.id} value={r.id}>{r.requisition_number}</option>)}
          </Select>
          <div className="grid grid-cols-2 gap-4">
            <DatePicker label="Opening Date" value={form.opening_date} onChange={v => setForm(prev => ({ ...prev, opening_date: v }))} />
            <DatePicker label="Closing Date" value={form.closing_date} onChange={v => setForm(prev => ({ ...prev, closing_date: v }))} />
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
