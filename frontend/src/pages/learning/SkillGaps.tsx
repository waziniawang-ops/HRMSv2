import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { TrendingUp } from 'lucide-react'
import api from '@/lib/api'

type Gap = {
  id: string; employee_name: string; skill_name: string
  required_level: number; current_level: number; gap: number
  recommended_course_title: string; is_closed: boolean
}

export default function SkillGaps() {
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['skill-gaps', page],
    queryFn: () => api.get(`/learning/skill-gaps/?page=${page}`).then(r => r.data),
  })

  function gapColor(gap: number) {
    if (gap >= 3) return 'text-red-600 bg-red-50'
    if (gap >= 2) return 'text-orange-600 bg-orange-50'
    return 'text-yellow-600 bg-yellow-50'
  }

  function levelBar(current: number, required: number) {
    const pct = Math.min((current / required) * 100, 100)
    return (
      <div className="flex items-center gap-2">
        <div className="w-20 h-1.5 bg-gray-100 rounded-full">
          <div className="h-full bg-blue-500 rounded-full" style={{ width: `${pct}%` }} />
        </div>
        <span className="text-xs text-gray-600">{current}/{required}</span>
      </div>
    )
  }

  return (
    <AppLayout title="Skill Gaps">
      <Card>
        {isLoading ? <PageSpinner /> : !data?.results?.length ? (
          <EmptyState icon={TrendingUp} title="No skill gaps tracked" description="Skill gaps are identified through performance and succession planning" />
        ) : (
          <>
            <Table>
              <Thead>
                <tr><Th>Employee</Th><Th>Skill</Th><Th>Level (Current/Required)</Th><Th>Gap</Th><Th>Recommended Course</Th><Th>Closed</Th></tr>
              </Thead>
              <Tbody>
                {data.results.map((g: Gap) => (
                  <Tr key={g.id}>
                    <Td className="font-medium text-gray-900">{g.employee_name || '—'}</Td>
                    <Td className="font-medium text-gray-800">{g.skill_name}</Td>
                    <Td>{levelBar(g.current_level, g.required_level)}</Td>
                    <Td>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${gapColor(g.gap)}`}>
                        -{g.gap}
                      </span>
                    </Td>
                    <Td className="text-sm text-blue-700">{g.recommended_course_title || '—'}</Td>
                    <Td><Badge status={g.is_closed ? 'ACTIVE' : 'PENDING'} label={g.is_closed ? 'Closed' : 'Open'} /></Td>
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
