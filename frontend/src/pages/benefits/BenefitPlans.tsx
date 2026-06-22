import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input, Select, Textarea } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Plus, Search, Pencil, Trash2, Heart } from 'lucide-react'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type Plan = { id: string; code: string; name: string; category: string; provider: string; is_active: boolean; employee_contribution_rate: string; employer_contribution_rate: string }
const emptyForm = { code: '', name: '', category: 'MEDICAL', provider: '', employee_contribution_rate: '0', employer_contribution_rate: '0', is_active: true }
const CATS = ['MEDICAL','DENTAL','VISION','LIFE','PENSION','EDUCATION','RECREATION','OTHER']

export default function BenefitPlans() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Plan | null>(null)
  const [form, setForm] = useState<typeof emptyForm>(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['benefit-plans', page],
    queryFn: () => api.get(`/benefits/benefit-plans/?page=${page}`).then(r => r.data),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }
  function openEdit(r: Plan) { setEditing(r); setForm({ code: r.code, name: r.name, category: r.category, provider: r.provider, employee_contribution_rate: r.employee_contribution_rate, employer_contribution_rate: r.employer_contribution_rate, is_active: r.is_active }); setModalOpen(true) }

  const save = useMutation({
    mutationFn: (body: object) => editing ? api.patch(`/benefits/benefit-plans/${editing.id}/`, body) : api.post('/benefits/benefit-plans/', body),
    onSuccess: () => { toast.success(editing ? 'Plan updated' : 'Plan created'); qc.invalidateQueries({ queryKey: ['benefit-plans'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to save'),
  })
  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/benefits/benefit-plans/${id}/`),
    onSuccess: () => { toast.success('Deleted'); qc.invalidateQueries({ queryKey: ['benefit-plans'] }) },
    onError: () => toast.error('Cannot delete'),
  })

  const filtered = search ? data?.results?.filter((r: Plan) => r.name?.toLowerCase().includes(search.toLowerCase()) || r.code?.includes(search)) : data?.results

  return (
    <AppLayout title="Benefit Plans">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search plans..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <Button onClick={openCreate}><Plus size={16} /> New Plan</Button>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={Heart} title="No benefit plans" action={<Button onClick={openCreate}><Plus size={16} />New Plan</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Code</Th><Th>Name</Th><Th>Category</Th><Th>Provider</Th><Th>Emp. Rate</Th><Th>Employer Rate</Th><Th>Active</Th><Th></Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: Plan) => (
                    <Tr key={r.id}>
                      <Td className="font-mono text-sm">{r.code}</Td>
                      <Td className="font-medium">{r.name}</Td>
                      <Td><span className="text-xs bg-pink-50 text-pink-700 px-2 py-0.5 rounded">{r.category}</span></Td>
                      <Td>{r.provider || '—'}</Td>
                      <Td>{(Number(r.employee_contribution_rate) * 100).toFixed(1)}%</Td>
                      <Td>{(Number(r.employer_contribution_rate) * 100).toFixed(1)}%</Td>
                      <Td>{r.is_active ? <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">Active</span> : <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">Inactive</span>}</Td>
                      <Td>
                        <div className="flex gap-2 justify-end">
                          <button onClick={() => openEdit(r)} className="p-1.5 text-gray-400 hover:text-blue-600 rounded-lg"><Pencil size={15} /></button>
                          <button onClick={() => window.confirm('Delete plan?') && remove.mutate(r.id)} className="p-1.5 text-gray-400 hover:text-red-600 rounded-lg"><Trash2 size={15} /></button>
                        </div>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              {!search && <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />}
            </>
          )}
        </Card>
      </div>
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Edit Benefit Plan' : 'New Benefit Plan'}>
        <form onSubmit={e => { e.preventDefault(); save.mutate(form) }} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input label="Code *" value={form.code} onChange={e => setForm(f => ({ ...f, code: e.target.value.toUpperCase() }))} required disabled={!!editing} />
            <Input label="Name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Select label="Category" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))}>
              {CATS.map(c => <option key={c} value={c}>{c}</option>)}
            </Select>
            <Input label="Provider" value={form.provider} onChange={e => setForm(f => ({ ...f, provider: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Employee Rate (0-1)" type="number" step="0.0001" min="0" max="1" value={form.employee_contribution_rate} onChange={e => setForm(f => ({ ...f, employee_contribution_rate: e.target.value }))} />
            <Input label="Employer Rate (0-1)" type="number" step="0.0001" min="0" max="1" value={form.employer_contribution_rate} onChange={e => setForm(f => ({ ...f, employer_contribution_rate: e.target.value }))} />
          </div>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} /> Active</label>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={save.isPending}>{editing ? 'Save' : 'Create'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
