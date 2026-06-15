import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Briefcase, Plus, Pencil, Trash2 } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input, Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import api from '@/lib/api'

interface Position {
  id: string
  position_code: string
  title: string
  status: string
  org_unit: string | null
  org_unit_display?: string
  grade: string | null
  grade_display?: string
  job: string | null
  job_display?: string
  cost_center: string | null
  is_critical: boolean
  headcount_budget: number
  reporting_to: string | null
  reporting_to_display?: string | null
}

interface OrgUnit { id: string; code: string; name: string }
interface Grade { id: string; grade_code: string; grade_name: string }
interface Job { id: string; job_code: string; job_title: string }
interface CostCenter { id: string; code: string; name: string }
interface ApiList<T> { count: number; results: T[] }

const PAGE_SIZE = 15
const POSITION_STATUSES = ['DRAFT', 'APPROVED', 'VACANT', 'OCCUPIED', 'FROZEN', 'CLOSED']

const emptyForm = {
  position_code: '',
  title: '',
  status: 'VACANT',
  org_unit: '',
  grade: '',
  job: '',
  cost_center: '',
  is_critical: false,
  headcount_budget: 1,
  reporting_to: '',
}

export default function Positions() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Position | null>(null)
  const [form, setForm] = useState(emptyForm)

  const params = {
    page,
    page_size: PAGE_SIZE,
    ...(search ? { search } : {}),
    ...(statusFilter ? { status: statusFilter } : {}),
  }

  const { data, isLoading } = useQuery<ApiList<Position>>({
    queryKey: ['positions', params],
    queryFn: () => api.get('/core/positions/', { params }).then(r => r.data),
  })

  const { data: orgUnits } = useQuery<ApiList<OrgUnit>>({
    queryKey: ['org-units-all'],
    queryFn: () => api.get('/core/org-units/', { params: { page_size: 500 } }).then(r => r.data),
  })
  const { data: grades } = useQuery<ApiList<Grade>>({
    queryKey: ['grades-all'],
    queryFn: () => api.get('/core/grades/', { params: { page_size: 500 } }).then(r => r.data),
  })
  const { data: jobs } = useQuery<ApiList<Job>>({
    queryKey: ['jobs-all'],
    queryFn: () => api.get('/core/jobs/', { params: { page_size: 500 } }).then(r => r.data),
  })
  const { data: costCenters } = useQuery<ApiList<CostCenter>>({
    queryKey: ['cost-centers-all'],
    queryFn: () => api.get('/core/cost-centers/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const { data: allPositions } = useQuery<ApiList<Position>>({
    queryKey: ['positions-all'],
    queryFn: () => api.get('/core/positions/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: (body: typeof emptyForm) => api.post('/core/positions/', body),
    onSuccess: () => { toast.success('Position created'); qc.invalidateQueries({ queryKey: ['positions'] }); closeModal() },
    onError: () => toast.error('Failed to create position'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) =>
      api.patch(`/core/positions/${id}/`, body),
    onSuccess: () => { toast.success('Position updated'); qc.invalidateQueries({ queryKey: ['positions'] }); closeModal() },
    onError: () => toast.error('Failed to update position'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/core/positions/${id}/`),
    onSuccess: () => { toast.success('Position deleted'); qc.invalidateQueries({ queryKey: ['positions'] }) },
    onError: () => toast.error('Cannot delete — position may have linked records'),
  })

  function openCreate() {
    setEditing(null)
    setForm(emptyForm)
    setModalOpen(true)
  }

  function openEdit(p: Position) {
    setEditing(p)
    setForm({
      position_code: p.position_code,
      title: p.title,
      status: p.status,
      org_unit: p.org_unit ?? '',
      grade: p.grade ?? '',
      job: p.job ?? '',
      cost_center: p.cost_center ?? '',
      is_critical: p.is_critical,
      headcount_budget: p.headcount_budget ?? 1,
      reporting_to: p.reporting_to ?? '',
    })
    setModalOpen(true)
  }

  function closeModal() {
    setModalOpen(false)
    setEditing(null)
    setForm(emptyForm)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = {
      ...form,
      org_unit: form.org_unit || null,
      grade: form.grade || null,
      job: form.job || null,
      cost_center: form.cost_center || null,
      reporting_to: form.reporting_to || null,
    }
    if (editing) {
      update.mutate({ id: editing.id, ...payload } as typeof emptyForm & { id: string })
    } else {
      create.mutate(payload as typeof emptyForm)
    }
  }

  function handleDelete(p: Position) {
    if (!window.confirm(`Delete position "${p.title}"? This cannot be undone.`)) return
    remove.mutate(p.id)
  }

  const set = (k: keyof typeof emptyForm) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm(prev => ({
        ...prev,
        [k]: k === 'is_critical'
          ? (e.target as HTMLInputElement).checked
          : k === 'headcount_budget'
            ? Number(e.target.value)
            : e.target.value,
      }))

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Positions">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Positions</CardTitle>
              <Button onClick={openCreate}><Plus size={16} />Add Position</Button>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <div className="flex gap-3">
              <Input
                placeholder="Search by title or code…"
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1) }}
                className="max-w-sm"
              />
              <Select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1) }} className="w-48">
                <option value="">All Statuses</option>
                {POSITION_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </Select>
            </div>
          </CardContent>

          {isLoading ? (
            <PageSpinner />
          ) : !data?.results.length ? (
            <EmptyState
              icon={Briefcase}
              title="No positions found"
              description="Add a position to begin building your workforce structure."
              action={<Button onClick={openCreate}><Plus size={16} />Add Position</Button>}
            />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Code</Th>
                    <Th>Title</Th>
                    <Th>Status</Th>
                    <Th>Department</Th>
                    <Th>Grade</Th>
                    <Th>Reports To</Th>
                    <Th>Critical</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map(p => (
                    <Tr key={p.id}>
                      <Td className="font-mono text-xs">{p.position_code}</Td>
                      <Td className="font-medium">{p.title}</Td>
                      <Td><Badge status={p.status} /></Td>
                      <Td className="text-gray-500">{p.org_unit_display ?? '—'}</Td>
                      <Td className="text-gray-500">{p.grade_display ?? '—'}</Td>
                      <Td className="text-gray-500 text-sm">{p.reporting_to_display ?? '—'}</Td>
                      <Td>
                        {p.is_critical
                          ? <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">Critical</span>
                          : <span className="text-gray-400 text-sm">—</span>}
                      </Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(p)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit">
                            <Pencil size={15} />
                          </button>
                          <button onClick={() => handleDelete(p)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete">
                            <Trash2 size={15} />
                          </button>
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

      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit — ${editing.title}` : 'Add Position'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="Position Code" required value={form.position_code} onChange={set('position_code')} placeholder="e.g. POS-001" />
            <Input label="Title" required value={form.title} onChange={set('title')} placeholder="e.g. Senior Engineer" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Select label="Status" value={form.status} onChange={set('status')}>
              {POSITION_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
            <Select label="Org Unit" value={form.org_unit} onChange={set('org_unit')}>
              <option value="">— Select —</option>
              {orgUnits?.results.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Select label="Job" required value={form.job} onChange={set('job')}>
              <option value="">— Select Job —</option>
              {jobs?.results.map(j => <option key={j.id} value={j.id}>{j.job_title} ({j.job_code})</option>)}
            </Select>
            <Select label="Grade" required value={form.grade} onChange={set('grade')}>
              <option value="">— Select Grade —</option>
              {grades?.results.map(g => <option key={g.id} value={g.id}>{g.grade_code} — {g.grade_name}</option>)}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Select label="Cost Centre" required value={form.cost_center} onChange={set('cost_center')}>
              <option value="">— Select Cost Centre —</option>
              {costCenters?.results.map(c => <option key={c.id} value={c.id}>{c.code} — {c.name}</option>)}
            </Select>
            <Input label="Headcount Budget" type="number" min={1} value={String(form.headcount_budget)} onChange={set('headcount_budget')} />
          </div>
          <Select label="Reports To (Position)" value={form.reporting_to} onChange={set('reporting_to')}>
            <option value="">— None —</option>
            {allPositions?.results
              .filter(p => p.id !== editing?.id)
              .map(p => <option key={p.id} value={p.id}>{p.title} ({p.position_code})</option>)}
          </Select>
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={form.is_critical}
              onChange={set('is_critical')}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Mark as Critical Position
          </label>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Create'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
