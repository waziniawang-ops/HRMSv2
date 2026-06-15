import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { BookOpen, FolderOpen, Plus, Pencil, Trash2 } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Table, Thead, Tbody, Th, Td, Tr } from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input, Select } from '@/components/ui/Input'
import { Pagination } from '@/components/ui/Pagination'
import { PageSpinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import api from '@/lib/api'

interface JobFamily { id: string; name: string; code: string; description: string }
interface Job {
  id: string
  job_code: string
  job_title: string
  job_family: string | null
  job_family_display?: string
  description: string
  is_active: boolean
}
interface ApiList<T> { count: number; results: T[] }

const PAGE_SIZE = 15

const emptyFamilyForm = { code: '', name: '', description: '' }
const emptyJobForm = { job_code: '', job_title: '', job_family: '', description: '', is_active: 'true' }

export default function Jobs() {
  const qc = useQueryClient()

  // Jobs state
  const [jobPage, setJobPage] = useState(1)
  const [jobSearch, setJobSearch] = useState('')
  const [jobModal, setJobModal] = useState(false)
  const [editingJob, setEditingJob] = useState<Job | null>(null)
  const [jobForm, setJobForm] = useState(emptyJobForm)

  // Job Families state
  const [familyPage, setFamilyPage] = useState(1)
  const [familySearch, setFamilySearch] = useState('')
  const [familyModal, setFamilyModal] = useState(false)
  const [editingFamily, setEditingFamily] = useState<JobFamily | null>(null)
  const [familyForm, setFamilyForm] = useState(emptyFamilyForm)

  const jobParams = { page: jobPage, page_size: PAGE_SIZE, ...(jobSearch ? { search: jobSearch } : {}) }
  const familyParams = { page: familyPage, page_size: PAGE_SIZE, ...(familySearch ? { search: familySearch } : {}) }

  const { data: jobs, isLoading: jobsLoading } = useQuery<ApiList<Job>>({
    queryKey: ['jobs', jobParams],
    queryFn: () => api.get('/core/jobs/', { params: jobParams }).then(r => r.data),
  })

  const { data: families, isLoading: familiesLoading } = useQuery<ApiList<JobFamily>>({
    queryKey: ['job-families', familyParams],
    queryFn: () => api.get('/core/job-families/', { params: familyParams }).then(r => r.data),
  })

  const { data: allFamilies } = useQuery<ApiList<JobFamily>>({
    queryKey: ['job-families-all'],
    queryFn: () => api.get('/core/job-families/', { params: { page_size: 200 } }).then(r => r.data),
  })

  // Job mutations
  const createJob = useMutation({
    mutationFn: (body: typeof emptyJobForm) => api.post('/core/jobs/', body),
    onSuccess: () => { toast.success('Job created'); qc.invalidateQueries({ queryKey: ['jobs'] }); closeJobModal() },
    onError: () => toast.error('Failed to create job'),
  })
  const updateJob = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyJobForm & { id: string }) => api.patch(`/core/jobs/${id}/`, body),
    onSuccess: () => { toast.success('Job updated'); qc.invalidateQueries({ queryKey: ['jobs'] }); closeJobModal() },
    onError: () => toast.error('Failed to update job'),
  })
  const deleteJob = useMutation({
    mutationFn: (id: string) => api.delete(`/core/jobs/${id}/`),
    onSuccess: () => { toast.success('Job deleted'); qc.invalidateQueries({ queryKey: ['jobs'] }) },
    onError: () => toast.error('Cannot delete — job may be linked to positions'),
  })

  // Job Family mutations
  const createFamily = useMutation({
    mutationFn: (body: typeof emptyFamilyForm) => api.post('/core/job-families/', body),
    onSuccess: () => { toast.success('Job family created'); qc.invalidateQueries({ queryKey: ['job-families'] }); qc.invalidateQueries({ queryKey: ['job-families-all'] }); closeFamilyModal() },
    onError: () => toast.error('Failed to create job family'),
  })
  const updateFamily = useMutation({
    mutationFn: ({ id, ...body }: typeof emptyFamilyForm & { id: string }) => api.patch(`/core/job-families/${id}/`, body),
    onSuccess: () => { toast.success('Job family updated'); qc.invalidateQueries({ queryKey: ['job-families'] }); qc.invalidateQueries({ queryKey: ['job-families-all'] }); closeFamilyModal() },
    onError: () => toast.error('Failed to update job family'),
  })
  const deleteFamily = useMutation({
    mutationFn: (id: string) => api.delete(`/core/job-families/${id}/`),
    onSuccess: () => { toast.success('Job family deleted'); qc.invalidateQueries({ queryKey: ['job-families'] }); qc.invalidateQueries({ queryKey: ['job-families-all'] }) },
    onError: () => toast.error('Cannot delete — family may be linked to jobs'),
  })

  // Job modal helpers
  function openCreateJob() { setEditingJob(null); setJobForm(emptyJobForm); setJobModal(true) }
  function openEditJob(j: Job) {
    setEditingJob(j)
    setJobForm({ job_code: j.job_code, job_title: j.job_title, job_family: j.job_family ?? '', description: j.description ?? '', is_active: j.is_active ? 'true' : 'false' })
    setJobModal(true)
  }
  function closeJobModal() { setJobModal(false); setEditingJob(null); setJobForm(emptyJobForm) }

  function handleJobSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = { ...jobForm, job_family: jobForm.job_family || null, is_active: jobForm.is_active === 'true' }
    if (editingJob) updateJob.mutate({ id: editingJob.id, ...payload } as unknown as typeof emptyJobForm & { id: string })
    else createJob.mutate(payload as unknown as typeof emptyJobForm)
  }

  function handleDeleteJob(j: Job) {
    if (!window.confirm(`Delete job "${j.job_title}"? This cannot be undone.`)) return
    deleteJob.mutate(j.id)
  }

  // Family modal helpers
  function openCreateFamily() { setEditingFamily(null); setFamilyForm(emptyFamilyForm); setFamilyModal(true) }
  function openEditFamily(f: JobFamily) {
    setEditingFamily(f)
    setFamilyForm({ code: f.code, name: f.name, description: f.description ?? '' })
    setFamilyModal(true)
  }
  function closeFamilyModal() { setFamilyModal(false); setEditingFamily(null); setFamilyForm(emptyFamilyForm) }

  function handleFamilySubmit(e: React.FormEvent) {
    e.preventDefault()
    if (editingFamily) updateFamily.mutate({ id: editingFamily.id, ...familyForm })
    else createFamily.mutate(familyForm)
  }

  function handleDeleteFamily(f: JobFamily) {
    if (!window.confirm(`Delete job family "${f.name}"? This cannot be undone.`)) return
    deleteFamily.mutate(f.id)
  }

  const setJob = (k: keyof typeof emptyJobForm) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setJobForm(prev => ({ ...prev, [k]: e.target.value }))

  const setFamily = (k: keyof typeof emptyFamilyForm) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setFamilyForm(prev => ({ ...prev, [k]: e.target.value }))

  return (
    <AppLayout title="Jobs">
      <div className="space-y-6">

        {/* Job Families */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FolderOpen size={18} className="text-blue-600" />
                <CardTitle>Job Families</CardTitle>
              </div>
              <Button onClick={openCreateFamily}><Plus size={16} />Add Job Family</Button>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <Input
              placeholder="Search job families…"
              value={familySearch}
              onChange={e => { setFamilySearch(e.target.value); setFamilyPage(1) }}
              className="max-w-sm"
            />
          </CardContent>
          {familiesLoading ? (
            <PageSpinner />
          ) : !families?.results.length ? (
            <EmptyState
              icon={FolderOpen}
              title="No job families found"
              description="Create job families to group related jobs together."
              action={<Button onClick={openCreateFamily}><Plus size={16} />Add Job Family</Button>}
            />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Code</Th>
                    <Th>Name</Th>
                    <Th>Description</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {families.results.map(f => (
                    <Tr key={f.id}>
                      <Td className="font-mono text-xs">{f.code}</Td>
                      <Td className="font-medium">{f.name}</Td>
                      <Td className="text-gray-500 text-sm max-w-xs truncate">{f.description || '—'}</Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEditFamily(f)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit">
                            <Pencil size={15} />
                          </button>
                          <button onClick={() => handleDeleteFamily(f)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete">
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              <Pagination count={families.count} page={familyPage} pageSize={PAGE_SIZE} onPage={setFamilyPage} />
            </>
          )}
        </Card>

        {/* Jobs */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookOpen size={18} className="text-blue-600" />
                <CardTitle>Job Catalogue</CardTitle>
              </div>
              <Button onClick={openCreateJob}><Plus size={16} />Add Job</Button>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-2 pt-4">
            <Input
              placeholder="Search by code or title…"
              value={jobSearch}
              onChange={e => { setJobSearch(e.target.value); setJobPage(1) }}
              className="max-w-sm"
            />
          </CardContent>
          {jobsLoading ? (
            <PageSpinner />
          ) : !jobs?.results.length ? (
            <EmptyState
              icon={BookOpen}
              title="No jobs found"
              description="Add job definitions to build your job catalogue."
              action={<Button onClick={openCreateJob}><Plus size={16} />Add Job</Button>}
            />
          ) : (
            <>
              <Table>
                <Thead>
                  <tr>
                    <Th>Code</Th>
                    <Th>Title</Th>
                    <Th>Job Family</Th>
                    <Th>Status</Th>
                    <Th></Th>
                  </tr>
                </Thead>
                <Tbody>
                  {jobs.results.map(j => (
                    <Tr key={j.id}>
                      <Td className="font-mono text-xs">{j.job_code}</Td>
                      <Td className="font-medium">{j.job_title}</Td>
                      <Td className="text-gray-500">{j.job_family_display ?? '—'}</Td>
                      <Td><Badge status={j.is_active ? 'ACTIVE' : 'INACTIVE'} /></Td>
                      <Td>
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => openEditJob(j)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit">
                            <Pencil size={15} />
                          </button>
                          <button onClick={() => handleDeleteJob(j)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete">
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
              <Pagination count={jobs.count} page={jobPage} pageSize={PAGE_SIZE} onPage={setJobPage} />
            </>
          )}
        </Card>
      </div>

      {/* Job Family Modal */}
      <Modal open={familyModal} onClose={closeFamilyModal} title={editingFamily ? `Edit — ${editingFamily.name}` : 'Add Job Family'}>
        <form onSubmit={handleFamilySubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="Code" required value={familyForm.code} onChange={setFamily('code')} placeholder="e.g. TECH" />
            <Input label="Name" required value={familyForm.name} onChange={setFamily('name')} placeholder="e.g. Technology" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={familyForm.description}
              onChange={e => setFamilyForm(prev => ({ ...prev, description: e.target.value }))}
              rows={3}
              placeholder="Brief description of this job family…"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeFamilyModal}>Cancel</Button>
            <Button type="submit" loading={createFamily.isPending || updateFamily.isPending}>
              {editingFamily ? 'Save Changes' : 'Create'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Job Modal */}
      <Modal open={jobModal} onClose={closeJobModal} title={editingJob ? `Edit — ${editingJob.job_title}` : 'Add Job'}>
        <form onSubmit={handleJobSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input label="Job Code" required value={jobForm.job_code} onChange={setJob('job_code')} placeholder="e.g. JOB-001" />
            <Input label="Job Title" required value={jobForm.job_title} onChange={setJob('job_title')} placeholder="e.g. Software Engineer" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Select label="Job Family" value={jobForm.job_family} onChange={setJob('job_family')}>
              <option value="">— None —</option>
              {allFamilies?.results.map(f => <option key={f.id} value={f.id}>{f.name} ({f.code})</option>)}
            </Select>
            <Select label="Status" value={jobForm.is_active} onChange={setJob('is_active')}>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </Select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={jobForm.description}
              onChange={e => setJobForm(prev => ({ ...prev, description: e.target.value }))}
              rows={3}
              placeholder="Brief description of this job…"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={closeJobModal}>Cancel</Button>
            <Button type="submit" loading={createJob.isPending || updateJob.isPending}>
              {editingJob ? 'Save Changes' : 'Create'}
            </Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  )
}
