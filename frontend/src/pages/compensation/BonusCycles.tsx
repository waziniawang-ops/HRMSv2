import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { Input, Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Plus, Gift } from 'lucide-react'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type BonusCycle = { id: string; name: string; year: number; bonus_type: string; budget_pool: string; currency: string; status: string }
const emptyForm = { name: '', year: new Date().getFullYear(), bonus_type: 'PERFORMANCE', budget_pool: '', currency: 'BND' }
const TYPES = ['PERFORMANCE','DISCRETIONARY','ANNUAL','FESTIVE','SPECIAL']

export default function BonusCycles() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState<typeof emptyForm>(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['bonus-cycles', page],
    queryFn: () => api.get(`/compensation/bonus-cycles/?page=${page}`).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: (body: object) => api.post('/compensation/bonus-cycles/', body),
    onSuccess: () => { toast.success('Bonus cycle created'); qc.invalidateQueries({ queryKey: ['bonus-cycles'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to create bonus cycle'),
  })

  const doAction = useMutation({
    mutationFn: ({ id, action }: { id: string; action: string }) => api.post(`/compensation/bonus-cycles/${id}/${action}/`, {}),
    onSuccess: () => { toast.success('Done'); qc.invalidateQueries({ queryKey: ['bonus-cycles'] }) },
    onError: () => toast.error('Action failed'),
  })

  return (
    <AppLayout title="Bonus Cycles">
      <div className="space-y-4">
        <div className="flex justify-end">
          <Button onClick={() => { setForm(emptyForm); setModalOpen(true) }}><Plus size={16} /> New Bonus Cycle</Button>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Gift} title="No bonus cycles" action={<Button onClick={() => setModalOpen(true)}><Plus size={16} />New Cycle</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Name</Th><Th>Year</Th><Th>Type</Th><Th>Budget Pool</Th><Th>Currency</Th><Th>Status</Th><Th></Th></tr></Thead>
                <Tbody>
                  {data.results.map((r: BonusCycle) => (
                    <Tr key={r.id}>
                      <Td className="font-medium">{r.name}</Td>
                      <Td>{r.year}</Td>
                      <Td><span className="text-xs bg-purple-50 text-purple-700 px-2 py-0.5 rounded">{r.bonus_type}</span></Td>
                      <Td className="font-semibold">{Number(r.budget_pool).toLocaleString()}</Td>
                      <Td>{r.currency}</Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td>
                        <div className="flex gap-1 justify-end">
                          {r.status === 'DRAFT' && <button onClick={() => doAction.mutate({ id: r.id, action: 'open_cycle' })} className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">Open</button>}
                          {r.status === 'OPEN' && <button onClick={() => doAction.mutate({ id: r.id, action: 'close_cycle' })} className="text-xs px-2 py-1 bg-yellow-100 text-yellow-700 rounded">Close</button>}
                          {r.status === 'CLOSED' && <button onClick={() => doAction.mutate({ id: r.id, action: 'mark_paid' })} className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">Mark Paid</button>}
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
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Bonus Cycle">
        <form onSubmit={e => { e.preventDefault(); create.mutate({ ...form, budget_pool: Number(form.budget_pool) }) }} className="space-y-4">
          <Input label="Name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Year *" type="number" value={String(form.year)} onChange={e => setForm(f => ({ ...f, year: Number(e.target.value) }))} required />
            <Select label="Type" value={form.bonus_type} onChange={e => setForm(f => ({ ...f, bonus_type: e.target.value }))}>
              {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Budget Pool *" type="number" step="0.01" value={form.budget_pool} onChange={e => setForm(f => ({ ...f, budget_pool: e.target.value }))} required />
            <Select label="Currency" value={form.currency} onChange={e => setForm(f => ({ ...f, currency: e.target.value }))}>
              {['BND','USD','SGD','MYR'].map(c => <option key={c} value={c}>{c}</option>)}
            </Select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Create</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
