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
import { Search, AlertTriangle } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type HSEIncident = {
  id: string; incident_number: string; title: string
  incident_type_display: string; severity: string
  reported_by_display: string; incident_date: string; status: string
}

export default function HSEIncidents() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['hse-incidents', page, severityFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (severityFilter) params.set('severity', severityFilter)
      return api.get(`/hse/incidents/?${params}`).then(r => r.data)
    },
  })

  const filtered = search
    ? data?.results?.filter((r: HSEIncident) =>
        r.title?.toLowerCase().includes(search.toLowerCase()) ||
        r.incident_number?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="HSE Incidents">
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search incident..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <Select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)} className="w-36">
            <option value="">All Severities</option>
            {['NEAR_MISS','MINOR','MODERATE','MAJOR','CRITICAL','FATAL'].map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
          </Select>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={AlertTriangle} title="No HSE incidents" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Incident #</Th><Th>Title</Th><Th>Type</Th><Th>Severity</Th><Th>Reported By</Th><Th>Date</Th><Th>Status</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: HSEIncident) => (
                    <Tr key={r.id}>
                      <Td className="font-mono text-sm">{r.incident_number}</Td>
                      <Td className="font-medium">{r.title}</Td>
                      <Td className="text-gray-600">{r.incident_type_display}</Td>
                      <Td><Badge status={r.severity} /></Td>
                      <Td>{r.reported_by_display}</Td>
                      <Td>{fmt(r.incident_date)}</Td>
                      <Td><Badge status={r.status} /></Td>
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
