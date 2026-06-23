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
  id: string; code: string; name: string; pay_group: string; frequency: string; is_active: boolean
}

const PAY_GROUPS = ['MONTHLY', 'BIWEEKLY', 'WEEKLY', 'FORTNIGHTLY']
const emptyForm = { code: '', name: '', pay_group: 'MONTHLY', frequency: '', is_active: true }

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
    setForm({ code: c.code, name: c.name, pay_group: c.pay_group, frequency: c.frequency || '', is_active: c.is_active })
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
                <Thead><tr><Th>Code</Th><Th>Name</Th><Th>Pay Group</Th><Th>Frequency</Th><Th>Status</Th><Th></Th></tr></Thead>
                <Tbody>
                  {data.results.map((c: PayrollCalendar) => (
                    <Tr key={c.id}>
                      <Td className="font-mono text-sm">{c.code}</Td>
                      <Td className="font-medium">{c.name}</Td>
                      <Td><span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{c.pay_group}</span></Td>
                      <Td className="text-gray-500">{c.frequency || '—'}</Td>
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
        <form onSubmit={e => { e.preventDefault(); save.mutate(form) }} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input label="Code *" value={form.code} onChange={e => setForm(f => ({ ...f, code: e.target.value.toUpperCase() }))} required disabled={!!editing} />
            <Input label="Name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
          </div>
          <Select label="Pay Group *" value={form.pay_group} onChange={e => setForm(f => ({ ...f, pay_group: e.target.value }))}>
            {PAY_GROUPS.map(v => <option key={v} value={v}>{v}</option>)}
          </Select>
          <Input label="Frequency Description" value={form.frequency} onChange={e => setForm(f => ({ ...f, frequency: e.target.value }))} placeholder="e.g. Paid on the last working day of each month" />
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
