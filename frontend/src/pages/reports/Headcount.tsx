import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { PageSpinner } from '@/components/ui/Spinner'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import api from '@/lib/api'

const COLORS = ['#3b82f6','#8b5cf6','#22c55e','#f59e0b','#ef4444','#06b6d4']

export default function HeadcountReport() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['report-headcount'],
    queryFn: () => api.get('/reports/headcount/').then(r => r.data),
    retry: false,
  })

  const chartData = (data ?? []).map((h: { org_unit__name: string; org_unit__type: string; headcount: number }) => ({
    name: h.org_unit__name,
    type: h.org_unit__type,
    count: h.headcount,
  }))

  const total = chartData.reduce((s: number, d: { count: number }) => s + d.count, 0)

  if (isError) return (
    <AppLayout title="Headcount by Department">
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <p className="text-lg font-semibold text-gray-700">Access Denied</p>
        <p className="text-sm text-gray-400 mt-1">You do not have permission to view this report.</p>
      </div>
    </AppLayout>
  )

  return (
    <AppLayout title="Headcount by Department">
      <div className="space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {chartData.slice(0, 4).map((d: { name: string; count: number }, i: number) => (
            <Card key={d.name}>
              <CardContent className="py-5">
                <div className="w-3 h-3 rounded-full mb-3" style={{ background: COLORS[i % COLORS.length] }} />
                <p className="text-2xl font-bold text-gray-900">{d.count}</p>
                <p className="text-sm text-gray-500 mt-0.5 truncate">{d.name}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Headcount Distribution</CardTitle>
            <span className="text-sm text-gray-500">Total: <strong className="text-gray-900">{total}</strong> employees</span>
          </CardHeader>
          <CardContent>
            {isLoading ? <PageSpinner /> : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData} barSize={40}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(v) => [`${v} employees`, 'Headcount']} />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {chartData.map((_: unknown, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Department Breakdown</CardTitle></CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Department</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Type</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">Headcount</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">% of Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {chartData.map((d: { name: string; type: string; count: number }, i: number) => (
                  <tr key={d.name} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full shrink-0" style={{ background: COLORS[i % COLORS.length] }} />
                        {d.name}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{d.type}</td>
                    <td className="px-4 py-3 text-right font-bold text-gray-900">{d.count}</td>
                    <td className="px-4 py-3 text-right text-gray-600">
                      {total ? `${((d.count / total) * 100).toFixed(1)}%` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}
