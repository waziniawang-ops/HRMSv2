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
import { Input, Select } from '@/components/ui/Input'
import { DatePicker } from '@/components/ui/DatePicker'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type Assignment = {
  id: string; employee: string; employee_name: string; course: string; course_title: string
  status: string; assigned_by_display: string; due_date: string; trigger: string
}

interface Employee { id: string; employee_number: string; full_name: string }
interface Course { id: string; code: string; title: string }
interface ApiList<T> { count: number; results: T[] }

const PAGE_SIZE = 15
const ASSIGNMENT_STATUSES = ['ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'OVERDUE', 'WAIVED']

const emptyForm = { employee: '', course: '', due_date: '', status: 'ASSIGNED' }

export default function Assignments() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Assignment | null>(null)
  const [form, setForm] = useState(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['assignments', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/learning/assignments/?${params}`).then(r => r.data)
    },
  })

  const { data: employees } = useQuery<ApiList<Employee>>({
    queryKey: ['employees-all'],
    queryFn: () => api.get('/core/employees/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const { data: courses } = useQuery<ApiList<Course>>({
    queryKey: ['courses-all'],
    queryFn: () => api.get('/learning/courses/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: (body: typeof emptyForm) => api.post('/learning/assignments/', body),
    onSuccess: () => { toast.success('Assignment created'); qc.invalidateQueries({ queryKey: ['assignments'] }); closeModal() },
    onError: () => toast.error('Failed to create assignment'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) => api.patch(`/learning/assignments/${id}/`, body),
    onSuccess: () => { toast.success('Assignment updated'); qc.invalidateQueries({ queryKey: ['assignments'] }); closeModal() },
    onError: () => toast.error('Failed to update assignment'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/learning/assignments/${id}/`),
    onSuccess: () => { toast.success('Assignment deleted'); qc.invalidateQueries({ queryKey: ['assignments'] }) },
    onError: () => toast.error('Cannot delete assignment'),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }
  function openEdit(a: Assignment) {
    setEditing(a)
    setForm({ employee: a.employee, course: a.course, due_date: a.due_date ?? '', status: a.status })
    setModalOpen(true)
  }
  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = { ...form, due_date: form.due_date || null }
    if (editing) update.mutate({ id: editing.id, ...payload } as typeof emptyForm & { id: string })
    else create.mutate(payload as typeof emptyForm)
  }

  function handleDelete(a: Assignment) {
    if (!window.confirm(`Delete assignment for "${a.employee_name}"? This cannot be undone.`)) return
    remove.mutate(a.id)
  }

  const set = (k: keyof typeof emptyForm) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [k]: e.target.value }))

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Learning Assignments">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Learning Assignments</CardTitle>
              <Button onClick={openCreate}><Plus size={16} />Assign Course</Button>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <Select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1) }} className="w-44">
              <option value="">All Statuses</option>
              {ASSIGNMENT_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </CardContent>

          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={BookOpen} title="No assignments" description="Learning assignments appear here once courses are assigned." action={<Button onClick={openCreate}><Plus size={16} />Assign Course</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Course</Th><Th>Trigger</Th><Th>Due Date</Th><Th>Assigned By</Th><Th>Status</Th><Th></Th></tr></Thead>
                <Tbody>
                  {data.results.map((a: Assignment) => (
                    <Tr key={a.id}>
                      <Td className="font-medium text-gray-900">{a.employee_name || '—'}</Td>
                      <Td className="text-gray-700">{a.course_title || '—'}</Td>
                      <Td className="text-xs text-gray-500">{a.trigger || 'MANUAL'}</Td>
                      <Td>{fmt(a.due_date)}</Td>
                      <Td className="text-sm text-gray-500">{a.assigned_by_display || '—'}</Td>
                      <Td><Badge status={a.status} /></Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(a)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit"><Pencil size={15} /></button>
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

      <Modal open={modalOpen} onClose={closeModal} title={editing ? 'Edit Assignment' : 'Assign Course'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select label="Employee" required value={form.employee} onChange={set('employee')} disabled={!!editing}>
            <option value="">— Select Employee —</option>
            {employees?.results.map(e => <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>)}
          </Select>
          <Select label="Course" required value={form.course} onChange={set('course')} disabled={!!editing}>
            <option value="">— Select Course —</option>
            {courses?.results.map(c => <option key={c.id} value={c.id}>{c.title} ({c.code})</option>)}
          </Select>
          <div className="grid grid-cols-2 gap-4">
            <DatePicker label="Due Date" value={form.due_date} onChange={v => setForm(prev => ({ ...prev, due_date: v }))} />
            <Select label="Status" value={form.status} onChange={set('status')}>
              {ASSIGNMENT_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Assign'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
