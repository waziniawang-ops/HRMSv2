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
import { Plus, Heart } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type WellbeingProgram = {
  id: string; name: string; program_type_display: string
  status: string; start_date: string; end_date: string | null
  max_participants: number | null; enrollment_count: number
}

const PROGRAM_TYPES = ['MENTAL_HEALTH','FITNESS','NUTRITION','EAP','ERGONOMICS','SOCIAL','OTHER']
const emptyForm = { name: '', description: '', program_type: 'MENTAL_HEALTH', start_date: '', end_date: '', status: 'PLANNED', max_participants: '', is_mandatory: false }

export default function WellbeingPrograms() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['wellbeing-programs', page],
    queryFn: () => api.get(`/hse/wellbeing-programs/?page=${page}`).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: (body: object) => api.post('/hse/wellbeing-programs/', body),
    onSuccess: () => { toast.success('Program created'); qc.invalidateQueries({ queryKey: ['wellbeing-programs'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to create program'),
  })

  return (
    <AppLayout title="Wellbeing Programs">
      <div className="space-y-4">
        <div className="flex justify-end">
          <Button onClick={() => { setForm(emptyForm); setModalOpen(true) }}><Plus size={16} /> New Program</Button>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Heart} title="No wellbeing programs" action={<Button onClick={() => setModalOpen(true)}><Plus size={16} />New Program</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Name</Th><Th>Type</Th><Th>Start</Th><Th>End</Th><Th>Enrolled / Capacity</Th><Th>Status</Th></tr></Thead>
                <Tbody>
                  {data.results.map((r: WellbeingProgram) => (
                    <Tr key={r.id}>
                      <Td className="font-medium">{r.name}</Td>
                      <Td className="text-gray-600">{r.program_type_display}</Td>
                      <Td>{fmt(r.start_date)}</Td>
                      <Td>{r.end_date ? fmt(r.end_date) : 'Ongoing'}</Td>
                      <Td>{r.enrollment_count} / {r.max_participants ?? '—'}</Td>
                      <Td><Badge status={r.status} /></Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Wellbeing Program">
        <form onSubmit={e => {
          e.preventDefault()
          const payload: Record<string, unknown> = { ...form }
          if (form.max_participants) payload.max_participants = Number(form.max_participants)
          else delete payload.max_participants
          if (!form.end_date) delete payload.end_date
          create.mutate(payload)
        }} className="space-y-4">
          <Input label="Name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
          <Select label="Program Type *" value={form.program_type} onChange={e => setForm(f => ({ ...f, program_type: e.target.value }))}>
            {PROGRAM_TYPES.map(t => <option key={t} value={t}>{t.replace('_',' ')}</option>)}
          </Select>
          <Textarea label="Description" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} rows={2} />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Start Date *" type="date" value={form.start_date} onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))} required />
            <Input label="End Date" type="date" value={form.end_date} onChange={e => setForm(f => ({ ...f, end_date: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Select label="Status" value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
              {['PLANNED','ACTIVE','COMPLETED','CANCELLED'].map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
            <Input label="Max Participants" type="number" value={form.max_participants} onChange={e => setForm(f => ({ ...f, max_participants: e.target.value }))} />
          </div>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_mandatory} onChange={e => setForm(f => ({ ...f, is_mandatory: e.target.checked }))} /> Mandatory</label>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Create Program</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
