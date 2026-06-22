import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { BarChart3 } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type Survey = {
  id: string; title: string; survey_type_display: string
  status: string; start_date: string; end_date: string
  response_count: number; target_response_count: number
  avg_score: string | null
}

export default function EngagementSurveys() {
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['engagement-surveys', page],
    queryFn: () => api.get(`/engagement/surveys/?page=${page}`).then(r => r.data),
  })

  return (
    <AppLayout title="Engagement Surveys">
      <div className="space-y-4">
        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={BarChart3} title="No surveys found" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Title</Th><Th>Type</Th><Th>Period</Th><Th>Responses</Th><Th>Avg Score</Th><Th>Status</Th></tr></Thead>
                <Tbody>
                  {data.results.map((r: Survey) => (
                    <Tr key={r.id}>
                      <Td className="font-medium">{r.title}</Td>
                      <Td className="text-gray-600">{r.survey_type_display}</Td>
                      <Td className="text-sm text-gray-500">{fmt(r.start_date)} – {fmt(r.end_date)}</Td>
                      <Td>{r.response_count} / {r.target_response_count || '—'}</Td>
                      <Td>{r.avg_score ? Number(r.avg_score).toFixed(1) : '—'}</Td>
                      <Td><Badge status={r.status} /></Td>
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
