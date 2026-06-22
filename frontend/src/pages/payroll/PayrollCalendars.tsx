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
import { Plus, Calendar, Pencil } from 'lucide-react'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type PayrollCalendar = {
  id: string; name: string; frequency: string; frequency_display: string
  first_period_start: string; pay_day_offset: number; is_active: boolean
}

const emptyForm = { name: '', frequency: 'MONTHLY', first_period_start: '', pay_day_offset: '5' }

export default function PayrollCalendars() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<PayrollCalendar | null>(null)
  const [form, setForm] = useState(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['payroll-calendars', page],
    queryFn: () => api.get(`/payroll/payroll-calendars/?page=${page}`).then(r => r.data),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }
  function openEdit(c: PayrollCalendar) {
    setEditing(c)
    setForm({ name: c.name, frequency: c.frequency, first_period_start: c.first_period_start, pay_day_offset: String(c.pay_day_offset) })
    setModalOpen(true)
  }

  const save = useMutation({
    mutationFn: (body: object) => editing
      ? api.patch(`/payroll/payroll-calendars/${editing.id}/`, body)
      : api.post('/payroll/payroll-calendars/', body),
    onSuccess: () => { toast.success(editing ? 'Calendar updated' : 'Calendar created'); qc.invalidateQueries({ queryKey: ['payroll-calendars'] }); setModalOpen(false) },
    onError: () => toast.error('Save failed'),
  })

  return (
    <AppLayout title="Payroll Calendars">
      <div className="space-y-4">
        <div className="flex justify-end">
          <Button onClick={openCreate}><Plus size={16} /> New Calendar</Button>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Calendar} title="No payroll calendars" action={<Button onClick={openCreate}><Plus size={16} />New Calendar</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Name</Th><Th>Frequency</Th><Th>First Period Start</Th><Th>Pay Day Offset</Th><Th>Status</Th><Th></Th></tr></Thead>
                <Tbody>
                  {data.results.map((c: PayrollCalendar) => (
                    <Tr key={c.id}>
                      <Td className="font-medium">{c.name}</Td>
                      <Td>{c.frequency_display || c.frequency}</Td>
                      <Td>{c.first_period_start}</Td>
                      <Td>{c.pay_day_offset}d</Td>
                      <Td><Badge status={c.is_active ? 'ACTIVE' : 'INACTIVE'} /></Td>
                      <Td><button onClick={() => openEdit(c)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"><Pencil size={15} /></button></Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Edit Calendar' : 'New Payroll Calendar'}>
        <form onSubmit={e => { e.preventDefault(); save.mutate({ ...form, pay_day_offset: Number(form.pay_day_offset) }) }} className="space-y-4">
          <Input label="Name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
          <Select label="Frequency *" value={form.frequency} onChange={e => setForm(f => ({ ...f, frequency: e.target.value }))}>
            {['WEEKLY','BIWEEKLY','SEMIMONTHLY','MONTHLY'].map(v => <option key={v} value={v}>{v}</option>)}
          </Select>
          <Input label="First Period Start *" type="date" value={form.first_period_start} onChange={e => setForm(f => ({ ...f, first_period_start: e.target.value }))} required />
          <Input label="Pay Day Offset (days)" type="number" value={form.pay_day_offset} onChange={e => setForm(f => ({ ...f, pay_day_offset: e.target.value }))} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={save.isPending}>{editing ? 'Save' : 'Create'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
