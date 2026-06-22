import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Search, FileText } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type Payslip = {
  id: string; employee: string; employee_name: string; employee_number: string
  payroll_run: string; basic_pay: string; gross_pay: string
  total_deductions: string; net_pay: string; payslip_date: string; is_locked: boolean
}

export default function Payslips() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [runFilter, setRunFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['payslips', page, runFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (runFilter) params.set('payroll_run', runFilter)
      return api.get(`/payroll/payslips/?${params}`).then(r => r.data)
    },
  })

  const filtered = search
    ? data?.results?.filter((r: Payslip) => r.employee_name?.toLowerCase().includes(search.toLowerCase()) || r.employee_number?.includes(search))
    : data?.results

  return (
    <AppLayout title="Payslips">
      <div className="space-y-4">
        <Card>
          <div className="p-4 border-b flex items-center gap-3">
            <div className="relative flex-1">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search employee..." value={search} onChange={e => setSearch(e.target.value)} />
            </div>
          </div>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={FileText} title="No payslips found" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee No.</Th><Th>Name</Th><Th>Payslip Date</Th><Th>Basic Pay</Th><Th>Gross Pay</Th><Th>Deductions</Th><Th>Net Pay</Th><Th>Locked</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: Payslip) => (
                    <Tr key={r.id}>
                      <Td className="font-mono text-sm">{r.employee_number}</Td>
                      <Td className="font-medium">{r.employee_name}</Td>
                      <Td>{fmt(r.payslip_date)}</Td>
                      <Td>{Number(r.basic_pay).toLocaleString()}</Td>
                      <Td>{Number(r.gross_pay).toLocaleString()}</Td>
                      <Td className="text-red-600">({Number(r.total_deductions).toLocaleString()})</Td>
                      <Td className="font-bold text-green-700">{Number(r.net_pay).toLocaleString()}</Td>
                      <Td>{r.is_locked ? <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">Locked</span> : <span className="text-xs text-gray-400">Open</span>}</Td>
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
