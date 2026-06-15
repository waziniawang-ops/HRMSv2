import { Fragment, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Select, Input } from '@/components/ui/Input'
import { DatePicker } from '@/components/ui/DatePicker'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Shield, ChevronDown, ChevronUp } from 'lucide-react'
import api from '@/lib/api'

type AuditLog = {
  id: string
  actor_display: string
  action: string
  object_type: string
  object_id: string
  module: string
  ip_address: string | null
  correlation_id: string
  before_json: Record<string, unknown> | null
  after_json: Record<string, unknown> | null
  created_at: string
}

const ACTION_COLOR: Record<string, string> = {
  CREATE: 'text-green-700 bg-green-50',
  UPDATE: 'text-blue-700 bg-blue-50',
  DELETE: 'text-red-700 bg-red-50',
  APPROVE: 'text-emerald-700 bg-emerald-50',
  REJECT: 'text-orange-700 bg-orange-50',
  RETURN: 'text-yellow-700 bg-yellow-50',
  LOGIN_SUCCESS: 'text-gray-700 bg-gray-100',
  LOGIN_FAILURE: 'text-red-700 bg-red-50',
  LOGOUT: 'text-gray-700 bg-gray-100',
  SUBMIT: 'text-purple-700 bg-purple-50',
}

function ActionBadge({ action }: { action: string }) {
  const cls = ACTION_COLOR[action] ?? 'text-gray-700 bg-gray-100'
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${cls}`}>
      {action}
    </span>
  )
}

function JsonBlock({ data }: { data: Record<string, unknown> | null }) {
  if (!data) return <span className="text-gray-400 text-xs">—</span>
  return (
    <pre className="text-xs bg-gray-900 text-green-300 rounded p-3 overflow-auto max-h-48 whitespace-pre-wrap">
      {JSON.stringify(data, null, 2)}
    </pre>
  )
}

function fmtDt(dt: string) {
  return new Date(dt).toLocaleString('en-MY', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

const ACTIONS = [
  'CREATE','UPDATE','DELETE','APPROVE','REJECT','RETURN','SUBMIT',
  'LOGIN_SUCCESS','LOGIN_FAILURE','LOGOUT','PUBLISH','EXPORT',
  'ROLE_CHANGED','PASSWORD_CHANGED','BREAK_GLASS_USED',
]

const MODULES = [
  'recruitment','onboarding','workforce','succession',
  'performance','learning','core_hr','attendance','workflow',
]

export default function Audit() {
  const [page, setPage] = useState(1)
  const [actionFilter, setActionFilter] = useState('')
  const [moduleFilter, setModuleFilter] = useState('')
  const [objectTypeFilter, setObjectTypeFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [search, setSearch] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', page, actionFilter, moduleFilter, objectTypeFilter, dateFrom, dateTo, search],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (actionFilter) params.set('action', actionFilter)
      if (moduleFilter) params.set('module', moduleFilter)
      if (objectTypeFilter) params.set('object_type', objectTypeFilter)
      if (dateFrom) params.set('date_from', dateFrom)
      if (dateTo) params.set('date_to', dateTo)
      if (search) params.set('search', search)
      return api.get(`/audit/?${params}`).then(r => r.data)
    },
  })

  function resetFilters() {
    setPage(1); setActionFilter(''); setModuleFilter(''); setObjectTypeFilter('')
    setDateFrom(''); setDateTo(''); setSearch('')
  }

  return (
    <AppLayout title="Audit Trail">
      <div className="space-y-4">
        {/* Filters */}
        <div className="flex flex-wrap items-end gap-3">
          <Select value={actionFilter} onChange={e => { setActionFilter(e.target.value); setPage(1) }} className="w-44">
            <option value="">All Actions</option>
            {ACTIONS.map(a => <option key={a} value={a}>{a.replace(/_/g, ' ')}</option>)}
          </Select>
          <Select value={moduleFilter} onChange={e => { setModuleFilter(e.target.value); setPage(1) }} className="w-44">
            <option value="">All Modules</option>
            {MODULES.map(m => (
              <option key={m} value={m}>{m.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>
            ))}
          </Select>
          <Input
            placeholder="Object type…"
            value={objectTypeFilter}
            onChange={e => { setObjectTypeFilter(e.target.value); setPage(1) }}
            className="w-44"
          />
          <DatePicker
            label="From"
            value={dateFrom}
            onChange={v => { setDateFrom(v); setPage(1) }}
            className="w-40"
          />
          <DatePicker
            label="To"
            value={dateTo}
            onChange={v => { setDateTo(v); setPage(1) }}
            className="w-40"
          />
          <Input
            placeholder="Search actor / object…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
            className="w-56"
          />
          {(actionFilter || moduleFilter || objectTypeFilter || dateFrom || dateTo || search) && (
            <button onClick={resetFilters} className="text-xs text-blue-600 hover:underline">
              Clear filters
            </button>
          )}
        </div>

        {data && (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Shield size={14} className="text-blue-500" />
            {data.count.toLocaleString()} immutable record{data.count !== 1 ? 's' : ''}
          </div>
        )}

        <Card>
          {isLoading ? (
            <PageSpinner />
          ) : !data?.results?.length ? (
            <EmptyState
              icon={Shield}
              title="No audit logs found"
              description="Audit records appear here as actions are performed across the system."
            />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th></Th>
                    <Th>Timestamp</Th>
                    <Th>Actor</Th>
                    <Th>Action</Th>
                    <Th>Module</Th>
                    <Th>Object Type</Th>
                    <Th>Object ID</Th>
                    <Th>IP Address</Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map((log: AuditLog) => (
                    <Fragment key={log.id}>
                      <Tr
                        className={`cursor-pointer ${expandedId === log.id ? 'bg-blue-50' : ''}`}
                        onClick={() => setExpandedId(prev => prev === log.id ? null : log.id)}
                      >
                        <Td>
                          {expandedId === log.id
                            ? <ChevronUp size={13} className="text-gray-400" />
                            : <ChevronDown size={13} className="text-gray-400" />}
                        </Td>
                        <Td className="font-mono text-xs text-gray-600 whitespace-nowrap">
                          {fmtDt(log.created_at)}
                        </Td>
                        <Td className="font-medium text-gray-900">{log.actor_display}</Td>
                        <Td><ActionBadge action={log.action} /></Td>
                        <Td className="text-sm text-gray-500">{log.module || '—'}</Td>
                        <Td className="text-sm text-gray-700">{log.object_type}</Td>
                        <Td>
                          <span className="font-mono text-xs text-gray-500">
                            {log.object_id ? log.object_id.slice(0, 8) + '…' : '—'}
                          </span>
                        </Td>
                        <Td className="font-mono text-xs text-gray-500">
                          {log.ip_address ?? '—'}
                        </Td>
                      </Tr>

                      {expandedId === log.id && (
                        <tr>
                          <td colSpan={8} className="bg-gray-50 px-6 py-4 border-b border-gray-200">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                              <div>
                                <p className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
                                  Before
                                </p>
                                <JsonBlock data={log.before_json} />
                              </div>
                              <div>
                                <p className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
                                  After
                                </p>
                                <JsonBlock data={log.after_json} />
                              </div>
                            </div>
                            {log.correlation_id && (
                              <p className="text-xs text-gray-400 mt-3">
                                Correlation ID: <span className="font-mono">{log.correlation_id}</span>
                              </p>
                            )}
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  ))}
                </Tbody>
              </Table>
              <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />
            </>
          )}
        </Card>
      </div>
    </AppLayout>
  )
}
