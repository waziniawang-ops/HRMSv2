import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Input, Select } from '@/components/ui/Input'
import { DatePicker } from '@/components/ui/DatePicker'
import { Modal } from '@/components/ui/Modal'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { GitBranch, Shield, Plus, Pencil, Trash2, GripVertical, X } from 'lucide-react'
import api from '@/lib/api'
import toast from 'react-hot-toast'

// ─── Types ───────────────────────────────────────────────────────────────────

type Step = { step: number; role: string; sla_hours: number }

type Rule = {
  id: string
  workflow_code: string
  module_code: string
  applies_to: string
  description: string
  steps: Step[]
  segregation_of_duties: boolean
  maker_cannot_approve: boolean
  audit_required: boolean
  is_active: boolean
  version: number
  effective_from: string
  effective_to: string | null
}

type FormStep = { role: string; sla_hours: string }

type FormData = {
  workflow_code: string
  module_code: string
  applies_to: string
  description: string
  segregation_of_duties: boolean
  maker_cannot_approve: boolean
  audit_required: boolean
  is_active: boolean
  effective_from: string
  effective_to: string
  steps: FormStep[]
}

// ─── Constants ───────────────────────────────────────────────────────────────

const ROLES = [
  { value: 'HR_CHECKER',      label: 'HR Checker' },
  { value: 'HR_ADMIN',        label: 'HR Admin' },
  { value: 'HR_MAKER',        label: 'HR Maker' },
  { value: 'SYSTEM_ADMIN',    label: 'System Admin' },
  { value: 'HIRING_MANAGER',  label: 'Hiring Manager' },
  { value: 'RECRUITER',       label: 'Recruiter' },
  { value: 'FINANCE_CHECKER', label: 'Finance Checker' },
  { value: 'TALENT_COMMITTEE',label: 'Talent Committee' },
  { value: 'HR_PERFORMANCE',  label: 'HR Performance Officer' },
  { value: 'LD_OFFICER',      label: 'L&D Officer' },
  { value: 'LD_CHECKER',      label: 'L&D Checker' },
  { value: 'MANAGER',         label: 'Manager' },
]

const MODULES = [
  'recruitment', 'onboarding', 'workforce', 'succession',
  'performance', 'learning', 'core_hr', 'attendance',
]

const BLANK_FORM: FormData = {
  workflow_code: '',
  module_code: '',
  applies_to: '',
  description: '',
  segregation_of_duties: true,
  maker_cannot_approve: true,
  audit_required: true,
  is_active: true,
  effective_from: new Date().toISOString().slice(0, 10),
  effective_to: '',
  steps: [{ role: 'HR_CHECKER', sla_hours: '24' }],
}

// ─── Step Builder ─────────────────────────────────────────────────────────────

function StepBuilder({
  steps, onChange,
}: {
  steps: FormStep[]
  onChange: (steps: FormStep[]) => void
}) {
  function addStep() {
    onChange([...steps, { role: 'HR_CHECKER', sla_hours: '24' }])
  }

  function removeStep(i: number) {
    onChange(steps.filter((_, idx) => idx !== i))
  }

  function updateStep(i: number, field: keyof FormStep, value: string) {
    onChange(steps.map((s, idx) => idx === i ? { ...s, [field]: value } : s))
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-700">Approval Steps</p>
        <Button type="button" size="sm" variant="secondary" onClick={addStep}>
          <Plus size={13} /> Add Step
        </Button>
      </div>

      {steps.length === 0 && (
        <p className="text-xs text-gray-400 py-2 text-center border border-dashed border-gray-200 rounded-lg">
          No steps — click "Add Step" to define the approval chain.
        </p>
      )}

      {steps.map((s, i) => (
        <div key={i} className="flex items-center gap-2 p-3 bg-gray-50 rounded-xl border border-gray-100">
          <GripVertical size={14} className="text-gray-300 shrink-0" />

          {/* Step number badge */}
          <span className="w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center shrink-0">
            {i + 1}
          </span>

          {/* Role */}
          <select
            value={s.role}
            onChange={e => updateStep(i, 'role', e.target.value)}
            className="flex-1 px-2 py-1.5 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {ROLES.map(r => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>

          {/* SLA */}
          <div className="flex items-center gap-1.5 shrink-0">
            <input
              type="number"
              min="1"
              max="720"
              value={s.sla_hours}
              onChange={e => updateStep(i, 'sla_hours', e.target.value)}
              className="w-16 px-2 py-1.5 border border-gray-200 rounded-lg text-sm text-center focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-xs text-gray-400 shrink-0">hrs SLA</span>
          </div>

          {/* Remove */}
          <button
            type="button"
            onClick={() => removeStep(i)}
            disabled={steps.length === 1}
            className="p-1 text-gray-300 hover:text-red-500 disabled:cursor-not-allowed disabled:opacity-30 transition-colors"
            title="Remove step"
          >
            <X size={15} />
          </button>
        </div>
      ))}
    </div>
  )
}

