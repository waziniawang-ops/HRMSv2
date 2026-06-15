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
import { Input, Select } from '@/components/ui/Input'
import { DatePicker } from '@/components/ui/DatePicker'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

interface Assignment {
  id: string
  employee: string
  employee_display: string
  employee_number: string
  position: string
  position_display: string
  org_unit: string
  org_unit_display: string
  grade: string
  grade_display: string
  manager: string | null
  manager_display: string | null
  is_primary: boolean
  valid_from: string
  valid_to: string | null
}

interface Employee { id: string; employee_number: string; full_name: string }
interface Position { id: string; position_code: string; title: string }
interface OrgUnit { id: string; code: string; name: string }
interface Grade { id: string; grade_code: string; grade_name: string }
interface ApiList<T> { count: number; results: T[] }

const PAGE_SIZE = 20

const emptyForm = {
  employee: '',
  position: '',
  org_unit: '',
  grade: '',
  manager: '',
  is_primary: 'false',
  valid_from: '',
  valid_to: '',
}

function assignmentType(a: Assignment) {
  if (a.is_primary) return { label: 'Primary', cls: 'bg-blue-100 text-blue-700' }
  if (!a.valid_to) return { label: 'Dual-Hat', cls: 'bg-purple-100 text-purple-700' }
  return { label: 'Acting', cls: 'bg-amber-100 text-amber-700' }
}

