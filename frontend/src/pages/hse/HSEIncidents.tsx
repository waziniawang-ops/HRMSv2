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
import { Plus, Search, AlertTriangle } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type HSEIncident = {
  id: string; incident_number: string; title: string
  incident_type_name: string; severity: string
  reported_by_display: string; incident_date: string; status: string
}

const SEVERITIES = ['NEAR_MISS','MINOR','MODERATE','MAJOR','CRITICAL','FATAL']
const emptyForm = { incident_type: '', title: '', description: '', incident_date: '', location: '', severity: 'MINOR', immediate_action_taken: '', is_work_related: true }

export default function HSEIncidents() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [incidentTypes, setIncidentTypes] = useState<{ id: string; name: string }[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['hse-incidents', page, severityFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (severityFilter) params.set('severity', severityFilter)
      return api.get(`/hse/incidents/?${params}`).then(r => r.data)
    },
  })

  function openCreate() {
    setForm(emptyForm)
    api.get('/hse/incident-types/?page_size=100').then(r => setIncidentTypes(r.data.results || []))
    setModalOpen(true)
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/hse/incidents/', body),
    onSuccess: () => { toast.success('Incident reported'); qc.invalidateQueries({ queryKey: ['hse-incidents'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to report incident'),
  })

  const filtered = search
    ? data?.results?.filter((r: HSEIncident) =>
        r.title?.toLowerCase().includes(search.toLowerCase()) ||
        r.incident_number?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="HSE Incidents">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-1">
            <div className="relative flex-1 max-w-sm">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search incident..." value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <Select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)} className="w-36">
              <option value="">All Severities</option>
              {SEVERITIES.map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
            </Select>
          </div>
          <Button onClick={openCreate}><Plus size={16} /> Report Incident</Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={AlertTriangle} title="No HSE incidents" action={<Button onClick={openCreate}><Plus size={16} />Report Incident</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Incident #</Th><Th>Title</Th><Th>Type</Th><Th>Severity</Th><Th>Reported By</Th><Th>Date</Th><Th>Status</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: HSEIncident) => (
                    <Tr key={r.id}>
                      <Td className="font-mono text-sm">{r.incident_number}</Td>
                      <Td className="font-medium">{r.title}</Td>
                      <Td className="text-gray-600">{r.incident_type_name}</Td>
                      <Td><Badge status={r.severity} /></Td>
                      <Td>{r.reported_by_display}</Td>
                      <Td>{fmt(r.incident_date)}</Td>
                      <Td><Badge status={r.status} /></Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              {!search && <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />}
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Report HSE Incident">
        <form onSubmit={e => { e.preventDefault(); create.mutate(form) }} className="space-y-4">
          <Select label="Incident Type *" value={form.incident_type} onChange={e => setForm(f => ({ ...f, incident_type: e.target.value }))} required>
            <option value="">Select type…</option>
            {incidentTypes.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
          </Select>
          <Input label="Title *" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} required />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Incident Date *" type="date" value={form.incident_date} onChange={e => setForm(f => ({ ...f, incident_date: e.target.value }))} required />
            <Select label="Severity *" value={form.severity} onChange={e => setForm(f => ({ ...f, severity: e.target.value }))}>
              {SEVERITIES.map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
            </Select>
          </div>
          <Input label="Location" value={form.location} onChange={e => setForm(f => ({ ...f, location: e.target.value }))} />
          <Textarea label="Description *" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} rows={3} required />
          <Textarea label="Immediate Action Taken" value={form.immediate_action_taken} onChange={e => setForm(f => ({ ...f, immediate_action_taken: e.target.value }))} rows={2} />
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_work_related} onChange={e => setForm(f => ({ ...f, is_work_related: e.target.checked }))} /> Work Related</label>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Report</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