// ─── Rule Form Modal ──────────────────────────────────────────────────────────

function RuleModal({
  open, onClose, editing,
}: {
  open: boolean
  onClose: () => void
  editing: Rule | null
}) {
  const qc = useQueryClient()
  const [form, setForm] = useState<FormData>(BLANK_FORM)

  useEffect(() => {
    if (!open) return
    if (editing) {
      setForm({
        workflow_code: editing.workflow_code,
        module_code: editing.module_code,
        applies_to: editing.applies_to,
        description: editing.description,
        segregation_of_duties: editing.segregation_of_duties,
        maker_cannot_approve: editing.maker_cannot_approve,
        audit_required: editing.audit_required,
        is_active: editing.is_active,
        effective_from: editing.effective_from,
        effective_to: editing.effective_to ?? '',
        steps: editing.steps.map(s => ({
          role: s.role,
          sla_hours: String(s.sla_hours),
        })),
      })
    } else {
      setForm({ ...BLANK_FORM, effective_from: new Date().toISOString().slice(0, 10) })
    }
  }, [open, editing])

  function set<K extends keyof FormData>(key: K, val: FormData[K]) {
    setForm(f => ({ ...f, [key]: val }))
  }

  function buildPayload() {
    return {
      workflow_code: form.workflow_code.trim().toUpperCase(),
      module_code: form.module_code,
      applies_to: form.applies_to.trim(),
      description: form.description.trim(),
      segregation_of_duties: form.segregation_of_duties,
      maker_cannot_approve: form.maker_cannot_approve,
      audit_required: form.audit_required,
      is_active: form.is_active,
      effective_from: form.effective_from,
      effective_to: form.effective_to || null,
      steps: form.steps.map((s, i) => ({
        step: i + 1,
        role: s.role,
        sla_hours: parseInt(s.sla_hours) || 24,
      })),
    }
  }

  const save = useMutation({
    mutationFn: (payload: ReturnType<typeof buildPayload>) =>
      editing
        ? api.patch(`/workflow/rules/${editing.id}/`, payload)
        : api.post('/workflow/rules/', payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['workflow-rules'] })
      toast.success(editing ? 'Rule updated' : 'Rule created')
      onClose()
    },
    onError: (e: { response?: { data?: Record<string, string[]> } }) => {
      const msgs = e?.response?.data
      if (msgs) {
        const first = Object.values(msgs)[0]
        toast.error(Array.isArray(first) ? first[0] : 'Validation error')
      } else {
        toast.error('Failed to save rule')
      }
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.workflow_code.trim()) { toast.error('Workflow code is required'); return }
    if (!form.module_code) { toast.error('Module is required'); return }
    if (!form.applies_to.trim()) { toast.error('Applies-to is required'); return }
    if (form.steps.length === 0) { toast.error('At least one approval step is required'); return }
    save.mutate(buildPayload())
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={editing ? `Edit — ${editing.workflow_code}` : 'New Workflow Rule'}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Row 1: code + module */}
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Workflow Code"
            value={form.workflow_code}
            onChange={e => set('workflow_code', e.target.value.toUpperCase())}
            placeholder="e.g. RECRUITMENT_POSTING"
            disabled={!!editing}
            required
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Module</label>
            <select
              value={form.module_code}
              onChange={e => set('module_code', e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select module…</option>
              {MODULES.map(m => (
                <option key={m} value={m}>{m.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Applies To */}
        <Input
          label="Applies To"
          value={form.applies_to}
          onChange={e => set('applies_to', e.target.value)}
          placeholder="e.g. recruitment.job_posting"
          required
        />

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            value={form.description}
            onChange={e => set('description', e.target.value)}
            rows={2}
            placeholder="Brief description of what this workflow governs…"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Step builder */}
        <StepBuilder
          steps={form.steps}
          onChange={steps => set('steps', steps)}
        />

        {/* Effective dates */}
        <div className="grid grid-cols-2 gap-4">
          <DatePicker
            label="Effective From"
            value={form.effective_from}
            onChange={v => set('effective_from', v)}
            required
          />
          <DatePicker
            label="Effective To (optional)"
            value={form.effective_to}
            onChange={v => set('effective_to', v)}
          />
        </div>

        {/* Toggles */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {(
            [
              { key: 'segregation_of_duties', label: 'Segregation of Duties' },
              { key: 'maker_cannot_approve',  label: 'Maker Cannot Approve' },
              { key: 'audit_required',         label: 'Audit Required' },
              { key: 'is_active',              label: 'Active' },
            ] as { key: keyof FormData; label: string }[]
          ).map(({ key, label }) => (
            <label
              key={key}
              className="flex items-center gap-2 p-3 rounded-xl border border-gray-100 cursor-pointer hover:bg-gray-50"
            >
              <input
                type="checkbox"
                checked={form[key] as boolean}
                onChange={e => set(key, e.target.checked)}
                className="rounded text-blue-600"
              />
              <span className="text-xs font-medium text-gray-700">{label}</span>
            </label>
          ))}
        </div>

        <div className="flex justify-end gap-3 pt-1">
          <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" loading={save.isPending}>
            {editing ? 'Save Changes' : 'Create Rule'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function WorkflowRules() {
  const qc = useQueryClient()
  const [selected, setSelected] = useState<Rule | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Rule | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['workflow-rules'],
    queryFn: () => api.get('/workflow/rules/?page_size=200').then(r => r.data),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/workflow/rules/${id}/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['workflow-rules'] })
      if (selected?.id === editing?.id) setSelected(null)
      toast.success('Rule deleted')
    },
    onError: () => toast.error('Failed to delete rule'),
  })

  function openCreate() {
    setEditing(null)
    setModalOpen(true)
  }

  function openEdit(rule: Rule) {
    setEditing(rule)
    setModalOpen(true)
  }

  function confirmDelete(rule: Rule) {
    if (window.confirm(`Delete workflow rule "${rule.workflow_code}"? This cannot be undone.`)) {
      remove.mutate(rule.id)
    }
  }

  return (
    <AppLayout title="Workflow Rules">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Rules table */}
        <div className="lg:col-span-2">
          <div className="flex justify-end mb-3">
            <Button onClick={openCreate}>
              <Plus size={15} /> New Rule
            </Button>
          </div>

          <Card>
            {isLoading ? (
              <PageSpinner />
            ) : !data?.results?.length ? (
              <EmptyState
                icon={GitBranch}
                title="No workflow rules"
                description="Create a rule to enable maker-checker approvals."
              />
            ) : (
              <Table>
                <Thead>
                  <tr>
                    <Th>Code</Th>
                    <Th>Module</Th>
                    <Th>Applies To</Th>
                    <Th>Steps</Th>
                    <Th>SoD</Th>
                    <Th>Active</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map((r: Rule) => (
                    <Tr
                      key={r.id}
                      onClick={() => setSelected(r)}
                      className={`cursor-pointer ${selected?.id === r.id ? 'bg-blue-50' : ''}`}
                    >
                      <Td>
                        <span className="font-mono text-xs font-semibold text-gray-700">
                          {r.workflow_code}
                        </span>
                      </Td>
                      <Td>
                        <Badge status={r.module_code} label={r.module_code} />
                      </Td>
                      <Td className="text-gray-700 text-sm">{r.applies_to}</Td>
                      <Td className="text-center font-bold text-blue-700">
                        {r.steps?.length ?? 0}
                      </Td>
                      <Td>
                        {r.segregation_of_duties
                          ? <Shield size={15} className="text-green-600" />
                          : <span className="text-gray-300">—</span>}
                      </Td>
                      <Td>
                        <Badge
                          status={r.is_active ? 'ACTIVE' : 'DRAFT'}
                          label={r.is_active ? 'Active' : 'Inactive'}
                        />
                      </Td>
                      <Td onClick={e => e.stopPropagation()}>
                        <div className="flex gap-1">
                          <button
                            onClick={() => openEdit(r)}
                            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="Edit"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => confirmDelete(r)}
                            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete"
                          >
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
        </div>

        {/* Detail panel */}
        <div>
          {selected ? (
            <Card>
              <CardHeader>
                <CardTitle>{selected.workflow_code}</CardTitle>
                <p className="text-sm text-gray-500 mt-1">{selected.description || 'No description.'}</p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500 text-xs">Module</p>
                    <p className="font-semibold text-gray-900">{selected.module_code}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs">Version</p>
                    <p className="font-semibold text-gray-900">v{selected.version}</p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-gray-500 text-xs">Applies To</p>
                    <p className="font-semibold text-gray-900 font-mono text-xs">{selected.applies_to}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs">Effective From</p>
                    <p className="font-semibold text-gray-900">{selected.effective_from}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs">Effective To</p>
                    <p className="font-semibold text-gray-900">{selected.effective_to ?? '—'}</p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 text-xs">
                  <span className={`px-2.5 py-1 rounded-lg font-medium ${selected.segregation_of_duties ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-400 line-through'}`}>
                    <Shield size={11} className="inline mr-1" />SoD
                  </span>
                  <span className={`px-2.5 py-1 rounded-lg font-medium ${selected.maker_cannot_approve ? 'bg-orange-50 text-orange-700' : 'bg-gray-100 text-gray-400 line-through'}`}>
                    Maker-Checker
                  </span>
                  <span className={`px-2.5 py-1 rounded-lg font-medium ${selected.audit_required ? 'bg-purple-50 text-purple-700' : 'bg-gray-100 text-gray-400 line-through'}`}>
                    Audit
                  </span>
                </div>

                <div>
                  <p className="text-sm font-semibold text-gray-700 mb-2">Approval Steps</p>
                  <ol className="space-y-2">
                    {(selected.steps ?? []).map((s: Step) => (
                      <li key={s.step} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                        <span className="w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center shrink-0">
                          {s.step}
                        </span>
                        <div>
                          <p className="text-sm font-semibold text-gray-900">
                            {ROLES.find(r => r.value === s.role)?.label ?? s.role}
                          </p>
                          <p className="text-xs text-gray-500">SLA: {s.sla_hours}h</p>
                        </div>
                      </li>
                    ))}
                  </ol>
                </div>

                <div className="flex gap-2 pt-1">
                  <Button variant="secondary" onClick={() => openEdit(selected)} className="flex-1">
                    <Pencil size={14} /> Edit
                  </Button>
                  <Button variant="danger" onClick={() => confirmDelete(selected)} className="flex-1">
                    <Trash2 size={14} /> Delete
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <GitBranch size={32} className="text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-gray-400">Select a rule to view details</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      <RuleModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editing={editing}
      />
    </AppLayout>
  )
}
