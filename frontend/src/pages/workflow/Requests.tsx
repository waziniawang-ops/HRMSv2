import { Fragment, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Select, Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import {
  GitPullRequest, CheckCircle2, XCircle, RotateCcw,
  ChevronDown, ChevronUp, MessageSquare,
} from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type WFStep = {
  id: string
  step_number: number
  approver_role: string
  approver_user_display: string | null
  status: string
  action: string
  comment: string
  sla_hours: number | null
  acted_at: string | null
  due_at: string | null
}

type WFComment = {
  id: string
  user_display: string
  comment: string
  visibility: string
  created_at: string
}

type WFHistory = {
  id: string
  from_status: string
  to_status: string
  actor_display: string
  step_number: number | null
  comment: string
  created_at: string
}

type WFRequest = {
  id: string
  workflow_code: string
  module_code: string
  object_type: string
  object_id: string
  maker_display: string
  status: string
  current_step: number
  submitted_at: string | null
  created_at: string
  steps: WFStep[]
  comments: WFComment[]
  history: WFHistory[]
}

type ActionModal = { type: 'reject' | 'return'; request: WFRequest }

const ACTIONABLE = ['SUBMITTED', 'IN_REVIEW', 'RESUBMITTED']

const STEP_DOT: Record<string, string> = {
  PENDING: 'bg-gray-300',
  IN_REVIEW: 'bg-blue-400',
  APPROVED: 'bg-green-500',
  REJECTED: 'bg-red-500',
  RETURNED: 'bg-yellow-500',
  SKIPPED: 'bg-gray-200',
}

function fmtDt(dt: string | null) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('en-MY', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function DetailPanel({
  request, onAddComment, addingComment, newComment, setNewComment,
}: {
  request: WFRequest
  onAddComment: (comment: string) => void
  addingComment: boolean
  newComment: string
  setNewComment: (v: string) => void
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 text-sm">
      {/* Steps */}
      <div>
        <p className="font-semibold text-gray-700 mb-3">Approval Steps</p>
        <div className="space-y-3">
          {request.steps.map(step => (
            <div key={step.id} className="flex items-start gap-3">
              <div className={`mt-1.5 w-2.5 h-2.5 rounded-full shrink-0 ${STEP_DOT[step.status] ?? 'bg-gray-300'}`} />
              <div className="min-w-0">
                <p className="font-medium text-gray-900">Step {step.step_number} — {step.approver_role}</p>
                <p className="text-xs text-gray-500 capitalize">{step.status.toLowerCase()}</p>
                {step.approver_user_display && (
                  <p className="text-xs text-gray-500">By: {step.approver_user_display}</p>
                )}
                {step.comment && (
                  <p className="text-xs text-gray-600 italic mt-0.5">"{step.comment}"</p>
                )}
                {step.acted_at && (
                  <p className="text-xs text-gray-400">{fmtDt(step.acted_at)}</p>
                )}
                {!step.acted_at && step.due_at && (
                  <p className="text-xs text-orange-500">Due: {fmtDt(step.due_at)}</p>
                )}
              </div>
            </div>
          ))}
          {!request.steps.length && <p className="text-xs text-gray-400">No steps defined.</p>}
        </div>
      </div>

      {/* History */}
      <div>
        <p className="font-semibold text-gray-700 mb-3">History</p>
        <div className="space-y-3">
          {request.history.map(h => (
            <div key={h.id} className="text-xs">
              <p className="font-medium text-gray-700">
                {h.from_status} → {h.to_status}
                <span className="text-gray-400 font-normal ml-2">by {h.actor_display}</span>
              </p>
              {h.comment && <p className="text-gray-600 italic mt-0.5">"{h.comment}"</p>}
              <p className="text-gray-400">{fmtDt(h.created_at)}</p>
            </div>
          ))}
          {!request.history.length && <p className="text-xs text-gray-400">No history yet.</p>}
        </div>
      </div>

      {/* Comments */}
      <div>
        <p className="font-semibold text-gray-700 mb-3 flex items-center gap-1.5">
          <MessageSquare size={13} /> Comments
        </p>
        <div className="space-y-2 mb-3 max-h-48 overflow-y-auto">
          {request.comments.map(c => (
            <div key={c.id} className="text-xs bg-white rounded-lg p-2 border border-gray-100">
              <p className="font-medium text-gray-700">
                {c.user_display}
                <span className="text-gray-400 font-normal ml-2">{fmtDt(c.created_at)}</span>
              </p>
              <p className="text-gray-600 mt-0.5">{c.comment}</p>
            </div>
          ))}
          {!request.comments.length && <p className="text-xs text-gray-400">No comments yet.</p>}
        </div>
        <div className="flex gap-2">
          <input
            className="flex-1 px-2 py-1.5 border border-gray-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
            placeholder="Add a comment…"
            value={newComment}
            onChange={e => setNewComment(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && newComment.trim()) onAddComment(newComment.trim())
            }}
          />
          <Button
            size="sm"
            onClick={() => { if (newComment.trim()) onAddComment(newComment.trim()) }}
            loading={addingComment}
            disabled={!newComment.trim()}
          >
            Post
          </Button>
        </div>
      </div>
    </div>
  )
}

export default function WorkflowRequests() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [moduleFilter, setModuleFilter] = useState('')
  const [search, setSearch] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [actionModal, setActionModal] = useState<ActionModal | null>(null)
  const [actionComment, setActionComment] = useState('')
  const [newComment, setNewComment] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['wf-requests', page, statusFilter, moduleFilter, search],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      if (moduleFilter) params.set('module_code', moduleFilter)
      if (search) params.set('search', search)
      return api.get(`/workflow/requests/?${params}`).then(r => r.data)
    },
  })

  const { data: detail, isLoading: detailLoading } = useQuery<WFRequest>({
    queryKey: ['wf-request-detail', expandedId],
    queryFn: () => api.get(`/workflow/requests/${expandedId}/`).then(r => r.data),
    enabled: !!expandedId,
  })

  const approve = useMutation({
    mutationFn: (id: string) => api.post(`/workflow/requests/${id}/approve/`, { comment: '' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['wf-requests'] })
      qc.invalidateQueries({ queryKey: ['wf-request-detail', expandedId] })
      toast.success('Approved')
    },
    onError: (e: { response?: { data?: { detail?: string; non_field_errors?: string[] } } }) =>
      toast.error(e?.response?.data?.detail ?? e?.response?.data?.non_field_errors?.[0] ?? 'Cannot approve'),
  })

  const reject = useMutation({
    mutationFn: ({ id, comment }: { id: string; comment: string }) =>
      api.post(`/workflow/requests/${id}/reject/`, { comment }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['wf-requests'] })
      qc.invalidateQueries({ queryKey: ['wf-request-detail', expandedId] })
      closeActionModal()
      toast.success('Rejected')
    },
    onError: (e: { response?: { data?: { comment?: string[]; detail?: string } } }) =>
      toast.error(e?.response?.data?.comment?.[0] ?? e?.response?.data?.detail ?? 'Cannot reject'),
  })

  const returnAmend = useMutation({
    mutationFn: ({ id, comment }: { id: string; comment: string }) =>
      api.post(`/workflow/requests/${id}/return/`, { comment }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['wf-requests'] })
      qc.invalidateQueries({ queryKey: ['wf-request-detail', expandedId] })
      closeActionModal()
      toast.success('Returned for amendment')
    },
    onError: (e: { response?: { data?: { comment?: string[]; detail?: string } } }) =>
      toast.error(e?.response?.data?.comment?.[0] ?? e?.response?.data?.detail ?? 'Cannot return'),
  })

  const addComment = useMutation({
    mutationFn: ({ id, comment }: { id: string; comment: string }) =>
      api.post(`/workflow/requests/${id}/comments/`, { comment }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['wf-request-detail', expandedId] })
      setNewComment('')
      toast.success('Comment added')
    },
    onError: () => toast.error('Failed to add comment'),
  })

  function closeActionModal() {
    setActionModal(null)
    setActionComment('')
  }

  function submitAction() {
    if (!actionModal) return
    if (actionComment.trim().length < 5) {
      toast.error('Comment must be at least 5 characters')
      return
    }
    if (actionModal.type === 'reject') {
      reject.mutate({ id: actionModal.request.id, comment: actionComment })
    } else {
      returnAmend.mutate({ id: actionModal.request.id, comment: actionComment })
    }
  }

  function toggleExpand(id: string) {
    setExpandedId(prev => (prev === id ? null : id))
    setNewComment('')
  }

  const actionPending = approve.isPending || reject.isPending || returnAmend.isPending

  return (
    <AppLayout title="Workflow Requests">
      <div className="space-y-4">
        {/* Filters */}
        <div className="flex flex-wrap items-end gap-3">
          <Select
            value={statusFilter}
            onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
            className="w-44"
          >
            <option value="">All Statuses</option>
            {['DRAFT','SUBMITTED','IN_REVIEW','RETURNED','RESUBMITTED','APPROVED','REJECTED','CANCELLED'].map(s => (
              <option key={s} value={s}>{s.replace('_', ' ')}</option>
            ))}
          </Select>
          <Select
            value={moduleFilter}
            onChange={e => { setModuleFilter(e.target.value); setPage(1) }}
            className="w-44"
          >
            <option value="">All Modules</option>
            {['recruitment','onboarding','workforce','succession','performance','learning','core_hr'].map(m => (
              <option key={m} value={m}>{m.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>
            ))}
          </Select>
          <Input
            placeholder="Search object ID…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
            className="w-56"
          />
        </div>

        <Card>
          {isLoading ? (
            <PageSpinner />
          ) : !data?.results?.length ? (
            <EmptyState
              icon={GitPullRequest}
              title="No workflow requests"
              description="Requests are created when records are submitted for approval."
            />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th></Th>
                    <Th>Workflow</Th>
                    <Th>Module</Th>
                    <Th>Object</Th>
                    <Th>Submitted By</Th>
                    <Th>Step</Th>
                    <Th>Status</Th>
                    <Th>Date</Th>
                    <Th>Actions</Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map((r: WFRequest) => (
                    <Fragment key={r.id}>
                      <Tr
                        className={`cursor-pointer ${expandedId === r.id ? 'bg-blue-50' : ''}`}
                        onClick={() => toggleExpand(r.id)}
                      >
                        <Td>
                          {expandedId === r.id
                            ? <ChevronUp size={14} className="text-gray-400" />
                            : <ChevronDown size={14} className="text-gray-400" />}
                        </Td>
                        <Td><span className="font-mono text-xs font-semibold">{r.workflow_code}</span></Td>
                        <Td className="text-sm text-gray-600">{r.module_code}</Td>
                        <Td className="text-sm text-gray-600">{r.object_type}</Td>
                        <Td className="font-medium text-gray-900">{r.maker_display || '—'}</Td>
                        <Td className="text-center font-bold text-blue-600">{r.current_step}</Td>
                        <Td><Badge status={r.status} /></Td>
                        <Td className="text-sm text-gray-500">{fmt(r.created_at)}</Td>
                        <Td onClick={e => e.stopPropagation()}>
                          {ACTIONABLE.includes(r.status) && (
                            <div className="flex gap-1 flex-wrap">
                              <Button
                                size="sm"
                                variant="success"
                                onClick={() => approve.mutate(r.id)}
                                loading={approve.isPending}
                                disabled={actionPending}
                              >
                                <CheckCircle2 size={13} /> Approve
                              </Button>
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => setActionModal({ type: 'return', request: r })}
                                disabled={actionPending}
                              >
                                <RotateCcw size={13} /> Return
                              </Button>
                              <Button
                                size="sm"
                                variant="danger"
                                onClick={() => setActionModal({ type: 'reject', request: r })}
                                disabled={actionPending}
                              >
                                <XCircle size={13} /> Reject
                              </Button>
                            </div>
                          )}
                        </Td>
                      </Tr>

                      {expandedId === r.id && (
                        <tr>
                          <td colSpan={9} className="bg-gray-50 px-6 py-5 border-b border-gray-200">
                            {detailLoading ? (
                              <p className="text-sm text-gray-500">Loading details…</p>
                            ) : detail?.id === r.id ? (
                              <DetailPanel
                                request={detail}
                                onAddComment={comment => addComment.mutate({ id: detail.id, comment })}
                                addingComment={addComment.isPending}
                                newComment={newComment}
                                setNewComment={setNewComment}
                              />
                            ) : null}
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  ))}
                </Tbody>
              </Table>
              <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />
            </>
          )}
        </Card>
      </div>

      {/* Reject / Return for Amendment modal */}
      <Modal
        open={!!actionModal}
        onClose={closeActionModal}
        title={actionModal?.type === 'reject' ? 'Reject Request' : 'Return for Amendment'}
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            {actionModal?.type === 'reject'
              ? 'Provide a reason for rejection (minimum 5 characters).'
              : 'Explain what needs to be amended (minimum 5 characters).'}
          </p>
          <textarea
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
            value={actionComment}
            onChange={e => setActionComment(e.target.value)}
            placeholder={actionModal?.type === 'reject' ? 'Reason for rejection…' : 'What needs to be amended…'}
          />
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={closeActionModal}>Cancel</Button>
            <Button
              variant={actionModal?.type === 'reject' ? 'danger' : 'secondary'}
              onClick={submitAction}
              loading={reject.isPending || returnAmend.isPending}
              disabled={actionComment.trim().length < 5}
            >
              {actionModal?.type === 'reject' ? 'Confirm Reject' : 'Confirm Return'}
            </Button>
          </div>
        </div>
      </Modal>
    </AppLayout>
  )
}
