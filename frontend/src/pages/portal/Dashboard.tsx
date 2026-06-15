import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Briefcase, ChevronRight, Clock } from 'lucide-react'
import { PortalLayout } from './PortalLayout'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { usePortalAuth } from '@/context/PortalAuthContext'
import portalApi from '@/lib/portalApi'
import { fmt } from '@/lib/utils'

interface Application {
  id: string
  job_title: string
  stage: string
  applied_at: string
  updated_at: string
}

const STAGE_LABELS: Record<string, string> = {
  APPLIED: 'Application Received',
  UNDER_REVIEW: 'Under Review',
  SHORTLISTED: 'Shortlisted',
  INTERVIEW_SCHEDULED: 'Interview Scheduled',
  INTERVIEW_COMPLETED: 'Interview Completed',
  OFFERED: 'Offer Extended',
  OFFER_ACCEPTED: 'Offer Accepted',
  ONBOARDING: 'Onboarding',
  HIRED: 'Hired',
  REJECTED: 'Not Shortlisted',
  WITHDRAWN: 'Withdrawn',
}

export default function PortalDashboard() {
  const { user } = usePortalAuth()

  const { data, isLoading } = useQuery<{ count: number; results: Application[] }>({
    queryKey: ['portal-my-apps'],
    queryFn: () => portalApi.get('/recruitment/applications/').then(r => r.data),
  })

  return (
    <PortalLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.first_name || user?.username}
        </h1>
        <p className="text-gray-500 text-sm mt-1">Track your applications below</p>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <Link to="/portal" className="bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition-all flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center">
            <Briefcase size={18} className="text-blue-600" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">Browse Jobs</p>
            <p className="text-xs text-gray-400">See open vacancies</p>
          </div>
        </Link>
        <Link to="/portal/profile" className="bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition-all flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-purple-50 flex items-center justify-center">
            <span className="text-purple-600 text-lg font-bold">{(user?.first_name?.[0] || user?.username?.[0] || 'A').toUpperCase()}</span>
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">My Profile</p>
            <p className="text-xs text-gray-400">Edit your info</p>
          </div>
        </Link>
        <Link to="/portal/documents" className="bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition-all flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-green-50 flex items-center justify-center">
            <Briefcase size={18} className="text-green-600" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">My Documents</p>
            <p className="text-xs text-gray-400">Manage uploads</p>
          </div>
        </Link>
      </div>

      {/* Applications */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">My Applications</h2>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12"><Spinner className="h-6 w-6" /></div>
        ) : !data?.results?.length ? (
          <div className="text-center py-16 text-gray-400">
            <Briefcase size={36} className="mx-auto mb-2 opacity-30" />
            <p className="text-gray-600 font-medium">No applications yet</p>
            <Link to="/portal" className="text-sm text-blue-600 hover:underline mt-1 inline-block">
              Browse open positions →
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {data.results.map((app) => (
              <div key={app.id} className="px-5 py-4 flex items-center justify-between gap-4 hover:bg-gray-50 transition-colors">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">{app.job_title}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <Badge status={app.stage} label={STAGE_LABELS[app.stage] ?? app.stage} />
                    <span className="flex items-center gap-1 text-xs text-gray-400">
                      <Clock size={11} /> Applied {fmt(app.applied_at)}
                    </span>
                  </div>
                </div>
                <ChevronRight size={16} className="text-gray-300 shrink-0" />
              </div>
            ))}
          </div>
        )}
      </div>
    </PortalLayout>
  )
}
