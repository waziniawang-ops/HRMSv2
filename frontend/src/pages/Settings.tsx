import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Settings2 } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Input'
import { useAuth } from '@/context/AuthContext'
import api from '@/lib/api'

type CurrencyOption = { code: string; name: string; symbol: string }
type CurrencyResponse = CurrencyOption & { currencies: CurrencyOption[] }

export default function Settings() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const isAdmin = user?.roles?.includes('SYSTEM_ADMIN') ?? user?.role === 'SYSTEM_ADMIN'

  const { data, isLoading } = useQuery<CurrencyResponse>({
    queryKey: ['currency-setting'],
    queryFn: () => api.get('/core/settings/currency/').then(r => r.data),
  })

  const [selected, setSelected] = useState('')

  const update = useMutation({
    mutationFn: (code: string) => api.put('/core/settings/currency/', { code }),
    onSuccess: (res) => {
      toast.success(`Currency updated to ${res.data.name}`)
      qc.invalidateQueries({ queryKey: ['currency-setting'] })
      setSelected('')
    },
    onError: () => toast.error('Failed to update currency'),
  })

  const currentCode = data?.code ?? 'BND'
  const activeCode = selected || currentCode

  return (
    <AppLayout title="System Settings">
      <div className="max-w-2xl space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Settings2 size={18} className="text-blue-600" />
              <CardTitle>Currency Settings</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-5 pb-6">
            {isLoading ? (
              <p className="text-sm text-gray-500">Loading…</p>
            ) : (
              <>
                <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl border border-gray-200">
                  <div className="flex-1">
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Active Currency</p>
                    <p className="text-lg font-bold text-gray-900">
                      {data?.symbol}&nbsp;
                      <span className="font-medium text-gray-600">{data?.name}</span>
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">Code: {data?.code}</p>
                  </div>
                </div>

                {isAdmin && (
                  <div className="space-y-3">
                    <label className="block text-sm font-medium text-gray-700">Change Currency</label>
                    <div className="flex items-center gap-3">
                      <Select
                        value={activeCode}
                        onChange={e => setSelected(e.target.value)}
                        className="flex-1"
                      >
                        {data?.currencies.map((c: CurrencyOption) => (
                          <option key={c.code} value={c.code}>
                            {c.symbol} — {c.name} ({c.code})
                          </option>
                        ))}
                      </Select>
                      <Button
                        onClick={() => update.mutate(activeCode)}
                        disabled={activeCode === currentCode || update.isPending}
                        loading={update.isPending}
                      >
                        Save
                      </Button>
                    </div>
                    <p className="text-xs text-gray-400">
                      This sets the currency symbol shown throughout the system for pay bands, salaries, and bonuses.
                    </p>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}
