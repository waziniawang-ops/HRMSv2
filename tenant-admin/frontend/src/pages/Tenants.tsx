import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import {
  Building2, Plus, Search, Pencil, Trash2, CheckCircle2, Clock, XCircle, Archive,
  Copy, AlertTriangle, ExternalLink, Loader2, KeyRound, ScrollText,
} from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardContent } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Input, Select, Textarea } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { fmt, apiErrorMessage } from '@/lib/utils'
import api from '@/lib/api'

type PlanSummary = {
  id: string
  name: string
  slug: string
  is_active: boolean
}

type Tenant = {
  id: string
  name: string
  slug: string
  domain: string | null
  plan: string
  plan_detail: PlanSummary | null
  status: string
  status_display: string
  admin_first_name: string
  admin_last_name: string
  admin_email: string
  admin_phone: string
  has_stored_password: boolean
  oauth_enabled: boolean
  oauth_issuer: string
  oauth_client_id: string
  has_oauth_client_secret: boolean
  oauth_button_label: string
  oauth_redirect_uri: string | null
  provisioning_status: string
  provisioning_status_display: string
  provisioning_error: string
  provisioning_log: string
  backend_url: string
  frontend_url: string
  notes: string
  created_at: string
  // Present exactly once, on whichever response first observes it after
  // provisioning succeeds — see tenant-admin/tenants/api.py's _pop_password.
  initial_admin_password?: string
}

const emptyForm = {
  name: '', slug: '', domain: '', plan: '', status: 'PENDING',
  admin_first_name: '', admin_last_name: '', admin_email: '', admin_phone: '',
  oauth_enabled: false, oauth_issuer: '', oauth_client_id: '', oauth_client_secret: '', oauth_button_label: '',
  notes: '',
}

const STAT_DEFS = [
  { status: 'ACTIVE', label: 'Active', icon: CheckCircle2, color: 'text-success-600 bg-success-50' },
  { status: 'PENDING', label: 'Pending', icon: Clock, color: 'text-warning-600 bg-warning-50' },
  { status: 'SUSPENDED', label: 'Suspended', icon: XCircle, color: 'text-danger-600 bg-danger-50' },
  { status: 'OFFBOARDED', label: 'Offboarded', icon: Archive, color: 'text-slate-500 bg-slate-100' },
]

function slugify(s: string) {
  return s.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
}

