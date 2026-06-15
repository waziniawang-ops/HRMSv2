import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Star } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type Review = {
  id: string; employee_name: string; reviewer_name?: string; review_type: string;
  status: string; overall_rating: string; submitted_at: string; cycle: string
}

function RatingStars({ rating }: { rating: string }) {
  const r = Number(rating)
  return (
    <div className="flex items-center gap-1">
      <span className="font-bold text-gray-900 text-sm">{r.toFixed(1)}</span>
      <div className="flex">
        {[1, 2, 3, 4, 5].map(i => (
          <Star key={i} size={12} className={i <= Math.round(r) ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'} />
        ))}
      </div>
    </div>
  )
}

export default function Reviews() {
  const [page, setPage] = useState(1)
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['reviews', page, typeFilter, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (typeFilter) params.set('review_type', typeFilter)
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/performance/review-forms/?${params}`).then(r => r.data)
    },
  })

  return (
    <AppLayout title="Performance Reviews">
      <div className="space-y-4">
        <div className="flex items-center gap-3 justify-end">
          <Select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className="w-40">
            <option value="">All Types</option>
            {['SELF','MANAGER','PEER','360'].map(t => <option key={t} value={t}>{t}</option>)}
          </Select>
          <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-40">
            <option value="">All Statuses</option>
            {['DRAFT','IN_PROGRESS','SUBMITTED','ACKNOWLEDGED'].map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Star} title="No reviews" description="Review forms appear here once performance cycles are active" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Reviewer</Th><Th>Type</Th><Th>Rating</Th><Th>Status</Th><Th>Submitted</Th></tr></Thead>
                <Tbody>
                  {data.results.map((r: Review) => (
                    <Tr key={r.id}>
                      <Td className="font-medium text-gray-900">{r.employee_name || '—'}</Td>
                      <Td className="text-gray-600">{r.reviewer_name || '—'}</Td>
                      <Td><Badge status={r.review_type} /></Td>
                      <Td>{r.overall_rating ? <RatingStars rating={r.overall_rating} /> : <span className="text-gray-400">—</span>}</Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td className="text-sm text-gray-500">{fmt(r.submitted_at)}</Td>
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
