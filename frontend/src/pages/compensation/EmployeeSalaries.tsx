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
import { Search, DollarSign } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type EmployeeSalary = {
  id: string; employee_number: string; full_name: string; employment_status: string
  position_display: string; org_unit_display: string; grade_display: string
  current_salary: string | null; salary_currency: string | null; salary_effective_date: string | null
}

type OrgUnit = { id: string; name: string }
type Grade = { id: string; grade_name: string }

export default function EmployeeSalaries() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [orgUnit, setOrgUnit] = useState('')
  const [grade, setGrade] = useState('')

  const { data: orgUnitsData } = useQuery({
    queryKey: ['org-units-for-salaries'],
    queryFn: () => api.get('/core/org-units/?page_size=200').then(r => r.data),
  })
  const orgUnits: OrgUnit[] = orgUnitsData?.results || []

  const { data: gradesData } = useQuery({
    queryKey: ['grades-for-salaries'],
    queryFn: () => api.get('/core/grades/?page_size=200').then(r => r.data),
  })
  const grades: Grade[] = gradesData?.results || []

  const { data, isLoading } = useQuery({
    queryKey: ['employee-salaries', page, search, orgUnit, grade],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (search) params.set('search', search)
      if (orgUnit) params.set('org_unit', orgUnit)
      if (grade) params.set('grade', grade)
      return api.get(`/compensation/employee-salaries/?${params}`).then(r => r.data)
    },
  })

  const rows: EmployeeSalary[] = data?.results || []
  const totalSalary = rows.reduce((s, r) => s + (r.current_salary ? Number(r.current_salary) : 0), 0)
  const missingCount = rows.filter(r => !r.current_salary).length

  return (
    <AppLayout title="Employee Salaries">
      <div className="space-y-4">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Search employee..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
            />
          </div>
          <Select value={orgUnit} onChange={e => { setOrgUnit(e.target.value); setPage(1) }} className="w-52">
            <option value="">All Departments</option>
            {orgUnits.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
          </Select>
          <Select value={grade} onChange={e => { setGrade(e.target.value); setPage(1) }} className="w-40">
            <option value="">All Grades</option>
            {grades.map(g => <option key={g.id} value={g.id}>{g.grade_name}</option>)}
          </Select>
        </div>

        {rows.length > 0 && (
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <div className="p-4">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Total Salary (this page)</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{totalSalary.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
              </div>
            </Card>
            <Card>
              <div className="p-4">
                <p className="text-xs text-gray-500 uppercase tracking-wide">No Active Package</p>
                <p className={`text-xl font-bold mt-1 ${missingCount ? 'text-amber-600' : 'text-gray-900'}`}>{missingCount}</p>
              </div>
            </Card>
          </div>
        )}

        <Card>
          {isLoading ? <PageSpinner /> : !rows.length ? (
            <EmptyState icon={DollarSign} title="No employees found" />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Employee No.</Th><Th>Name</Th><Th>Department</Th><Th>Position</Th>
                    <Th>Grade</Th><Th>Current Salary</Th><Th>Effective Date</Th><Th>Status</Th>
                  </tr>
                </Thead>
                <Tbody>
                  {rows.map(r => (
                    <Tr key={r.id}>
                      <Td className="font-mono text-sm">{r.employee_number}</Td>
                      <Td className="font-medium">{r.full_name}</Td>
                      <Td>{r.org_unit_display || <span className="text-gray-400">—</span>}</Td>
                      <Td>{r.position_display || <span className="text-gray-400">—</span>}</Td>
                      <Td>{r.grade_display || <span className="text-gray-400">—</span>}</Td>
                      <Td className="font-semibold">
                        {r.current_salary
                          ? `${r.salary_currency} ${Number(r.current_salary).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                          : <span className="text-amber-600 text-xs">No active package</span>}
                      </Td>
                      <Td>{r.salary_effective_date ? fmt(r.salary_effective_date) : <span className="text-gray-400">—</span>}</Td>
                      <Td><Badge status={r.employment_status} /></Td>
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
