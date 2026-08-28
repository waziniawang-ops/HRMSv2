import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { AxiosError } from 'axios'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Select } from '@/components/ui/Input'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { BookOpen, RefreshCw, Send, Download, UploadCloud } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type PayrollRun = {
  id: string; calendar_display: string
  period_start: string; period_end: string; status: string
}

type GLPosting = {
  id: string; payroll_run: string; gl_account: string; entry_type: 'DEBIT' | 'CREDIT'
  description: string; amount: string; cost_center: string | null; cost_center_display: string
  posting_date: string; is_posted: boolean; posted_at: string | null; sent_to_accounting_at: string | null
}

type AccountingIntegration = { is_configured: boolean; name: string }

const GENERATABLE_STATUSES = ['LOCKED', 'APPROVED', 'PAID']

export default function PayrollGLPostings() {
  const qc = useQueryClient()
  const [runId, setRunId] = useState('')

  const { data: runsData } = useQuery({
    queryKey: ['payroll-runs-for-gl'],
    queryFn: () => api.get('/payroll/payroll-runs/?page_size=100').then(r => r.data),
  })
  const runs: PayrollRun[] = runsData?.results || []
  const effectiveRunId = runId || runs[0]?.id || ''

  const selectedRun = runs.find(r => r.id === effectiveRunId)

  const { data: postingsData, isLoading } = useQuery({
    queryKey: ['payroll-gl-postings', effectiveRunId],
    queryFn: () => api.get(`/payroll/payroll-gl-postings/?payroll_run=${effectiveRunId}&page_size=200`).then(r => r.data),
    enabled: !!effectiveRunId,
  })
  const postings: GLPosting[] = postingsData?.results || []

  const { data: acctData } = useQuery<AccountingIntegration>({
    queryKey: ['accounting-integration'],
    queryFn: () => api.get('/payroll/accounting-integration/').then(r => r.data),
  })

  const totalDebit = postings.filter(p => p.entry_type === 'DEBIT').reduce((s, p) => s + Number(p.amount), 0)
  const totalCredit = postings.filter(p => p.entry_type === 'CREDIT').reduce((s, p) => s + Number(p.amount), 0)
  const balanced = postings.length > 0 && Math.abs(totalDebit - totalCredit) < 0.01

  function errorDetail(e: unknown, fallback: string) {
    const detail = (e as AxiosError<{ detail?: string }>)?.response?.data?.detail
    return detail || fallback
  }

  const generate = useMutation({
    mutationFn: () => api.post(`/payroll/payroll-runs/${effectiveRunId}/generate_gl_postings/`, {}),
    onSuccess: (r) => {
      toast.success(`Generated ${r.data.created} GL postings`)
      qc.invalidateQueries({ queryKey: ['payroll-gl-postings', effectiveRunId] })
    },
    onError: (e: unknown) => toast.error(errorDetail(e, 'Failed to generate GL postings')),
  })

  const postAll = useMutation({
    mutationFn: () => api.post(`/payroll/payroll-runs/${effectiveRunId}/post_gl_postings/`, {}),
    onSuccess: (r) => {
      toast.success(`Posted ${r.data.posted} entries to GL`)
      qc.invalidateQueries({ queryKey: ['payroll-gl-postings', effectiveRunId] })
    },
    onError: (e: unknown) => toast.error(errorDetail(e, 'Failed to post entries')),
  })

  const postOne = useMutation({
    mutationFn: (id: string) => api.post(`/payroll/payroll-gl-postings/${id}/post_to_gl/`, {}),
    onSuccess: () => {
      toast.success('Posted')
      qc.invalidateQueries({ queryKey: ['payroll-gl-postings', effectiveRunId] })
    },
    onError: () => toast.error('Failed to post entry'),
  })

  const [exporting, setExporting] = useState(false)
  async function exportCsv() {
    if (!selectedRun) return
    setExporting(true)
    try {
      const res = await api.get(`/payroll/payroll-runs/${effectiveRunId}/export_gl_csv/`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = `gl_postings_${selectedRun.period_start}_${selectedRun.period_end}.csv`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      toast.error('Failed to export CSV')
    } finally {
      setExporting(false)
    }
  }

  const sendToAccounting = useMutation({
    mutationFn: () => api.post(`/payroll/payroll-runs/${effectiveRunId}/send_gl_to_accounting/`, {}),
    onSuccess: (r) => {
      toast.success(`Sent ${r.data.sent} entries to ${acctData?.name || 'accounting system'}`)
      qc.invalidateQueries({ queryKey: ['payroll-gl-postings', effectiveRunId] })
    },
    onError: (e: unknown) => toast.error(errorDetail(e, 'Failed to send to accounting system')),
  })

  const canGenerate = !!selectedRun && GENERATABLE_STATUSES.includes(selectedRun.status)
  const hasUnposted = postings.some(p => !p.is_posted)
  const hasPendingSend = postings.some(p => p.is_posted && !p.sent_to_accounting_at)

  return (
    <AppLayout title="GL Postings">
      <div className="space-y-4">
        <Card>
          <div className="p-4 flex flex-wrap items-center gap-3 justify-between">
            <div className="flex items-center gap-3">
              <Select value={effectiveRunId} onChange={e => setRunId(e.target.value)} className="w-80">
                {runs.map(r => (
                  <option key={r.id} value={r.id}>
                    {r.calendar_display} — {fmt(r.period_start)} to {fmt(r.period_end)} [{r.status}]
                  </option>
                ))}
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                onClick={() => generate.mutate()}
                loading={generate.isPending}
                disabled={!canGenerate}
                title={!canGenerate ? 'Run must be locked, approved, or paid, with payslips already generated' : undefined}
              >
                <RefreshCw size={16} /> Generate GL Postings
              </Button>
              <Button
                onClick={() => postAll.mutate()}
                loading={postAll.isPending}
                disabled={!hasUnposted}
              >
                <Send size={16} /> Post All to GL
              </Button>
              <Button
                variant="secondary"
                onClick={exportCsv}
                loading={exporting}
                disabled={!postings.length}
              >
                <Download size={16} /> Export CSV
              </Button>
              <Button
                variant="secondary"
                onClick={() => sendToAccounting.mutate()}
                loading={sendToAccounting.isPending}
                disabled={!acctData?.is_configured || !hasPendingSend}
                title={!acctData?.is_configured ? 'Configure the accounting system API in Settings first' : !hasPendingSend ? 'No posted entries pending send' : undefined}
              >
                <UploadCloud size={16} /> Send to Accounting System
              </Button>
            </div>
          </div>
        </Card>

        {postings.length > 0 && (
          <div className="grid grid-cols-3 gap-4">
            <Card>
              <div className="p-4">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Total Debit</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{totalDebit.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
              </div>
            </Card>
            <Card>
              <div className="p-4">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Total Credit</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{totalCredit.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
              </div>
            </Card>
            <Card>
              <div className="p-4">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Balance Check</p>
                <p className={`text-xl font-bold mt-1 ${balanced ? 'text-green-600' : 'text-red-600'}`}>
                  {balanced ? 'Balanced' : 'Out of Balance'}
                </p>
              </div>
            </Card>
          </div>
        )}

        <Card>
          {isLoading ? <PageSpinner /> : !postings.length ? (
            <EmptyState
              icon={BookOpen}
              title="No GL postings for this run"
              action={canGenerate ? <Button onClick={() => generate.mutate()} loading={generate.isPending}><RefreshCw size={16} />Generate GL Postings</Button> : undefined}
            />
          ) : (
            <Table>
              <Thead><tr><Th>GL Account</Th><Th>Type</Th><Th>Description</Th><Th>Cost Center</Th><Th>Amount</Th><Th>Posting Date</Th><Th>Status</Th><Th>Sent</Th><Th></Th></tr></Thead>
              <Tbody>
                {postings.map(p => (
                  <Tr key={p.id}>
                    <Td className="font-mono text-sm">{p.gl_account}</Td>
                    <Td><Badge status={p.entry_type} className={p.entry_type === 'DEBIT' ? 'bg-orange-100 text-orange-700' : 'bg-purple-100 text-purple-700'} /></Td>
                    <Td>{p.description}</Td>
                    <Td>{p.cost_center_display || <span className="text-gray-400">—</span>}</Td>
                    <Td className="font-semibold">{Number(p.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</Td>
                    <Td>{fmt(p.posting_date)}</Td>
                    <Td>{p.is_posted
                      ? <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">Posted</span>
                      : <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">Unposted</span>}
                    </Td>
                    <Td>{p.sent_to_accounting_at
                      ? <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded">Sent</span>
                      : <span className="text-gray-400">—</span>}
                    </Td>
                    <Td>
                      {!p.is_posted && (
                        <button
                          onClick={() => postOne.mutate(p.id)}
                          className="text-xs px-2 py-1 bg-orange-100 text-orange-700 rounded hover:bg-orange-200"
                        >
                          Post
                        </button>
                      )}
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </Card>
      </div>
    </AppLayout>
  )
}
