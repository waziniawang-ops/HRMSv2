import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { UserCheck, Plus, Pencil, Trash2 } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input, Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import api from '@/lib/api'

interface Applicant {
  id: string
  full_name: string
  email: string
  phone: string
  profile_status: string
  linkedin_url?: string
}

interface ApiList { count: number; results: Applicant[] }

const PAGE_SIZE = 15
const PROFILE_STATUSES = ['ACTIVE', 'INACTIVE', 'BLACKLISTED']

const emptyForm = { full_name: '', email: '', phone: '', profile_status: 'ACTIVE', linkedin_url: '' }

export default function Applicants() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Applicant | null>(null)
  const [form, setForm] = useState(emptyForm)

  const params = { page, page_size: PAGE_SIZE, ...(search ? { search } : {}) }

  const { data, isLoading } = useQuery<ApiList>({
    queryKey: ['applicants', params],
    queryFn: () => api.get('/recruitment/applicants/', { params }).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: (body: typeof emptyForm) => api.post('/recruitment/applicants/', body),
    onSuccess: () => { toast.success('Applicant created'); qc.invalidateQueries({ queryKey: ['applicants'] }); closeModal() },
    onError: () => toast.error('Failed to create applicant — email may already be registered'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) => api.patch(`/recruitment/applicants/${id}/`, body),
    onSuccess: () => { toast.success('Applicant updated'); qc.invalidateQueries({ queryKey: ['applicants'] }); closeModal() },
    onError: () => toast.error('Failed to update applicant'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/recruitment/applicants/${id}/`),
    onSuccess: () => { toast.success('Applicant deleted'); qc.invalidateQueries({ queryKey: ['applicants'] }) },
    onError: () => toast.error('Cannot delete — applicant may have linked applications'),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }
  function openEdit(a: Applicant) {
    setEditing(a)
    setForm({ full_name: a.full_name, email: a.email, phone: a.phone ?? '', profile_status: a.profile_status, linkedin_url: a.linkedin_url ?? '' })
    setModalOpen(true)
  }
  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (editing) update.mutate({ id: editing.id, ...form })
    else create.mutate(form)
  }

  function handleDelete(a: Applicant) {
    if (!window.confirm(`Delete applicant "${a.full_name}"? This cannot be undone.`)) return
    remove.mutate(a.id)
  }

  const set = (k: keyof typeof emptyForm) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [k]: e.target.value }))

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Applicants">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Applicants</CardTitle>
              <Button onClick={openCreate}><Plus size={16} />Add Applicant</Button>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <Input placeholder="Search by name or email…" value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} className="max-w-sm" />
          </CardContent>

          {isLoading ? <PageSpinner /> : !data?.results.length ? (
            <EmptyState icon={UserCheck} title="No applicants found" description="No applicants match your search criteria." action={<Button onClick={openCreate}><Plus size={16} />Add Applicant</Button>} />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr><Th>Full Name</Th><Th>Email</Th><Th>Phone</Th><Th>Status</Th><Th></Th></tr>
                </Thead>
                <Tbody>
                  {data.results.map(a => (
                    <Tr key={a.id}>
                      <Td className="font-medium">{a.full_name}</Td>
                      <Td className="text-gray-500">{a.email}</Td>
                      <Td className="text-gray-500">{a.phone || '—'}</Td>
                      <Td><Badge status={a.profile_status} /></Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(a)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit"><Pencil size={15} /></button>
                          <button onClick={() => handleDelete(a)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete"><Trash2 size={15} /></button>
                        </div>
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

      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit — ${editing.full_name}` : 'Add Applicant'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="Full Name" required value={form.full_name} onChange={set('full_name')} placeholder="e.g. Ahmad bin Razif" />
            <Input label="Email" type="email" required value={form.email} onChange={set('email')} placeholder="ahmad@email.com" disabled={!!editing} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Phone" value={form.phone} onChange={set('phone')} placeholder="+60 12-345 6789" />
            <Select label="Profile Status" value={form.profile_status} onChange={set('profile_status')}>
              {PROFILE_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <Input label="LinkedIn URL" value={form.linkedin_url} onChange={set('linkedin_url')} placeholder="https://linkedin.com/in/..." />
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Create'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
