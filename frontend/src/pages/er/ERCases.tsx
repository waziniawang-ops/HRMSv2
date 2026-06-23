import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
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
import { Plus, Search, Scale } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type ERCase = {
  id: string; case_number: string; subject: string
  subject_employee_name: string; category_name: string
  severity: string; status: string; created_at: string
}

const SEVERITIES = ['LOW','MEDIUM','HIGH','CRITICAL']
const CASE_TYPES = ['GRIEVANCE','DISCIPLINARY','PERFORMANCE','GENERAL']
const emptyForm = { category: '', subject: '', description: '', case_type: 'DISCIPLINARY', severity: 'MEDIUM', subject_employee: '', confidential: false }

export default function ERCases() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [categories, setCategories] = useState<{ id: string; name: string }[]>([])
  const [employees, setEmployees] = useState<{ id: string; employee_number: string; full_name: string }[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['er-cases', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/er/cases/?${params}`).then(r => r.data)
    },
  })

  function openCreate() {
    setForm(emptyForm)
    Promise.all([
      api.get('/er/categories/?page_size=100').then(r => setCategories(r.data.results || [])),
      api.get('/core/employees/?page_size=200').then(r => setEmployees(r.data.results || [])),
    ]).then(() => setModalOpen(true))
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/er/cases/', body),
    onSuccess: () => { toast.success('ER case created'); qc.invalidateQueries({ queryKey: ['er-cases'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to create case'),
  })

  const filtered = search
    ? data?.results?.filter((r: ERCase) =>
        r.case_number?.toLowerCase().includes(search.toLowerCase()) ||
        r.subject?.toLowerCase().includes(search.toLowerCase()) ||
        r.subject_employee_name?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="ER Cases">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-1">
            <div className="relative flex-1 max-w-sm">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search case or employee..." value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-44">
              <option value="">All Statuses</option>
              {['OPEN','INVESTIGATING','PENDING_HEARING','PENDING_OUTCOME','CLOSED','WITHDRAWN'].map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
            </Select>
          </div>
          <Button onClick={openCreate}><Plus size={16} /> New Case</Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={Scale} title="No ER cases found" action={<Button onClick={openCreate}><Plus size={16} />New Case</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Case #</Th><Th>Subject</Th><Th>Employee</Th><Th>Category</Th><Th>Severity</Th><Th>Status</Th><Th>Created</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: ERCase) => (
                    <Tr key={r.id} className="cursor-pointer hover:bg-gray-50" onClick={() => navigate(`/er/cases/${r.id}`)}>
                      <Td className="font-mono text-sm font-medium text-blue-600">{r.case_number}</Td>
                      <Td className="font-medium">{r.subject}</Td>
                      <Td>{r.subject_employee_name || '—'}</Td>
                      <Td className="text-gray-600">{r.category_name}</Td>
                      <Td><Badge status={r.severity} /></Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td className="text-gray-500">{fmt(r.created_at)}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              {!search && <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />}
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New ER Case">
        <form onSubmit={e => { e.preventDefault(); create.mutate(form) }} className="space-y-4">
          <Select label="Category *" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} required>
            <option value="">Select category…</option>
            {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </Select>
          <Select label="Subject Employee" value={form.subject_employee} onChange={e => setForm(f => ({ ...f, subject_employee: e.target.value }))}>
            <option value="">Select employee…</option>
            {employees.map(e => <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>)}
          </Select>
          <Input label="Subject *" value={form.subject} onChange={e => setForm(f => ({ ...f, subject: e.target.value }))} required />
          <div className="grid grid-cols-2 gap-3">
            <Select label="Case Type *" value={form.case_type} onChange={e => setForm(f => ({ ...f, case_type: e.target.value }))}>
              {CASE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </Select>
            <Select label="Severity *" value={form.severity} onChange={e => setForm(f => ({ ...f, severity: e.target.value }))}>
              {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <Textarea label="Description *" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} rows={4} required />
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.confidential} onChange={e => setForm(f => ({ ...f, confidential: e.target.checked }))} /> Confidential</label>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Create Case</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
