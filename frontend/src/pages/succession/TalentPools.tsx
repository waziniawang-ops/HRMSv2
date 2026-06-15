import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { Input, Select, Textarea } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Plus, Users, Pencil, Trash2 } from 'lucide-react'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type Pool = { id: string; name: string; tier: string; description: string; is_active: boolean }

const TIER_LABELS: Record<string, string> = {
  HI_POT: 'High Potential',
  HI_PERF: 'High Performer',
  CORE: 'Core Contributor',
  WATCH: 'Watch List',
}

const emptyForm = { name: '', tier: 'HI_POT', description: '', is_active: 'true' }

export default function TalentPools() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Pool | null>(null)
  const [form, setForm] = useState(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['talent-pools', page],
    queryFn: () => api.get(`/succession/talent-pools/?page=${page}`).then(r => r.data),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }
  function openEdit(p: Pool) {
    setEditing(p)
    setForm({ name: p.name, tier: p.tier, description: p.description ?? '', is_active: p.is_active ? 'true' : 'false' })
    setModalOpen(true)
  }
  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/succession/talent-pools/', body),
    onSuccess: () => { toast.success('Talent pool created'); qc.invalidateQueries({ queryKey: ['talent-pools'] }); closeModal() },
    onError: () => toast.error('Failed to create pool'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) => api.patch(`/succession/talent-pools/${id}/`, body),
    onSuccess: () => { toast.success('Pool updated'); qc.invalidateQueries({ queryKey: ['talent-pools'] }); closeModal() },
    onError: () => toast.error('Failed to update pool'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/succession/talent-pools/${id}/`),
    onSuccess: () => { toast.success('Pool deleted'); qc.invalidateQueries({ queryKey: ['talent-pools'] }) },
    onError: () => toast.error('Cannot delete pool'),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = { ...form, is_active: form.is_active === 'true' }
    if (editing) update.mutate({ id: editing.id, ...payload } as typeof emptyForm & { id: string })
    else create.mutate(payload)
  }

  function handleDelete(p: Pool) {
    if (!window.confirm(`Delete pool "${p.name}"? This cannot be undone.`)) return
    remove.mutate(p.id)
  }

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Talent Pools">
      <div className="space-y-4">
        <div className="flex justify-end">
          <Button onClick={openCreate}><Plus size={16} /> New Pool</Button>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState
              icon={Users}
              title="No talent pools"
              description="Create talent pools to group employees by potential and performance"
              action={<Button onClick={openCreate}><Plus size={16} />New Pool</Button>}
            />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Name</Th>
                    <Th>Tier</Th>
                    <Th>Description</Th>
                    <Th>Active</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map((p: Pool) => (
                    <Tr key={p.id}>
                      <Td className="font-semibold text-gray-900">{p.name}</Td>
                      <Td>
                        <Badge status={p.tier} label={TIER_LABELS[p.tier] ?? p.tier} />
                      </Td>
                      <Td className="text-gray-600 max-w-xs truncate">{p.description || '—'}</Td>
                      <Td>
                        <Badge
                          status={p.is_active ? 'ACTIVE' : 'DRAFT'}
                          label={p.is_active ? 'Active' : 'Inactive'}
                        />
                      </Td>
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
              <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit — ${editing.name}` : 'New Talent Pool'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Name *"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            placeholder="High Potential Leaders"
            required
          />
          <Select
            label="Tier"
            value={form.tier}
            onChange={e => setForm(f => ({ ...f, tier: e.target.value }))}
          >
            {Object.entries(TIER_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </Select>
          <Textarea
            label="Description"
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
          />
          <Select
            label="Status"
            value={form.is_active}
            onChange={e => setForm(f => ({ ...f, is_active: e.target.value }))}
          >
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </Select>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Create'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
