import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { PageSpinner } from '@/components/ui/Spinner'
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'
import { BookOpen, CheckCircle2, AlertCircle, TrendingUp } from 'lucide-react'
import api from '@/lib/api'

export default function LearningReport() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['report-learning'],
    queryFn: () => api.get('/reports/learning-compliance/').then(r => r.data),
    retry: false,
  })

  const rate = data?.compliance_rate ?? 0
  const radialData = [{ name: 'Compliance', value: rate, fill: rate >= 80 ? '#22c55e' : rate >= 60 ? '#f59e0b' : '#ef4444' }]

  if (isError) return (
    <AppLayout title="Learning Compliance">
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <p className="text-lg font-semibold text-gray-700">Access Denied</p>
        <p className="text-sm text-gray-400 mt-1">You do not have permission to view this report.</p>
      </div>
    </AppLayout>
  )

  return (
    <AppLayout title="Learning Compliance">
      {isLoading ? <PageSpinner /> : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader><CardTitle>Compliance Rate</CardTitle></CardHeader>
              <CardContent className="flex items-center gap-6">
                <div className="relative w-36 h-36">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="100%" data={radialData} startAngle={90} endAngle={-270}>
                      <RadialBar dataKey="value" cornerRadius={10} background={{ fill: '#f1f5f9' }} />
                    </RadialBarChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-0 flex items-center justify-center flex-col">
                    <span className="text-2xl font-bold text-gray-900">{rate.toFixed(0)}%</span>
                    <span className="text-xs text-gray-500">compliance</span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
                      <BookOpen size={18} className="text-blue-600" />
                    </div>
                    <div>
                      <p className="text-lg font-bold text-gray-900">{data?.mandatory_assignments_total}</p>
                      <p className="text-xs text-gray-500">Mandatory Assignments</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-green-100 flex items-center justify-center">
                      <CheckCircle2 size={18} className="text-green-600" />
                    </div>
                    <div>
                      <p className="text-lg font-bold text-gray-900">{data?.completed}</p>
                      <p className="text-xs text-gray-500">Completed</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center">
                      <AlertCircle size={18} className="text-red-500" />
                    </div>
                    <div>
                      <p className="text-lg font-bold text-gray-900">{data?.overdue}</p>
                      <p className="text-xs text-gray-500">Overdue</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Compliance Status</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className={`p-5 rounded-2xl ${rate >= 80 ? 'bg-green-50' : rate >= 60 ? 'bg-yellow-50' : 'bg-red-50'}`}>
                  <div className="flex items-center gap-3">
                    <TrendingUp size={24} className={rate >= 80 ? 'text-green-600' : rate >= 60 ? 'text-yellow-600' : 'text-red-600'} />
                    <div>
                      <p className={`font-bold text-lg ${rate >= 80 ? 'text-green-800' : rate >= 60 ? 'text-yellow-800' : 'text-red-800'}`}>
                        {rate >= 80 ? '✓ On Track' : rate >= 60 ? '⚠ Needs Attention' : '✗ Below Target'}
                      </p>
                      <p className={`text-sm mt-0.5 ${rate >= 80 ? 'text-green-600' : rate >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {rate >= 80 ? 'Mandatory training compliance is healthy'
                          : rate >= 60 ? 'Some employees are behind on mandatory courses'
                          : 'Urgent action required — many overdue assignments'}
                      </p>
                    </div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600">Overall Progress</span>
                    <span className="font-bold text-gray-900">{data?.completed}/{data?.mandatory_assignments_total}</span>
                  </div>
                  <div className="w-full h-4 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{ width: `${rate}%`, background: rate >= 80 ? '#22c55e' : rate >= 60 ? '#f59e0b' : '#ef4444' }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </AppLayout>
  )
}
