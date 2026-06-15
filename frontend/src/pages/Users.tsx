import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { Input, Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Plus, Search, Users, Pencil, Trash2 } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

const ALL_ROLES = [
  { code: 'SYSTEM_ADMIN',    label: 'System Admin' },
  { code: 'HR_ADMIN',        label: 'HR Admin' },
  { code: 'HR_MAKER',        label: 'HR Maker' },
  { code: 'HR_CHECKER',      label: 'HR Checker' },
  { code: 'HIRING_MANAGER',  label: 'Hiring Manager' },
  { code: 'INTERVIEWER',     label: 'Interviewer' },
  { code: 'RECRUITER',       label: 'Recruiter' },
  { code: 'FINANCE_CHECKER', label: 'Finance Checker' },
  { code: 'TALENT_COMMITTEE',label: 'Talent Committee' },
  { code: 'HR_PERFORMANCE',  label: 'HR Performance' },
  { code: 'LD_OFFICER',      label: 'L&D Officer' },
  { code: 'LD_CHECKER',      label: 'L&D Checker' },
  { code: 'MANAGER',         label: 'Manager' },
  { code: 'EMPLOYEE',        label: 'Employee' },
  { code: 'APPLICANT',       label: 'Applicant' },
]

type User = {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  /** Primary / display role */
  role: string
  /** All effective roles (M2M + primary) */
  roles: string[]
  user_type: string
  is_active: boolean
  date_joined: string
}

const defaultForm = {
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  primary_role: 'EMPLOYEE',
  role_codes: ['EMPLOYEE'] as string[],
  user_type: 'INTERNAL',
  password: '',
  is_active: 'true',
}

