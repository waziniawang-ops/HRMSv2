import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Landmark, Plus, Pencil, Trash2 } from 'lucide-react'
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

interface CostCenter {
  id: string
  code: string
  name: string
  org_unit: string
  org_unit_name?: string
  is_active: boolean
  created_at: string
}

interface OrgUnit { id: string; code: string; name: string }

interface ApiList { count: number; results: CostCenter[] }
interface OrgUnitList { count: number; results: OrgUnit[] }

const PAGE_SIZE = 15

const emptyForm = { code: '', name: '', org_unit: '', is_active: 'true' }

export default function CostCenters() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<CostCenter | null>(null)
  const [form, setForm] = useState(emptyForm)

  const params = { page, page_size: PAGE_SIZE, ...(search ? { search } : {}) }

  const { data, isLoading } = useQuery<ApiList>({
    queryKey: ['cost-centers', params],
    queryFn: () => api.get('/core/cost-centers/', { params }).then(r => r.data),
  })

  const { data: orgUnits } = useQuery<OrgUnitList>({
    queryKey: ['org-units-all'],
    queryFn: () => api.get('/core/org-units/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: (body: object) => api.post('/core/cost-centers/', body),
    onSuccess: () => { toast.success('Cost centre created'); qc.invalidateQueries({ queryKey: ['cost-centers'] }); closeModal() },
    onError: () => toast.error('Failed to create cost centre'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: { id: string } & object) => api.patch(`/core/cost-centers/${id}/`, body),
    onSuccess: () => { toast.success('Cost centre updated'); qc.invalidateQueries({ queryKey: ['cost-centers'] }); closeModal() },
    onError: () => toast.error('Failed to update cost centre'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/core/cost-centers/${id}/`),
    onSuccess: () => { toast.success('Cost centre deleted'); qc.invalidateQueries({ queryKey: ['cost-centers'] }) },
    onError: () => toast.error('Cannot delete — cost centre may have linked records'),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }

  function openEdit(c: CostCenter) {
    setEditing(c)
    setForm({ code: c.code, name: c.name, org_unit: c.org_unit, is_active: String(c.is_active) })
    setModalOpen(true)
  }

  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = { ...form, is_active: form.is_active === 'true' }
    if (editing) update.mutate({ id: editing.id, ...payload })
    else create.mutate(payload)
  }

  function handleDelete(c: CostCenter) {
    if (!window.confirm(`Delete "${c.name}"? This cannot be undone.`)) return
    remove.mutate(c.id)
  }

  const set = (k: keyof typeof emptyForm) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm(prev => ({ ...prev, [k]: e.target.value }))

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Cost Centres">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Cost Centres</CardTitle>
              <Button onClick={openCreate}><Plus size={16} />Add Cost Centre</Button>
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
              icon={Landmark}
              title="No cost centres found"
              description="Create your first cost centre to get started."
              action={<Button onClick={openCreate}><Plus size={16} />Add Cost Centre</Button>}
            />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Code</Th>
                    <Th>Name</Th>
                    <Th>Org Unit</Th>
                    <Th>Status</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map(c => (
                    <Tr key={c.id}>
                      <Td className="font-mono text-xs">{c.code}</Td>
                      <Td className="font-medium">{c.name}</Td>
                      <Td className="text-gray-500 text-sm">{c.org_unit_name ?? '—'}</Td>
                      <Td><Badge status={c.is_active ? 'ACTIVE' : 'INACTIVE'} /></Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button
                            onClick={() => openEdit(c)}
                            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="Edit"
                          >
                            <Pencil size={15} />
                          </button>
                          <button
                            onClick={() => handleDelete(c)}
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
        title={editing ? `Edit — ${editing.name}` : 'Add Cost Centre'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="Code" required value={form.code} onChange={set('code')} placeholder="e.g. CC-001" />
            <Input label="Name" required value={form.name} onChange={set('name')} placeholder="e.g. Engineering" />
          </div>
          <Select label="Org Unit" required value={form.org_unit} onChange={set('org_unit')}>
            <option value="">— Select org unit —</option>
            {orgUnits?.results.map(u => (
              <option key={u.id} value={u.id}>{u.name} ({u.code})</option>
            ))}
          </Select>
          <Select label="Status" value={form.is_active} onChange={set('is_active')}>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
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
