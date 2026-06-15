import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Input, Select } from '@/components/ui/Input'
import { DatePicker } from '@/components/ui/DatePicker'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Clock } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type Record = {
  id: string
  employee: string
  employee_name: string
  employee_number: string
  date: string
  check_in: string | null
  check_out: string | null
  hours_worked: number | null
  method: string
}

function fmtTime(dt: string | null) {
  if (!dt) return '—'
  try { return new Date(dt).toLocaleTimeString('en-MY', { hour: '2-digit', minute: '2-digit', hour12: true }) }
  catch { return dt }
}

export default function AttendanceRecords() {
  const [page, setPage] = useState(1)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [methodFilter, setMethodFilter] = useState('')
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['attendance-records', page, dateFrom, dateTo, methodFilter, search],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (dateFrom) params.set('date__gte', dateFrom)
      if (dateTo) params.set('date__lte', dateTo)
      if (methodFilter) params.set('method', methodFilter)
      if (search) params.set('search', search)
      return api.get(`/attendance/records/?${params}`).then(r => r.data)
    },
  })

  return (
    <AppLayout title="Attendance Records">
      <div className="space-y-4">
        {/* Filters */}
        <div className="flex flex-wrap items-end gap-3">
          <DatePicker
            label="From"
            value={dateFrom}
            onChange={v => { setDateFrom(v); setPage(1) }}
            className="w-40"
          />
          <DatePicker
            label="To"
            value={dateTo}
            onChange={v => { setDateTo(v); setPage(1) }}
            className="w-40"
          />
          <Select
            value={methodFilter}
            onChange={e => { setMethodFilter(e.target.value); setPage(1) }}
            className="w-40"
          >
            <option value="">All Methods</option>
            <option value="FACE">Face</option>
            <option value="MANUAL">Manual</option>
          </Select>
          <Input
            placeholder="Search employee…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
            className="w-56"
          />
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Clock} title="No attendance records" description="Records appear here once employees check in via the kiosk." />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Employee</Th>
                    <Th>Number</Th>
                    <Th>Date</Th>
                    <Th>Check In</Th>
                    <Th>Check Out</Th>
                    <Th>Hours</Th>
                    <Th>Method</Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map((r: Record) => (
                    <Tr key={r.id}>
                      <Td className="font-medium text-gray-900">{r.employee_name}</Td>
                      <Td><span className="font-mono text-xs text-gray-600">{r.employee_number}</span></Td>
                      <Td>{fmt(r.date)}</Td>
                      <Td className="font-mono text-sm text-green-700">{fmtTime(r.check_in)}</Td>
                      <Td className="font-mono text-sm text-blue-700">{fmtTime(r.check_out)}</Td>
                      <Td>
                        {r.hours_worked != null
                          ? <span className="font-semibold text-gray-900">{r.hours_worked}h</span>
                          : <span className="text-gray-400 text-sm">—</span>}
                      </Td>
                      <Td>
                        <Badge
                          status={r.method === 'FACE' ? 'ACTIVE' : 'DRAFT'}
                          label={r.method === 'FACE' ? 'Face' : 'Manual'}
                        />
                      </Td>
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
