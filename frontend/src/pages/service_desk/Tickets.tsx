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
import { Plus, Search, Ticket } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type HRTicket = { id: string; ticket_number: string; subject: string; category_name: string; priority: string; status: string; raised_by_display: string; assigned_to_display: string; created_at: string }
const emptyForm = { category: '', subject: '', description: '', priority: 'MEDIUM' }
const PRIORITIES = ['LOW','MEDIUM','HIGH','URGENT']

export default function Tickets() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [categories, setCategories] = useState<{ id: string; name: string }[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['hr-tickets', page, statusFilter, priorityFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      if (priorityFilter) params.set('priority', priorityFilter)
      return api.get(`/service-desk/tickets/?${params}`).then(r => r.data)
    },
  })

  function openCreate() {
    setForm(emptyForm)
    api.get('/service-desk/ticket-categories/?page_size=100').then(r => setCategories(r.data.results || []))
    setModalOpen(true)
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/service-desk/tickets/', body),
    onSuccess: () => { toast.success('Ticket created'); qc.invalidateQueries({ queryKey: ['hr-tickets'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to create ticket'),
  })

  const doAction = useMutation({
    mutationFn: ({ id, action }: { id: string; action: string }) => api.post(`/service-desk/tickets/${id}/${action}/`, {}),
    onSuccess: () => { toast.success('Done'); qc.invalidateQueries({ queryKey: ['hr-tickets'] }) },
    onError: () => toast.error('Action failed'),
  })

  const filtered = search ? data?.results?.filter((r: HRTicket) => r.subject?.toLowerCase().includes(search.toLowerCase()) || r.ticket_number?.includes(search)) : data?.results

  return (
    <AppLayout title="HR Service Desk">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-1">
            <div className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search tickets..." value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-36">
              <option value="">All Statuses</option>
              {['OPEN','IN_PROGRESS','PENDING_INFO','RESOLVED','CLOSED'].map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
            <Select value={priorityFilter} onChange={e => setPriorityFilter(e.target.value)} className="w-32">
              <option value="">All Priorities</option>
              {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
            </Select>
          </div>
          <Button onClick={openCreate}><Plus size={16} /> New Ticket</Button>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={Ticket} title="No tickets" action={<Button onClick={openCreate}><Plus size={16} />New Ticket</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Ticket #</Th><Th>Subject</Th><Th>Category</Th><Th>Priority</Th><Th>Raised By</Th><Th>Assigned To</Th><Th>Status</Th><Th>Created</Th><Th></Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: HRTicket) => (
                    <Tr key={r.id}>
                      <Td className="font-mono text-xs">{r.ticket_number}</Td>
                      <Td className="font-medium max-w-xs truncate">{r.subject}</Td>
                      <Td className="text-sm">{r.category_name}</Td>
                      <Td><span className={`text-xs px-2 py-0.5 rounded font-medium ${r.priority === 'URGENT' ? 'bg-red-100 text-red-700' : r.priority === 'HIGH' ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-600'}`}>{r.priority}</span></Td>
                      <Td className="text-sm">{r.raised_by_display}</Td>
                      <Td className="text-sm">{r.assigned_to_display || '—'}</Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td className="text-sm text-gray-500">{fmt(r.created_at)}</Td>
                      <Td>
                        <div className="flex gap-1 justify-end">
                          {r.status === 'OPEN' && <button onClick={() => doAction.mutate({ id: r.id, action: 'resolve' })} className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">Resolve</button>}
                          {r.status === 'RESOLVED' && <button onClick={() => doAction.mutate({ id: r.id, action: 'close' })} className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Close</button>}
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
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Support Ticket">
        <form onSubmit={e => { e.preventDefault(); create.mutate(form) }} className="space-y-4">
          <Select label="Category *" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} required>
            <option value="">Select category…</option>
            {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </Select>
          <Input label="Subject *" value={form.subject} onChange={e => setForm(f => ({ ...f, subject: e.target.value }))} required />
          <Select label="Priority" value={form.priority} onChange={e => setForm(f => ({ ...f, priority: e.target.value }))}>
            {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
          </Select>
          <Textarea label="Description *" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} required rows={4} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Submit Ticket</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
