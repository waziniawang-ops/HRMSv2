import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Search, Inbox } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type ESSRequest = {
  id: string; employee_name: string; employee_number: string
  request_type_display: string; subject: string; status: string; created_at: string
}

export default function ESSRequests() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['ess-requests', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/ess/requests/?${params}`).then(r => r.data)
    },
  })

  const resolve = useMutation({
    mutationFn: (id: string) => api.post(`/ess/requests/${id}/resolve/`, { resolution_notes: 'Resolved by HR' }),
    onSuccess: () => { toast.success('Request resolved'); qc.invalidateQueries({ queryKey: ['ess-requests'] }) },
    onError: () => toast.error('Failed to resolve'),
  })

  const filtered = search
    ? data?.results?.filter((r: ESSRequest) => r.employee_name?.toLowerCase().includes(search.toLowerCase()) || r.subject?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="ESS Requests">
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search employee or subject..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-44">
            <option value="">All Statuses</option>
            {['DRAFT','SUBMITTED','IN_REVIEW','APPROVED','REJECTED','COMPLETED','CANCELLED'].map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={Inbox} title="No ESS requests" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Type</Th><Th>Subject</Th><Th>Status</Th><Th>Submitted</Th><Th></Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: ESSRequest) => (
                    <Tr key={r.id}>
                      <Td className="font-medium">{r.employee_name} <span className="text-gray-400 text-xs">#{r.employee_number}</span></Td>
                      <Td className="text-sm text-gray-600">{r.request_type_display}</Td>
                      <Td className="max-w-xs truncate">{r.subject}</Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td className="text-gray-500">{fmt(r.created_at)}</Td>
                      <Td>
                        {r.status === 'SUBMITTED' && (
                          <button onClick={() => resolve.mutate(r.id)} className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200">Resolve</button>
                        )}
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              {!search && <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />}
            </>
          )}
        </Card>
      </div>
    </AppLayout>
  )
}
