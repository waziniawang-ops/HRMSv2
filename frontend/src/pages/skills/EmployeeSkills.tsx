import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { Input, Select, Textarea } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Plus, Search, Star } from 'lucide-react'
import { fmt } from '@/lib/utils'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type EmployeeSkill = {
  id: string; employee_name: string; employee_number: string
  skill_name: string; proficiency_name: string
  is_endorsed: boolean; assessed_date: string | null
}

const emptyForm = { employee: '', skill: '', proficiency: '', is_self_assessed: true, evidence_description: '', assessed_date: '' }

export default function EmployeeSkills() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [employees, setEmployees] = useState<{ id: string; employee_number: string; full_name: string }[]>([])
  const [skills, setSkills] = useState<{ id: string; name: string; code: string }[]>([])
  const [proficiencies, setProficiencies] = useState<{ id: string; name: string; level: number }[]>([])

  const { data, isLoading } = useQuery({
    queryKey: ['employee-skills', page],
    queryFn: () => api.get(`/skills/employee-skills/?page=${page}`).then(r => r.data),
  })

  function openCreate() {
    setForm(emptyForm)
    Promise.all([
      api.get('/core/employees/?page_size=200').then(r => setEmployees(r.data.results || [])),
      api.get('/skills/skills/?page_size=200').then(r => setSkills(r.data.results || [])),
      api.get('/skills/proficiency-scales/?page_size=50').then(r => setProficiencies(r.data.results || [])),
    ]).then(() => setModalOpen(true))
  }

  const create = useMutation({
    mutationFn: (body: object) => api.post('/skills/employee-skills/', body),
    onSuccess: () => { toast.success('Skill recorded'); qc.invalidateQueries({ queryKey: ['employee-skills'] }); setModalOpen(false) },
    onError: () => toast.error('Failed to record skill'),
  })

  const filtered = search
    ? data?.results?.filter((r: EmployeeSkill) =>
        r.employee_name?.toLowerCase().includes(search.toLowerCase()) ||
        r.skill_name?.toLowerCase().includes(search.toLowerCase()))
    : data?.results

  return (
    <AppLayout title="Employee Skills">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="relative max-w-sm">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Search employee or skill..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <Button onClick={openCreate}><Plus size={16} /> Add Skill</Button>
        </div>

        <Card>
          {isLoading ? <PageSpinner /> : !filtered?.length ? (
            <EmptyState icon={Star} title="No employee skills recorded" action={<Button onClick={openCreate}><Plus size={16} />Add Skill</Button>} />
          ) : (
            <>
              <Table>
                <Thead><tr><Th>Employee</Th><Th>Skill</Th><Th>Proficiency</Th><Th>Endorsed</Th><Th>Assessed</Th></tr></Thead>
                <Tbody>
                  {filtered.map((r: EmployeeSkill) => (
                    <Tr key={r.id}>
                      <Td className="font-medium">{r.employee_name} <span className="text-gray-400 text-xs">#{r.employee_number}</span></Td>
                      <Td>{r.skill_name}</Td>
                      <Td>{r.proficiency_name}</Td>
                      <Td><Badge status={r.is_endorsed ? 'ENDORSED' : 'SELF_ASSESSED'} /></Td>
                      <Td className="text-gray-500">{r.assessed_date ? fmt(r.assessed_date) : '—'}</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              {!search && <Pagination count={data.count} page={page} pageSize={20} onPage={setPage} />}
            </>
          )}
        </Card>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Record Employee Skill">
        <form onSubmit={e => {
          e.preventDefault()
          const payload: Record<string, unknown> = { ...form }
          if (!form.assessed_date) delete payload.assessed_date
          create.mutate(payload)
        }} className="space-y-4">
          <Select label="Employee *" value={form.employee} onChange={e => setForm(f => ({ ...f, employee: e.target.value }))} required>
            <option value="">Select employee…</option>
            {employees.map(e => <option key={e.id} value={e.id}>{e.full_name} ({e.employee_number})</option>)}
          </Select>
          <Select label="Skill *" value={form.skill} onChange={e => setForm(f => ({ ...f, skill: e.target.value }))} required>
            <option value="">Select skill…</option>
            {skills.map(s => <option key={s.id} value={s.id}>{s.name} ({s.code})</option>)}
          </Select>
          <Select label="Proficiency *" value={form.proficiency} onChange={e => setForm(f => ({ ...f, proficiency: e.target.value }))} required>
            <option value="">Select level…</option>
            {proficiencies.sort((a, b) => a.level - b.level).map(p => <option key={p.id} value={p.id}>L{p.level} — {p.name}</option>)}
          </Select>
          <Input label="Assessment Date" type="date" value={form.assessed_date} onChange={e => setForm(f => ({ ...f, assessed_date: e.target.value }))} />
          <Textarea label="Evidence Description" value={form.evidence_description} onChange={e => setForm(f => ({ ...f, evidence_description: e.target.value }))} rows={2} />
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_self_assessed} onChange={e => setForm(f => ({ ...f, is_self_assessed: e.target.checked }))} /> Self-assessed</label>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Save</Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
