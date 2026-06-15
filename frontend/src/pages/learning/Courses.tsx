import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { BookOpen, Plus, Pencil, Trash2 } from 'lucide-react'
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
import api from '@/lib/api'
import { useAuth } from '@/context/AuthContext'

type Course = {
  id: string; code: string; title: string; course_type: string
  duration_hours: string; passing_score: number; is_mandatory: boolean; status: string
  description?: string
}

const PAGE_SIZE = 15
const emptyForm = { code: '', title: '', course_type: 'ELEARNING', duration_hours: '', passing_score: '75', is_mandatory: 'false', description: '', status: 'DRAFT' }

export default function Courses() {
  const qc = useQueryClient()
  const { user } = useAuth()
  const canEdit = ['SYSTEM_ADMIN', 'HR_ADMIN', 'LD_OFFICER'].some(r => user?.roles?.includes(r) ?? user?.role === r)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Course | null>(null)
  const [form, setForm] = useState(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['courses', page, search],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (search) params.set('search', search)
      return api.get(`/learning/courses/?${params}`).then(r => r.data)
    },
  })

  const create = useMutation({
    mutationFn: (body: typeof emptyForm) => api.post('/learning/courses/', body),
    onSuccess: () => { toast.success('Course created'); qc.invalidateQueries({ queryKey: ['courses'] }); closeModal() },
    onError: () => toast.error('Failed to create course'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) => api.patch(`/learning/courses/${id}/`, body),
    onSuccess: () => { toast.success('Course updated'); qc.invalidateQueries({ queryKey: ['courses'] }); closeModal() },
    onError: () => toast.error('Failed to update course'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/learning/courses/${id}/`),
    onSuccess: () => { toast.success('Course deleted'); qc.invalidateQueries({ queryKey: ['courses'] }) },
    onError: () => toast.error('Cannot delete — course may have assignments'),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }
  function openEdit(c: Course) {
    setEditing(c)
    setForm({
      code: c.code,
      title: c.title,
      course_type: c.course_type,
      duration_hours: String(c.duration_hours),
      passing_score: String(c.passing_score),
      is_mandatory: c.is_mandatory ? 'true' : 'false',
      description: c.description ?? '',
      status: c.status,
    })
    setModalOpen(true)
  }
  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = { ...form, duration_hours: Number(form.duration_hours), passing_score: Number(form.passing_score), is_mandatory: form.is_mandatory === 'true' }
    if (editing) update.mutate({ id: editing.id, ...payload } as unknown as typeof emptyForm & { id: string })
    else create.mutate(payload as unknown as typeof emptyForm)
  }

  function handleDelete(c: Course) {
    if (!window.confirm(`Delete course "${c.title}"? This cannot be undone.`)) return
    remove.mutate(c.id)
  }

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Courses">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Courses</CardTitle>
              {canEdit && <Button onClick={openCreate}><Plus size={16} />Add Course</Button>}
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <Input placeholder="Search courses…" value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} className="max-w-sm" />
          </CardContent>

          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={BookOpen} title="No courses" action={canEdit ? <Button onClick={openCreate}><Plus size={16} />Add Course</Button> : undefined} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Code</Th><Th>Title</Th><Th>Type</Th><Th>Duration</Th><Th>Pass Score</Th><Th>Mandatory</Th><Th>Status</Th><Th></Th></tr></Thead>
                <Tbody>
                  {data.results.map((c: Course) => (
                    <Tr key={c.id}>
                      <Td><span className="font-mono text-xs font-semibold text-gray-700 bg-gray-100 px-2 py-0.5 rounded">{c.code}</span></Td>
                      <Td className="font-medium text-gray-900 max-w-xs">{c.title}</Td>
                      <Td><Badge status={c.course_type} /></Td>
                      <Td>{c.duration_hours}h</Td>
                      <Td>{c.passing_score}%</Td>
                      <Td>{c.is_mandatory ? <Badge status="OCCUPIED" label="Yes" /> : <span className="text-gray-400 text-sm">No</span>}</Td>
                      <Td><Badge status={c.status} /></Td>
                      <Td>
                        {canEdit && (
                          <div className="flex items-center gap-2 justify-end">
                            <button onClick={() => openEdit(c)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit"><Pencil size={15} /></button>
                            <button onClick={() => handleDelete(c)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete"><Trash2 size={15} /></button>
                          </div>
                        )}
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

      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit — ${editing.title}` : 'Add Course'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="Course Code" required value={form.code} onChange={e => setForm(f => ({ ...f, code: e.target.value }))} placeholder="AWS-SAA-001" />
            <Input label="Title" required value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="AWS Solutions Architect" />
          </div>
          <Textarea label="Description" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
          <div className="grid grid-cols-3 gap-4">
            <Select label="Type" value={form.course_type} onChange={e => setForm(f => ({ ...f, course_type: e.target.value }))}>
              {['ELEARNING', 'CLASSROOM', 'BLENDED', 'VIRTUAL', 'ON_THE_JOB'].map(t => <option key={t} value={t}>{t}</option>)}
            </Select>
            <Input label="Duration (hours)" type="number" step="0.5" required value={form.duration_hours} onChange={e => setForm(f => ({ ...f, duration_hours: e.target.value }))} />
            <Input label="Passing Score (%)" type="number" value={form.passing_score} onChange={e => setForm(f => ({ ...f, passing_score: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Select label="Mandatory" value={form.is_mandatory} onChange={e => setForm(f => ({ ...f, is_mandatory: e.target.value }))}>
              <option value="false">No</option>
              <option value="true">Yes</option>
            </Select>
            <Select label="Status" value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
              {['DRAFT', 'PUBLISHED', 'ARCHIVED'].map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Create Course'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
