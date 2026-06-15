import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { PageSpinner } from '@/components/ui/Spinner'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import api from '@/lib/api'

const COLORS: Record<string, string> = {
  EXCEEDS: '#22c55e', MEETS: '#3b82f6', PARTIALLY: '#f59e0b', BELOW: '#ef4444'
}

export default function PerformanceReport() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['report-perf'],
    queryFn: () => api.get('/reports/performance-distribution/').then(r => r.data),
    retry: false,
  })

  const chartData = (data?.distribution ?? []).map((d: { outcome_label: string; count: number }) => ({
    name: d.outcome_label,
    value: d.count,
    color: COLORS[d.outcome_label] ?? '#94a3b8',
  }))

  if (isError) return (
    <AppLayout title="Performance Distribution">
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <p className="text-lg font-semibold text-gray-700">Access Denied</p>
        <p className="text-sm text-gray-400 mt-1">You do not have permission to view this report.</p>
      </div>
    </AppLayout>
  )

  return (
    <AppLayout title="Performance Distribution">
      {isLoading ? <PageSpinner /> : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {['EXCEEDS','MEETS','PARTIALLY','BELOW'].map(label => {
              const d = chartData.find((x: { name: string }) => x.name === label)
              return (
                <Card key={label}>
                  <CardContent className="py-5 text-center">
                    <div className="w-3 h-3 rounded-full mx-auto mb-3" style={{ background: COLORS[label] }} />
                    <p className="text-3xl font-bold text-gray-900">{d?.value ?? 0}</p>
                    <p className="text-sm text-gray-500 mt-1">{label.replace('_', ' ')}</p>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader><CardTitle>Outcome Distribution</CardTitle></CardHeader>
              <CardContent>
                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <PieChart>
                      <Pie data={chartData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}>
                        {chartData.map((d: { color: string }, i: number) => <Cell key={i} fill={d.color} />)}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                ) : <p className="text-center text-gray-400 py-12">No data available</p>}
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Summary Statistics</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-blue-50 rounded-xl">
                  <p className="text-sm text-blue-600 font-medium">Average Rating</p>
                  <p className="text-4xl font-bold text-blue-800 mt-1">{Number(data?.average_rating ?? 0).toFixed(2)}<span className="text-xl text-blue-400">/5.0</span></p>
                </div>
                <div className="space-y-3">
                  {chartData.map((d: { name: string; value: number; color: string }) => {
                    const total = chartData.reduce((s: number, x: { value: number }) => s + x.value, 0)
                    const pct = total > 0 ? (d.value / total) * 100 : 0
                    return (
                      <div key={d.name}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="font-medium text-gray-700">{d.name.replace('_', ' ')}</span>
                          <span className="text-gray-500">{d.value} · {pct.toFixed(1)}%</span>
                        </div>
                        <div className="w-full h-2 bg-gray-100 rounded-full">
                          <div className="h-full rounded-full" style={{ width: `${pct}%`, background: d.color }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </AppLayout>
  )
}
