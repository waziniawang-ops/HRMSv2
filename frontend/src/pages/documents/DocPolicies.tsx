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
import { Plus, Search, BookOpen } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type DocPolicy = {
  id: string; code: string; name: string; version: string
  category_name: string; status: string
  effective_date: string; expiry_date: string | null; requires_acknowledgement: boolean
}

const emptyForm = { code: '', name: '', category: '', version: '1.0', content: '', status: 'DRAFT', effective_date: '', requires_acknowledgement: false }

export default function DocPolicies() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [categories, setCategories] = useState<{ id: string; name: string }[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['doc-policies', page],
    queryFn: () => api.get(`/documents/policies/?page=${page}`).then(r => r.data),
  })

  function openCreate() {
    setForm(emptyForm)
    api.get('/documents/categories/?page_size=100').then(r => setCategories(r.data.results || []))
    setModalOpen(true)
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/documents/policies/', body),
    onSuccess: () => { toast.success('Policy created'); qc.invalidateQueries({ queryKey: ['doc-policies'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to create policy'),
  })

  const filtered = search
    ? data?.results?.filter((r: DocPolicy) => r.name?.toLowerCase().includes(search.toLowerCase()) || r.code?.includes(search))
    : data?.results

  return (
    <AppLayout title="Policies">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="relative max-w-sm">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search policy name..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <Button onClick={openCreate}><Plus size={16} /> New Policy</Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={BookOpen} title="No policies found" action={<Button onClick={openCreate}><Plus size={16} />New Policy</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Code</Th><Th>Name</Th><Th>Version</Th><Th>Category</Th><Th>Effective</Th><Th>Expiry</Th><Th>Ack Required</Th><Th>Status</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: DocPolicy) => (
                    <Tr key={r.id}>
                      <Td className="font-mono text-sm">{r.code}</Td>
                      <Td className="font-medium">{r.name}</Td>
                      <Td className="text-gray-600">v{r.version}</Td>
                      <Td className="text-gray-600">{r.category_name}</Td>
                      <Td>{r.effective_date ? fmt(r.effective_date) : '—'}</Td>
                      <Td>{r.expiry_date ? fmt(r.expiry_date) : '—'}</Td>
                      <Td>{r.requires_acknowledgement ? <Badge status="REQUIRED" /> : <span className="text-gray-400 text-sm">No</span>}</Td>
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

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Policy">
        <form onSubmit={e => { e.preventDefault(); create.mutate(form) }} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input label="Code *" value={form.code} onChange={e => setForm(f => ({ ...f, code: e.target.value.toUpperCase() }))} required />
            <Input label="Version" value={form.version} onChange={e => setForm(f => ({ ...f, version: e.target.value }))} />
          </div>
          <Input label="Name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
          <Select label="Category *" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} required>
            <option value="">Select category…</option>
            {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </Select>
          <Textarea label="Content *" value={form.content} onChange={e => setForm(f => ({ ...f, content: e.target.value }))} rows={5} required />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Effective Date" type="date" value={form.effective_date} onChange={e => setForm(f => ({ ...f, effective_date: e.target.value }))} />
            <Select label="Status" value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
              {['DRAFT','PUBLISHED','ARCHIVED'].map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </div>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.requires_acknowledgement} onChange={e => setForm(f => ({ ...f, requires_acknowledgement: e.target.checked }))} /> Requires Acknowledgement</label>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Create Policy</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
