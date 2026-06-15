import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { PageSpinner } from '@/components/ui/Spinner'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import api from '@/lib/api'

export default function HiringFunnel() {
  const [year, setYear] = useState(new Date().getFullYear())

  const { data, isLoading, isError } = useQuery({
    queryKey: ['report-funnel', year],
    queryFn: () => api.get(`/reports/hiring-funnel/?year=${year}`).then(r => r.data),
    retry: false,
  })

  const chartData = data ? [
    { stage: 'Applications', count: data.total_applications, color: '#3b82f6' },
    { stage: 'Shortlisted', count: data.shortlisted, color: '#8b5cf6' },
    { stage: 'Offers Made', count: data.offers_made, color: '#f59e0b' },
    { stage: 'Accepted', count: data.offers_accepted, color: '#22c55e' },
  ] : []

  if (isError) return (
    <AppLayout title="Hiring Funnel">
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <p className="text-lg font-semibold text-gray-700">Access Denied</p>
        <p className="text-sm text-gray-400 mt-1">You do not have permission to view this report.</p>
      </div>
    </AppLayout>
  )

  return (
    <AppLayout title="Hiring Funnel">
      <div className="space-y-6">
        <div className="flex justify-end">
          <select
            value={year}
            onChange={e => setYear(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {[2024, 2025, 2026, 2027].map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>

        {isLoading ? <PageSpinner /> : data && (
          <>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {chartData.map(d => (
                <Card key={d.stage}>
                  <CardContent className="py-5 text-center">
                    <p className="text-3xl font-bold text-gray-900">{d.count}</p>
                    <p className="text-sm text-gray-500 mt-1">{d.stage}</p>
                    <div className="w-full h-1 mt-3 rounded-full" style={{ background: d.color }} />
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Funnel Chart — {year}</CardTitle>
                <span className="text-sm font-semibold text-green-700">
                  Offer Acceptance: {data.offer_acceptance_rate?.toFixed(1)}%
                </span>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={chartData} layout="vertical" barSize={36}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                    <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
                    <YAxis dataKey="stage" type="category" tick={{ fontSize: 12 }} width={100} />
                    <Tooltip />
                    <Bar dataKey="count" radius={[0, 6, 6, 0]} fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="py-5">
                <div className="flex items-center gap-3 p-4 bg-green-50 rounded-xl">
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-green-800">Conversion Rate</p>
                    <p className="text-xs text-green-600 mt-0.5">
                      {data.total_applications} applications → {data.offers_accepted} hires
                      ({data.total_applications > 0 ? ((data.offers_accepted / data.total_applications) * 100).toFixed(1) : 0}% overall)
                    </p>
                  </div>
                  <p className="text-3xl font-bold text-green-700">{data.offer_acceptance_rate?.toFixed(0)}%</p>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </AppLayout>
  )
}
