import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input, Select } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Plus, Calendar, Pencil, Trash2 } from 'lucide-react'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type LeaveType = {
  id: string; code: string; name: string; days_per_year: string
  is_paid: boolean; requires_approval: boolean; carry_forward: boolean
  max_carry_days: number; is_active: boolean
}

const emptyForm = {
  code: '', name: '', days_per_year: '', is_paid: 'true',
  requires_approval: 'true', carry_forward: 'false', max_carry_days: '0', is_active: 'true',
}

export default function LeaveTypes() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<LeaveType | null>(null)
  const [form, setForm] = useState(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['leave-types', page],
    queryFn: () => api.get(`/workforce/leave-types/?page=${page}`).then(r => r.data),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }
  function openEdit(lt: LeaveType) {
    setEditing(lt)
    setForm({
      code: lt.code,
      name: lt.name,
      days_per_year: String(lt.days_per_year),
      is_paid: lt.is_paid ? 'true' : 'false',
      requires_approval: lt.requires_approval ? 'true' : 'false',
      carry_forward: lt.carry_forward ? 'true' : 'false',
      max_carry_days: String(lt.max_carry_days ?? 0),
      is_active: lt.is_active ? 'true' : 'false',
    })
    setModalOpen(true)
  }
  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/workforce/leave-types/', body),
    onSuccess: () => { toast.success('Leave type created'); qc.invalidateQueries({ queryKey: ['leave-types'] }); closeModal() },
    onError: () => toast.error('Failed to create leave type'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) => api.patch(`/workforce/leave-types/${id}/`, body),
    onSuccess: () => { toast.success('Leave type updated'); qc.invalidateQueries({ queryKey: ['leave-types'] }); closeModal() },
    onError: () => toast.error('Failed to update leave type'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/workforce/leave-types/${id}/`),
    onSuccess: () => { toast.success('Leave type deleted'); qc.invalidateQueries({ queryKey: ['leave-types'] }) },
    onError: () => toast.error('Cannot delete — leave type may have linked requests'),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = {
      ...form,
      is_paid: form.is_paid === 'true',
      requires_approval: form.requires_approval === 'true',
      carry_forward: form.carry_forward === 'true',
      is_active: form.is_active === 'true',
      days_per_year: Number(form.days_per_year),
      max_carry_days: Number(form.max_carry_days),
    }
    if (editing) update.mutate({ id: editing.id, ...payload } as unknown as typeof emptyForm & { id: string })
    else create.mutate(payload)
  }

  function handleDelete(lt: LeaveType) {
    if (!window.confirm(`Delete leave type "${lt.name}"? This cannot be undone.`)) return
    remove.mutate(lt.id)
  }

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Leave Types">
      <div className="space-y-4">
        <div className="flex justify-end">
          <Button onClick={openCreate}><Plus size={16} /> Add Leave Type</Button>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Calendar} title="No leave types" description="Create your first leave type" action={<Button onClick={openCreate}><Plus size={16} />Add Leave Type</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Code</Th><Th>Name</Th><Th>Days/Year</Th><Th>Paid</Th><Th>Carry Forward</Th><Th>Active</Th><Th></Th></tr></Thead>
                <Tbody>
                  {data.results.map((lt: LeaveType) => (
                    <Tr key={lt.id}>
                      <Td><span className="font-mono text-xs font-semibold text-gray-700">{lt.code}</span></Td>
                      <Td className="font-medium text-gray-900">{lt.name}</Td>
                      <Td>{lt.days_per_year} days</Td>
                      <Td><Badge status={lt.is_paid ? 'ACTIVE' : 'DRAFT'} label={lt.is_paid ? 'Paid' : 'Unpaid'} /></Td>
                      <Td><Badge status={lt.carry_forward ? 'ACTIVE' : 'DRAFT'} label={lt.carry_forward ? 'Yes' : 'No'} /></Td>
                      <Td><Badge status={lt.is_active ? 'ACTIVE' : 'DRAFT'} label={lt.is_active ? 'Active' : 'Inactive'} /></Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(lt)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit"><Pencil size={15} /></button>
                          <button onClick={() => handleDelete(lt)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete"><Trash2 size={15} /></button>
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

      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit — ${editing.name}` : 'Add Leave Type'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="Code *" value={form.code} onChange={e => setForm(f => ({ ...f, code: e.target.value }))} placeholder="AL" required />
            <Input label="Name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Annual Leave" required />
          </div>
          <Input label="Days Per Year *" type="number" value={form.days_per_year} onChange={e => setForm(f => ({ ...f, days_per_year: e.target.value }))} placeholder="14" required />
          <div className="grid grid-cols-3 gap-4">
            <Select label="Paid Leave" value={form.is_paid} onChange={e => setForm(f => ({ ...f, is_paid: e.target.value }))}>
              <option value="true">Paid</option>
              <option value="false">Unpaid</option>
            </Select>
            <Select label="Requires Approval" value={form.requires_approval} onChange={e => setForm(f => ({ ...f, requires_approval: e.target.value }))}>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </Select>
            <Select label="Carry Forward" value={form.carry_forward} onChange={e => setForm(f => ({ ...f, carry_forward: e.target.value }))}>
              <option value="false">No</option>
              <option value="true">Yes</option>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Max Carry Days" type="number" value={form.max_carry_days} onChange={e => setForm(f => ({ ...f, max_carry_days: e.target.value }))} />
            <Select label="Active" value={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.value }))}>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </Select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Create'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
