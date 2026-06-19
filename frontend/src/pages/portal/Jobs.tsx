import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Briefcase, Search, MapPin, Clock, ChevronRight } from 'lucide-react'
import { PortalLayout } from './PortalLayout'
import { Spinner } from '@/components/ui/Spinner'
import portalApi from '@/lib/portalApi'
import { fmt } from '@/lib/utils'

interface Job {
  id: string
  title: string
  description: string
  position_title: string
  department: string
  grade: string
  closing_date: string
  opening_date: string
}

export default function PortalJobs() {
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery<{ count: number; results: Job[] }>({
    queryKey: ['portal-jobs', search],
    queryFn: () => {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      return portalApi.get(`/recruitment/jobs/?${params}`).then(r => r.data)
    },
  })

  return (
    <PortalLayout>
      {/* Hero */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Open Vacancies</h1>
        <p className="text-gray-500">Find your next opportunity at Visionaries Sdn Bhd</p>
      </div>

      {/* Search */}
      <div className="relative mb-8 max-w-xl mx-auto">
        <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search by job title or keyword…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white shadow-sm"
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner className="h-8 w-8" /></div>
      ) : !data?.results?.length ? (
        <div className="text-center py-20 text-gray-400">
          <Briefcase size={40} className="mx-auto mb-3 opacity-30" />
          <p className="font-medium text-gray-600">No open vacancies at this time</p>
          <p className="text-sm mt-1">Check back soon!</p>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-gray-500">{data.count} position{data.count !== 1 ? 's' : ''} available</p>
          {data.results.map((job) => (
            <Link
              key={job.id}
              to={`/portal/jobs/${job.id}`}
              className="block bg-white rounded-xl border border-gray-200 p-5 hover:border-blue-300 hover:shadow-md transition-all group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h2 className="font-semibold text-gray-900 text-lg group-hover:text-blue-700 transition-colors">{job.title}</h2>
                  {job.position_title && (
                    <p className="text-sm text-blue-600 font-medium mt-0.5">{job.position_title}</p>
                  )}
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-sm text-gray-500">
                    {job.department && (
                      <span className="flex items-center gap-1"><MapPin size={13} />{job.department}</span>
                    )}
                    {job.grade && (
                      <span className="flex items-center gap-1"><Briefcase size={13} />Grade: {job.grade}</span>
                    )}
                    {job.closing_date && (
                      <span className="flex items-center gap-1"><Clock size={13} />Closes {fmt(job.closing_date)}</span>
                    )}
                  </div>
                  {job.description && (
                    <p className="text-sm text-gray-500 mt-2 line-clamp-2">{job.description}</p>
                  )}
                </div>
                <ChevronRight size={20} className="text-gray-300 group-hover:text-blue-500 shrink-0 mt-1 transition-colors" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </PortalLayout>
  )
}
