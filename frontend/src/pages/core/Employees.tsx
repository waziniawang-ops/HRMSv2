import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Users, Plus, Pencil, Trash2, KeyRound, Copy } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input, Select } from '@/components/ui/Input'
import { DatePicker } from '@/components/ui/DatePicker'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import { grantableStaffRoles } from '@/lib/roles'
import { useAuth } from '@/context/AuthContext'

interface Employee {
  id: string
  employee_number: string
  full_name: string
  employment_status: string
  position: string | null
  position_display?: string
  org_unit: string | null
  org_unit_display?: string
  grade: string | null
  grade_display?: string
  manager: string | null
  manager_display?: string
  hire_date: string | null
  person: string
  person_detail?: {
    id: string
    legal_name: string
    email: string
    phone: string
    gender: string
    nationality: string
    date_of_birth: string | null
  }
  /** The linked login account, or null if this employee can't sign in yet. */
  login: { id: string; username: string; role: string; is_active: boolean } | null
}

/** Who the "Login Access" form is creating a login for. */
interface LoginTarget { id: string; name: string; email: string }
interface CreatedLogin { username: string; password?: string }

interface OrgUnit { id: string; name: string }
interface Grade { id: string; grade_code: string; grade_name: string }
interface Position { id: string; position_code: string; title: string }
interface ApiList<T> { count: number; results: T[] }

const PAGE_SIZE = 15
const STATUSES = ['PROBATION', 'ACTIVE', 'SUSPENDED', 'TERMINATED', 'RESIGNED', 'RETIRED']
const GENDERS = ['MALE', 'FEMALE', 'OTHER', 'PREFER_NOT_TO_SAY']

const emptyPersonForm = {
  legal_name: '',
  email: '',
  phone: '',
  gender: '',
  nationality: '',
  date_of_birth: '',
}

const emptyLoginForm = {
  username: '',
  role: 'EMPLOYEE',
  role_codes: [] as string[],
  passwordMode: 'generate' as 'generate' | 'set',
  password: '',
}

function suggestedUsername(email: string) {
  return email.split('@')[0].toLowerCase().replace(/[^a-z0-9._-]/g, '')
}

/** The most useful message from a DRF error response. */
function apiErrorMessage(err: unknown, fallback: string) {
  const data = (err as { response?: { data?: Record<string, unknown> } })?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const first = Object.values(data)[0]
  return Array.isArray(first) && typeof first[0] === 'string' ? first[0] : fallback
}

const emptyEmpForm = {
  employee_number: '',
  hire_date: '',
  employment_status: 'PROBATION',
  position: '',
  org_unit: '',
  grade: '',
  manager: '',
}

