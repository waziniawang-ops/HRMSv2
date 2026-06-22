import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Heart } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type WellbeingProgram = {
  id: string; name: string; program_type_display: string
  status: string; start_date: string; end_date: string | null
  capacity: number | null; enrolled_count: number
}

export default function WellbeingPrograms() {
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['wellbeing-programs', page],
    queryFn: () => api.get(`/hse/wellbeing-programs/?page=${page}`).then(r => r.data),
  })

  return (
    <AppLayout title="Wellbeing Programs">
      <div className="space-y-4">
        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Heart} title="No wellbeing programs" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Name</Th><Th>Type</Th><Th>Start</Th><Th>End</Th><Th>Enrolled / Capacity</Th><Th>Status</Th></tr></Thead>
                <Tbody>
                  {data.results.map((r: WellbeingProgram) => (
                    <Tr key={r.id}>
                      <Td className="font-medium">{r.name}</Td>
                      <Td className="text-gray-600">{r.program_type_display}</Td>
                      <Td>{fmt(r.start_date)}</Td>
                      <Td>{r.end_date ? fmt(r.end_date) : 'Ongoing'}</Td>
                      <Td>{r.enrolled_count} / {r.capacity ?? '—'}</Td>
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
