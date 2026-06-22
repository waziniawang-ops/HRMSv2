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
import { Plus, Search, Send } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type ESS = { id: string; subject: string; request_type_display: string; status: string; created_at: string; description: string }
const emptyForm = { request_type: '', subject: '', description: '' }

export default function MyRequests() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [requestTypes, setRequestTypes] = useState<{ id: string; name: string }[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['ess-my-requests', page],
    queryFn: () => api.get(`/ess/ess-requests/my_requests/?page=${page}`).then(r => r.data),
  })

  function openCreate() {
    setForm(emptyForm)
    api.get('/ess/ess-request-types/?page_size=100').then(r => setRequestTypes(r.data.results || []))
    setModalOpen(true)
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/ess/ess-requests/', body),
    onSuccess: () => { toast.success('Request submitted'); qc.invalidateQueries({ queryKey: ['ess-my-requests'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to submit request'),
  })

  return (
    <AppLayout title="My Requests">
      <div className="space-y-4">
        <div className="flex justify-end">
          <Button onClick={openCreate}><Plus size={16} /> New Request</Button>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Send} title="No requests" action={<Button onClick={openCreate}><Plus size={16} />New Request</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Subject</Th><Th>Type</Th><Th>Status</Th><Th>Submitted</Th></tr></Thead>
                <Tbody>
                  {data.results.map((r: ESS) => (
                    <Tr key={r.id}>
                      <Td className="font-medium">{r.subject}</Td>
                      <Td>{r.request_type_display}</Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td>{fmt(r.created_at)}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />
            </>
          )}
        </Card>
      </div>
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Self-Service Request">
        <form onSubmit={e => { e.preventDefault(); create.mutate(form) }} className="space-y-4">
          <Select label="Request Type *" value={form.request_type} onChange={e => setForm(f => ({ ...f, request_type: e.target.value }))} required>
            <option value="">Select type…</option>
            {requestTypes.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
          </Select>
          <Input label="Subject *" value={form.subject} onChange={e => setForm(f => ({ ...f, subject: e.target.value }))} required />
          <Textarea label="Description *" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} required rows={4} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Submit Request</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
