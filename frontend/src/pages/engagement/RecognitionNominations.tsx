import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { Select } from '@/components/ui/Input'
import { Textarea } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Plus, Award } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type Nomination = {
  id: string; nominator_name: string; nominee_name: string
  recognition_type_display: string; reason: string; status: string; created_at: string
}

const emptyForm = { nominee: '', recognition_type: '', reason: '' }

export default function RecognitionNominations() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [employees, setEmployees] = useState<{ id: string; person_display: string }[]>([])
  const [types, setTypes] = useState<{ id: string; name: string }[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['recognition-nominations', page],
    queryFn: () => api.get(`/engagement/nominations/?page=${page}`).then(r => r.data),
  })

  function openCreate() {
    setForm(emptyForm)
    Promise.all([
      api.get('/core/employees/?page_size=200').then(r => r.data.results),
      api.get('/engagement/recognition-types/?page_size=50').then(r => r.data.results),
    ]).then(([emps, ts]) => { setEmployees(emps); setTypes(ts); setModalOpen(true) })
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/engagement/nominations/', body),
    onSuccess: () => { toast.success('Nomination submitted'); qc.invalidateQueries({ queryKey: ['recognition-nominations'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to submit nomination'),
  })

  return (
    <AppLayout title="Recognition Nominations">
      <div className="space-y-4">
        <div className="flex justify-end">
          <Button onClick={openCreate}><Plus size={16} /> Nominate</Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Award} title="No nominations yet" action={<Button onClick={openCreate}><Plus size={16} />Nominate</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Nominator</Th><Th>Nominee</Th><Th>Recognition Type</Th><Th>Status</Th><Th>Submitted</Th></tr></Thead>
                <Tbody>
                  {data.results.map((r: Nomination) => (
                    <Tr key={r.id}>
                      <Td>{r.nominator_name}</Td>
                      <Td className="font-medium">{r.nominee_name}</Td>
                      <Td>{r.recognition_type_display}</Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td className="text-gray-500">{fmt(r.created_at)}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Recognition Nomination">
        <form onSubmit={e => { e.preventDefault(); create.mutate(form) }} className="space-y-4">
          <Select label="Nominee *" value={form.nominee} onChange={e => setForm(f => ({ ...f, nominee: e.target.value }))} required>
            <option value="">Select employee…</option>
            {employees.map(e => <option key={e.id} value={e.id}>{e.person_display}</option>)}
          </Select>
          <Select label="Recognition Type *" value={form.recognition_type} onChange={e => setForm(f => ({ ...f, recognition_type: e.target.value }))} required>
            <option value="">Select type…</option>
            {types.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
          </Select>
          <Textarea label="Reason *" value={form.reason} onChange={e => setForm(f => ({ ...f, reason: e.target.value }))} required />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Submit</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
