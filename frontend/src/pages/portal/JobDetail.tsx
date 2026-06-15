import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { ArrowLeft, Briefcase, MapPin, Clock, CheckCircle } from 'lucide-react'
import { PortalLayout } from './PortalLayout'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { usePortalAuth } from '@/context/PortalAuthContext'
import portalApi from '@/lib/portalApi'
import { fmt } from '@/lib/utils'

interface Job {
  id: string
  title: string
  description: string
  requirements: string
  responsibilities: string
  position_title: string
  department: string
  grade: string
  closing_date: string
  opening_date: string
  screening_questions: Record<string, string>
}

export default function PortalJobDetail() {
  const { id } = useParams<{ id: string }>()
  const { user } = usePortalAuth()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [coverLetter, setCoverLetter] = useState('')
  const [applied, setApplied] = useState(false)

  const { data: job, isLoading } = useQuery<Job>({
    queryKey: ['portal-job', id],
    queryFn: () => portalApi.get(`/recruitment/jobs/${id}/`).then(r => r.data),
  })

  const { data: myApps } = useQuery({
    queryKey: ['portal-my-apps'],
    queryFn: () => portalApi.get('/recruitment/applications/').then(r => r.data),
    enabled: !!user,
  })

  const alreadyApplied = myApps?.results?.some((a: { job_posting: string }) => a.job_posting === id)

  const apply = useMutation({
    mutationFn: () => portalApi.post('/recruitment/applications/', {
      job_posting: id,
      cover_letter: coverLetter,
    }),
    onSuccess: () => {
      toast.success('Application submitted!')
      qc.invalidateQueries({ queryKey: ['portal-my-apps'] })
      setApplied(true)
    },
    onError: (err: { response?: { data?: { detail?: string; non_field_errors?: string[] } } }) => {
      const detail = err.response?.data?.detail || err.response?.data?.non_field_errors?.[0] || 'Failed to apply'
      toast.error(detail)
    },
  })

  if (isLoading) return (
    <PortalLayout>
      <div className="flex justify-center py-20"><Spinner className="h-8 w-8" /></div>
    </PortalLayout>
  )

  if (!job) return (
    <PortalLayout>
      <p className="text-center text-gray-500 py-16">Job not found.</p>
    </PortalLayout>
  )

  return (
    <PortalLayout>
      <Link to="/portal" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 mb-6 transition-colors">
        <ArrowLeft size={15} /> Back to all jobs
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-1">{job.title}</h1>
            {job.position_title && <p className="text-blue-600 font-medium mb-3">{job.position_title}</p>}
            <div className="flex flex-wrap gap-4 text-sm text-gray-500 mb-4">
              {job.department && <span className="flex items-center gap-1"><MapPin size={13} />{job.department}</span>}
              {job.grade && <span className="flex items-center gap-1"><Briefcase size={13} />Grade: {job.grade}</span>}
              {job.closing_date && <span className="flex items-center gap-1"><Clock size={13} />Apply by {fmt(job.closing_date)}</span>}
            </div>
          </div>

          {job.description && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="font-semibold text-gray-900 mb-3">About the Role</h2>
              <p className="text-sm text-gray-600 whitespace-pre-line">{job.description}</p>
            </div>
          )}

          {job.responsibilities && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="font-semibold text-gray-900 mb-3">Responsibilities</h2>
              <p className="text-sm text-gray-600 whitespace-pre-line">{job.responsibilities}</p>
            </div>
          )}

          {job.requirements && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="font-semibold text-gray-900 mb-3">Requirements</h2>
              <p className="text-sm text-gray-600 whitespace-pre-line">{job.requirements}</p>
            </div>
          )}
        </div>

        {/* Apply panel */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 p-6 sticky top-24">
            {applied || alreadyApplied ? (
              <div className="text-center py-4">
                <CheckCircle size={40} className="text-green-500 mx-auto mb-2" />
                <p className="font-semibold text-gray-900">Application Submitted</p>
                <p className="text-sm text-gray-500 mt-1">We'll be in touch!</p>
                <Link to="/portal/dashboard" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
                  View my applications →
                </Link>
              </div>
            ) : !user ? (
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-4">Sign in to apply for this position</p>
                <Button onClick={() => navigate('/portal/login')} className="w-full justify-center">Sign In to Apply</Button>
                <p className="text-xs text-gray-400 mt-3">
                  New here?{' '}
                  <Link to="/portal/register" className="text-blue-600 hover:underline">Create an account</Link>
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900">Apply for this role</h3>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1.5">Cover Letter <span className="text-gray-400">(optional)</span></label>
                  <textarea
                    rows={6}
                    value={coverLetter}
                    onChange={e => setCoverLetter(e.target.value)}
                    placeholder="Tell us why you're a great fit…"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  />
                </div>
                <Button
                  className="w-full justify-center"
                  loading={apply.isPending}
                  onClick={() => apply.mutate()}
                >
                  Submit Application
                </Button>
                <p className="text-xs text-gray-400 text-center">
                  Make sure your{' '}
                  <Link to="/portal/profile" className="text-blue-600 hover:underline">profile</Link>
                  {' '}and{' '}
                  <Link to="/portal/documents" className="text-blue-600 hover:underline">documents</Link>
                  {' '}are up to date before applying.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </PortalLayout>
  )
}
