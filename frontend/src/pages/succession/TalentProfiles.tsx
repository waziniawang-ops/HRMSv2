import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { User, Plus, Pencil, Trash2, Send, CheckCircle, XCircle } from 'lucide-react'
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
import { fmt } from '@/lib/utils'
import { useAuth } from '@/context/AuthContext'
import api from '@/lib/api'

type WorkflowRequest = { id: string; status: string; current_step: number }

type Profile = {
  id: string
  employee: string
  employee_name: string
  employee_number: string
  talent_pool: string | null
  talent_pool_name: string | null
  nine_box_score: number | null
  nine_box_label: string
  flight_risk: string
  career_aspirations: string
  key_strengths: string
  development_areas: string
  mobility_preference: string
  assessed_by: string | null
  assessed_by_display: string | null
  last_assessed_at: string | null
  workflow_request: WorkflowRequest | null
  created_at: string
}

interface Employee { id: string; employee_number: string; full_name: string }
interface TalentPool { id: string; name: string; tier: string }
interface ApiList<T> { count: number; results: T[] }

const NINE_BOX = [
  { value: 9, label: '9 — Star (High Perf / High Pot)' },
  { value: 8, label: '8 — High Performer (High Perf / Mod Pot)' },
  { value: 7, label: '7 — High Potential (High Perf / Low Pot)' },
  { value: 6, label: '6 — Core Player (Mod Perf / High Pot)' },
  { value: 5, label: '5 — Key Player (Mod Perf / Mod Pot)' },
  { value: 4, label: '4 — Contributor (Mod Perf / Low Pot)' },
  { value: 3, label: '3 — Rough Diamond (Low Perf / High Pot)' },
  { value: 2, label: '2 — Risk (Low Perf / Mod Pot)' },
  { value: 1, label: '1 — Under Performer (Low Perf / Low Pot)' },
]

const nineBoxColor: Record<number, string> = {
  9: 'bg-green-600', 8: 'bg-green-500', 7: 'bg-blue-600',
  6: 'bg-blue-500', 5: 'bg-indigo-600', 4: 'bg-yellow-500',
  3: 'bg-yellow-400', 2: 'bg-orange-500', 1: 'bg-red-500',
}

const CHECKER_ROLES = ['HR_CHECKER', 'HR_ADMIN', 'SYSTEM_ADMIN']
const COMMITTEE_ROLES = ['TALENT_COMMITTEE', 'HR_ADMIN', 'SYSTEM_ADMIN']

const emptyForm = {
  employee: '',
  talent_pool: '',
  nine_box_score: '',
  flight_risk: 'LOW',
  career_aspirations: '',
  key_strengths: '',
  development_areas: '',
  mobility_preference: 'LOCAL',
}

