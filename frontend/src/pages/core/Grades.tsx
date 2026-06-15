import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { BarChart2, Plus, Pencil, Trash2 } from 'lucide-react'
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
import { currency } from '@/lib/utils'
import { useCurrency } from '@/hooks/useCurrency'
import api from '@/lib/api'

interface Grade {
  id: string
  grade_code: string
  grade_name: string
  level: number
  pay_band_min: string | number | null
  pay_band_max: string | number | null
  is_active: boolean
}

interface ApiList {
  count: number
  results: Grade[]
}

const PAGE_SIZE = 15

const emptyForm = {
  grade_code: '',
  grade_name: '',
  level: '',
  pay_band_min: '',
  pay_band_max: '',
  is_active: 'true',
}

export default function Grades() {
  const qc = useQueryClient()
  const { symbol } = useCurrency()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Grade | null>(null)
  const [form, setForm] = useState(emptyForm)

  const params = { page, page_size: PAGE_SIZE, ...(search ? { search } : {}) }

  const { data, isLoading } = useQuery<ApiList>({
    queryKey: ['grades', params],
    queryFn: () => api.get('/core/grades/', { params }).then(r => r.data),
  })

  const create = useMutation({
    mutationFn: (body: typeof emptyForm) => api.post('/core/grades/', body),
    onSuccess: () => {
      toast.success('Grade created')
      qc.invalidateQueries({ queryKey: ['grades'] })
      closeModal()
    },
    onError: () => toast.error('Failed to create grade'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyForm & { id: string }) =>
      api.patch(`/core/grades/${id}/`, body),
    onSuccess: () => {
      toast.success('Grade updated')
      qc.invalidateQueries({ queryKey: ['grades'] })
      closeModal()
    },
    onError: () => toast.error('Failed to update grade'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/core/grades/${id}/`),
    onSuccess: () => { toast.success('Grade deleted'); qc.invalidateQueries({ queryKey: ['grades'] }) },
    onError: () => toast.error('Cannot delete — grade may be linked to positions or employees'),
  })

  function openCreate() {
    setEditing(null)
    setForm(emptyForm)
    setModalOpen(true)
  }

  function openEdit(g: Grade) {
    setEditing(g)
    setForm({
      grade_code: g.grade_code,
      grade_name: g.grade_name,
      level: String(g.level),
      pay_band_min: g.pay_band_min != null ? String(g.pay_band_min) : '',
      pay_band_max: g.pay_band_max != null ? String(g.pay_band_max) : '',
      is_active: g.is_active ? 'true' : 'false',
    })
    setModalOpen(true)
  }

  function closeModal() {
    setModalOpen(false)
    setEditing(null)
    setForm(emptyForm)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = {
      ...form,
      is_active: form.is_active === 'true',
      pay_band_min: form.pay_band_min || null,
      pay_band_max: form.pay_band_max || null,
    }
    if (editing) {
      update.mutate({ id: editing.id, ...payload } as typeof emptyForm & { id: string })
    } else {
      create.mutate(payload as typeof emptyForm)
    }
  }

  function handleDelete(g: Grade) {
    if (!window.confirm(`Delete grade "${g.grade_name}"? This cannot be undone.`)) return
    remove.mutate(g.id)
  }

  const set = (k: keyof typeof emptyForm) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm(prev => ({ ...prev, [k]: e.target.value }))

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="Grades">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Grades & Pay Bands</CardTitle>
              <Button onClick={openCreate}><Plus size={16} />Add Grade</Button>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <Input
              placeholder="Search by code or name…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
              className="max-w-sm"
            />
          </CardContent>

          {isLoading ? (
            <PageSpinner />
          ) : !data?.results.length ? (
            <EmptyState
              icon={BarChart2}
              title="No grades found"
              description="Create pay grades to define compensation bands."
              action={<Button onClick={openCreate}><Plus size={16} />Add Grade</Button>}
            />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Code</Th>
                    <Th>Name</Th>
                    <Th>Level</Th>
                    <Th>Pay Band Min</Th>
                    <Th>Pay Band Max</Th>
                    <Th>Status</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map(g => (
                    <Tr key={g.id}>
                      <Td className="font-mono text-xs">{g.grade_code}</Td>
                      <Td className="font-medium">{g.grade_name}</Td>
                      <Td>{g.level}</Td>
                      <Td>{currency(g.pay_band_min, symbol)}</Td>
                      <Td>{currency(g.pay_band_max, symbol)}</Td>
                      <Td><Badge status={g.is_active ? 'ACTIVE' : 'INACTIVE'} /></Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(g)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit">
                            <Pencil size={15} />
                          </button>
                          <button onClick={() => handleDelete(g)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete">
                            <Trash2 size={15} />
                          </button>
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

      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit — ${editing.grade_name}` : 'Add Grade'}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="Grade Code" required value={form.grade_code} onChange={set('grade_code')} placeholder="e.g. G7" />
            <Input label="Grade Name" required value={form.grade_name} onChange={set('grade_name')} placeholder="e.g. Senior" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Level" type="number" min={1} required value={form.level} onChange={set('level')} placeholder="e.g. 7" />
            <Select label="Status" value={form.is_active} onChange={set('is_active')}>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label={`Pay Band Min (${symbol})`} type="number" step="0.01" value={form.pay_band_min} onChange={set('pay_band_min')} placeholder="e.g. 5000.00" />
            <Input label={`Pay Band Max (${symbol})`} type="number" step="0.01" value={form.pay_band_max} onChange={set('pay_band_max')} placeholder="e.g. 9000.00" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Create'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
