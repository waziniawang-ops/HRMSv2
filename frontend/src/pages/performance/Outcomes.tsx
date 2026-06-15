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
import { Award } from 'lucide-react'
import { currency } from '@/lib/utils'
import { useCurrency } from '@/hooks/useCurrency'
import api from '@/lib/api'

type Outcome = {
  id: string; employee_name: string; cycle_name: string; outcome_label: string;
  final_rating: string; eligible_for_increment: boolean; increment_percentage: string;
  eligible_for_bonus: boolean; bonus_amount: string; notes: string
}

export default function Outcomes() {
  const { symbol } = useCurrency()
  const [page, setPage] = useState(1)
  const [outcomeFilter, setOutcomeFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['outcomes', page, outcomeFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (outcomeFilter) params.set('outcome_label', outcomeFilter)
      return api.get(`/performance/final-outcomes/?${params}`).then(r => r.data)
    },
  })

  const summary = data?.results?.reduce((acc: Record<string, number>, o: Outcome) => {
    acc[o.outcome_label] = (acc[o.outcome_label] || 0) + 1
    return acc
  }, {})

  const outcomeColors: Record<string, string> = {
    EXCEEDS: 'bg-green-600', MEETS: 'bg-blue-600', PARTIALLY: 'bg-yellow-500', BELOW: 'bg-red-500',
  }

  return (
    <AppLayout title="Performance Outcomes">
      <div className="space-y-6">
        {data?.results?.length > 0 && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {['EXCEEDS','MEETS','PARTIALLY','BELOW'].map(label => (
              <Card key={label}>
                <CardContent className="text-center py-5">
                  <div className={`w-10 h-10 rounded-xl ${outcomeColors[label]} mx-auto mb-2 flex items-center justify-center`}>
                    <Award size={20} className="text-white" />
                  </div>
                  <p className="text-2xl font-bold text-gray-900">{summary?.[label] ?? 0}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{label.replace('_', ' ')}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Final Outcomes</CardTitle>
            <Select value={outcomeFilter} onChange={e => setOutcomeFilter(e.target.value)} className="w-40">
              <option value="">All Labels</option>
              {['EXCEEDS','MEETS','PARTIALLY','BELOW'].map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
          </CardHeader>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Award} title="No outcomes" description="Outcomes are generated at the end of calibration" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Cycle</Th><Th>Outcome</Th><Th>Rating</Th><Th>Increment</Th><Th>Bonus</Th></tr></Thead>
                <Tbody>
                  {data.results.map((o: Outcome) => (
                    <Tr key={o.id}>
                      <Td className="font-medium text-gray-900">{o.employee_name || '—'}</Td>
                      <Td className="text-gray-600">{o.cycle_name || '—'}</Td>
                      <Td><Badge status={o.outcome_label} /></Td>
                      <Td>
                        <span className="font-bold text-gray-900">{Number(o.final_rating).toFixed(1)}</span>
                        <span className="text-gray-400 text-xs">/5</span>
                      </Td>
                      <Td>
                        {o.eligible_for_increment
                          ? <span className="text-green-700 font-semibold">{o.increment_percentage}%</span>
                          : <span className="text-gray-400">—</span>}
                      </Td>
                      <Td>
                        {o.eligible_for_bonus
                          ? <span className="text-green-700 font-semibold">{currency(o.bonus_amount, symbol)}</span>
                          : <span className="text-gray-400">—</span>}
                      </Td>
                    </Tr>
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
