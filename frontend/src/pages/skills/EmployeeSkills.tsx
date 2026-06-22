import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Search, Star } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type EmployeeSkill = {
  id: string; employee_name: string; employee_number: string
  skill_name: string; proficiency_display: string
  is_verified: boolean; acquired_date: string | null; expiry_date: string | null
}

export default function EmployeeSkills() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['employee-skills', page],
    queryFn: () => api.get(`/skills/employee-skills/?page=${page}`).then(r => r.data),
  })

  const filtered = search
    ? data?.results?.filter((r: EmployeeSkill) =>
        r.employee_name?.toLowerCase().includes(search.toLowerCase()) ||
        r.skill_name?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="Employee Skills">
      <div className="space-y-4">
        <div className="relative max-w-sm">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search employee or skill..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={Star} title="No employee skills recorded" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Skill</Th><Th>Proficiency</Th><Th>Verified</Th><Th>Acquired</Th><Th>Expires</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: EmployeeSkill) => (
                    <Tr key={r.id}>
                      <Td className="font-medium">{r.employee_name} <span className="text-gray-400 text-xs">#{r.employee_number}</span></Td>
                      <Td>{r.skill_name}</Td>
                      <Td>{r.proficiency_display}</Td>
                      <Td><Badge status={r.is_verified ? 'VERIFIED' : 'UNVERIFIED'} /></Td>
                      <Td className="text-gray-500">{r.acquired_date ? fmt(r.acquired_date) : '—'}</Td>
                      <Td className="text-gray-500">{r.expiry_date ? fmt(r.expiry_date) : '—'}</Td>
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