export default function Employees() {
  const qc = useQueryClient()
  const { user } = useAuth()
  const roleOptions = grantableStaffRoles(user?.roles ?? [])
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Employee | null>(null)
  const [step, setStep] = useState<1 | 2 | 3>(1)
  const [personForm, setPersonForm] = useState(emptyPersonForm)
  const [empForm, setEmpForm] = useState(emptyEmpForm)
  const [createdPersonId, setCreatedPersonId] = useState<string | null>(null)
  const [loginTarget, setLoginTarget] = useState<LoginTarget | null>(null)
  const [loginForm, setLoginForm] = useState(emptyLoginForm)
  const [createdLogin, setCreatedLogin] = useState<CreatedLogin | null>(null)
  // true when the modal was opened from the list just to add a login
  const [loginOnly, setLoginOnly] = useState(false)

  const params = {
    page,
    page_size: PAGE_SIZE,
    ...(search ? { search } : {}),
    ...(statusFilter ? { employment_status: statusFilter } : {}),
  }

  const { data, isLoading } = useQuery<ApiList<Employee>>({
    queryKey: ['employees', params],
    queryFn: () => api.get('/core/employees/', { params }).then(r => r.data),
  })

  const { data: orgUnits } = useQuery<ApiList<OrgUnit>>({
    queryKey: ['org-units-all'],
    queryFn: () => api.get('/core/org-units/', { params: { page_size: 500 } }).then(r => r.data),
  })
  const { data: grades } = useQuery<ApiList<Grade>>({
    queryKey: ['grades-all'],
    queryFn: () => api.get('/core/grades/', { params: { page_size: 500 } }).then(r => r.data),
  })
  const { data: positions } = useQuery<ApiList<Position>>({
    queryKey: ['positions-all'],
    queryFn: () => api.get('/core/positions/', { params: { page_size: 500 } }).then(r => r.data),
  })
  const { data: allEmployees } = useQuery<ApiList<Employee>>({
    queryKey: ['employees-all'],
    queryFn: () => api.get('/core/employees/', { params: { page_size: 500 } }).then(r => r.data),
  })

  const createPerson = useMutation({
    mutationFn: (body: typeof emptyPersonForm) => api.post('/core/persons/', body).then(r => r.data),
  })

  const createEmployee = useMutation({
    mutationFn: (body: object) => api.post('/core/employees/', body).then(r => r.data as Employee),
    onSuccess: (emp) => {
      toast.success('Employee created')
      qc.invalidateQueries({ queryKey: ['employees'] })
      openLoginStep({ id: emp.id, name: personForm.legal_name, email: personForm.email })
      setStep(3)
    },
    onError: () => toast.error('Failed to create employee'),
  })

  const createLogin = useMutation({
    mutationFn: ({ employeeId, body }: { employeeId: string; body: object }) =>
      api.post(`/core/employees/${employeeId}/create_login/`, body).then(r => r.data),
    onSuccess: (data) => {
      toast.success('Login created')
      qc.invalidateQueries({ queryKey: ['employees'] })
      setCreatedLogin({ username: data.user.username, password: data.generated_password })
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Failed to create login')),
  })

  const updatePerson = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyPersonForm & { id: string }) =>
      api.patch(`/core/persons/${id}/`, body),
  })

  const updateEmployee = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyEmpForm & { id: string }) =>
      api.patch(`/core/employees/${id}/`, body),
    onSuccess: () => {
      toast.success('Employee updated')
      qc.invalidateQueries({ queryKey: ['employees'] })
      closeModal()
    },
    onError: () => toast.error('Failed to update employee'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/core/employees/${id}/`),
    onSuccess: () => { toast.success('Employee deleted'); qc.invalidateQueries({ queryKey: ['employees'] }) },
    onError: () => toast.error('Cannot delete — employee may have linked records'),
  })

  function openCreate() {
    setEditing(null)
    setPersonForm(emptyPersonForm)
    setEmpForm(emptyEmpForm)
    setCreatedPersonId(null)
    setStep(1)
    setModalOpen(true)
  }

  function openEdit(emp: Employee) {
    setEditing(emp)
    setPersonForm({
      legal_name: emp.person_detail?.legal_name ?? emp.full_name,
      email: emp.person_detail?.email ?? '',
      phone: emp.person_detail?.phone ?? '',
      gender: emp.person_detail?.gender ?? '',
      nationality: emp.person_detail?.nationality ?? '',
      date_of_birth: emp.person_detail?.date_of_birth ?? '',
    })
    setEmpForm({
      employee_number: emp.employee_number,
      hire_date: emp.hire_date ?? '',
      employment_status: emp.employment_status,
      position: emp.position ?? '',
      org_unit: emp.org_unit ?? '',
      grade: emp.grade ?? '',
      manager: emp.manager ?? '',
    })
    setStep(1)
    setModalOpen(true)
  }

  function openLoginStep(target: LoginTarget) {
    setLoginTarget(target)
    setLoginForm({ ...emptyLoginForm, username: suggestedUsername(target.email) })
    setCreatedLogin(null)
  }

  function openCreateLogin(emp: Employee) {
    setEditing(null)
    setLoginOnly(true)
    openLoginStep({ id: emp.id, name: emp.full_name, email: emp.person_detail?.email ?? '' })
    setStep(3)
    setModalOpen(true)
  }

  function closeModal() {
    setModalOpen(false)
    setEditing(null)
    setPersonForm(emptyPersonForm)
    setEmpForm(emptyEmpForm)
    setCreatedPersonId(null)
    setLoginTarget(null)
    setLoginForm(emptyLoginForm)
    setCreatedLogin(null)
    setLoginOnly(false)
    setStep(1)
  }

  function handleStep3(e: React.FormEvent) {
    e.preventDefault()
    if (!loginTarget) return
    createLogin.mutate({
      employeeId: loginTarget.id,
      body: {
        username: loginForm.username,
        role: loginForm.role,
        role_codes: loginForm.role_codes.filter(c => c !== loginForm.role),
        ...(loginForm.passwordMode === 'set' ? { password: loginForm.password } : {}),
      },
    })
  }

  function toggleExtraRole(code: string) {
    setLoginForm(prev => ({
      ...prev,
      role_codes: prev.role_codes.includes(code) ? prev.role_codes.filter(c => c !== code) : [...prev.role_codes, code],
    }))
  }

  function copyCredentials() {
    if (!createdLogin) return
    const text = `Username: ${createdLogin.username}${createdLogin.password ? `\nPassword: ${createdLogin.password}` : ''}`
    navigator.clipboard.writeText(text).then(() => toast.success('Copied')).catch(() => toast.error('Copy failed — select the text instead'))
  }

  async function handleStep1(e: React.FormEvent) {
    e.preventDefault()
    if (editing) {
      setStep(2)
      return
    }
    try {
      // A blank date must go as null — the API rejects an empty string.
      const person = await createPerson.mutateAsync({ ...personForm, date_of_birth: personForm.date_of_birth || null } as unknown as typeof emptyPersonForm)
      setCreatedPersonId(person.id)
      setStep(2)
    } catch {
      toast.error('Failed to save personal info — email may already be registered')
    }
  }

  async function handleStep2(e: React.FormEvent) {
    e.preventDefault()
    const payload = {
      ...empForm,
      position: empForm.position || null,
      org_unit: empForm.org_unit || null,
      grade: empForm.grade || null,
      manager: empForm.manager || null,
    }
    if (editing) {
      const personPayload = { ...personForm, date_of_birth: personForm.date_of_birth || null }
      await updatePerson.mutateAsync({ id: editing.person, ...personPayload } as unknown as Parameters<typeof updatePerson.mutateAsync>[0])
      updateEmployee.mutate({ id: editing.id, ...payload } as unknown as typeof emptyEmpForm & { id: string })
    } else {
      createEmployee.mutate({ ...payload, person: createdPersonId })
    }
  }

  function handleDelete(emp: Employee) {
    if (!window.confirm(`Delete employee "${emp.full_name}"? This cannot be undone.`)) return
    remove.mutate(emp.id)
  }

  const setPerson = (k: keyof typeof emptyPersonForm) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setPersonForm(prev => ({ ...prev, [k]: e.target.value }))

  const setEmp = (k: keyof typeof emptyEmpForm) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setEmpForm(prev => ({ ...prev, [k]: e.target.value }))

  const isStep1Pending = createPerson.isPending
  const isStep2Pending = createEmployee.isPending || updateEmployee.isPending

  return (
    <AppLayout title="Employees">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Employees</CardTitle>
              <Button onClick={openCreate}><Plus size={16} />Add Employee</Button>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <div className="flex gap-3">
              <Input
                placeholder="Search by name or employee number…"
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1) }}
                className="max-w-sm"
              />
              <Select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1) }} className="w-48">
                <option value="">All Statuses</option>
                {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </Select>
            </div>
          </CardContent>

          {isLoading ? (
            <PageSpinner />
          ) : !data?.results.length ? (
            <EmptyState
              icon={Users}
              title="No employees found"
              description="No employees match your search criteria."
              action={<Button onClick={openCreate}><Plus size={16} />Add Employee</Button>}
            />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Employee #</Th>
                    <Th>Name</Th>
                    <Th>Status</Th>
                    <Th>Position</Th>
                    <Th>Department</Th>
                    <Th>Grade</Th>
                    <Th>Hire Date</Th>
                    <Th>Login</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {data.results.map(emp => (
                    <Tr key={emp.id}>
                      <Td className="font-mono text-xs">{emp.employee_number}</Td>
                      <Td className="font-medium">{emp.full_name}</Td>
                      <Td><Badge status={emp.employment_status} /></Td>
                      <Td className="text-gray-500">{emp.position_display ?? '—'}</Td>
                      <Td className="text-gray-500">{emp.org_unit_display ?? '—'}</Td>
                      <Td className="text-gray-500">{emp.grade_display ?? '—'}</Td>
                      <Td className="text-gray-500">{fmt(emp.hire_date)}</Td>
                      <Td>
                        {emp.login ? (
                          <span className={`font-mono text-xs ${emp.login.is_active ? 'text-gray-700' : 'text-gray-400 line-through'}`} title={emp.login.is_active ? 'Can sign in' : 'Login deactivated'}>
                            {emp.login.username}
                          </span>
                        ) : (
                          <button onClick={() => openCreateLogin(emp)} className="inline-flex items-center gap-1 text-xs font-medium text-orange-600 hover:text-orange-700 hover:underline">
                            <KeyRound size={13} /> Create login
                          </button>
                        )}
                      </Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(emp)} className="p-1.5 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors" title="Edit">
                            <Pencil size={15} />
                          </button>
                          <button onClick={() => handleDelete(emp)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete">
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              <Pagination count={data.count} page={page} pageSize={PAGE_SIZE} onPage={setPage} />
            </>
          )}
        </Card>
      </div>

      <Modal
        open={modalOpen}
        onClose={closeModal}
        title={editing ? `Edit — ${editing.full_name}` : loginOnly ? `Create login — ${loginTarget?.name ?? ''}` : 'Add Employee'}
      >
        {/* Step indicator — the login step only exists when adding an employee */}
        {!loginOnly && (
          <div className="flex items-center gap-3 mb-6">
            {(editing ? [1, 2] : [1, 2, 3]).map((n, i, all) => (
              <div key={n} className="flex items-center gap-2">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${step === n ? 'bg-orange-600 text-white' : step > n ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-400'}`}>
                  {n}
                </div>
                <span className={`text-xs font-medium ${step === n ? 'text-orange-700' : 'text-gray-400'}`}>
                  {n === 1 ? 'Personal Info' : n === 2 ? 'Employment Details' : 'Login Access'}
                </span>
                {i < all.length - 1 && <div className="w-8 h-px bg-gray-200 ml-1" />}
              </div>
            ))}
          </div>
        )}

        {step === 3 ? (
          createdLogin ? (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                <span className="font-medium text-gray-900">{loginTarget?.name}</span> can now sign in.
                {createdLogin.password
                  ? ' Give them these details securely. The password is shown only once — they can ask an administrator to reset it later.'
                  : ' They sign in with the password you set.'}
              </p>
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 font-mono text-sm space-y-1 select-all">
                <div>Username: {createdLogin.username}</div>
                {createdLogin.password && <div>Password: {createdLogin.password}</div>}
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="secondary" onClick={copyCredentials}><Copy size={15} />Copy</Button>
                <Button type="button" onClick={closeModal}>Done</Button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleStep3} className="space-y-4">
              <p className="text-sm text-gray-600">
                Give <span className="font-medium text-gray-900">{loginTarget?.name}</span> a login so they can use the system — no need to add them again on the Users page.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <Input label="Username" required value={loginForm.username} onChange={e => setLoginForm(prev => ({ ...prev, username: e.target.value }))} />
                <Select label="Primary Role" value={loginForm.role} onChange={e => setLoginForm(prev => ({ ...prev, role: e.target.value }))}>
                  {roleOptions.map(r => <option key={r.code} value={r.code}>{r.label}</option>)}
                </Select>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Additional Roles <span className="font-normal text-gray-400">(optional)</span></p>
                <div className="grid grid-cols-3 gap-x-3 gap-y-1.5 rounded-lg border border-gray-200 bg-gray-50 p-3 max-h-40 overflow-y-auto">
                  {roleOptions.filter(r => r.code !== loginForm.role).map(r => (
                    <label key={r.code} className="flex items-center gap-2 text-xs text-gray-700">
                      <input type="checkbox" checked={loginForm.role_codes.includes(r.code)} onChange={() => toggleExtraRole(r.code)} className="accent-orange-600" />
                      {r.label}
                    </label>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-700">Password</p>
                <label className="flex items-center gap-2 text-sm text-gray-700">
                  <input type="radio" name="passwordMode" checked={loginForm.passwordMode === 'generate'} onChange={() => setLoginForm(prev => ({ ...prev, passwordMode: 'generate' }))} className="accent-orange-600" />
                  Generate one for me
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-700">
                  <input type="radio" name="passwordMode" checked={loginForm.passwordMode === 'set'} onChange={() => setLoginForm(prev => ({ ...prev, passwordMode: 'set' }))} className="accent-orange-600" />
                  Set it myself
                </label>
                {loginForm.passwordMode === 'set' && (
                  <Input type="password" required minLength={8} value={loginForm.password} onChange={e => setLoginForm(prev => ({ ...prev, password: e.target.value }))} placeholder="At least 8 characters" />
                )}
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="secondary" onClick={closeModal}>{loginOnly ? 'Cancel' : 'Skip for now'}</Button>
                <Button type="submit" loading={createLogin.isPending}>Create Login</Button>
              </div>
            </form>
          )
        ) : step === 1 ? (
          <form onSubmit={handleStep1} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input label="Full Legal Name" required value={personForm.legal_name} onChange={setPerson('legal_name')} placeholder="e.g. Ahmad bin Razif" />
              <Input label="Work Email" type="email" required value={personForm.email} onChange={setPerson('email')} placeholder="ahmad@company.com" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Input label="Phone" value={personForm.phone} onChange={setPerson('phone')} placeholder="+60 12-345 6789" />
              <DatePicker label="Date of Birth" value={personForm.date_of_birth} onChange={v => setPersonForm(prev => ({ ...prev, date_of_birth: v }))} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Select label="Gender" value={personForm.gender} onChange={setPerson('gender')}>
                <option value="">— Select —</option>
                {GENDERS.map(g => <option key={g} value={g}>{g.replace('_', ' ')}</option>)}
              </Select>
              <Input label="Nationality" value={personForm.nationality} onChange={setPerson('nationality')} placeholder="e.g. Malaysian" />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
              <Button type="submit" loading={isStep1Pending}>
                {editing ? 'Next →' : 'Save & Continue →'}
              </Button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleStep2} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input label="Employee Number" required value={empForm.employee_number} onChange={setEmp('employee_number')} placeholder="e.g. EMP-001" />
              <DatePicker label="Hire Date" required value={empForm.hire_date} onChange={v => setEmpForm(prev => ({ ...prev, hire_date: v }))} />
            </div>
            <Select label="Employment Status" value={empForm.employment_status} onChange={setEmp('employment_status')}>
              {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </Select>
            <div className="grid grid-cols-2 gap-4">
              <Select label="Position" value={empForm.position} onChange={setEmp('position')}>
                <option value="">— None —</option>
                {positions?.results.map(p => <option key={p.id} value={p.id}>{p.title} ({p.position_code})</option>)}
              </Select>
              <Select label="Org Unit" value={empForm.org_unit} onChange={setEmp('org_unit')}>
                <option value="">— None —</option>
                {orgUnits?.results.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Select label="Grade" value={empForm.grade} onChange={setEmp('grade')}>
                <option value="">— None —</option>
                {grades?.results.map(g => <option key={g.id} value={g.id}>{g.grade_code} — {g.grade_name}</option>)}
              </Select>
              <Select label="Manager" value={empForm.manager} onChange={setEmp('manager')}>
                <option value="">— None —</option>
                {allEmployees?.results
                  .filter(e => e.id !== editing?.id)
                  .map(e => <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>)}
              </Select>
            </div>
            <div className="flex justify-between gap-3 pt-2">
              <Button type="button" variant="secondary" onClick={() => setStep(1)}>← Back</Button>
              <div className="flex gap-3">
                <Button type="button" variant="secondary" onClick={closeModal}>Cancel</Button>
                <Button type="submit" loading={isStep2Pending}>{editing ? 'Save Changes' : 'Create Employee'}</Button>
              </div>
            </div>
          </form>
        )}
      </Modal>
    </AppLayout>
  )
}
