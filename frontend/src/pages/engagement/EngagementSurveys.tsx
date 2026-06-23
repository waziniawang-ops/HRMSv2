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
import { Plus, BarChart3 } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type Survey = {
  id: string; title: string; survey_type: string
  status: string; open_date: string; close_date: string
  response_count: number; is_anonymous: boolean
}

const emptyForm = { template: '', title: '', description: '', open_date: '', close_date: '', is_anonymous: true, target_audience: 'ALL' }
const AUDIENCES = ['ALL','DEPARTMENT','JOB_FAMILY','CUSTOM']

export default function EngagementSurveys() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [templates, setTemplates] = useState<{ id: string; name: string; survey_type: string }[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['engagement-surveys', page],
    queryFn: () => api.get(`/engagement/surveys/?page=${page}`).then(r => r.data),
  })

  function openCreate() {
    setForm(emptyForm)
    api.get('/engagement/survey-templates/?page_size=100').then(r => setTemplates(r.data.results || []))
    setModalOpen(true)
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/engagement/surveys/', body),
    onSuccess: () => { toast.success('Survey created'); qc.invalidateQueries({ queryKey: ['engagement-surveys'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to create survey'),
  })

  return (
    <AppLayout title="Engagement Surveys">
      <div className="space-y-4">
        <div className="flex justify-end">
          <Button onClick={openCreate}><Plus size={16} /> New Survey</Button>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={BarChart3} title="No surveys found" action={<Button onClick={openCreate}><Plus size={16} />New Survey</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Title</Th><Th>Type</Th><Th>Open</Th><Th>Close</Th><Th>Responses</Th><Th>Anonymous</Th><Th>Status</Th></tr></Thead>
                <Tbody>
                  {data.results.map((r: Survey) => (
                    <Tr key={r.id}>
                      <Td className="font-medium">{r.title}</Td>
                      <Td className="text-gray-600">{r.survey_type}</Td>
                      <Td className="text-sm text-gray-500">{r.open_date ? fmt(r.open_date) : '—'}</Td>
                      <Td className="text-sm text-gray-500">{r.close_date ? fmt(r.close_date) : '—'}</Td>
                      <Td>{r.response_count}</Td>
                      <Td>{r.is_anonymous ? 'Yes' : 'No'}</Td>
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

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Engagement Survey">
        <form onSubmit={e => { e.preventDefault(); create.mutate(form) }} className="space-y-4">
          <Select label="Template *" value={form.template} onChange={e => setForm(f => ({ ...f, template: e.target.value }))} required>
            <option value="">Select template…</option>
            {templates.map(t => <option key={t.id} value={t.id}>{t.name} ({t.survey_type})</option>)}
          </Select>
          <Input label="Title *" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} required />
          <Textarea label="Description" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} rows={2} />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Open Date *" type="date" value={form.open_date} onChange={e => setForm(f => ({ ...f, open_date: e.target.value }))} required />
            <Input label="Close Date *" type="date" value={form.close_date} onChange={e => setForm(f => ({ ...f, close_date: e.target.value }))} required />
          </div>
          <Select label="Target Audience" value={form.target_audience} onChange={e => setForm(f => ({ ...f, target_audience: e.target.value }))}>
            {AUDIENCES.map(a => <option key={a} value={a}>{a}</option>)}
          </Select>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_anonymous} onChange={e => setForm(f => ({ ...f, is_anonymous: e.target.checked }))} /> Anonymous responses</label>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Create Survey</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
