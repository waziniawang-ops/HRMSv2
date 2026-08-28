import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { AxiosError } from 'axios'
import toast from 'react-hot-toast'
import { Settings2 } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Select, Input } from '@/components/ui/Input'
import { useAuth } from '@/context/AuthContext'
import api from '@/lib/api'

type CurrencyOption = { code: string; name: string; symbol: string }
type CurrencyResponse = CurrencyOption & { currencies: CurrencyOption[] }
type GLSettings = { net_pay_account: string; contributions_payable_account: string }
type AccountingIntegration = {
  name: string; api_url: string; api_key_set: boolean
  auth_header_name: string; auth_header_prefix: string; is_configured: boolean
  last_test_at: string | null; last_test_success: boolean | null; last_test_detail: string
}
type AccountingForm = { name: string; api_url: string; api_key: string; auth_header_name: string; auth_header_prefix: string }

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

  const { data: glData, isLoading: glLoading } = useQuery<GLSettings>({
    queryKey: ['payroll-gl-settings'],
    queryFn: () => api.get('/payroll/gl-settings/').then(r => r.data),
  })
  const [glForm, setGlForm] = useState<GLSettings | null>(null)
  const activeGl = glForm ?? glData

  const updateGl = useMutation({
    mutationFn: (body: GLSettings) => api.put('/payroll/gl-settings/', body),
    onSuccess: () => {
      toast.success('GL posting accounts updated')
      qc.invalidateQueries({ queryKey: ['payroll-gl-settings'] })
      setGlForm(null)
    },
    onError: () => toast.error('Failed to update GL posting accounts'),
  })

  function errorDetail(e: unknown, fallback: string) {
    const detail = (e as AxiosError<{ detail?: string }>)?.response?.data?.detail
    return detail || fallback
  }

  const { data: acctData, isLoading: acctLoading } = useQuery<AccountingIntegration>({
    queryKey: ['accounting-integration'],
    queryFn: () => api.get('/payroll/accounting-integration/').then(r => r.data),
  })
  const [acctForm, setAcctForm] = useState<AccountingForm | null>(null)
  const activeAcct = acctForm ?? (acctData ? {
    name: acctData.name, api_url: acctData.api_url, api_key: '',
    auth_header_name: acctData.auth_header_name, auth_header_prefix: acctData.auth_header_prefix,
  } : null)

  const updateAcct = useMutation({
    mutationFn: (body: AccountingForm) => api.put('/payroll/accounting-integration/', body),
    onSuccess: () => {
      toast.success('Accounting integration settings updated')
      qc.invalidateQueries({ queryKey: ['accounting-integration'] })
      setAcctForm(null)
    },
    onError: (e: unknown) => toast.error(errorDetail(e, 'Failed to update accounting integration')),
  })

  const testAcct = useMutation({
    mutationFn: () => api.post('/payroll/accounting-integration/test/', {}),
    onSuccess: () => { toast.success('Test connection succeeded'); qc.invalidateQueries({ queryKey: ['accounting-integration'] }) },
    onError: (e: unknown) => {
      toast.error(errorDetail(e, 'Test connection failed'))
      qc.invalidateQueries({ queryKey: ['accounting-integration'] })
    },
  })

  return (
    <AppLayout title="System Settings">
      <div className="max-w-2xl space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Settings2 size={18} className="text-orange-600" />
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

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Settings2 size={18} className="text-orange-600" />
              <CardTitle>Payroll GL Posting Settings</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-5 pb-6">
            {glLoading ? (
              <p className="text-sm text-gray-500">Loading…</p>
            ) : (
              <>
                <p className="text-xs text-gray-400">
                  These GL account codes are used when auto-generating GL postings from a payroll run. Per-element accounts
                  (basic pay, allowances, deductions, tax) are configured individually on the <strong>Payroll → Elements</strong> page.
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="Net Pay Payable Account"
                    value={activeGl?.net_pay_account ?? ''}
                    onChange={e => setGlForm({
                      net_pay_account: e.target.value,
                      contributions_payable_account: activeGl?.contributions_payable_account ?? '',
                    })}
                    disabled={!isAdmin}
                  />
                  <Input
                    label="Contributions Payable Account"
                    value={activeGl?.contributions_payable_account ?? ''}
                    onChange={e => setGlForm({
                      net_pay_account: activeGl?.net_pay_account ?? '',
                      contributions_payable_account: e.target.value,
                    })}
                    disabled={!isAdmin}
                  />
                </div>
                {isAdmin && (
                  <div className="flex justify-end">
                    <Button
                      onClick={() => activeGl && updateGl.mutate(activeGl)}
                      disabled={!glForm || updateGl.isPending}
                      loading={updateGl.isPending}
                    >
                      Save
                    </Button>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Settings2 size={18} className="text-orange-600" />
                <CardTitle>Accounting System Integration</CardTitle>
              </div>
              {acctData && (
                <Badge
                  status={acctData.is_configured ? 'CONFIGURED' : 'NOT_CONFIGURED'}
                  className={acctData.is_configured ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}
                />
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-5 pb-6">
            {acctLoading ? (
              <p className="text-sm text-gray-500">Loading…</p>
            ) : (
              <>
                <p className="text-xs text-gray-400">
                  Configure a base URL and API key to enable "Send to Accounting System" on the GL Postings page.
                  HRMSv2 will POST a JSON payload of GL journal entries to this endpoint. Until this is configured
                  and saved, that button stays disabled — CSV export works regardless.
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="Display Name"
                    placeholder="e.g. Xero, QuickBooks, Internal ERP"
                    value={activeAcct?.name ?? ''}
                    onChange={e => setAcctForm({ ...(activeAcct as AccountingForm), name: e.target.value })}
                    disabled={!isAdmin}
                  />
                  <Input
                    label="API Base URL"
                    placeholder="https://api.example.com/journal-entries"
                    value={activeAcct?.api_url ?? ''}
                    onChange={e => setAcctForm({ ...(activeAcct as AccountingForm), api_url: e.target.value })}
                    disabled={!isAdmin}
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="Auth Header Name"
                    placeholder="Authorization"
                    value={activeAcct?.auth_header_name ?? ''}
                    onChange={e => setAcctForm({ ...(activeAcct as AccountingForm), auth_header_name: e.target.value })}
                    disabled={!isAdmin}
                  />
                  <Input
                    label="Auth Header Prefix"
                    placeholder="Bearer"
                    value={activeAcct?.auth_header_prefix ?? ''}
                    onChange={e => setAcctForm({ ...(activeAcct as AccountingForm), auth_header_prefix: e.target.value })}
                    disabled={!isAdmin}
                  />
                </div>
                <Input
                  label="API Key"
                  type="password"
                  placeholder={acctData?.api_key_set ? '•••••••• (leave blank to keep unchanged)' : 'Enter API key'}
                  value={activeAcct?.api_key ?? ''}
                  onChange={e => setAcctForm({ ...(activeAcct as AccountingForm), api_key: e.target.value })}
                  disabled={!isAdmin}
                />

                {acctData?.last_test_at && (
                  <p className={`text-xs ${acctData.last_test_success ? 'text-green-600' : 'text-red-600'}`}>
                    Last test ({new Date(acctData.last_test_at).toLocaleString()}): {acctData.last_test_success ? 'Success' : 'Failed'} — {acctData.last_test_detail}
                  </p>
                )}

                {isAdmin && (
                  <div className="flex justify-end gap-3">
                    <Button
                      variant="secondary"
                      onClick={() => testAcct.mutate()}
                      disabled={!acctData?.is_configured || testAcct.isPending}
                      loading={testAcct.isPending}
                    >
                      Test Connection
                    </Button>
                    <Button
                      onClick={() => activeAcct && updateAcct.mutate(activeAcct)}
                      disabled={!acctForm || updateAcct.isPending}
                      loading={updateAcct.isPending}
                    >
                      Save
                    </Button>
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