export default function TalentProfiles() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [flightFilter, setFlightFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Profile | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [commentModal, setCommentModal] = useState<{ action: 'approve' | 'reject'; profile: Profile } | null>(null)
  const [comment, setComment] = useState('')

  const params: Record<string, string | number> = { page, page_size: 20 }
  if (flightFilter) params.flight_risk = flightFilter

  const { data, isLoading } = useQuery<ApiList<Profile>>({
    queryKey: ['talent-profiles', page, flightFilter],
    queryFn: () => api.get('/succession/talent-profiles/', { params }).then(r => r.data),
  })

  const { data: employees } = useQuery<ApiList<Employee>>({
    queryKey: ['employees-all'],
    queryFn: () => api.get('/core/employees/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const { data: pools } = useQuery<ApiList<TalentPool>>({
    queryKey: ['talent-pools-all'],
    queryFn: () => api.get('/succession/talent-pools/', { params: { page_size: 500 } }).then(r => r.data),
  })

  function invalidate() { qc.invalidateQueries({ queryKey: ['talent-profiles'] }) }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/succession/talent-profiles/', body),
    onSuccess: () => { toast.success('Talent profile created'); invalidate(); closeModal() },
    onError: (e: any) => toast.error(e?.response?.data?.employee?.[0] ?? 'Failed to create profile'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: { id: string } & object) =>
      api.patch(`/succession/talent-profiles/${id}/`, body),
    onSuccess: () => { toast.success('Profile updated'); invalidate(); closeModal() },
    onError: () => toast.error('Failed to update profile'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/succession/talent-profiles/${id}/`),
    onSuccess: () => { toast.success('Profile deleted'); invalidate() },
    onError: () => toast.error('Cannot delete profile'),
  })

  const submitForApproval = useMutation({
    mutationFn: (id: string) => api.post(`/succession/talent-profiles/${id}/submit_for_approval/`),
    onSuccess: () => { toast.success('Submitted for review'); invalidate() },
    onError: () => toast.error('Failed to submit'),
  })

  const approve = useMutation({
    mutationFn: ({ id, comment }: { id: string; comment: string }) =>
      api.post(`/succession/talent-profiles/${id}/workflow_approve/`, { comment }),
    onSuccess: () => { toast.success('Approved'); invalidate(); setCommentModal(null); setComment('') },
    onError: () => toast.error('Failed to approve'),
  })

  const reject = useMutation({
    mutationFn: ({ id, comment }: { id: string; comment: string }) =>
      api.post(`/succession/talent-profiles/${id}/workflow_reject/`, { comment }),
    onSuccess: () => { toast.success('Rejected'); invalidate(); setCommentModal(null); setComment('') },
    onError: () => toast.error('Failed to reject'),
  })

  function openCreate() { setEditing(null); setForm(emptyForm); setModalOpen(true) }

  function openEdit(p: Profile) {
    setEditing(p)
    setForm({
      employee: p.employee,
      talent_pool: p.talent_pool ?? '',
      nine_box_score: p.nine_box_score != null ? String(p.nine_box_score) : '',
      flight_risk: p.flight_risk,
      career_aspirations: p.career_aspirations,
      key_strengths: p.key_strengths,
      development_areas: p.development_areas,
      mobility_preference: p.mobility_preference,
    })
    setModalOpen(true)
  }

  function closeModal() { setModalOpen(false); setEditing(null); setForm(emptyForm) }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = {
      ...form,
      nine_box_score: form.nine_box_score ? Number(form.nine_box_score) : null,
      talent_pool: form.talent_pool || null,
    }
    if (editing) update.mutate({ id: editing.id, ...payload })
    else create.mutate(payload)
  }

  function handleDelete(p: Profile) {
    if (!window.confirm(`Delete talent profile for ${p.employee_name}?`)) return
    remove.mutate(p.id)
  }

  const set = (k: keyof typeof emptyForm) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setForm(prev => ({ ...prev, [k]: e.target.value }))

  const isPending = create.isPending || update.isPending

  // Determine if current user can approve at the current step
  function canApprove(p: Profile) {
    if (!p.workflow_request) return false
    const wf = p.workflow_request
    if (!['SUBMITTED', 'IN_REVIEW', 'RESUBMITTED'].includes(wf.status)) return false
    if (wf.current_step === 1) return CHECKER_ROLES.some(r => user?.roles?.includes(r) ?? user?.role === r)
    if (wf.current_step === 2) return COMMITTEE_ROLES.some(r => user?.roles?.includes(r) ?? user?.role === r)
    return false
  }

  function wfStatus(p: Profile) {
    const s = p.workflow_request?.status
    if (!s) return null
    const map: Record<string, string> = {
      DRAFT: 'DRAFT', SUBMITTED: 'SUBMITTED', IN_REVIEW: 'IN_REVIEW',
      APPROVED: 'APPROVED', REJECTED: 'REJECTED', RETURNED: 'RETURNED',
      RESUBMITTED: 'RESUBMITTED',
    }
    return map[s] ?? s
  }

  return (
    <AppLayout title="Talent Profiles">
      <div className="space-y-4">

        {/* Workflow explanation */}
        <div className="rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-800">
          <p className="font-semibold mb-1">Talent Profile Review Workflow</p>
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-indigo-700">
            <span>1. Create profile (Manager / HR)</span>
            <span>→ 2. Submit for approval</span>
            <span>→ 3. HR Checker reviews (Step 1, 48h)</span>
            <span>→ 4. Talent Committee ratifies (Step 2, 72h)</span>
            <span>→ 5. Approved &amp; visible in succession reports</span>
          </div>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Talent Profiles</CardTitle>
              <Button onClick={openCreate}><Plus size={16} />Add Profile</Button>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <Select value={flightFilter} onChange={e => { setFlightFilter(e.target.value); setPage(1) }} className="w-44">
              <option value="">All Flight Risk</option>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
            </Select>
          </CardContent>

          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState
              icon={User}
              title="No talent profiles"
              description="Create a talent profile for an employee to include them in succession planning."
              action={<Button onClick={openCreate}><Plus size={16} />Add Profile</Button>}
            />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Employee</Th>
                    <Th>9-Box</Th>
                    <Th>Talent Pool</Th>
                    <Th>Flight Risk</Th>
                    <Th>Mobility</Th>
                    <Th>Assessed By</Th>
                    <Th>Workflow</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map(p => {
                    const status = wfStatus(p)
                    const step = p.workflow_request?.current_step
                    return (
                      <Tr key={p.id}>
                        <Td>
                          <p className="font-medium text-gray-900 text-sm">{p.employee_name}</p>
                          <p className="text-xs text-gray-400">{p.employee_number}</p>
                        </Td>
                        <Td>
                          {p.nine_box_score != null ? (
                            <div className="flex items-center gap-2">
                              <span className={`w-7 h-7 rounded-lg ${nineBoxColor[p.nine_box_score] ?? 'bg-gray-400'} text-white text-xs font-bold flex items-center justify-center`}>
                                {p.nine_box_score}
                              </span>
                              <span className="text-xs text-gray-600">{p.nine_box_label}</span>
                            </div>
                          ) : <span className="text-gray-400">—</span>}
                        </Td>
                        <Td className="text-sm text-gray-600">{p.talent_pool_name ?? '—'}</Td>
                        <Td>
                          <Badge
                            status={p.flight_risk === 'HIGH' ? 'REJECTED' : p.flight_risk === 'LOW' ? 'ACTIVE' : 'PENDING'}
                            label={p.flight_risk}
                          />
                        </Td>
                        <Td className="text-sm text-gray-500">{p.mobility_preference}</Td>
                        <Td className="text-sm text-gray-500">
                          <p>{p.assessed_by_display ?? '—'}</p>
                          {p.last_assessed_at && <p className="text-xs text-gray-400">{fmt(p.last_assessed_at)}</p>}
                        </Td>
                        <Td>
                          {status ? (
                            <div className="space-y-1">
                              <Badge status={status} />
                              {step && ['SUBMITTED','IN_REVIEW','RESUBMITTED'].includes(status) && (
                                <p className="text-xs text-gray-400">Step {step}</p>
                              )}
                            </div>
                          ) : (
                            <span className="text-xs text-gray-400">Not submitted</span>
                          )}
                        </Td>
                        <Td>
                          <div className="flex items-center gap-1 justify-end">
                            {/* Submit */}
                            {!p.workflow_request && (
                              <button
                                onClick={() => submitForApproval.mutate(p.id)}
                                className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                title="Submit for Approval"
                              >
                                <Send size={14} />
                              </button>
                            )}
                            {/* Approve / Reject */}
                            {canApprove(p) && (
                              <>
                                <button
                                  onClick={() => setCommentModal({ action: 'approve', profile: p })}
                                  className="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                                  title="Approve"
                                >
                                  <CheckCircle size={14} />
                                </button>
                                <button
                                  onClick={() => setCommentModal({ action: 'reject', profile: p })}
                                  className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                  title="Reject"
                                >
                                  <XCircle size={14} />
                                </button>
                              </>
                            )}
                            {/* Edit */}
                            <button onClick={() => openEdit(p)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit">
                              <Pencil size={14} />
                            </button>
                            {/* Delete */}
                            <button onClick={() => handleDelete(p)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete">
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </Td>
                      </Tr>
                    )
                  })}
                </Tbody>
              </Table>
              <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />
            </>
          )}
        </Card>
      </div>

      {/* Create / Edit Modal */}
      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit Profile — ${editing.employee_name}` : 'Add Talent Profile'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select label="Employee *" required value={form.employee} onChange={set('employee')} disabled={!!editing}>
            <option value="">— Select Employee —</option>
            {employees?.results.map(e => (
              <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>
            ))}
          </Select>

          <div className="grid grid-cols-2 gap-4">
            <Select label="9-Box Score" value={form.nine_box_score} onChange={set('nine_box_score')}>
              <option value="">— Not Assessed —</option>
              {NINE_BOX.map(n => <option key={n.value} value={n.value}>{n.label}</option>)}
            </Select>
            <Select label="Talent Pool" value={form.talent_pool} onChange={set('talent_pool')}>
              <option value="">— None —</option>
              {pools?.results.map(p => <option key={p.id} value={p.id}>{p.name} ({p.tier})</option>)}
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Select label="Flight Risk" value={form.flight_risk} onChange={set('flight_risk')}>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
            </Select>
            <Select label="Mobility Preference" value={form.mobility_preference} onChange={set('mobility_preference')}>
              <option value="LOCAL">Local Only</option>
              <option value="DOMESTIC">Domestic</option>
              <option value="INTERNATIONAL">International</option>
              <option value="ANY">Any Location</option>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Key Strengths</label>
            <textarea
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={2}
              value={form.key_strengths}
              onChange={set('key_strengths')}
              placeholder="e.g. Strategic thinking, strong stakeholder management…"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Development Areas</label>
            <textarea
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={2}
              value={form.development_areas}
              onChange={set('development_areas')}
              placeholder="e.g. Financial literacy, cross-functional experience…"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Career Aspirations</label>
            <textarea
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={2}
              value={form.career_aspirations}
              onChange={set('career_aspirations')}
              placeholder="e.g. Aspires to head of division within 3 years…"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Create Profile'}</Button>
          </div>
        </form>
      </Modal>

      {/* Approve / Reject comment modal */}
      {commentModal && (
        <Modal
          open
          onClose={() => { setCommentModal(null); setComment('') }}
          title={commentModal.action === 'approve' ? 'Approve Profile' : 'Reject Profile'}
        >
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              {commentModal.action === 'approve'
                ? `Approving talent profile for ${commentModal.profile.employee_name} (Step ${commentModal.profile.workflow_request?.current_step}).`
                : `Rejecting talent profile for ${commentModal.profile.employee_name}. It will be returned to the maker.`}
            </p>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Comment {commentModal.action === 'reject' ? '(required)' : '(optional)'}</label>
              <textarea
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                rows={3}
                value={comment}
                onChange={e => setComment(e.target.value)}
                placeholder="Add a comment…"
              />
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="secondary" onClick={() => { setCommentModal(null); setComment('') }}>Cancel</Button>
              {commentModal.action === 'approve' ? (
                <Button
                  onClick={() => approve.mutate({ id: commentModal.profile.id, comment })}
                  loading={approve.isPending}
                >
                  <CheckCircle size={14} /> Approve
                </Button>
              ) : (
                <Button
                  variant="danger"
                  onClick={() => reject.mutate({ id: commentModal.profile.id, comment })}
                  loading={reject.isPending}
                  disabled={!comment.trim()}
                >
                  <XCircle size={14} /> Reject
                </Button>
              )}
            </div>
          </div>
        </Modal>
      )}
    </AppLayout>
  )
}
