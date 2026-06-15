import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Target, Plus, Pencil, Trash2 } from 'lucide-react'
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

type Cycle = {
  id: string; name: string; cycle_year: number; status: string
  goal_setting_start: string; goal_setting_end: string; year_end_start: string; year_end_end: string
}

const PAGE_SIZE = 15
const emptyForm = {
  name: '', cycle_year: new Date().getFullYear().toString(), status: 'DRAFT',
  goal_setting_start: '', goal_setting_end: '', year_end_start: '', year_end_end: '',
}

export default function Cycles() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Cycle | null>(null)
  const [form, setForm] = useState(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['perf-cycles', page],
    queryFn: () => api.get(`/performance/cycles/?page=${page}`).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: (body: typeof emptyForm) => api.post('/performance/cycles/', body),
    onSuccess: () => { toast.success('Cycle created'); qc.invalidateQueries({ queryKey: ['perf-cycles'] }); closeModal() },
    onError: () => toast.error('Failed to create cycle'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) => api.patch(`/performance/cycles/${id}/`, body),
    onSuccess: () => { toast.success('Cycle updated'); qc.invalidateQueries({ queryKey: ['perf-cycles'] }); closeModal() },
    onError: () => toast.error('Failed to update cycle'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/performance/cycles/${id}/`),
    onSuccess: () => { toast.success('Cycle deleted'); qc.invalidateQueries({ queryKey: ['perf-cycles'] }) },
    onError: () => toast.error('Cannot delete — cycle may have linked goal plans'),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }
  function openEdit(c: Cycle) {
    setEditing(c)
    setForm({
      name: c.name,
      cycle_year: String(c.cycle_year),
      status: c.status,
      goal_setting_start: c.goal_setting_start ?? '',
      goal_setting_end: c.goal_setting_end ?? '',
      year_end_start: c.year_end_start ?? '',
      year_end_end: c.year_end_end ?? '',
    })
    setModalOpen(true)
  }
  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = {
      ...form,
      cycle_year: Number(form.cycle_year),
      goal_setting_start: form.goal_setting_start || null,
      goal_setting_end: form.goal_setting_end || null,
      year_end_start: form.year_end_start || null,
      year_end_end: form.year_end_end || null,
    }
    if (editing) update.mutate({ id: editing.id, ...payload } as typeof emptyForm & { id: string })
    else create.mutate(payload as typeof emptyForm)
  }

  function handleDelete(c: Cycle) {
    if (!window.confirm(`Delete cycle "${c.name}"? This cannot be undone.`)) return
    remove.mutate(c.id)
  }

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Performance Cycles">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Performance Cycles</CardTitle>
              <Button onClick={openCreate}><Plus size={16} />New Cycle</Button>
            </div>
          </CardHeader>

          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Target} title="No performance cycles" action={<Button onClick={openCreate}><Plus size={16} />New Cycle</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Name</Th><Th>Year</Th><Th>Status</Th><Th>Goal Setting</Th><Th>Year End Review</Th><Th></Th></tr></Thead>
                <Tbody>
                  {data.results.map((c: Cycle) => (
                    <Tr key={c.id}>
                      <Td className="font-semibold text-gray-900">{c.name}</Td>
                      <Td className="font-mono">{c.cycle_year}</Td>
                      <Td><Badge status={c.status} /></Td>
                      <Td className="text-sm text-gray-600">{fmt(c.goal_setting_start)} – {fmt(c.goal_setting_end)}</Td>
                      <Td className="text-sm text-gray-600">{fmt(c.year_end_start)} – {fmt(c.year_end_end)}</Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(c)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit"><Pencil size={15} /></button>
                          <button onClick={() => handleDelete(c)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete"><Trash2 size={15} /></button>
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

      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit — ${editing.name}` : 'New Performance Cycle'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="Cycle Name" required value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="FY2027 Annual Review" />
            <Input label="Year" type="number" required value={form.cycle_year} onChange={e => setForm(f => ({ ...f, cycle_year: e.target.value }))} />
          </div>
          <Select label="Status" value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
            {['DRAFT', 'ACTIVE', 'CLOSED', 'ARCHIVED'].map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
          <div className="p-3 bg-blue-50 rounded-xl">
            <p className="text-xs font-semibold text-blue-700 mb-3">Goal Setting Period</p>
            <div className="grid grid-cols-2 gap-3">
              <DatePicker label="Start" value={form.goal_setting_start} onChange={v => setForm(f => ({ ...f, goal_setting_start: v }))} />
              <DatePicker label="End" value={form.goal_setting_end} onChange={v => setForm(f => ({ ...f, goal_setting_end: v }))} />
            </div>
          </div>
          <div className="p-3 bg-purple-50 rounded-xl">
            <p className="text-xs font-semibold text-purple-700 mb-3">Year-End Review Period</p>
            <div className="grid grid-cols-2 gap-3">
              <DatePicker label="Start" value={form.year_end_start} onChange={v => setForm(f => ({ ...f, year_end_start: v }))} />
              <DatePicker label="End" value={form.year_end_end} onChange={v => setForm(f => ({ ...f, year_end_end: v }))} />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Create Cycle'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
