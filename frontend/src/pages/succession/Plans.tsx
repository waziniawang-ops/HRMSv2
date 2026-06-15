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
import { Plus, GitBranch, Pencil, Trash2 } from 'lucide-react'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type Plan = {
  id: string
  position: string
  position_title: string
  incumbent_name: string | null
  plan_year: number
  risk_level: string
  status: string
  notes: string
  nominees: { id: string }[]
}

const emptyForm = {
  position: '', plan_year: new Date().getFullYear().toString(),
  risk_level: 'MEDIUM', status: 'DRAFT', notes: '',
}

export default function SuccessionPlans() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Plan | null>(null)
  const [positions, setPositions] = useState<{ id: string; title: string; position_code: string }[]>([])
  const [form, setForm] = useState(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['succession-plans', page],
    queryFn: () => api.get(`/succession/plans/?page=${page}`).then(r => r.data),
  })

  function openCreate() {
    setEditing(null)
    setForm(emptyForm)
    api.get('/core/positions/?page_size=200').then(r => { setPositions(r.data.results); setModalOpen(true) })
  }

  function openEdit(p: Plan) {
    setEditing(p)
    setForm({
      position: p.position,
      plan_year: String(p.plan_year),
      risk_level: p.risk_level,
      status: p.status,
      notes: p.notes ?? '',
    })
    api.get('/core/positions/?page_size=200').then(r => { setPositions(r.data.results); setModalOpen(true) })
  }

  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/succession/plans/', body),
    onSuccess: () => { toast.success('Succession plan created'); qc.invalidateQueries({ queryKey: ['succession-plans'] }); closeModal() },
    onError: () => toast.error('Failed to create plan'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) => api.patch(`/succession/plans/${id}/`, body),
    onSuccess: () => { toast.success('Plan updated'); qc.invalidateQueries({ queryKey: ['succession-plans'] }); closeModal() },
    onError: () => toast.error('Failed to update plan'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/succession/plans/${id}/`),
    onSuccess: () => { toast.success('Plan deleted'); qc.invalidateQueries({ queryKey: ['succession-plans'] }) },
    onError: () => toast.error('Cannot delete plan'),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = { ...form, plan_year: Number(form.plan_year) }
    if (editing) update.mutate({ id: editing.id, ...payload } as unknown as typeof emptyForm & { id: string })
    else create.mutate(payload)
  }

  function handleDelete(p: Plan) {
    if (!window.confirm(`Delete plan for "${p.position_title}"? This cannot be undone.`)) return
    remove.mutate(p.id)
  }

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Succession Plans">
      <div className="space-y-4">
        <div className="flex justify-end">
          <Button onClick={openCreate}><Plus size={16} /> New Plan</Button>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState
              icon={GitBranch}
              title="No succession plans"
              description="Create succession plans for critical positions"
              action={<Button onClick={openCreate}><Plus size={16} />New Plan</Button>}
            />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Position</Th>
                    <Th>Incumbent</Th>
                    <Th>Year</Th>
                    <Th>Risk Level</Th>
                    <Th>Nominees</Th>
                    <Th>Status</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map((p: Plan) => (
                    <Tr key={p.id}>
                      <Td className="font-semibold text-gray-900">{p.position_title || '—'}</Td>
                      <Td className="text-gray-600">{p.incumbent_name || '—'}</Td>
                      <Td className="font-mono">{p.plan_year}</Td>
                      <Td><Badge status={p.risk_level} /></Td>
                      <Td className="text-center font-semibold">{p.nominees?.length ?? 0}</Td>
                      <Td><Badge status={p.status} /></Td>
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

      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit — ${editing.position_title}` : 'New Succession Plan'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select
            label="Critical Position *"
            value={form.position}
            onChange={e => setForm(f => ({ ...f, position: e.target.value }))}
            required
            disabled={!!editing}
          >
            <option value="">Select position…</option>
            {positions.map(p => (
              <option key={p.id} value={p.id}>{p.title} ({p.position_code})</option>
            ))}
          </Select>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Plan Year *"
              type="number"
              value={form.plan_year}
              onChange={e => setForm(f => ({ ...f, plan_year: e.target.value }))}
              required
            />
            <Select
              label="Risk Level"
              value={form.risk_level}
              onChange={e => setForm(f => ({ ...f, risk_level: e.target.value }))}
            >
              {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(r => (
                <option key={r} value={r}>{r}</option>
              ))}
            </Select>
          </div>
          <Select
            label="Status"
            value={form.status}
            onChange={e => setForm(f => ({ ...f, status: e.target.value }))}
          >
            {['DRAFT', 'ACTIVE', 'CLOSED', 'ARCHIVED'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </Select>
          <Textarea
            label="Notes"
            value={form.notes}
            onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
          />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Create'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
