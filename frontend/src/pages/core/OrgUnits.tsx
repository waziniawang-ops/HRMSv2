import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Building2, Plus, Pencil, Trash2 } from 'lucide-react'
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
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

interface OrgUnit {
  id: string
  code: string
  name: string
  type: string
  parent: string | null
  parent_name?: string | null
  head_employee: string | null
  head_employee_display?: string | null
  status: string
  created_by_display?: string | null
  created_at: string
}

interface Employee { id: string; employee_number: string; full_name: string }

interface ApiList {
  count: number
  results: OrgUnit[]
}

interface EmployeeList { count: number; results: Employee[] }

const PAGE_SIZE = 15

const ORG_TYPES = ['ORGANIZATION', 'COMPANY', 'DIVISION', 'DEPARTMENT', 'UNIT', 'BRANCH']
const STATUSES = ['ACTIVE', 'INACTIVE']

const emptyForm = {
  code: '',
  name: '',
  type: 'DEPARTMENT',
  parent: '',
  head_employee: '',
  status: 'ACTIVE',
}

export default function OrgUnits() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<OrgUnit | null>(null)
  const [form, setForm] = useState(emptyForm)

  const params = { page, page_size: PAGE_SIZE, ...(search ? { search } : {}) }

  const { data, isLoading } = useQuery<ApiList>({
    queryKey: ['org-units', params],
    queryFn: () => api.get('/core/org-units/', { params }).then(r => r.data),
  })

  const { data: allUnits } = useQuery<ApiList>({
    queryKey: ['org-units-all'],
    queryFn: () => api.get('/core/org-units/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const { data: allEmployees } = useQuery<EmployeeList>({
    queryKey: ['employees-all'],
    queryFn: () => api.get('/core/employees/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: (body: typeof emptyForm) => api.post('/core/org-units/', body),
    onSuccess: () => {
      toast.success('Org unit created')
      qc.invalidateQueries({ queryKey: ['org-units'] })
      closeModal()
    },
    onError: () => toast.error('Failed to create org unit'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) =>
      api.patch(`/core/org-units/${id}/`, body),
    onSuccess: () => {
      toast.success('Org unit updated')
      qc.invalidateQueries({ queryKey: ['org-units'] })
      closeModal()
    },
    onError: () => toast.error('Failed to update org unit'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/core/org-units/${id}/`),
    onSuccess: () => {
      toast.success('Org unit deleted')
      qc.invalidateQueries({ queryKey: ['org-units'] })
    },
    onError: () => toast.error('Cannot delete — org unit may have linked records'),
  })

  function openCreate() {
    setEditing(null)
    setForm(emptyForm)
    setModalOpen(true)
  }

  function openEdit(u: OrgUnit) {
    setEditing(u)
    setForm({ code: u.code, name: u.name, type: u.type, parent: u.parent ?? '', head_employee: u.head_employee ?? '', status: u.status })
    setModalOpen(true)
  }

  function closeModal() {
    setModalOpen(false)
    setEditing(null)
    setForm(emptyForm)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = { ...form, parent: form.parent || null, head_employee: form.head_employee || null }
    if (editing) {
      update.mutate({ id: editing.id, ...payload } as typeof emptyForm & { id: string })
    } else {
      create.mutate(payload as typeof emptyForm)
    }
  }

  function handleDelete(u: OrgUnit) {
    if (!window.confirm(`Delete "${u.name}"? This cannot be undone.`)) return
    remove.mutate(u.id)
  }

  const set = (k: keyof typeof emptyForm) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm(prev => ({ ...prev, [k]: e.target.value }))

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Organisation Units">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Organisation Units</CardTitle>
              <Button onClick={openCreate}><Plus size={16} />Add Org Unit</Button>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <Input
              placeholder="Search by name or code…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
              className="max-w-sm"
            />
          </CardContent>

          {isLoading ? (
            <PageSpinner />
          ) : !data?.results.length ? (
            <EmptyState
              icon={Building2}
              title="No org units found"
              description="Create your first organisational unit to get started."
              action={<Button onClick={openCreate}><Plus size={16} />Add Org Unit</Button>}
            />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Code</Th>
                    <Th>Name</Th>
                    <Th>Type</Th>
                    <Th>Parent</Th>
                    <Th>Head</Th>
                    <Th>Status</Th>
                    <Th>Created By</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map(u => (
                    <Tr key={u.id}>
                      <Td className="font-mono text-xs">{u.code}</Td>
                      <Td className="font-medium">{u.name}</Td>
                      <Td><Badge status={u.type} /></Td>
                      <Td className="text-gray-500">{u.parent_name ?? '—'}</Td>
                      <Td className="text-gray-500 text-sm">{u.head_employee_display ?? '—'}</Td>
                      <Td><Badge status={u.status} /></Td>
                      <Td className="text-gray-500 text-sm">{u.created_by_display ?? '—'}</Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button
                            onClick={() => openEdit(u)}
                            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="Edit"
                          >
                            <Pencil size={15} />
                          </button>
                          <button
                            onClick={() => handleDelete(u)}
                            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete"
                          >
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

      <Modal
        open={modalOpen}
        onClose={closeModal}
        title={editing ? `Edit — ${editing.name}` : 'Add Org Unit'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="Code" required value={form.code} onChange={set('code')} placeholder="e.g. HR-001" />
            <Input label="Name" required value={form.name} onChange={set('name')} placeholder="e.g. Human Resources" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Select label="Type" value={form.type} onChange={set('type')}>
              {ORG_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </Select>
            <Select label="Status" value={form.status} onChange={set('status')}>
              {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <Select label="Parent Unit" value={form.parent} onChange={set('parent')}>
            <option value="">— None (Top Level) —</option>
            {allUnits?.results
              .filter(u => u.id !== editing?.id)
              .map(u => (
                <option key={u.id} value={u.id}>{u.name} ({u.code})</option>
              ))}
          </Select>
          <Select label="Head of Unit (Employee)" value={form.head_employee} onChange={set('head_employee')}>
            <option value="">— None —</option>
            {allEmployees?.results.map(e => (
              <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>
            ))}
          </Select>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Create'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
