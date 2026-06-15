import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { FileText, Plus, Pencil, Trash2 } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input, Select } from '@/components/ui/Input'
import { DatePicker } from '@/components/ui/DatePicker'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { fmt, currency } from '@/lib/utils'
import { useCurrency } from '@/hooks/useCurrency'
import api from '@/lib/api'
import { useAuth } from '@/context/AuthContext'

interface Offer {
  id: string
  offer_number: string
  application: string
  applicant_name: string
  position: string | null
  position_display: string
  grade: string | null
  basic_salary: string
  total_package: string
  employment_type: string
  status: string
  start_date: string
  expiry_date: string
}

interface Application { id: string; applicant_display?: string; job_title?: string }
interface Position { id: string; title: string; position_code: string }
interface Grade { id: string; grade_code: string; grade_name: string }
interface ApiList<T> { count: number; results: T[] }

const PAGE_SIZE = 15
const OFFER_STATUSES = ['DRAFT', 'PENDING', 'APPROVED', 'EXTENDED', 'ACCEPTED', 'REJECTED', 'EXPIRED', 'WITHDRAWN']
const EMP_TYPES = ['PERMANENT', 'CONTRACT', 'PART_TIME', 'INTERNSHIP', 'FREELANCE']

const emptyForm = {
  application: '',
  position: '',
  grade: '',
  basic_salary: '',
  allowances: '{}',
  total_package: '',
  employment_type: 'PERMANENT',
  start_date: '',
  expiry_date: '',
  status: 'DRAFT',
}

