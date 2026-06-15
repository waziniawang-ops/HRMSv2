import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { UserCheck, CheckCircle2, Circle, X } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type Case = {
  id: string
  applicant_name: string
  status: string
  target_start_date: string
  completion_percentage: number
  assigned_hr_display: string
}

type Task = {
  id: string
  title: string
  task_code: string
  status: string
  is_required: boolean
  order: number
  hr_verified: boolean
}

export default function Cases() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [selected, setSelected] = useState<Case | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['onboarding-cases', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/onboarding/cases/?${params}`).then(r => r.data)
    },
  })

  const { data: tasks } = useQuery({
    queryKey: ['onboarding-tasks', selected?.id],
    queryFn: () => api.get(`/onboarding/tasks/?onboarding_case=${selected!.id}&page_size=50`).then(r => r.data.results),
    enabled: !!selected,
  })

  function taskIcon(status: string) {
    if (status === 'COMPLETED') return <CheckCircle2 size={16} className="text-green-500" />
    if (status === 'SKIPPED') return <X size={16} className="text-gray-400" />
    return <Circle size={16} className="text-gray-300" />
  }

  return (
    <AppLayout title="Onboarding Cases">
      <div className="space-y-4">
        <div className="flex justify-end">
          <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-44">
            <option value="">All Statuses</option>
            {['PENDING','IN_PROGRESS','COMPLETED','CANCELLED'].map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card>
              {isLoading ? <PageSpinner /> : !data?.results?.length ? (
                <EmptyState icon={UserCheck} title="No onboarding cases" description="Cases are created automatically when an offer is accepted" />
              ) : (
                <>
                  <Table>
                    <Thead>
                      <tr><Th>Candidate</Th><Th>Status</Th><Th>Completion</Th><Th>Start Date</Th><Th>HR</Th></tr>
                    </Thead>
                    <Tbody>
                      {data.results.map((c: Case) => (
                        <Tr key={c.id} onClick={() => setSelected(c)} className={selected?.id === c.id ? 'bg-blue-50' : ''}>
                          <Td className="font-medium text-gray-900">{c.applicant_name || `Case ${c.id.slice(0, 8)}`}</Td>
                          <Td><Badge status={c.status} /></Td>
                          <Td>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1.5 bg-gray-100 rounded-full w-20">
                                <div
                                  className="h-full bg-green-500 rounded-full"
                                  style={{ width: `${c.completion_percentage}%` }}
                                />
                              </div>
                              <span className="text-xs font-semibold text-gray-700">{c.completion_percentage}%</span>
                            </div>
                          </Td>
                          <Td>{fmt(c.target_start_date)}</Td>
                          <Td className="text-sm text-gray-500">{c.assigned_hr_display || '—'}</Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                  <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />
                </>
              )}
            </Card>
          </div>

          <div>
            {selected ? (
              <Card>
                <CardHeader>
                  <CardTitle>Onboarding Checklist</CardTitle>
                  <p className="text-sm text-gray-500 mt-1">{selected.applicant_name || `Case ${selected.id.slice(0, 8)}`}</p>
                </CardHeader>
                <CardContent className="p-0">
                  {tasks ? (
                    <ul className="divide-y divide-gray-100">
                      {tasks.map((t: Task) => (
                        <li key={t.id} className="flex items-start gap-3 px-4 py-3">
                          <div className="mt-0.5">{taskIcon(t.status)}</div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">{t.title}</p>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="text-xs text-gray-400">{t.task_code}</span>
                              {t.is_required && <span className="text-xs text-red-500">Required</span>}
                              {t.hr_verified && <span className="text-xs text-green-600">Verified</span>}
                            </div>
                          </div>
                          <Badge status={t.status} />
                        </li>
                      ))}
                    </ul>
                  ) : <PageSpinner />}
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="text-center py-12">
                  <UserCheck size={32} className="text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-400">Select a case to view checklist</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