export default function UsersPage() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<User | null>(null)
  const [form, setForm] = useState(defaultForm)

  const { data, isLoading } = useQuery({
    queryKey: ['users', page, search],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page) })
      if (search) params.set('search', search)
      return api.get(`/auth/users/?${params}`).then(r => r.data)
    },
  })

  function openCreate() {
    setEditing(null)
    setForm(defaultForm)
    setModalOpen(true)
  }

  function openEdit(u: User) {
    setEditing(u)
    setForm({
      username: u.username,
      email: u.email,
      first_name: u.first_name,
      last_name: u.last_name,
      primary_role: u.role,
      role_codes: u.roles?.length ? u.roles : [u.role],
      user_type: u.user_type,
      password: '',
      is_active: u.is_active ? 'true' : 'false',
    })
    setModalOpen(true)
  }

  function closeModal() {
    setModalOpen(false)
    setEditing(null)
    setForm(defaultForm)
  }

  function toggleRole(code: string) {
    setForm(f => {
      const has = f.role_codes.includes(code)
      let next = has
        ? f.role_codes.filter(r => r !== code)
        : [...f.role_codes, code]
      // always keep at least one role
      if (next.length === 0) next = [code]
      // keep primary_role in sync: if primary was removed, pick first remaining
      const primary = next.includes(f.primary_role) ? f.primary_role : next[0]
      return { ...f, role_codes: next, primary_role: primary }
    })
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/auth/users/', body),
    onSuccess: () => { toast.success('User created'); qc.invalidateQueries({ queryKey: ['users'] }); closeModal() },
    onError: () => toast.error('Failed to create user'),
  })

  const update = useMutation({
    mutationFn: ({ id, ...body }: { id: string } & object) => api.patch(`/auth/users/${id}/`, body),
    onSuccess: () => { toast.success('User updated'); qc.invalidateQueries({ queryKey: ['users'] }); closeModal() },
    onError: () => toast.error('Failed to update user'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/auth/users/${id}/`),
    onSuccess: () => { toast.success('User deleted'); qc.invalidateQueries({ queryKey: ['users'] }) },
    onError: () => toast.error('Cannot delete user'),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = {
      first_name: form.first_name,
      last_name: form.last_name,
      role: form.primary_role,
      role_codes: form.role_codes,
      user_type: form.user_type,
      is_active: form.is_active,
      ...(form.password ? { password: form.password } : {}),
    }
    if (editing) {
      update.mutate({ id: editing.id, ...payload })
    } else {
      create.mutate({ username: form.username, email: form.email, ...payload })
    }
  }

  function handleDelete(u: User) {
    if (!window.confirm(`Delete user "${u.username}"? This cannot be undone.`)) return
    remove.mutate(u.id)
  }

  const isPending = create.isPending || update.isPending

  return (
    <AppLayout title="User Management">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Search users…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
            />
          </div>
          <Button onClick={openCreate}><Plus size={16} /> Add User</Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !data?.results?.length ? (
            <EmptyState icon={Users} title="No users found" action={<Button onClick={openCreate}><Plus size={16} />Add User</Button>} />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Username</Th>
                    <Th>Full Name</Th>
                    <Th>Email</Th>
                    <Th>Primary Role</Th>
                    <Th>All Roles</Th>
                    <Th>Type</Th>
                    <Th>Active</Th>
                    <Th>Joined</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map((u: User) => (
                    <Tr key={u.id}>
                      <Td><span className="font-mono text-xs font-semibold text-gray-700">{u.username}</span></Td>
                      <Td className="font-medium text-gray-900">{u.first_name} {u.last_name}</Td>
                      <Td className="text-gray-600 text-sm">{u.email}</Td>
                      <Td><Badge status={u.role} label={u.role.replace(/_/g, ' ')} /></Td>
                      <Td>
                        <div className="flex flex-wrap gap-1">
                          {(u.roles?.length ? u.roles : [u.role]).map(r => (
                            r !== u.role && (
                              <span key={r} className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200">
                                {r.replace(/_/g, ' ')}
                              </span>
                            )
                          ))}
                        </div>
                      </Td>
                      <Td className="text-sm text-gray-500">{u.user_type}</Td>
                      <Td><Badge status={u.is_active ? 'ACTIVE' : 'REJECTED'} label={u.is_active ? 'Active' : 'Inactive'} /></Td>
                      <Td className="text-sm text-gray-500">{fmt(u.date_joined)}</Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(u)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit"><Pencil size={15} /></button>
                          <button onClick={() => handleDelete(u)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete"><Trash2 size={15} /></button>
                        </div>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={closeModal} title={editing ? `Edit User — ${editing.username}` : 'Add User'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="First Name *" value={form.first_name} onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))} required />
            <Input label="Last Name" value={form.last_name} onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Username *" value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} required disabled={!!editing} />
            <Input label="Email *" type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} required disabled={!!editing} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Select label="Primary Role *" value={form.primary_role} onChange={e => setForm(f => {
              const next = e.target.value
              // ensure primary is always in role_codes
              const codes = f.role_codes.includes(next) ? f.role_codes : [...f.role_codes, next]
              return { ...f, primary_role: next, role_codes: codes }
            })}>
              {ALL_ROLES.map(r => <option key={r.code} value={r.code}>{r.label}</option>)}
            </Select>
            <Select label="User Type" value={form.user_type} onChange={e => setForm(f => ({ ...f, user_type: e.target.value }))}>
              <option value="INTERNAL">Internal</option>
              <option value="EXTERNAL">External</option>
            </Select>
          </div>

          {/* Dynamic multi-role assignment */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Additional Roles <span className="text-gray-400 font-normal">(select all that apply)</span>
            </label>
            <div className="grid grid-cols-3 gap-2 p-3 border border-gray-200 rounded-lg bg-gray-50 max-h-52 overflow-y-auto">
              {ALL_ROLES.map(r => {
                const checked = form.role_codes.includes(r.code)
                const isPrimary = r.code === form.primary_role
                return (
                  <label
                    key={r.code}
                    className={`flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer transition-colors text-xs ${
                      checked ? 'bg-blue-100 text-blue-800' : 'hover:bg-gray-100 text-gray-700'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      disabled={isPrimary}
                      onChange={() => toggleRole(r.code)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="leading-tight">{r.label}</span>
                    {isPrimary && <span className="text-[9px] text-blue-600 font-semibold uppercase ml-auto">primary</span>}
                  </label>
                )
              })}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {form.role_codes.length} role{form.role_codes.length !== 1 ? 's' : ''} selected
            </p>
          </div>

          {editing && (
            <Select label="Active" value={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.value }))}>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </Select>
          )}
          <Input
            label={editing ? 'New Password (leave blank to keep current)' : 'Password *'}
            type="password"
            value={form.password}
            onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
            required={!editing}
          />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={closeModal}>Cancel</Button>
            <Button type="submit" loading={isPending}>{editing ? 'Save Changes' : 'Create User'}</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
