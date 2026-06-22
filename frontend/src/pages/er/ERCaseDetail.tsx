import { useQuery } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { PageSpinner } from '@/components/ui/Spinner'
import { ArrowLeft } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'

export default function ERCaseDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: c, isLoading } = useQuery({
    queryKey: ['er-case', id],
    queryFn: () => api.get(`/er/cases/${id}/`).then(r => r.data),
    enabled: !!id,
  })

  if (isLoading) return <AppLayout title="ER Case"><PageSpinner /></AppLayout>
  if (!c) return <AppLayout title="ER Case"><p className="text-gray-500 p-6">Case not found.</p></AppLayout>

  return (
    <AppLayout title={`ER Case — ${c.case_number}`}>
      <div className="space-y-6 max-w-4xl">
        <Button variant="secondary" onClick={() => navigate('/er/cases')}><ArrowLeft size={16} /> Back to Cases</Button>

        <Card className="p-6 space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">{c.title}</h2>
              <p className="text-sm text-gray-500 mt-0.5">{c.case_number} · Opened {fmt(c.opened_date)}</p>
            </div>
            <div className="flex gap-2">
              <Badge status={c.severity} />
              <Badge status={c.status} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="text-gray-500">Subject Employee:</span> <span className="font-medium ml-1">{c.subject_employee_name}</span></div>
            <div><span className="text-gray-500">Category:</span> <span className="font-medium ml-1">{c.category_display}</span></div>
            <div><span className="text-gray-500">Assigned Officer:</span> <span className="font-medium ml-1">{c.assigned_officer_display || '—'}</span></div>
            <div><span className="text-gray-500">Closed Date:</span> <span className="font-medium ml-1">{c.closed_date ? fmt(c.closed_date) : '—'}</span></div>
          </div>
          {c.description && <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3">{c.description}</p>}
        </Card>

        {c.parties?.length > 0 && (
          <Card className="p-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Parties Involved</h3>
            <div className="space-y-2">
              {c.parties.map((p: { id: string; employee_name: string; role_display: string }) => (
                <div key={p.id} className="flex items-center gap-3 text-sm">
                  <span className="w-24 text-gray-500">{p.role_display}</span>
                  <span className="font-medium">{p.employee_name}</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {c.hearings?.length > 0 && (
          <Card className="p-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Hearings</h3>
            <div className="space-y-2">
              {c.hearings.map((h: { id: string; hearing_date: string; hearing_type_display: string; status: string; venue: string }) => (
                <div key={h.id} className="flex items-center gap-4 text-sm py-2 border-b last:border-0">
                  <span className="text-gray-500 w-32">{fmt(h.hearing_date)}</span>
                  <span>{h.hearing_type_display}</span>
                  <span className="text-gray-500">{h.venue}</span>
                  <Badge status={h.status} />
                </div>
              ))}
            </div>
          </Card>
        )}

        {c.outcome && (
          <Card className="p-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Outcome</h3>
            <div className="text-sm space-y-2">
              <div><span className="text-gray-500">Decision:</span> <span className="font-medium ml-1">{c.outcome.decision_display}</span></div>
              {c.outcome.sanction && <div><span className="text-gray-500">Sanction:</span> <span className="font-medium ml-1">{c.outcome.sanction}</span></div>}
              {c.outcome.summary && <p className="text-gray-700 bg-gray-50 rounded-lg p-3 mt-2">{c.outcome.summary}</p>}
            </div>
          </Card>
        )}
      </div>
    </AppLayout>
  )
}
