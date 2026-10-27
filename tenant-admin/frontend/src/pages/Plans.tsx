import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Package, Blocks, Plus, Pencil, Trash2, Users } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardContent } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Input, Select, Textarea } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { cn, apiErrorMessage } from '@/lib/utils'
import api from '@/lib/api'

type ModuleT = {
  id: string
  code: string
  name: string
  category: string
  category_display: string
  description: string
  is_active: boolean
}

type Plan = {
  id: string
  name: string
  slug: string
  description: string
  monthly_price: string | null
  seat_limit: number | null
  is_active: boolean
  modules: string[]
  module_details: ModuleT[]
  tenant_count: number
}

const CATEGORIES = [
  { value: 'CORE', label: 'Core' },
  { value: 'TALENT', label: 'Talent' },
  { value: 'FINANCE', label: 'Finance & Rewards' },
  { value: 'OPERATIONS', label: 'Operations' },
]

function slugify(s: string) {
  return s.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
}

function fmtPrice(price: string | null) {
  if (price === null) return 'Custom pricing'
  const n = Number(price)
  if (n === 0) return 'Free'
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}/mo`
}

const emptyPlanForm = {
  name: '', slug: '', description: '', monthly_price: '', seat_limit: '',
  is_active: true, modules: [] as string[],
}

const emptyModuleForm = {
  code: '', name: '', category: 'CORE', description: '', is_active: true,
}

export default function Plans() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<'plans' | 'modules'>('plans')

  const { data: modulesData, isLoading: modulesLoading } = useQuery({
    queryKey: ['modules'],
    queryFn: () => api.get('/modules/?page_size=100').then(r => r.data),
  })
  const modules: ModuleT[] = modulesData?.results ?? []

  const { data: plansData, isLoading: plansLoading } = useQuery({
    queryKey: ['plans'],
    queryFn: () => api.get('/plans/?page_size=100').then(r => r.data),
  })
  const plans: Plan[] = plansData?.results ?? []

  // ---- Plan modal state ----
  const [planModalOpen, setPlanModalOpen] = useState(false)
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null)
  const [planForm, setPlanForm] = useState(emptyPlanForm)
  const [slugTouched, setSlugTouched] = useState(false)

  function openCreatePlan() {
    setEditingPlan(null)
    setPlanForm(emptyPlanForm)
    setSlugTouched(false)
    setPlanModalOpen(true)
  }

  function openEditPlan(p: Plan) {
    setEditingPlan(p)
    setPlanForm({
      name: p.name, slug: p.slug, description: p.description,
      monthly_price: p.monthly_price ?? '', seat_limit: p.seat_limit != null ? String(p.seat_limit) : '',
      is_active: p.is_active, modules: p.modules,
    })
    setSlugTouched(true)
    setPlanModalOpen(true)
  }

  const createPlan = useMutation({
    mutationFn: (body: object) => api.post('/plans/', body),
    onSuccess: () => {
      toast.success('Plan created')
      qc.invalidateQueries({ queryKey: ['plans'] })
      setPlanModalOpen(false)
    },
    onError: (e: unknown) => toast.error(apiErrorMessage(e, 'Failed to create plan')),
  })

  const updatePlan = useMutation({
    mutationFn: ({ id, ...body }: { id: string } & object) => api.patch(`/plans/${id}/`, body),
    onSuccess: () => {
      toast.success('Plan updated')
      qc.invalidateQueries({ queryKey: ['plans'] })
      setPlanModalOpen(false)
    },
    onError: (e: unknown) => toast.error(apiErrorMessage(e, 'Failed to update plan')),
  })

  const deletePlan = useMutation({
    mutationFn: (id: string) => api.delete(`/plans/${id}/`),
    onSuccess: () => {
      toast.success('Plan deleted')
      qc.invalidateQueries({ queryKey: ['plans'] })
    },
    onError: (e: unknown) => toast.error(apiErrorMessage(e, 'Failed to delete plan')),
  })

  function submitPlan(e: React.FormEvent) {
    e.preventDefault()
    const body = {
      ...planForm,
      monthly_price: planForm.monthly_price === '' ? null : planForm.monthly_price,
      seat_limit: planForm.seat_limit === '' ? null : Number(planForm.seat_limit),
    }
    if (editingPlan) updatePlan.mutate({ id: editingPlan.id, ...body })
    else createPlan.mutate(body)
  }

  function toggleModuleInPlan(moduleId: string) {
    setPlanForm(f => ({
      ...f,
      modules: f.modules.includes(moduleId) ? f.modules.filter(id => id !== moduleId) : [...f.modules, moduleId],
    }))
  }

  function handleDeletePlan(p: Plan) {
    if (confirm(`Delete the "${p.name}" plan?${p.tenant_count ? ` ${p.tenant_count} tenant(s) are on it and must be moved first.` : ''}`)) {
      deletePlan.mutate(p.id)
    }
  }

  // ---- Module modal state ----
  const [moduleModalOpen, setModuleModalOpen] = useState(false)
  const [editingModule, setEditingModule] = useState<ModuleT | null>(null)
  const [moduleForm, setModuleForm] = useState(emptyModuleForm)

  function openCreateModule() {
    setEditingModule(null)
    setModuleForm(emptyModuleForm)
    setModuleModalOpen(true)
  }

  function openEditModule(m: ModuleT) {
    setEditingModule(m)
    setModuleForm({ code: m.code, name: m.name, category: m.category, description: m.description, is_active: m.is_active })
    setModuleModalOpen(true)
  }

  const createModule = useMutation({
    mutationFn: (body: object) => api.post('/modules/', body),
    onSuccess: () => {
      toast.success('Module created')
      qc.invalidateQueries({ queryKey: ['modules'] })
      setModuleModalOpen(false)
    },
    onError: (e: unknown) => toast.error(apiErrorMessage(e, 'Failed to create module')),
  })

  const updateModule = useMutation({
    mutationFn: ({ id, ...body }: { id: string } & object) => api.patch(`/modules/${id}/`, body),
    onSuccess: () => {
      toast.success('Module updated')
      qc.invalidateQueries({ queryKey: ['modules'] })
      qc.invalidateQueries({ queryKey: ['plans'] })
      setModuleModalOpen(false)
    },
    onError: (e: unknown) => toast.error(apiErrorMessage(e, 'Failed to update module')),
  })

  const deleteModule = useMutation({
    mutationFn: (id: string) => api.delete(`/modules/${id}/`),
    onSuccess: () => {
      toast.success('Module deleted')
      qc.invalidateQueries({ queryKey: ['modules'] })
      qc.invalidateQueries({ queryKey: ['plans'] })
    },
    onError: (e: unknown) => toast.error(apiErrorMessage(e, 'Failed to delete module')),
  })

  function submitModule(e: React.FormEvent) {
    e.preventDefault()
    if (editingModule) updateModule.mutate({ id: editingModule.id, ...moduleForm })
    else createModule.mutate(moduleForm)
  }

  function handleDeleteModule(m: ModuleT) {
    if (confirm(`Delete the "${m.name}" module? It will be removed from every plan that includes it.`)) {
      deleteModule.mutate(m.id)
    }
  }

  return (
    <AppLayout title="Plans">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex gap-1 bg-slate-100 p-1 rounded-lg w-fit">
            <button
              onClick={() => setTab('plans')}
              className={cn('px-4 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5', tab === 'plans' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700')}
            >
              <Package size={14} /> Plans
            </button>
            <button
              onClick={() => setTab('modules')}
              className={cn('px-4 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5', tab === 'modules' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700')}
            >
              <Blocks size={14} /> Modules
            </button>
          </div>
          {tab === 'plans' ? (
            <Button onClick={openCreatePlan}><Plus size={16} /> Add Plan</Button>
          ) : (
            <Button onClick={openCreateModule}><Plus size={16} /> Add Module</Button>
          )}
        </div>

        {tab === 'plans' && (
          plansLoading ? <PageSpinner /> : !plans.length ? (
            <Card><EmptyState icon={Package} title="No plans yet" description="Add a plan to start assigning tenants to it." action={<Button onClick={openCreatePlan}><Plus size={16} /> Add Plan</Button>} /></Card>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {plans.map(p => (
                <Card key={p.id} className={cn(!p.is_active && 'opacity-60')}>
                  <CardContent className="space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-semibold text-slate-900">{p.name}</p>
                        <p className="text-xs text-slate-400 font-mono">{p.slug}</p>
                      </div>
                      <div className="flex items-center gap-1">
                        <button onClick={() => openEditPlan(p)} className="p-1.5 rounded-lg text-slate-400 hover:text-primary-600 hover:bg-primary-50">
                          <Pencil size={14} />
                        </button>
                        <button onClick={() => handleDeletePlan(p)} className="p-1.5 rounded-lg text-slate-400 hover:text-danger-600 hover:bg-danger-50">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                    {p.description && <p className="text-sm text-slate-500">{p.description}</p>}
                    <div className="flex items-center gap-4 text-sm">
                      <span className="font-semibold text-slate-900">{fmtPrice(p.monthly_price)}</span>
                      <span className="text-slate-400">·</span>
                      <span className="text-slate-500">{p.seat_limit != null ? `${p.seat_limit} seats` : 'Unlimited seats'}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-slate-500">
                      <Users size={13} /> {p.tenant_count} tenant{p.tenant_count === 1 ? '' : 's'}
                      {!p.is_active && <Badge status="OFFBOARDED" label="Inactive" className="ml-2" />}
                    </div>
                    <div className="pt-2 border-t border-slate-100">
                      <p className="text-xs font-medium text-slate-500 mb-1.5">{p.module_details.length} module{p.module_details.length === 1 ? '' : 's'} included</p>
                      <div className="flex flex-wrap gap-1">
                        {p.module_details.slice(0, 6).map(m => (
                          <span key={m.id} className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs">{m.name}</span>
                        ))}
                        {p.module_details.length > 6 && (
                          <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-xs">+{p.module_details.length - 6} more</span>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )
        )}

        {tab === 'modules' && (
          <Card>
            {modulesLoading ? <PageSpinner /> : !modules.length ? (
              <EmptyState icon={Blocks} title="No modules yet" description="Add a module so it can be assigned to plans." action={<Button onClick={openCreateModule}><Plus size={16} /> Add Module</Button>} />
            ) : (
              <Table>
                <Thead>
                  <tr>
                    <Th>Name</Th>
                    <Th>Code</Th>
                    <Th>Category</Th>
                    <Th>Description</Th>
                    <Th>Status</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {modules.map(m => (
                    <Tr key={m.id}>
                      <Td className="font-medium text-slate-900">{m.name}</Td>
                      <Td><span className="font-mono text-xs text-slate-500">{m.code}</span></Td>
                      <Td><Badge status={m.category} label={m.category_display} /></Td>
                      <Td className="text-slate-500">{m.description || '—'}</Td>
                      <Td>{m.is_active ? <Badge status="ACTIVE" label="Active" /> : <Badge status="OFFBOARDED" label="Inactive" />}</Td>
                      <Td onClick={e => e.stopPropagation()}>
                        <div className="flex items-center gap-1 justify-end">
                          <button onClick={() => openEditModule(m)} className="p-1.5 rounded-lg text-slate-400 hover:text-primary-600 hover:bg-primary-50">
                            <Pencil size={14} />
                          </button>
                          <button onClick={() => handleDeleteModule(m)} className="p-1.5 rounded-lg text-slate-400 hover:text-danger-600 hover:bg-danger-50">
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            )}
          </Card>
        )}
      </div>

      {/* Plan modal */}
      <Modal open={planModalOpen} onClose={() => setPlanModalOpen(false)} title={editingPlan ? 'Edit Plan' : 'Add Plan'} size="lg">
        <form onSubmit={submitPlan} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Plan name" required value={planForm.name}
              onChange={e => {
                const name = e.target.value
                setPlanForm(f => ({ ...f, name, slug: slugTouched ? f.slug : slugify(name) }))
              }}
              placeholder="Professional"
            />
            <Input
              label="Slug" required value={planForm.slug}
              onChange={e => { setSlugTouched(true); setPlanForm(f => ({ ...f, slug: e.target.value })) }}
              placeholder="professional"
            />
          </div>
          <Textarea
            label="Description" value={planForm.description}
            onChange={e => setPlanForm(f => ({ ...f, description: e.target.value }))}
            placeholder="Who this plan is for"
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Monthly price (USD)" type="number" min="0" step="1" value={planForm.monthly_price}
              onChange={e => setPlanForm(f => ({ ...f, monthly_price: e.target.value }))}
              placeholder="Leave blank for custom pricing"
            />
            <Input
              label="Seat limit" type="number" min="1" step="1" value={planForm.seat_limit}
              onChange={e => setPlanForm(f => ({ ...f, seat_limit: e.target.value }))}
              placeholder="Leave blank for unlimited"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={planForm.is_active} onChange={e => setPlanForm(f => ({ ...f, is_active: e.target.checked }))} className="rounded border-slate-300 text-primary-600 focus:ring-primary-500" />
            Active — selectable for new tenants
          </label>

          <div>
            <p className="text-sm font-medium text-slate-700 mb-2">Modules included</p>
            <div className="border border-slate-200 rounded-lg divide-y divide-slate-100 max-h-72 overflow-y-auto">
              {CATEGORIES.map(cat => {
                const catModules = modules.filter(m => m.category === cat.value)
                if (!catModules.length) return null
                return (
                  <div key={cat.value} className="p-3">
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">{cat.label}</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                      {catModules.map(m => (
                        <label key={m.id} className={cn('flex items-center gap-2 text-sm px-2 py-1 rounded-md cursor-pointer', !m.is_active && 'opacity-50')}>
                          <input
                            type="checkbox"
                            checked={planForm.modules.includes(m.id)}
                            onChange={() => toggleModuleInPlan(m.id)}
                            className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                          />
                          <span className="text-slate-700">{m.name}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={() => setPlanModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={createPlan.isPending || updatePlan.isPending}>{editingPlan ? 'Save Changes' : 'Create Plan'}</Button>
          </div>
        </form>
      </Modal>

      {/* Module modal */}
      <Modal open={moduleModalOpen} onClose={() => setModuleModalOpen(false)} title={editingModule ? 'Edit Module' : 'Add Module'} size="md">
        <form onSubmit={submitModule} className="space-y-4">
          <Input
            label="Name" required value={moduleForm.name}
            onChange={e => setModuleForm(f => ({ ...f, name: e.target.value }))}
            placeholder="Payroll"
          />
          <Input
            label="Code" required value={moduleForm.code}
            onChange={e => setModuleForm(f => ({ ...f, code: slugify(e.target.value) }))}
            placeholder="payroll"
          />
          <Select label="Category" value={moduleForm.category} onChange={e => setModuleForm(f => ({ ...f, category: e.target.value }))}>
            {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </Select>
          <Input
            label="Description" value={moduleForm.description}
            onChange={e => setModuleForm(f => ({ ...f, description: e.target.value }))}
            placeholder="What this module covers"
          />
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={moduleForm.is_active} onChange={e => setModuleForm(f => ({ ...f, is_active: e.target.checked }))} className="rounded border-slate-300 text-primary-600 focus:ring-primary-500" />
            Active — selectable in the plan editor
          </label>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={() => setModuleModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={createModule.isPending || updateModule.isPending}>{editingModule ? 'Save Changes' : 'Create Module'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
