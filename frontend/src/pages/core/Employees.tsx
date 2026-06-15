import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Users, Plus, Pencil, Trash2 } from 'lucide-react'
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
}

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
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Employee | null>(null)
  const [step, setStep] = useState<1 | 2>(1)
  const [personForm, setPersonForm] = useState(emptyPersonForm)
  const [empForm, setEmpForm] = useState(emptyEmpForm)
  const [createdPersonId, setCreatedPersonId] = useState<string | null>(null)

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
    mutationFn: (body: object) => api.post('/core/employees/', body),
    onSuccess: () => {
      toast.success('Employee created')
      qc.invalidateQueries({ queryKey: ['employees'] })
      closeModal()
    },
    onError: () => toast.error('Failed to create employee'),
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

  function closeModal() {
    setModalOpen(false)
    setEditing(null)
    setPersonForm(emptyPersonForm)
    setEmpForm(emptyEmpForm)
    setCreatedPersonId(null)
    setStep(1)
  }

  async function handleStep1(e: React.FormEvent) {
    e.preventDefault()
    if (editing) {
      setStep(2)
      return
    }
    try {
      const person = await createPerson.mutateAsync(personForm)
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
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEdit(emp)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit">
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
        title={editing ? `Edit — ${editing.full_name}` : 'Add Employee'}
      >
        {/* Step indicator */}
        <div className="flex items-center gap-3 mb-6">
          {[1, 2].map(n => (
            <div key={n} className="flex items-center gap-2">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${step === n ? 'bg-blue-600 text-white' : step > n ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-400'}`}>
                {n}
              </div>
              <span className={`text-xs font-medium ${step === n ? 'text-blue-700' : 'text-gray-400'}`}>
                {n === 1 ? 'Personal Info' : 'Employment Details'}
              </span>
              {n < 2 && <div className="w-8 h-px bg-gray-200 ml-1" />}
            </div>
          ))}
        </div>

        {step === 1 ? (
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
