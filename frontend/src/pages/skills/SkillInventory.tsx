import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Search, Zap } from 'lucide-react'
import api from '@/lib/api'

type Skill = {
  id: string; code: string; name: string; category_display: string
  skill_type_display: string; is_active: boolean
}

export default function SkillInventory() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['skills', page],
    queryFn: () => api.get(`/skills/skills/?page=${page}`).then(r => r.data),
  })

  const filtered = search
    ? data?.results?.filter((r: Skill) =>
        r.name?.toLowerCase().includes(search.toLowerCase()) ||
        r.code?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="Skill Inventory">
      <div className="space-y-4">
        <div className="relative max-w-sm">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search skills..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={Zap} title="No skills defined" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Code</Th><Th>Name</Th><Th>Category</Th><Th>Type</Th><Th>Status</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: Skill) => (
                    <Tr key={r.id}>
                      <Td className="font-mono text-sm">{r.code}</Td>
                      <Td className="font-medium">{r.name}</Td>
                      <Td className="text-gray-600">{r.category_display}</Td>
                      <Td className="text-gray-600">{r.skill_type_display}</Td>
                      <Td><Badge status={r.is_active ? 'ACTIVE' : 'INACTIVE'} /></Td>
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
