import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Search, Scale } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type ERCase = {
  id: string; case_number: string; title: string
  subject_employee_name: string; category_display: string
  severity: string; status: string; opened_date: string
}

export default function ERCases() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['er-cases', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/er/cases/?${params}`).then(r => r.data)
    },
  })

  const filtered = search
    ? data?.results?.filter((r: ERCase) =>
        r.case_number?.toLowerCase().includes(search.toLowerCase()) ||
        r.title?.toLowerCase().includes(search.toLowerCase()) ||
        r.subject_employee_name?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="ER Cases">
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search case or employee..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-40">
            <option value="">All Statuses</option>
            {['OPEN','INVESTIGATING','PENDING_HEARING','PENDING_OUTCOME','CLOSED','WITHDRAWN'].map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
          </Select>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={Scale} title="No ER cases found" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Case #</Th><Th>Title</Th><Th>Subject Employee</Th><Th>Category</Th><Th>Severity</Th><Th>Status</Th><Th>Opened</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: ERCase) => (
                    <Tr key={r.id} className="cursor-pointer hover:bg-gray-50" onClick={() => navigate(`/er/cases/${r.id}`)}>
                      <Td className="font-mono text-sm font-medium text-blue-600">{r.case_number}</Td>
                      <Td className="font-medium">{r.title}</Td>
                      <Td>{r.subject_employee_name}</Td>
                      <Td className="text-gray-600">{r.category_display}</Td>
                      <Td><Badge status={r.severity} /></Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td className="text-gray-500">{fmt(r.opened_date)}</Td>
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