export default function Tenants() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [planFilter, setPlanFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Tenant | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [slugTouched, setSlugTouched] = useState(false)

  // Tracks the last password value the operator dismissed, so the modal
  // doesn't pop back open for the same value from a stale cached response.
  const [dismissedPassword, setDismissedPassword] = useState<string | null>(null)

  // Populated on demand by the "reveal password" action per row (separate
  // from the auto-popup above, which only ever fires once right after
  // creation) — cleared as soon as its modal is closed, never cached.
  const [manualReveal, setManualReveal] = useState<{ tenantName: string; password: string } | null>(null)

  // Which tenant's provisioning log is open, by id — not the tenant object
  // itself, so the modal always reads the live (polling-refreshed) log text
  // out of `tenants` below rather than a stale snapshot from when it opened.
  const [logTenantId, setLogTenantId] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['tenants', page, search, statusFilter, planFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (search) params.set('search', search)
      if (statusFilter) params.set('status', statusFilter)
      if (planFilter) params.set('plan', planFilter)
      return api.get(`/tenants/?${params}`).then(r => r.data)
    },
    // Only keep polling while something is actually mid-provisioning, so an
    // idle screen doesn't hit the API every 3s forever.
    refetchInterval: query => {
      const results = (query.state.data as { results?: Tenant[] } | undefined)?.results
      return results?.some(t => t.provisioning_status === 'PROVISIONING' || t.provisioning_status === 'DEPROVISIONING') ? 3000 : false
    },
  })

  const { data: allTenants } = useQuery({
    queryKey: ['tenants-all-for-stats'],
    queryFn: () => api.get('/tenants/?page_size=1000').then(r => r.data),
    refetchInterval: query => {
      const results = (query.state.data as { results?: Tenant[] } | undefined)?.results
      return results?.some(t => t.provisioning_status === 'PROVISIONING' || t.provisioning_status === 'DEPROVISIONING') ? 3000 : false
    },
  })

  // The freshly-generated admin password rides along on whichever of the
  // two queries above first re-fetches after provisioning succeeds (the API
  // hands it out exactly once, then never again) — derived directly from
  // render-time data rather than mirrored into state via an effect.
  const passwordSource: Tenant[] = data?.results ?? allTenants?.results ?? []
  const passwordCandidate = passwordSource.find(t => t.initial_admin_password)
  const revealedPassword =
    passwordCandidate?.initial_admin_password && passwordCandidate.initial_admin_password !== dismissedPassword
      ? { tenantName: passwordCandidate.name, password: passwordCandidate.initial_admin_password }
      : null
  const activePasswordModal = revealedPassword ?? manualReveal
  const statCounts = STAT_DEFS.map(s => ({
    ...s,
    count: (allTenants?.results ?? []).filter((t: Tenant) => t.status === s.status).length,
  }))

  const { data: plansData } = useQuery({
    queryKey: ['plans-for-tenant-form'],
    queryFn: () => api.get('/plans/?page_size=100').then(r => r.data),
  })
  const plans: PlanSummary[] = plansData?.results ?? []

  function openCreate() {
    setEditing(null)
    setForm({ ...emptyForm, plan: plans.find(p => p.slug === 'trial')?.id ?? plans[0]?.id ?? '' })
    setSlugTouched(false)
    setModalOpen(true)
  }

  function openEdit(t: Tenant) {
    setEditing(t)
    setForm({
      name: t.name, slug: t.slug, domain: t.domain ?? '', plan: t.plan,
      status: t.status,
      admin_first_name: t.admin_first_name, admin_last_name: t.admin_last_name,
      admin_email: t.admin_email, admin_phone: t.admin_phone,
      // oauth_client_secret is write-only and never comes back from the API
      // — left blank here on purpose, matching "blank on save = keep the
      // existing secret" (see has_oauth_client_secret for what's shown to
      // the operator instead of the actual value).
      oauth_enabled: t.oauth_enabled, oauth_issuer: t.oauth_issuer, oauth_client_id: t.oauth_client_id,
      oauth_client_secret: '', oauth_button_label: t.oauth_button_label,
      notes: t.notes,
    })
    setSlugTouched(true)
    setModalOpen(true)
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/tenants/', body),
    onSuccess: () => {
      toast.success('Tenant created — provisioning its deployment now')
      qc.invalidateQueries({ queryKey: ['tenants'] })
      qc.invalidateQueries({ queryKey: ['tenants-all-for-stats'] })
      setModalOpen(false)
    },
    onError: (e: unknown) => toast.error(apiErrorMessage(e, 'Failed to create tenant')),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: { id: string } & object) => api.patch(`/tenants/${id}/`, body),
    onSuccess: () => {
      toast.success('Tenant updated')
      qc.invalidateQueries({ queryKey: ['tenants'] })
      qc.invalidateQueries({ queryKey: ['tenants-all-for-stats'] })
      setModalOpen(false)
    },
    onError: (e: unknown) => toast.error(apiErrorMessage(e, 'Failed to update tenant')),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/tenants/${id}/`),
    onSuccess: () => {
      toast.success('Deleting Render services — this tenant will disappear once teardown finishes')
      qc.invalidateQueries({ queryKey: ['tenants'] })
      qc.invalidateQueries({ queryKey: ['tenants-all-for-stats'] })
    },
    onError: (e: unknown) => toast.error(apiErrorMessage(e, 'Failed to delete tenant')),
  })

  const revealPassword = useMutation({
    mutationFn: (t: Tenant) => api.post(`/tenants/${t.id}/reveal-password/`).then(r => ({ tenant: t, password: r.data.admin_password as string })),
    onSuccess: ({ tenant, password }) => setManualReveal({ tenantName: tenant.name, password }),
    onError: (e: unknown) => toast.error(apiErrorMessage(e, 'Failed to reveal password')),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const body = { ...form, domain: form.domain || null }
    if (editing) update.mutate({ id: editing.id, ...body })
    else create.mutate(body)
  }

  function handleDelete(t: Tenant) {
    if (confirm(`Delete "${t.name}"? This permanently deletes its database and Render services (backend + frontend). This cannot be undone.`)) {
      remove.mutate(t.id)
    }
  }

  const tenants: Tenant[] = data?.results ?? []
  const saving = create.isPending || update.isPending
  // Re-derived from the live (polling-refreshed) list every render, not
  // captured once when the modal opened, so the log text updates in place
  // while provisioning is still running.
  const logTenant = tenants.find(t => t.id === logTenantId) ?? null
  const logIsLive = logTenant?.provisioning_status === 'PROVISIONING' || logTenant?.provisioning_status === 'DEPROVISIONING'
  const logScrollRef = useRef<HTMLPreElement>(null)

  // Jump straight to the latest line when the modal opens, then keep
  // pinned to the bottom as new entries stream in from polling — but don't
  // fight the operator if they've scrolled up to read something earlier.
  useEffect(() => {
    const el = logScrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [logTenantId])
  useEffect(() => {
    const el = logScrollRef.current
    if (!el || !logTenant) return
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40
    if (nearBottom) el.scrollTop = el.scrollHeight
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [logTenant?.provisioning_log])

  return (
    <AppLayout title="Tenants">
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {statCounts.map(s => (
            <Card key={s.status}>
              <CardContent className="flex items-center gap-3 py-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${s.color}`}>
                  <s.icon size={18} />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900 leading-none">{s.count}</p>
                  <p className="text-xs text-slate-500 mt-1">{s.label}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="flex flex-wrap items-end gap-3 justify-between">
          <div className="flex flex-wrap items-end gap-3">
            <div className="relative">
              <Search size={15} className="absolute left-3 top-[38px] -translate-y-1/2 text-slate-400" />
              <Input
                label="Search"
                placeholder="Name, slug, domain, admin name/email…"
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1) }}
                className="pl-9 w-64"
              />
            </div>
            <Select label="Status" value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1) }} className="w-40">
              <option value="">All Statuses</option>
              <option value="PENDING">Pending</option>
              <option value="ACTIVE">Active</option>
              <option value="SUSPENDED">Suspended</option>
              <option value="OFFBOARDED">Offboarded</option>
            </Select>
            <Select label="Plan" value={planFilter} onChange={e => { setPlanFilter(e.target.value); setPage(1) }} className="w-36">
              <option value="">All Plans</option>
              {plans.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </Select>
          </div>
          <Button onClick={openCreate}>
            <Plus size={16} /> Add Tenant
          </Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !tenants.length ? (
            <EmptyState
              icon={Building2}
              title="No tenants yet"
              description="Add your first tenant to start tracking its lifecycle, plan, and deployment."
              action={<Button onClick={openCreate}><Plus size={16} /> Add Tenant</Button>}
            />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Name</Th>
                    <Th>Slug</Th>
                    <Th>Domain</Th>
                    <Th>Plan</Th>
                    <Th>Status</Th>
                    <Th>Provisioning</Th>
                    <Th>Admin</Th>
                    <Th>Created</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {tenants.map(t => (
                    <Tr key={t.id}>
                      <Td className="font-medium text-slate-900">{t.name}</Td>
                      <Td><span className="font-mono text-xs text-slate-500">{t.slug}</span></Td>
                      <Td className="text-slate-500">{t.domain || '—'}</Td>
                      <Td>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
                          {t.plan_detail?.name ?? '—'}
                        </span>
                      </Td>
                      <Td><Badge status={t.status} label={t.status_display} /></Td>
                      <Td>
                        <div className="flex items-center gap-1.5">
                          {(t.provisioning_status === 'PROVISIONING' || t.provisioning_status === 'DEPROVISIONING') && (
                            <Loader2 size={13} className="animate-spin text-primary-600 shrink-0" />
                          )}
                          <Badge status={t.provisioning_status} label={t.provisioning_status_display} />
                          {(t.provisioning_status === 'FAILED' || t.provisioning_status === 'DEPROVISION_FAILED') && t.provisioning_error && (
                            <span title={t.provisioning_error}>
                              <AlertTriangle size={14} className="text-danger-600 shrink-0" />
                            </span>
                          )}
                        </div>
                        {t.provisioning_status === 'ACTIVE' && (t.backend_url || t.frontend_url) && (
                          <div className="flex items-center gap-2 mt-1">
                            {t.frontend_url && (
                              <a href={t.frontend_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-0.5 text-xs text-primary-600 hover:underline">
                                App <ExternalLink size={10} />
                              </a>
                            )}
                            {t.backend_url && (
                              <a href={t.backend_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-0.5 text-xs text-slate-400 hover:underline">
                                API <ExternalLink size={10} />
                              </a>
                            )}
                          </div>
                        )}
                      </Td>
                      <Td>
                        {t.admin_first_name || t.admin_last_name || t.admin_email ? (
                          <div>
                            {(t.admin_first_name || t.admin_last_name) && (
                              <p className="text-slate-900 leading-tight">{[t.admin_first_name, t.admin_last_name].filter(Boolean).join(' ')}</p>
                            )}
                            {t.admin_email && <p className="text-xs text-slate-500 leading-tight">{t.admin_email}</p>}
                          </div>
                        ) : (
                          <span className="text-slate-500">—</span>
                        )}
                      </Td>
                      <Td className="text-slate-500">{fmt(t.created_at)}</Td>
                      <Td onClick={e => e.stopPropagation()}>
                        <div className="flex items-center gap-1 justify-end">
                          <button
                            onClick={() => setLogTenantId(t.id)}
                            disabled={!t.provisioning_log}
                            title={t.provisioning_log ? 'View provisioning log' : 'No provisioning log yet'}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-primary-600 hover:bg-primary-50 disabled:opacity-40 disabled:hover:text-slate-400 disabled:hover:bg-transparent disabled:cursor-not-allowed"
                          >
                            <ScrollText size={15} />
                          </button>
                          <button
                            onClick={() => revealPassword.mutate(t)}
                            disabled={!t.has_stored_password || revealPassword.isPending}
                            title={t.has_stored_password ? 'Reveal admin password' : 'No stored password — provisioned before this feature, or provisioning never completed'}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-primary-600 hover:bg-primary-50 disabled:opacity-40 disabled:hover:text-slate-400 disabled:hover:bg-transparent disabled:cursor-not-allowed"
                          >
                            <KeyRound size={15} />
                          </button>
                          <button onClick={() => openEdit(t)} className="p-1.5 rounded-lg text-slate-400 hover:text-primary-600 hover:bg-primary-50">
                            <Pencil size={15} />
                          </button>
                          <button
                            onClick={() => handleDelete(t)}
                            disabled={t.provisioning_status === 'PROVISIONING' || t.provisioning_status === 'DEPROVISIONING'}
                            title={t.provisioning_status === 'PROVISIONING' ? 'Wait for provisioning to finish' : t.provisioning_status === 'DEPROVISIONING' ? 'Already being deleted' : 'Delete tenant'}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-danger-600 hover:bg-danger-50 disabled:opacity-40 disabled:hover:text-slate-400 disabled:hover:bg-transparent disabled:cursor-not-allowed"
                          >
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              <Pagination count={data?.count ?? 0} page={page} pageSize={50} onPage={setPage} />
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Edit Tenant' : 'Add Tenant'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Company name"
              required
              value={form.name}
              onChange={e => {
                const name = e.target.value
                setForm(f => ({ ...f, name, slug: slugTouched ? f.slug : slugify(name) }))
              }}
              placeholder="Acme Sdn Bhd"
            />
            <Input
              label="Slug"
              required
              value={form.slug}
              onChange={e => { setSlugTouched(true); setForm(f => ({ ...f, slug: e.target.value })) }}
              placeholder="acme"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select label="Plan" required value={form.plan} onChange={e => setForm(f => ({ ...f, plan: e.target.value }))}>
              <option value="" disabled>Select a plan…</option>
              {plans.map(p => (
                <option key={p.id} value={p.id} disabled={!p.is_active && p.id !== editing?.plan}>
                  {p.name}{!p.is_active ? ' (inactive)' : ''}
                </option>
              ))}
            </Select>
            <Select label="Status" value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
              <option value="PENDING">Pending — not yet provisioned</option>
              <option value="ACTIVE">Active</option>
              <option value="SUSPENDED">Suspended</option>
              <option value="OFFBOARDED">Offboarded</option>
            </Select>
          </div>
          <Input
            label="Domain"
            value={form.domain}
            onChange={e => setForm(f => ({ ...f, domain: e.target.value }))}
            placeholder="acme-hr.com (leave blank until provisioned)"
          />
          <div className="pt-1">
            <p className="text-sm font-medium text-slate-700 mb-3">Admin user</p>
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="First name"
                  value={form.admin_first_name}
                  onChange={e => setForm(f => ({ ...f, admin_first_name: e.target.value }))}
                  placeholder="Aisyah"
                />
                <Input
                  label="Last name"
                  value={form.admin_last_name}
                  onChange={e => setForm(f => ({ ...f, admin_last_name: e.target.value }))}
                  placeholder="Rahman"
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Email"
                  type="email"
                  value={form.admin_email}
                  onChange={e => setForm(f => ({ ...f, admin_email: e.target.value }))}
                  placeholder="ops@acme.example"
                />
                <Input
                  label="Phone"
                  value={form.admin_phone}
                  onChange={e => setForm(f => ({ ...f, admin_phone: e.target.value }))}
                  placeholder="+60 12-345 6789"
                />
              </div>
            </div>
          </div>
          <div className="pt-1">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form.oauth_enabled}
                onChange={e => setForm(f => ({ ...f, oauth_enabled: e.target.checked }))}
                className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm font-medium text-slate-700">Enable OAuth / SSO login</span>
            </label>
            <p className="text-xs text-slate-500 mt-1 ml-6">
              Adds an SSO option on this tenant's login page, alongside username/password. Works with any
              OpenID Connect provider (Microsoft Entra ID, Google Workspace, Okta, Auth0, a customer's own IdP, …).
              A successful SSO login only ever signs in a user whose email already exists in this tenant's user
              list — it never auto-creates an account.
            </p>

            {form.oauth_enabled && (
              <div className="mt-4 space-y-4 pl-6 border-l-2 border-slate-100">
                <Input
                  label="Issuer URL"
                  required
                  value={form.oauth_issuer}
                  onChange={e => setForm(f => ({ ...f, oauth_issuer: e.target.value }))}
                  placeholder="https://login.microsoftonline.com/<tenant-id>/v2.0"
                />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Input
                    label="Client ID"
                    required
                    value={form.oauth_client_id}
                    onChange={e => setForm(f => ({ ...f, oauth_client_id: e.target.value }))}
                  />
                  <Input
                    label={editing?.has_oauth_client_secret ? 'Client secret (configured — leave blank to keep)' : 'Client secret'}
                    type="password"
                    required={!editing?.has_oauth_client_secret}
                    value={form.oauth_client_secret}
                    onChange={e => setForm(f => ({ ...f, oauth_client_secret: e.target.value }))}
                    placeholder={editing?.has_oauth_client_secret ? '••••••••' : ''}
                  />
                </div>
                <Input
                  label="Login button label (optional)"
                  value={form.oauth_button_label}
                  onChange={e => setForm(f => ({ ...f, oauth_button_label: e.target.value }))}
                  placeholder="Sign in with SSO"
                />
                {editing?.oauth_redirect_uri && (
                  <div>
                    <label className="text-sm font-medium text-slate-700">Redirect URI to register with the IdP</label>
                    <div className="flex items-center gap-2 mt-1">
                      <code className="flex-1 px-3 py-2 rounded-lg bg-slate-100 text-slate-900 text-xs font-mono break-all">
                        {editing.oauth_redirect_uri}
                      </code>
                      <button
                        type="button"
                        onClick={() => {
                          navigator.clipboard.writeText(editing.oauth_redirect_uri!)
                          toast.success('Copied to clipboard')
                        }}
                        className="p-2 rounded-lg text-slate-500 hover:text-primary-600 hover:bg-primary-50 shrink-0"
                        title="Copy redirect URI"
                      >
                        <Copy size={16} />
                      </button>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      Register this exact URL as an allowed redirect/callback URI in the IdP's app registration.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
          <Textarea
            label="Notes"
            value={form.notes}
            onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
            placeholder="Provisioning steps done, contract details, etc."
          />
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={saving}>{editing ? 'Save Changes' : 'Create Tenant'}</Button>
          </div>
        </form>
      </Modal>

      <Modal
        open={!!activePasswordModal}
        onClose={() => {
          if (revealedPassword) setDismissedPassword(revealedPassword.password)
          setManualReveal(null)
        }}
        title="Admin password"
        size="sm"
      >
        {activePasswordModal && (
          <div className="space-y-4">
            <p className="text-sm text-slate-600">
              Login password for <span className="font-medium text-slate-900">{activePasswordModal.tenantName}</span>'s admin account.
              {revealedPassword && (
                <> <span className="font-medium text-danger-600">Save it now —</span> this one-time notice won't repeat, but you can always reveal it again from the table.</>
              )}
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 px-3 py-2 rounded-lg bg-slate-100 text-slate-900 text-sm font-mono break-all">
                {activePasswordModal.password}
              </code>
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(activePasswordModal.password)
                  toast.success('Copied to clipboard')
                }}
                className="p-2 rounded-lg text-slate-500 hover:text-primary-600 hover:bg-primary-50 shrink-0"
                title="Copy password"
              >
                <Copy size={16} />
              </button>
            </div>
            <div className="flex justify-end pt-2">
              <Button onClick={() => {
                if (revealedPassword) setDismissedPassword(revealedPassword.password)
                setManualReveal(null)
              }}>Done</Button>
            </div>
          </div>
        )}
      </Modal>

      <Modal
        open={!!logTenant}
        onClose={() => setLogTenantId(null)}
        title={logTenant ? `Provisioning log — ${logTenant.name}` : 'Provisioning log'}
        size="lg"
      >
        {logTenant && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Badge status={logTenant.provisioning_status} label={logTenant.provisioning_status_display} />
              {logIsLive && (
                <span className="inline-flex items-center gap-1 text-xs text-primary-600">
                  <Loader2 size={12} className="animate-spin" /> Updating live
                </span>
              )}
            </div>
            <pre
              ref={logScrollRef}
              className="max-h-96 overflow-y-auto rounded-lg bg-slate-900 text-slate-100 text-xs font-mono p-3 whitespace-pre-wrap break-words"
            >
              {logTenant.provisioning_log || 'No log entries yet.'}
            </pre>
            {(logTenant.provisioning_status === 'FAILED' || logTenant.provisioning_status === 'DEPROVISION_FAILED') && logTenant.provisioning_error && (
              <div className="flex items-start gap-2 rounded-lg bg-danger-50 text-danger-700 text-xs p-3">
                <AlertTriangle size={14} className="shrink-0 mt-0.5" />
                <span>{logTenant.provisioning_error}</span>
              </div>
            )}
            <div className="flex justify-end pt-1">
              <Button variant="secondary" onClick={() => setLogTenantId(null)}>Close</Button>
            </div>
          </div>
        )}
      </Modal>
    </AppLayout>
  )
}
