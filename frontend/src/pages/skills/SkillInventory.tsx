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
import { Plus, Search, Zap } from 'lucide-react'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type Skill = {
  id: string; code: string; name: string; category_name: string; is_active: boolean
}

const emptyForm = { code: '', name: '', category: '', description: '', is_active: true }

export default function SkillInventory() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [categories, setCategories] = useState<{ id: string; name: string }[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['skills', page],
    queryFn: () => api.get(`/skills/skills/?page=${page}`).then(r => r.data),
  })

  function openCreate() {
    setForm(emptyForm)
    api.get('/skills/categories/?page_size=100').then(r => setCategories(r.data.results || []))
    setModalOpen(true)
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/skills/skills/', body),
    onSuccess: () => { toast.success('Skill created'); qc.invalidateQueries({ queryKey: ['skills'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to create skill'),
  })

  const filtered = search
    ? data?.results?.filter((r: Skill) =>
        r.name?.toLowerCase().includes(search.toLowerCase()) ||
        r.code?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="Skill Inventory">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="relative max-w-sm">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search skills..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <Button onClick={openCreate}><Plus size={16} /> New Skill</Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={Zap} title="No skills defined" action={<Button onClick={openCreate}><Plus size={16} />New Skill</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Code</Th><Th>Name</Th><Th>Category</Th><Th>Status</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: Skill) => (
                    <Tr key={r.id}>
                      <Td className="font-mono text-sm">{r.code}</Td>
                      <Td className="font-medium">{r.name}</Td>
                      <Td className="text-gray-600">{r.category_name}</Td>
                      <Td><Badge status={r.is_active ? 'ACTIVE' : 'INACTIVE'} /></Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              {!search && <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />}
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Skill">
        <form onSubmit={e => { e.preventDefault(); create.mutate(form) }} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input label="Code *" value={form.code} onChange={e => setForm(f => ({ ...f, code: e.target.value.toUpperCase() }))} required />
            <Input label="Name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
          </div>
          <Select label="Category *" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} required>
            <option value="">Select category…</option>
            {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </Select>
          <Textarea label="Description" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} rows={2} />
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} /> Active</label>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Create Skill</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