export default function EmployeeAssignments() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [empFilter, setEmpFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Assignment | null>(null)
  const [form, setForm] = useState(emptyForm)

  const params: Record<string, string | number> = { page, page_size: PAGE_SIZE }
  if (empFilter) params.employee = empFilter

  const { data, isLoading } = useQuery<ApiList<Assignment>>({
    queryKey: ['assignments', page, empFilter],
    queryFn: () => api.get('/core/assignments/', { params }).then(r => r.data),
  })

  const { data: employees } = useQuery<ApiList<Employee>>({
    queryKey: ['employees-all'],
    queryFn: () => api.get('/core/employees/', { params: { page_size: 500 } }).then(r => r.data),
  })
  const { data: positions } = useQuery<ApiList<Position>>({
    queryKey: ['positions-all'],
    queryFn: () => api.get('/core/positions/', { params: { page_size: 500 } }).then(r => r.data),
  })
  const { data: orgUnits } = useQuery<ApiList<OrgUnit>>({
    queryKey: ['org-units-all'],
    queryFn: () => api.get('/core/org-units/', { params: { page_size: 500 } }).then(r => r.data),
  })
  const { data: grades } = useQuery<ApiList<Grade>>({
    queryKey: ['grades-all'],
    queryFn: () => api.get('/core/grades/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: (body: object) => api.post('/core/assignments/', body),
    onSuccess: () => { toast.success('Assignment created'); qc.invalidateQueries({ queryKey: ['assignments'] }); closeModal() },
    onError: () => toast.error('Failed to create assignment'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: { id: string } & object) => api.patch(`/core/assignments/${id}/`, body),
    onSuccess: () => { toast.success('Assignment updated'); qc.invalidateQueries({ queryKey: ['assignments'] }); closeModal() },
    onError: () => toast.error('Failed to update assignment'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/core/assignments/${id}/`),
    onSuccess: () => { toast.success('Assignment removed'); qc.invalidateQueries({ queryKey: ['assignments'] }) },
    onError: () => toast.error('Cannot delete assignment'),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }

  function openEdit(a: Assignment) {
    setEditing(a)
    setForm({
      employee: a.employee,
      position: a.position,
      org_unit: a.org_unit,
      grade: a.grade,
      manager: a.manager ?? '',
      is_primary: a.is_primary ? 'true' : 'false',
      valid_from: a.valid_from,
      valid_to: a.valid_to ?? '',
    })
    setModalOpen(true)
  }

  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = {
      ...form,
      is_primary: form.is_primary === 'true',
      manager: form.manager || null,
      valid_to: form.valid_to || null,
    }
    if (editing) update.mutate({ id: editing.id, ...payload })
    else create.mutate(payload)
  }

  function handleDelete(a: Assignment) {
    if (!window.confirm(`Remove "${a.position_display}" assignment for ${a.employee_display}?`)) return
    remove.mutate(a.id)
  }

  const set = (k: keyof typeof emptyForm) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm(prev => ({ ...prev, [k]: e.target.value }))

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Employee Assignments">
      <div className="space-y-4">

        {/* Info banner */}
        <div className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800 space-y-1">
          <p className="font-semibold">Assignment types</p>
          <div className="flex flex-wrap gap-4 text-xs mt-1">
            <span><span className="inline-block px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium mr-1">Primary</span>Main substantive position</span>
            <span><span className="inline-block px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 font-medium mr-1">Dual-Hat</span>Ongoing secondary role — no end date</span>
            <span><span className="inline-block px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium mr-1">Acting</span>Temporary secondary role — has an end date</span>
          </div>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Assignments</CardTitle>
              <Button onClick={openCreate}><Plus size={16} />Add Assignment</Button>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <Select
              value={empFilter}
              onChange={e => { setEmpFilter(e.target.value); setPage(1) }}
              className="w-72"
            >
              <option value="">All Employees</option>
              {employees?.results.map(e => (
                <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>
              ))}
            </Select>
          </CardContent>

          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState
              icon={ClipboardList}
              title="No assignments"
              description="Use assignments to record dual-hatting or acting roles."
              action={<Button onClick={openCreate}><Plus size={16} />Add Assignment</Button>}
            />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Employee</Th>
                    <Th>Position</Th>
                    <Th>Org Unit</Th>
                    <Th>Grade</Th>
                    <Th>Manager</Th>
                    <Th>Type</Th>
                    <Th>From</Th>
                    <Th>To</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map(a => {
                    const type = assignmentType(a)
                    return (
                      <Tr key={a.id}>
                        <Td>
                          <p className="font-medium text-gray-900 text-sm">{a.employee_display}</p>
                          <p className="text-xs text-gray-400">{a.employee_number}</p>
                        </Td>
                        <Td className="text-sm text-gray-700">{a.position_display}</Td>
                        <Td className="text-sm text-gray-500">{a.org_unit_display}</Td>
                        <Td className="text-sm text-gray-500">{a.grade_display}</Td>
                        <Td className="text-sm text-gray-500">{a.manager_display ?? '—'}</Td>
                        <Td>
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${type.cls}`}>
                            {type.label}
                          </span>
                        </Td>
                        <Td className="text-sm text-gray-500">{fmt(a.valid_from)}</Td>
                        <Td className="text-sm text-gray-500">{a.valid_to ? fmt(a.valid_to) : <span className="text-gray-300">Ongoing</span>}</Td>
                        <Td>
                          <div className="flex items-center gap-2 justify-end">
                            <button onClick={() => openEdit(a)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit">
                              <Pencil size={15} />
                            </button>
                            <button onClick={() => handleDelete(a)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Remove">
                              <Trash2 size={15} />
                            </button>
                          </div>
                        </Td>
                      </Tr>
                    )
                  })}
                </Tbody>
              </Table>
              <Pagination count={data.count} page={page} pageSize={PAGE_SIZE} onPage={setPage} />
            </>
          )}
        </Card>
      </div>

      <Modal
        open={modalOpen}
        onClose={closeModal}
        title={editing ? 'Edit Assignment' : 'Add Assignment'}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select label="Employee *" required value={form.employee} onChange={set('employee')} disabled={!!editing}>
            <option value="">— Select Employee —</option>
            {employees?.results.map(e => (
              <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>
            ))}
          </Select>

          <Select label="Position *" required value={form.position} onChange={set('position')}>
            <option value="">— Select Position —</option>
            {positions?.results.map(p => (
              <option key={p.id} value={p.id}>{p.title} ({p.position_code})</option>
            ))}
          </Select>

          <div className="grid grid-cols-2 gap-4">
            <Select label="Org Unit *" required value={form.org_unit} onChange={set('org_unit')}>
              <option value="">— Select —</option>
              {orgUnits?.results.map(u => (
                <option key={u.id} value={u.id}>{u.name}</option>
              ))}
            </Select>
            <Select label="Grade *" required value={form.grade} onChange={set('grade')}>
              <option value="">— Select —</option>
              {grades?.results.map(g => (
                <option key={g.id} value={g.id}>{g.grade_code} — {g.grade_name}</option>
              ))}
            </Select>
          </div>

          <Select label="Reporting Manager" value={form.manager} onChange={set('manager')}>
            <option value="">— None —</option>
            {employees?.results
              .filter(e => e.id !== form.employee)
              .map(e => (
                <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>
              ))}
          </Select>

          <Select label="Assignment Type *" value={form.is_primary} onChange={set('is_primary')}>
            <option value="true">Primary — main substantive role</option>
            <option value="false">Secondary — dual-hat or acting</option>
          </Select>

          <div className="grid grid-cols-2 gap-4">
            <DatePicker label="Effective From" required value={form.valid_from} onChange={v => setForm(prev => ({ ...prev, valid_from: v }))} />
            <DatePicker
              label="Effective To (leave blank if ongoing)"
              value={form.valid_to}
              onChange={v => setForm(prev => ({ ...prev, valid_to: v }))}
            />
          </div>

          {form.is_primary === 'false' && (
            <p className="text-xs text-gray-500 bg-gray-50 rounded-lg px-3 py-2">
              {form.valid_to
                ? 'This will be recorded as an Acting role — temporary, with a defined end date.'
                : 'This will be recorded as a Dual-Hat role — ongoing secondary position with no end date.'}
            </p>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Create Assignment'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
