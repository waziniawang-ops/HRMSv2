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
import { Search, LogOut } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type OffboardingCase = {
  id: string; employee_name: string; employee_number: string
  exit_type_display: string; status: string
  last_day: string; created_at: string
}

export default function OffboardingCases() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['offboarding-cases', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/offboarding/cases/?${params}`).then(r => r.data)
    },
  })

  const filtered = search
    ? data?.results?.filter((r: OffboardingCase) =>
        r.employee_name?.toLowerCase().includes(search.toLowerCase()) ||
        r.employee_number?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="Offboarding Cases">
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search employee..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-40">
            <option value="">All Statuses</option>
            {['INITIATED','IN_PROGRESS','PENDING_CLEARANCE','COMPLETED','CANCELLED'].map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
          </Select>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={LogOut} title="No offboarding cases" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Exit Type</Th><Th>Last Day</Th><Th>Status</Th><Th>Initiated</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: OffboardingCase) => (
                    <Tr key={r.id}>
                      <Td className="font-medium">{r.employee_name} <span className="text-gray-400 text-xs">#{r.employee_number}</span></Td>
                      <Td>{r.exit_type_display}</Td>
                      <Td>{r.last_day ? fmt(r.last_day) : '—'}</Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td className="text-gray-500">{fmt(r.created_at)}</Td>
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
