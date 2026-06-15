import { Fragment, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Target } from 'lucide-react'
import api from '@/lib/api'

type GoalPlan = {
  id: string; employee_name: string; cycle_name: string; status: string;
  overall_weight_total: string; goals: Goal[]
}
type Goal = { id: string; title: string; category: string; weight: string; status: string; completion_percentage: number }

export default function Goals() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['goal-plans', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/performance/goal-plans/?${params}`).then(r => r.data)
    },
  })

  return (
    <AppLayout title="Goal Plans">
      <div className="space-y-4">
        <div className="flex justify-end">
          <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-44">
            <option value="">All Statuses</option>
            {['DRAFT','SUBMITTED','MANAGER_APPROVED','HR_APPROVED','ACTIVE','COMPLETED'].map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Target} title="No goal plans" description="Goal plans will appear here once created by employees" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Cycle</Th><Th>Status</Th><Th>Total Weight</Th><Th>Goals</Th></tr></Thead>
                <Tbody>
                  {data.results.map((gp: GoalPlan) => (
                    <Fragment key={gp.id}>
                      <Tr onClick={() => setExpanded(expanded === gp.id ? null : gp.id)}>
                        <Td className="font-medium text-gray-900">{gp.employee_name || '—'}</Td>
                        <Td className="text-gray-600">{gp.cycle_name || '—'}</Td>
                        <Td><Badge status={gp.status} /></Td>
                        <Td className="font-semibold">{gp.overall_weight_total}</Td>
                        <Td>
                          <span className="text-xs text-blue-600 font-medium">
                            {expanded === gp.id ? '▲ Collapse' : '▼ Show goals'}
                          </span>
                        </Td>
                      </Tr>
                      {expanded === gp.id && gp.goals?.map((g: Goal) => (
                        <tr key={g.id} className="bg-blue-50/30">
                          <td className="px-4 py-2 pl-12 text-sm text-gray-800" colSpan={2}>{g.title}</td>
                          <td className="px-4 py-2 text-sm"><Badge status={g.status} /></td>
                          <td className="px-4 py-2 text-sm text-gray-600">{g.category} · w={g.weight}</td>
                          <td className="px-4 py-2 text-sm">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1.5 bg-gray-200 rounded-full">
                                <div className="h-full bg-blue-500 rounded-full" style={{ width: `${g.completion_percentage}%` }} />
                              </div>
                              <span className="text-xs text-gray-600">{g.completion_percentage}%</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </Fragment>
                  ))}
                </Tbody>
              </Table>
              <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />
            </>
          )}
        </Card>
      </div>
    </AppLayout>
  )
}
