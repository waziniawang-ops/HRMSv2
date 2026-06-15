import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { CheckCircle2, Award } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type Completion = {
  id: string; employee_name: string; course_title: string
  score: string; hours_completed: string; completed_at: string; is_valid: boolean
  certificate?: { certificate_number: string; expiry_date: string }
}

export default function Completions() {
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['completions', page],
    queryFn: () => api.get(`/learning/completions/?page=${page}`).then(r => r.data),
  })

  return (
    <AppLayout title="Course Completions & Certificates">
      <Card>
        {isLoading ? <PageSpinner /> : !data?.results?.length ? (
          <EmptyState icon={CheckCircle2} title="No completions" description="Course completions appear here as employees finish courses" />
        ) : (
          <>
            <Table>
              <Thead>
                <tr><Th>Employee</Th><Th>Course</Th><Th>Score</Th><Th>Hours</Th><Th>Completed</Th><Th>Valid</Th><Th>Certificate</Th></tr>
              </Thead>
              <Tbody>
                {data.results.map((c: Completion) => (
                  <Tr key={c.id}>
                    <Td className="font-medium text-gray-900">{c.employee_name || '—'}</Td>
                    <Td className="text-gray-700">{c.course_title || '—'}</Td>
                    <Td>
                      <span className={`font-bold ${Number(c.score) >= 80 ? 'text-green-700' : Number(c.score) >= 60 ? 'text-yellow-700' : 'text-red-600'}`}>
                        {c.score}%
                      </span>
                    </Td>
                    <Td>{c.hours_completed}h</Td>
                    <Td className="text-sm">{fmt(c.completed_at)}</Td>
                    <Td><Badge status={c.is_valid ? 'ACTIVE' : 'DRAFT'} label={c.is_valid ? 'Valid' : 'Expired'} /></Td>
                    <Td>
                      {c.certificate ? (
                        <div className="flex items-center gap-1 text-xs text-amber-700">
                          <Award size={13} />
                          <span className="font-mono">{c.certificate.certificate_number}</span>
                        </div>
                      ) : <span className="text-gray-400 text-xs">—</span>}
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
            <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />
          </>
        )}
      </Card>
    </AppLayout>
  )
}
