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
import { Plus, Search, Receipt } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type ClaimRequest = {
  id: string; claim_number: string; employee_name: string; employee_number: string
  claim_title: string; total_amount: string; currency: string
  status: string; submitted_at: string | null; created_at: string
}

const emptyForm = { employee: '', claim_title: '', period_start: '', period_end: '', currency: 'BND', notes: '' }

export default function ClaimRequests() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [employees, setEmployees] = useState<{ id: string; employee_number: string; full_name: string }[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['claim-requests', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/claims/claims/?${params}`).then(r => r.data)
    },
  })

  function openCreate() {
    setForm(emptyForm)
    api.get('/core/employees/?page_size=200').then(r => setEmployees(r.data.results || []))
    setModalOpen(true)
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/claims/claims/', body),
    onSuccess: () => { toast.success('Claim request created'); qc.invalidateQueries({ queryKey: ['claim-requests'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to create claim request'),
  })

  const filtered = search
    ? data?.results?.filter((r: ClaimRequest) =>
        r.claim_number?.toLowerCase().includes(search.toLowerCase()) ||
        r.employee_name?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="Claim Requests">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-1">
            <div className="relative flex-1 max-w-sm">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search claim or employee..." value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-40">
              <option value="">All Statuses</option>
              {['DRAFT','SUBMITTED','UNDER_REVIEW','APPROVED','REJECTED','PAID','CANCELLED'].map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
            </Select>
          </div>
          <Button onClick={openCreate}><Plus size={16} /> New Claim</Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={Receipt} title="No claim requests" action={<Button onClick={openCreate}><Plus size={16} />New Claim</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Claim #</Th><Th>Employee</Th><Th>Title</Th><Th>Amount</Th><Th>Status</Th><Th>Submitted</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: ClaimRequest) => (
                    <Tr key={r.id}>
                      <Td className="font-mono text-sm">{r.claim_number}</Td>
                      <Td className="font-medium">{r.employee_name} <span className="text-gray-400 text-xs">#{r.employee_number}</span></Td>
                      <Td className="text-gray-600">{r.claim_title}</Td>
                      <Td className="font-semibold">{Number(r.total_amount).toLocaleString()} {r.currency}</Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td className="text-gray-500">{r.submitted_at ? fmt(r.submitted_at) : '—'}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              {!search && <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />}
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Claim Request">
        <form onSubmit={e => { e.preventDefault(); create.mutate(form) }} className="space-y-4">
          <Select label="Employee *" value={form.employee} onChange={e => setForm(f => ({ ...f, employee: e.target.value }))} required>
            <option value="">Select employee…</option>
            {employees.map(e => <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>)}
          </Select>
          <Input label="Claim Title *" value={form.claim_title} onChange={e => setForm(f => ({ ...f, claim_title: e.target.value }))} required />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Period Start *" type="date" value={form.period_start} onChange={e => setForm(f => ({ ...f, period_start: e.target.value }))} required />
            <Input label="Period End *" type="date" value={form.period_end} onChange={e => setForm(f => ({ ...f, period_end: e.target.value }))} required />
          </div>
          <Select label="Currency" value={form.currency} onChange={e => setForm(f => ({ ...f, currency: e.target.value }))}>
            {['BND','USD','SGD','MYR'].map(c => <option key={c} value={c}>{c}</option>)}
          </Select>
          <Textarea label="Notes" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} rows={3} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Create Claim</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
