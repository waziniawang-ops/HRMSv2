import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Bell, CheckCheck } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type Notif = {
  id: string
  channel: string
  subject: string
  body: string
  status: string
  created_at: string
  reference_type: string
}

export default function Notifications() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('SENT')

  function invalidate() {
    qc.invalidateQueries({ queryKey: ['notifications'] })
    qc.invalidateQueries({ queryKey: ['notif-unread-count'] })
  }

  const { data, isLoading } = useQuery({
    queryKey: ['notifications', page, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      return api.get(`/notifications/inbox/?${params}`).then(r => r.data)
    },
  })

  const markRead = useMutation({
    mutationFn: (id: string) => api.post(`/notifications/inbox/${id}/mark_read/`),
    onSuccess: () => { invalidate(); toast.success('Marked as read') },
  })

  const markAllRead = useMutation({
    mutationFn: () => api.post('/notifications/inbox/mark_all_read/'),
    onSuccess: () => { invalidate(); toast.success('All notifications marked as read') },
  })

  const unreadCount = data?.count ?? 0

  return (
    <AppLayout title="Notifications">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <Select
            value={statusFilter}
            onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
            className="w-44"
          >
            <option value="SENT">Unread</option>
            <option value="">All</option>
            <option value="READ">Read</option>
            <option value="PENDING">Pending</option>
            <option value="FAILED">Failed</option>
          </Select>

          {statusFilter === 'SENT' && unreadCount > 0 && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => markAllRead.mutate()}
              disabled={markAllRead.isPending}
            >
              <CheckCheck size={14} />
              Mark all read ({unreadCount})
            </Button>
          )}
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState
              icon={Bell}
              title="No notifications"
              description={statusFilter === 'SENT' ? 'You have no unread notifications' : 'No notifications match the selected filter'}
            />
          ) : (
            <>
              <ul className="divide-y divide-gray-100">
                {data.results.map((n: Notif) => (
                  <li key={n.id} className={`flex items-start gap-4 px-5 py-4 ${n.status !== 'READ' ? 'bg-blue-50/40' : ''}`}>
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${n.channel === 'EMAIL' ? 'bg-blue-100' : 'bg-purple-100'}`}>
                      <Bell size={16} className={n.channel === 'EMAIL' ? 'text-blue-600' : 'text-purple-600'} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <p className="text-sm font-semibold text-gray-900 truncate">{n.subject || 'Notification'}</p>
                        <Badge status={n.channel} />
                        <Badge status={n.status} />
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-2">{n.body}</p>
                      <p className="text-xs text-gray-400 mt-1">{fmt(n.created_at, 'dd MMM yyyy HH:mm')} · {n.reference_type || 'System'}</p>
                    </div>
                    {n.status !== 'READ' && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => markRead.mutate(n.id)}
                        disabled={markRead.isPending}
                      >
                        <CheckCheck size={14} /> Mark read
                      </Button>
                    )}
                  </li>
                ))}
              </ul>
              <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />
            </>
          )}
        </Card>
      </div>
    </AppLayout>
  )
}
