import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { PageSpinner } from '@/components/ui/Spinner'
import api from '@/lib/api'
import {
  Users, Briefcase, GitPullRequest, UserPlus, FileText, CheckCircle2,
  TrendingUp, BookOpen, ArrowUpRight
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts'

interface DashboardData {
  total_active_employees: number
  open_vacancies: number
  pending_approvals: number
  active_requisitions: number
  open_job_postings: number
  pending_onboarding_cases: number
  new_hires_this_month: number
}

const PIE_COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6']

function StatCard({
  label, value, icon: Icon, color, delta
}: { label: string; value: number; icon: React.ElementType; color: string; delta?: string }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
          <Icon size={22} className="text-white" />
        </div>
        <div className="flex-1">
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-sm text-gray-500">{label}</p>
        </div>
        {delta && (
          <div className="flex items-center gap-0.5 text-green-600 text-xs font-medium">
            <ArrowUpRight size={14} />{delta}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default function Dashboard() {
  const { data, isLoading, isError } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: () => api.get('/reports/dashboard/').then(r => r.data),
    refetchInterval: 30000,
    retry: false,
  })

  const { data: headcount } = useQuery({
    queryKey: ['headcount'],
    queryFn: () => api.get('/reports/headcount/').then(r => r.data),
  })

  const { data: funnel } = useQuery({
    queryKey: ['funnel'],
    queryFn: () => api.get('/reports/hiring-funnel/').then(r => r.data),
  })

  const { data: perfDist } = useQuery({
    queryKey: ['perf-dist'],
    queryFn: () => api.get('/reports/performance-distribution/').then(r => r.data),
  })

  const { data: learning } = useQuery({
    queryKey: ['learning-compliance'],
    queryFn: () => api.get('/reports/learning-compliance/').then(r => r.data),
  })

  if (isLoading) return <AppLayout title="Dashboard"><PageSpinner /></AppLayout>
  if (isError || !data) return (
    <AppLayout title="Dashboard">
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center mb-4">
          <TrendingUp size={28} className="text-blue-600" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Welcome to HRMSv2</h2>
        <p className="text-sm text-gray-500 max-w-sm">Use the sidebar to navigate to your available modules.</p>
      </div>
    </AppLayout>
  )

  const headcountChart = (headcount ?? []).map((h: { org_unit__name: string; headcount: number }) => ({
    name: h.org_unit__name,
    count: h.headcount,
  }))

  const funnelChart = funnel ? [
    { stage: 'Applications', count: funnel.total_applications },
    { stage: 'Shortlisted', count: funnel.shortlisted },
    { stage: 'Offers Made', count: funnel.offers_made },
    { stage: 'Accepted', count: funnel.offers_accepted },
  ] : []

  const perfChart = (perfDist?.distribution ?? []).map((d: { outcome_label: string; count: number }) => ({
    name: d.outcome_label,
    value: d.count,
  }))

  return (
    <AppLayout title="HR Executive Dashboard">
      <div className="space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Active Employees" value={data.total_active_employees} icon={Users} color="bg-blue-600" />
          <StatCard label="Open Vacancies" value={data.open_vacancies} icon={Briefcase} color="bg-orange-500" />
          <StatCard label="Active Requisitions" value={data.active_requisitions} icon={GitPullRequest} color="bg-purple-600" />
          <StatCard label="Open Job Postings" value={data.open_job_postings} icon={FileText} color="bg-teal-600" />
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Pending Approvals" value={data.pending_approvals} icon={CheckCircle2} color="bg-yellow-500" />
          <StatCard label="New Hires This Month" value={data.new_hires_this_month} icon={UserPlus} color="bg-green-600" />
          <StatCard label="Pending Onboarding" value={data.pending_onboarding_cases} icon={UserPlus} color="bg-indigo-600" />
          <StatCard
            label="Learning Compliance"
            value={learning?.compliance_rate ?? 0}
            icon={BookOpen}
            color="bg-pink-600"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Headcount by Org Unit */}
          <Card>
            <CardHeader>
              <CardTitle>Headcount by Department</CardTitle>
            </CardHeader>
            <CardContent>
              {headcountChart.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={headcountChart} barSize={32}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <p className="text-sm text-gray-400 text-center py-8">No data available</p>}
            </CardContent>
          </Card>

          {/* Hiring Funnel */}
          <Card>
            <CardHeader>
              <CardTitle>Hiring Funnel (Current Year)</CardTitle>
            </CardHeader>
            <CardContent>
              {funnelChart.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={funnelChart} barSize={32} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                    <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
                    <YAxis dataKey="stage" type="category" tick={{ fontSize: 11 }} width={90} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <p className="text-sm text-gray-400 text-center py-8">No data available</p>}
            </CardContent>
          </Card>
        </div>

        {/* Performance + Learning */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Performance Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              {perfChart.length > 0 ? (
                <div className="flex items-center gap-4">
                  <ResponsiveContainer width="60%" height={180}>
                    <PieChart>
                      <Pie data={perfChart} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value">
                        {perfChart.map((_: unknown, i: number) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex-1 space-y-2">
                    {perfChart.map((d: { name: string; value: number }, i: number) => (
                      <div key={d.name} className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                        <span className="text-xs text-gray-600">{d.name}: <strong>{d.value}</strong></span>
                      </div>
                    ))}
                    {perfDist?.average_rating && (
                      <div className="pt-2 border-t border-gray-100">
                        <p className="text-xs text-gray-500">Avg Rating</p>
                        <p className="text-xl font-bold text-blue-600">{Number(perfDist.average_rating).toFixed(1)}</p>
                      </div>
                    )}
                  </div>
                </div>
              ) : <p className="text-sm text-gray-400 text-center py-8">No data available</p>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Learning & Compliance</CardTitle>
            </CardHeader>
            <CardContent>
              {learning ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="p-3 rounded-xl bg-blue-50">
                      <p className="text-xl font-bold text-blue-700">{learning.mandatory_assignments_total}</p>
                      <p className="text-xs text-blue-600 mt-0.5">Mandatory</p>
                    </div>
                    <div className="p-3 rounded-xl bg-green-50">
                      <p className="text-xl font-bold text-green-700">{learning.completed}</p>
                      <p className="text-xs text-green-600 mt-0.5">Completed</p>
                    </div>
                    <div className="p-3 rounded-xl bg-red-50">
                      <p className="text-xl font-bold text-red-700">{learning.overdue}</p>
                      <p className="text-xs text-red-600 mt-0.5">Overdue</p>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600 font-medium">Compliance Rate</span>
                      <span className="font-bold text-gray-900">{learning.compliance_rate}%</span>
                    </div>
                    <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-green-500 rounded-full transition-all"
                        style={{ width: `${learning.compliance_rate}%` }}
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-2 p-3 rounded-xl bg-teal-50">
                    <TrendingUp size={18} className="text-teal-600" />
                    <p className="text-sm text-teal-700 font-medium">
                      {learning.compliance_rate >= 80 ? 'On track — good compliance' : 'Below target — review assignments'}
                    </p>
                  </div>
                </div>
              ) : <p className="text-sm text-gray-400 text-center py-8">No data available</p>}
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  )
}
