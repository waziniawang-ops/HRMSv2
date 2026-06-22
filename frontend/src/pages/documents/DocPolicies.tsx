import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Search, BookOpen } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type DocPolicy = {
  id: string; name: string; version: string; policy_number: string
  category_display: string; status: string
  effective_date: string; expiry_date: string | null; acknowledgement_required: boolean
}

export default function DocPolicies() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['doc-policies', page],
    queryFn: () => api.get(`/documents/policies/?page=${page}`).then(r => r.data),
  })

  const filtered = search
    ? data?.results?.filter((r: DocPolicy) => r.name?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="Policies">
      <div className="space-y-4">
        <div className="relative max-w-sm">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search policy name..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={BookOpen} title="No policies found" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Policy #</Th><Th>Name</Th><Th>Version</Th><Th>Category</Th><Th>Effective</Th><Th>Expiry</Th><Th>Ack Required</Th><Th>Status</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: DocPolicy) => (
                    <Tr key={r.id}>
                      <Td className="font-mono text-sm">{r.policy_number}</Td>
                      <Td className="font-medium">{r.name}</Td>
                      <Td className="text-gray-600">v{r.version}</Td>
                      <Td className="text-gray-600">{r.category_display}</Td>
                      <Td>{fmt(r.effective_date)}</Td>
                      <Td>{r.expiry_date ? fmt(r.expiry_date) : '—'}</Td>
                      <Td>{r.acknowledgement_required ? <Badge status="REQUIRED" /> : <span className="text-gray-400 text-sm">No</span>}</Td>
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
