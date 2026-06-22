import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { UserCog } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type PCR = { id: string; employee: string; employee_name: string; field_label: string; old_value: string; new_value: string; status: string; created_at: string }

export default function ProfileChanges() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('PENDING')

  const { data, isLoading } = useQuery({
    queryKey: ['profile-changes', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/ess/profile-change-requests/?${params}`).then(r => r.data)
    },
  })

  const doAction = useMutation({
    mutationFn: ({ id, action, notes }: { id: string; action: string; notes?: string }) => api.post(`/ess/profile-change-requests/${id}/${action}/`, { review_notes: notes }),
    onSuccess: () => { toast.success('Done'); qc.invalidateQueries({ queryKey: ['profile-changes'] }) },
    onError: () => toast.error('Action failed'),
  })

  return (
    <AppLayout title="Profile Change Requests">
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-36">
            <option value="">All Statuses</option>
            {['PENDING','APPROVED','REJECTED'].map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
        </div>
        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={UserCog} title="No profile change requests" />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Field</Th><Th>Old Value</Th><Th>New Value</Th><Th>Requested</Th><Th>Status</Th><Th></Th></tr></Thead>
                <Tbody>
                  {data.results.map((r: PCR) => (
                    <Tr key={r.id}>
                      <Td className="font-medium">{r.employee_name}</Td>
                      <Td><span className="text-xs font-mono bg-gray-100 px-1.5 py-0.5 rounded">{r.field_label || r.field_label}</span></Td>
                      <Td className="text-gray-500 max-w-xs truncate">{r.old_value || '—'}</Td>
                      <Td className="font-medium max-w-xs truncate">{r.new_value}</Td>
                      <Td>{fmt(r.created_at)}</Td>
                      <Td><Badge status={r.status} /></Td>
                      <Td>
                        {r.status === 'PENDING' && (
                          <div className="flex gap-1 justify-end">
                            <button onClick={() => doAction.mutate({ id: r.id, action: 'approve' })} className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200">Approve</button>
                            <button onClick={() => doAction.mutate({ id: r.id, action: 'reject' })} className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200">Reject</button>
                          </div>
                        )}
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
