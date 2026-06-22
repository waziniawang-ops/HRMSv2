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
import { Search, FileText } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

type DocRecord = {
  id: string; title: string; document_number: string
  category_display: string; owner_employee_name: string
  status: string; issue_date: string; expiry_date: string | null
}

export default function DocRecords() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['doc-records', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/documents/records/?${params}`).then(r => r.data)
    },
  })

  const filtered = search
    ? data?.results?.filter((r: DocRecord) =>
        r.title?.toLowerCase().includes(search.toLowerCase()) ||
        r.document_number?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="Document Records">
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search title or doc number..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-36">
            <option value="">All Statuses</option>
            {['ACTIVE','EXPIRED','REVOKED','ARCHIVED'].map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={FileText} title="No document records" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Doc #</Th><Th>Title</Th><Th>Category</Th><Th>Owner</Th><Th>Issued</Th><Th>Expires</Th><Th>Status</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: DocRecord) => (
                    <Tr key={r.id}>
                      <Td className="font-mono text-sm">{r.document_number}</Td>
                      <Td className="font-medium">{r.title}</Td>
                      <Td className="text-gray-600">{r.category_display}</Td>
                      <Td>{r.owner_employee_name || '—'}</Td>
                      <Td>{fmt(r.issue_date)}</Td>
                      <Td>{r.expiry_date ? fmt(r.expiry_date) : '—'}</Td>
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
