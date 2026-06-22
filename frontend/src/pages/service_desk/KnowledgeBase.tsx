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
import { Plus, Search, Pencil, BookOpen } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type Article = { id: string; title: string; category_name: string; status: string; views_count: number; is_featured: boolean; published_at: string | null }
const emptyForm = { title: '', slug: '', content: '', status: 'DRAFT', is_featured: false }

export default function KnowledgeBase() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Article | null>(null)
  const [form, setForm] = useState<typeof emptyForm>(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['knowledge-articles', page],
    queryFn: () => api.get(`/service-desk/knowledge-articles/?page=${page}`).then(r => r.data),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }
  function openEdit(r: Article) { setEditing(r); setForm({ title: r.title, slug: '', content: '', status: r.status, is_featured: r.is_featured }); setModalOpen(true) }

  const save = useMutation({
    mutationFn: (body: object) => editing ? api.patch(`/service-desk/knowledge-articles/${editing.id}/`, body) : api.post('/service-desk/knowledge-articles/', body),
    onSuccess: () => { toast.success(editing ? 'Article updated' : 'Article created'); qc.invalidateQueries({ queryKey: ['knowledge-articles'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to save'),
  })

  const publish = useMutation({
    mutationFn: (id: string) => api.post(`/service-desk/knowledge-articles/${id}/publish/`, {}),
    onSuccess: () => { toast.success('Published'); qc.invalidateQueries({ queryKey: ['knowledge-articles'] }) },
    onError: () => toast.error('Failed to publish'),
  })

  const filtered = search ? data?.results?.filter((r: Article) => r.title?.toLowerCase().includes(search.toLowerCase())) : data?.results

  return (
    <AppLayout title="Knowledge Base">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search articles..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <Button onClick={openCreate}><Plus size={16} /> New Article</Button>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={BookOpen} title="No articles" action={<Button onClick={openCreate}><Plus size={16} />New Article</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Title</Th><Th>Status</Th><Th>Views</Th><Th>Featured</Th><Th>Published</Th><Th></Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: Article) => (
                    <Tr key={r.id}>
                      <Td className="font-medium max-w-sm truncate">{r.title}</Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td>{r.views_count}</Td>
                      <Td>{r.is_featured ? '⭐' : '—'}</Td>
                      <Td>{r.published_at ? fmt(r.published_at) : '—'}</Td>
                      <Td>
                        <div className="flex gap-2 justify-end">
                          <button onClick={() => openEdit(r)} className="p-1.5 text-gray-400 hover:text-blue-600 rounded-lg"><Pencil size={15} /></button>
                          {r.status === 'DRAFT' && <button onClick={() => publish.mutate(r.id)} className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">Publish</button>}
                        </div>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              {!search && <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />}
            </>
          )}
        </Card>
      </div>
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Edit Article' : 'New Article'}>
        <form onSubmit={e => { e.preventDefault(); save.mutate(form) }} className="space-y-4">
          <Input label="Title *" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value, slug: e.target.value.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '') }))} required />
          {!editing && <Input label="Slug *" value={form.slug} onChange={e => setForm(f => ({ ...f, slug: e.target.value }))} required />}
          <Textarea label="Content *" value={form.content} onChange={e => setForm(f => ({ ...f, content: e.target.value }))} rows={6} required={!editing} />
          <div className="flex items-center gap-4">
            <Select label="Status" value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
              {['DRAFT','PUBLISHED','ARCHIVED'].map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
            <label className="flex items-center gap-2 text-sm mt-5"><input type="checkbox" checked={form.is_featured} onChange={e => setForm(f => ({ ...f, is_featured: e.target.checked }))} /> Featured</label>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={save.isPending}>{editing ? 'Save' : 'Create'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
