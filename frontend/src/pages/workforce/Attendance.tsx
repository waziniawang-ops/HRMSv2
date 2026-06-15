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
import { Clock } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type AttendanceLog = {
  id: string
  employee_name: string
  date: string
  clock_in: string
  clock_out: string
  hours_worked: string
  is_present: boolean
  is_late: boolean
  source: string
}

export default function Attendance() {
  const [page, setPage] = useState(1)
  const [sourceFilter, setSourceFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['attendance', page, sourceFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (sourceFilter) params.set('source', sourceFilter)
      return api.get(`/workforce/attendance/?${params}`).then(r => r.data)
    },
  })

  function fmtTime(dt: string | null) {
    if (!dt) return '—'
    try { return new Date(dt).toLocaleTimeString('en-MY', { hour: '2-digit', minute: '2-digit', hour12: true }) }
    catch { return dt }
  }

  return (
    <AppLayout title="Attendance Logs">
      <div className="space-y-4">
        <div className="flex justify-end">
          <Select value={sourceFilter} onChange={e => setSourceFilter(e.target.value)} className="w-44">
            <option value="">All Sources</option>
            {['BIOMETRIC','MANUAL','MOBILE','SYSTEM'].map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Clock} title="No attendance records" description="Logs will appear here once check-ins are recorded" />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr><Th>Employee</Th><Th>Date</Th><Th>Clock In</Th><Th>Clock Out</Th><Th>Hours</Th><Th>Present</Th><Th>Late</Th><Th>Source</Th></tr>
                </Thead>
                <Tbody>
                  {data.results.map((log: AttendanceLog) => (
                    <Tr key={log.id}>
                      <Td className="font-medium text-gray-900">{log.employee_name || '—'}</Td>
                      <Td>{fmt(log.date)}</Td>
                      <Td className="font-mono text-xs">{fmtTime(log.clock_in)}</Td>
                      <Td className="font-mono text-xs">{fmtTime(log.clock_out)}</Td>
                      <Td className="font-semibold">{log.hours_worked ? `${log.hours_worked}h` : '—'}</Td>
                      <Td><Badge status={log.is_present ? 'ACTIVE' : 'REJECTED'} label={log.is_present ? 'Yes' : 'No'} /></Td>
                      <Td>{log.is_late ? <Badge status="PENDING" label="Late" /> : <span className="text-gray-400 text-xs">On time</span>}</Td>
                      <Td><span className="text-xs text-gray-500">{log.source}</span></Td>
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