export default function Offers() {
  const qc = useQueryClient()
  const { user } = useAuth()
  const canEdit = ['SYSTEM_ADMIN', 'HR_ADMIN', 'HR_MAKER', 'HR_CHECKER', 'RECRUITER'].some(r => user?.roles?.includes(r) ?? user?.role === r)
  const { symbol } = useCurrency()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Offer | null>(null)
  const [form, setForm] = useState(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['offers', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/recruitment/offers/?${params}`).then(r => r.data)
    },
  })

  const { data: applications } = useQuery<ApiList<Application>>({
    queryKey: ['applications-all'],
    queryFn: () => api.get('/recruitment/applications/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const { data: positions } = useQuery<ApiList<Position>>({
    queryKey: ['positions-all'],
    queryFn: () => api.get('/core/positions/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const { data: grades } = useQuery<ApiList<Grade>>({
    queryKey: ['grades-all'],
    queryFn: () => api.get('/core/grades/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: (body: typeof emptyForm) => api.post('/recruitment/offers/', body),
    onSuccess: () => { toast.success('Offer created'); qc.invalidateQueries({ queryKey: ['offers'] }); closeModal() },
    onError: () => toast.error('Failed to create offer'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) => api.patch(`/recruitment/offers/${id}/`, body),
    onSuccess: () => { toast.success('Offer updated'); qc.invalidateQueries({ queryKey: ['offers'] }); closeModal() },
    onError: () => toast.error('Failed to update offer'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/recruitment/offers/${id}/`),
    onSuccess: () => { toast.success('Offer deleted'); qc.invalidateQueries({ queryKey: ['offers'] }) },
    onError: () => toast.error('Cannot delete offer'),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }
  function openEdit(o: Offer) {
    setEditing(o)
    setForm({
      application: o.application,
      position: o.position ?? '',
      grade: o.grade ?? '',
      basic_salary: o.basic_salary ?? '',
      allowances: '{}',
      total_package: o.total_package ?? '',
      employment_type: o.employment_type,
      start_date: o.start_date ?? '',
      expiry_date: o.expiry_date ?? '',
      status: o.status,
    })
    setModalOpen(true)
  }
  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = {
      ...form,
      position: form.position || null,
      grade: form.grade || null,
      start_date: form.start_date || null,
      expiry_date: form.expiry_date || null,
    }
    if (editing) update.mutate({ id: editing.id, ...payload } as unknown as typeof emptyForm & { id: string })
    else create.mutate(payload as unknown as typeof emptyForm)
  }

  function handleDelete(o: Offer) {
    if (!window.confirm(`Delete offer "${o.offer_number}"? This cannot be undone.`)) return
    remove.mutate(o.id)
  }

  const set = (k: keyof typeof emptyForm) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [k]: e.target.value }))

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Offer Letters">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Offer Letters</CardTitle>
              {canEdit && <Button onClick={openCreate}><Plus size={16} />New Offer</Button>}
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-44">
              <option value="">All Statuses</option>
              {OFFER_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </CardContent>

          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={FileText} title="No offers" description="Offer letters appear here after interview stage." action={canEdit ? <Button onClick={openCreate}><Plus size={16} />New Offer</Button> : undefined} />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Offer #</Th><Th>Candidate</Th><Th>Position</Th>
                    <Th>Basic Salary</Th><Th>Total Package</Th><Th>Type</Th>
                    <Th>Start Date</Th><Th>Status</Th><Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map((o: Offer) => (
                    <Tr key={o.id}>
                      <Td><span className="font-mono text-xs font-semibold text-gray-700">{o.offer_number}</span></Td>
                      <Td className="font-medium text-gray-900">{o.applicant_name || '—'}</Td>
                      <Td className="text-gray-600 text-sm">{o.position_display || '—'}</Td>
                      <Td className="font-semibold text-gray-900">{currency(o.basic_salary, symbol)}</Td>
                      <Td className="font-semibold text-blue-700">{currency(o.total_package, symbol)}</Td>
                      <Td className="text-sm text-gray-600">{o.employment_type}</Td>
                      <Td>{fmt(o.start_date)}</Td>
                      <Td><Badge status={o.status} /></Td>
                      <Td>
                        {canEdit && (
                          <div className="flex items-center gap-2 justify-end">
                            <button onClick={() => openEdit(o)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit"><Pencil size={15} /></button>
                            <button onClick={() => handleDelete(o)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete"><Trash2 size={15} /></button>
                          </div>
                        )}
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              <Pagination count={data.count} page={page} pageSize={PAGE_SIZE} onPage={setPage} />
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit Offer — ${editing.offer_number}` : 'New Offer Letter'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select label="Application" required value={form.application} onChange={set('application')} disabled={!!editing}>
            <option value="">— Select Application —</option>
            {applications?.results.map(a => <option key={a.id} value={a.id}>{a.applicant_display ?? a.id}</option>)}
          </Select>
          <div className="grid grid-cols-2 gap-4">
            <Select label="Position" value={form.position} onChange={set('position')}>
              <option value="">— Select Position —</option>
              {positions?.results.map(p => <option key={p.id} value={p.id}>{p.title} ({p.position_code})</option>)}
            </Select>
            <Select label="Grade" value={form.grade} onChange={set('grade')}>
              <option value="">— Select Grade —</option>
              {grades?.results.map(g => <option key={g.id} value={g.id}>{g.grade_code} — {g.grade_name}</option>)}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label={`Basic Salary (${symbol})`} type="number" step="0.01" required value={form.basic_salary} onChange={set('basic_salary')} placeholder="e.g. 5000.00" />
            <Input label={`Total Package (${symbol})`} type="number" step="0.01" required value={form.total_package} onChange={set('total_package')} placeholder="e.g. 6500.00" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Select label="Employment Type" value={form.employment_type} onChange={set('employment_type')}>
              {EMP_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </Select>
            <Select label="Status" value={form.status} onChange={set('status')}>
              {OFFER_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <DatePicker label="Start Date" value={form.start_date} onChange={v => setForm(prev => ({ ...prev, start_date: v }))} />
            <DatePicker label="Expiry Date" value={form.expiry_date} onChange={v => setForm(prev => ({ ...prev, expiry_date: v }))} />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Create Offer'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
