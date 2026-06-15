import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Send, Pencil, Trash2, Plus } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input, Select, Textarea } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

interface Application {
  id: string
  applicant_display: string
  applicant: string
  job_title?: string
  job_posting: string | null
  stage: string
  score: number | null
  notes?: string
  applied_at: string | null
}

interface Posting { id: string; title: string }
interface Applicant { id: string; full_name: string; email: string }
interface ApiList<T> { count: number; results: T[] }

const PAGE_SIZE = 15
const APPLICATION_STAGES = [
  'APPLIED', 'UNDER_REVIEW', 'SHORTLISTED', 'INTERVIEW_SCHEDULED',
  'INTERVIEW_COMPLETED', 'OFFERED', 'OFFER_ACCEPTED', 'ONBOARDING',
  'HIRED', 'REJECTED', 'WITHDRAWN',
]

const emptyForm = { job_posting: '', applicant: '', stage: 'APPLIED', score: '', notes: '' }

export default function Applications() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [stageFilter, setStageFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Application | null>(null)
  const [form, setForm] = useState(emptyForm)

  const params = {
    page, page_size: PAGE_SIZE,
    ...(search ? { search } : {}),
    ...(stageFilter ? { stage: stageFilter } : {}),
  }

  const { data, isLoading } = useQuery<ApiList<Application>>({
    queryKey: ['applications', params],
    queryFn: () => api.get('/recruitment/applications/', { params }).then(r => r.data),
  })

  const { data: postings } = useQuery<ApiList<Posting>>({
    queryKey: ['postings-all'],
    queryFn: () => api.get('/recruitment/postings/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const { data: applicants } = useQuery<ApiList<Applicant>>({
    queryKey: ['applicants-all'],
    queryFn: () => api.get('/recruitment/applicants/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: { id: string; stage: string; score: string; notes: string }) =>
      api.patch(`/recruitment/applications/${id}/`, {
        stage: body.stage,
        score: body.score ? Number(body.score) : null,
        notes: body.notes ?? '',
      }),
    onSuccess: () => { toast.success('Application updated'); qc.invalidateQueries({ queryKey: ['applications'] }); closeModal() },
    onError: () => toast.error('Failed to update application'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/recruitment/applications/${id}/`),
    onSuccess: () => { toast.success('Application deleted'); qc.invalidateQueries({ queryKey: ['applications'] }) },
    onError: () => toast.error('Cannot delete application'),
  })

  function openEdit(a: Application) {
    setEditing(a)
    setForm({ job_posting: a.job_posting ?? '', applicant: a.applicant, stage: a.stage, score: a.score != null ? String(a.score) : '', notes: a.notes ?? '' })
    setModalOpen(true)
  }
  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!editing) return
    update.mutate({ id: editing.id, stage: form.stage, score: form.score, notes: form.notes })
  }

  function handleDelete(a: Application) {
    if (!window.confirm(`Delete this application from "${a.applicant_display}"? This cannot be undone.`)) return
    remove.mutate(a.id)
  }

  const set = (k: keyof typeof emptyForm) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [k]: e.target.value }))

  return (
    <AppLayout title="Applications">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Applications</CardTitle>
              <span className="text-sm text-gray-500">{data ? `${data.count} application${data.count !== 1 ? 's' : ''}` : ''}</span>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <div className="flex gap-3">
              <Input placeholder="Search by applicant name…" value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} className="max-w-sm" />
              <Select value={stageFilter} onChange={e => { setStageFilter(e.target.value); setPage(1) }} className="w-48">
                <option value="">All Stages</option>
                {APPLICATION_STAGES.map(s => <option key={s} value={s}>{s}</option>)}
              </Select>
            </div>
          </CardContent>

          {isLoading ? <PageSpinner /> : !data?.results.length ? (
            <EmptyState icon={Send} title="No applications found" description="No applications match your search criteria." />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr><Th>Applicant</Th><Th>Stage</Th><Th>Score</Th><Th>Applied Date</Th><Th>Posting</Th><Th></Th></tr>
                </Thead>
                <Tbody>
                  {data.results.map(a => (
                    <Tr key={a.id}>
                      <Td className="font-medium">{a.applicant_display}</Td>
                      <Td><Badge status={a.stage} /></Td>
                      <Td>{a.score != null ? a.score : '—'}</Td>
                      <Td className="text-gray-500">{fmt(a.applied_at)}</Td>
                      <Td className="text-gray-500">{a.job_title ?? '—'}</Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(a)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit Stage/Score"><Pencil size={15} /></button>
                          <button onClick={() => handleDelete(a)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete"><Trash2 size={15} /></button>
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

      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit Application — ${editing.applicant_display}` : 'Edit Application'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select label="Stage" value={form.stage} onChange={set('stage')}>
            {APPLICATION_STAGES.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
          </Select>
          <Input label="Score (0–100)" type="number" min={0} max={100} value={form.score} onChange={set('score')} placeholder="e.g. 85" />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea
              value={form.notes}
              onChange={e => setForm(prev => ({ ...prev, notes: e.target.value }))}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="Internal notes about this application…"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={update.isPending}>Save Changes</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
