import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input, Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Plus, Search, Pencil, Trash2, Settings } from 'lucide-react'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type Element = { id: string; code: string; name: string; category: string; is_taxable: boolean; is_pensionable: boolean; is_active: boolean; display_order: number }

const emptyForm = { code: '', name: '', category: 'BASIC', is_taxable: true, is_pensionable: false, is_active: true, display_order: 0 }
const CATEGORIES = ['BASIC','ALLOWANCE','DEDUCTION','CONTRIBUTION','TAX']

export default function PayrollElements() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Element | null>(null)
  const [form, setForm] = useState<typeof emptyForm>(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['payroll-elements', page],
    queryFn: () => api.get(`/payroll/payroll-elements/?page=${page}`).then(r => r.data),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }
  function openEdit(r: Element) { setEditing(r); setForm({ code: r.code, name: r.name, category: r.category, is_taxable: r.is_taxable, is_pensionable: r.is_pensionable, is_active: r.is_active, display_order: r.display_order }); setModalOpen(true) }

  const save = useMutation({
    mutationFn: (body: object) => editing ? api.patch(`/payroll/payroll-elements/${editing.id}/`, body) : api.post('/payroll/payroll-elements/', body),
    onSuccess: () => { toast.success(editing ? 'Element updated' : 'Element created'); qc.invalidateQueries({ queryKey: ['payroll-elements'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to save element'),
  })
  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/payroll/payroll-elements/${id}/`),
    onSuccess: () => { toast.success('Deleted'); qc.invalidateQueries({ queryKey: ['payroll-elements'] }) },
    onError: () => toast.error('Cannot delete'),
  })

  const filtered = search ? data?.results?.filter((r: Element) => r.name?.toLowerCase().includes(search.toLowerCase()) || r.code?.includes(search)) : data?.results

  return (
    <AppLayout title="Payroll Elements">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search elements..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <Button onClick={openCreate}><Plus size={16} /> New Element</Button>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={Settings} title="No payroll elements" action={<Button onClick={openCreate}><Plus size={16} />New Element</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Code</Th><Th>Name</Th><Th>Category</Th><Th>Taxable</Th><Th>Pensionable</Th><Th>Order</Th><Th>Active</Th><Th></Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: Element) => (
                    <Tr key={r.id}>
                      <Td className="font-mono text-sm">{r.code}</Td>
                      <Td className="font-medium">{r.name}</Td>
                      <Td><span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{r.category}</span></Td>
                      <Td>{r.is_taxable ? '✓' : '—'}</Td>
                      <Td>{r.is_pensionable ? '✓' : '—'}</Td>
                      <Td>{r.display_order}</Td>
                      <Td>{r.is_active ? <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">Active</span> : <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">Inactive</span>}</Td>
                      <Td>
                        <div className="flex gap-2 justify-end">
                          <button onClick={() => openEdit(r)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"><Pencil size={15} /></button>
                          <button onClick={() => window.confirm('Delete this element?') && remove.mutate(r.id)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"><Trash2 size={15} /></button>
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
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Edit Element' : 'New Payroll Element'}>
        <form onSubmit={e => { e.preventDefault(); save.mutate(form) }} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input label="Code *" value={form.code} onChange={e => setForm(f => ({ ...f, code: e.target.value.toUpperCase() }))} required />
            <Input label="Name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Select label="Category" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))}>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </Select>
            <Input label="Display Order" type="number" value={String(form.display_order)} onChange={e => setForm(f => ({ ...f, display_order: Number(e.target.value) }))} />
          </div>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_taxable} onChange={e => setForm(f => ({ ...f, is_taxable: e.target.checked }))} /> Taxable</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_pensionable} onChange={e => setForm(f => ({ ...f, is_pensionable: e.target.checked }))} /> Pensionable</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} /> Active</label>
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
