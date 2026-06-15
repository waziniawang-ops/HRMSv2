import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Save, Plus, Trash2 } from 'lucide-react'
import { PortalLayout } from './PortalLayout'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import portalApi from '@/lib/portalApi'

interface ApplicantData {
  id: string
  full_name: string
  email: string
  phone: string
  linkedin_url: string
  resume: string | null
  profile?: {
    summary: string
    education: EducationEntry[]
    experience: ExpEntry[]
    skills: string[]
    certifications: string[]
    languages: string[]
  }
}

interface EducationEntry { institution: string; degree: string; field: string; year: string }
interface ExpEntry { company: string; role: string; from: string; to: string; description: string }

const emptyEdu: EducationEntry = { institution: '', degree: '', field: '', year: '' }
const emptyExp: ExpEntry = { company: '', role: '', from: '', to: '', description: '' }

export default function PortalProfile() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<'basic' | 'profile'>('basic')

  const { data: applicant, isLoading } = useQuery<ApplicantData>({
    queryKey: ['portal-me'],
    queryFn: () => portalApi.get('/recruitment/applicants/me/').then(r => r.data),
  })

  const [basic, setBasic] = useState({ full_name: '', phone: '', linkedin_url: '' })
  const [summary, setSummary] = useState('')
  const [education, setEducation] = useState<EducationEntry[]>([])
  const [experience, setExperience] = useState<ExpEntry[]>([])
  const [skills, setSkills] = useState<string[]>([])
  const [skillInput, setSkillInput] = useState('')
  const [certifications, setCertifications] = useState<string[]>([])
  const [certInput, setCertInput] = useState('')
  const [languages, setLanguages] = useState<string[]>([])
  const [langInput, setLangInput] = useState('')

  useEffect(() => {
    if (applicant) {
      setBasic({ full_name: applicant.full_name, phone: applicant.phone, linkedin_url: applicant.linkedin_url })
      if (applicant.profile) {
        setSummary(applicant.profile.summary || '')
        setEducation(applicant.profile.education || [])
        setExperience(applicant.profile.experience || [])
        setSkills(applicant.profile.skills || [])
        setCertifications(applicant.profile.certifications || [])
        setLanguages(applicant.profile.languages || [])
      }
    }
  }, [applicant])

  const updateBasic = useMutation({
    mutationFn: () => portalApi.patch('/recruitment/applicants/me/', basic),
    onSuccess: () => { toast.success('Profile updated'); qc.invalidateQueries({ queryKey: ['portal-me'] }) },
    onError: () => toast.error('Failed to update'),
  })

  const updateProfile = useMutation({
    mutationFn: () => portalApi.put('/recruitment/applicant/profile/', {
      summary, education, experience, skills, certifications, languages,
    }),
    onSuccess: () => { toast.success('Profile updated'); qc.invalidateQueries({ queryKey: ['portal-me'] }) },
    onError: () => toast.error('Failed to update'),
  })

  if (isLoading) return (
    <PortalLayout><div className="flex justify-center py-16"><Spinner className="h-8 w-8" /></div></PortalLayout>
  )

  const tabCls = (t: typeof tab) =>
    `px-4 py-2 text-sm font-medium rounded-lg transition-colors ${tab === t ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`

  return (
    <PortalLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
        <p className="text-sm text-gray-500 mt-1">Keep your profile complete to stand out to recruiters</p>
      </div>

      <div className="flex gap-2 mb-6">
        <button className={tabCls('basic')} onClick={() => setTab('basic')}>Basic Info</button>
        <button className={tabCls('profile')} onClick={() => setTab('profile')}>Experience & Skills</button>
      </div>

      {tab === 'basic' && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Full Name</label>
            <input value={basic.full_name} onChange={e => setBasic(p => ({ ...p, full_name: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Email <span className="text-gray-400">(cannot change)</span></label>
            <input value={applicant?.email ?? ''} disabled
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-gray-50 text-gray-400 cursor-not-allowed" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Phone</label>
            <input value={basic.phone} onChange={e => setBasic(p => ({ ...p, phone: e.target.value }))} placeholder="+60 12-345 6789"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">LinkedIn URL</label>
            <input value={basic.linkedin_url} onChange={e => setBasic(p => ({ ...p, linkedin_url: e.target.value }))} placeholder="https://linkedin.com/in/yourname"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="flex justify-end pt-2">
            <Button onClick={() => updateBasic.mutate()} loading={updateBasic.isPending}>
              <Save size={15} /> Save Basic Info
            </Button>
          </div>
        </div>
      )}

      {tab === 'profile' && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Professional Summary</h3>
            <textarea rows={4} value={summary} onChange={e => setSummary(e.target.value)} placeholder="Write a short professional summary…"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
          </div>

          {/* Education */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">Education</h3>
              <button onClick={() => setEducation(p => [...p, { ...emptyEdu }])} className="flex items-center gap-1 text-xs text-blue-600 hover:underline"><Plus size={13} />Add</button>
            </div>
            <div className="space-y-4">
              {education.map((edu, i) => (
                <div key={i} className="border border-gray-100 rounded-lg p-4 space-y-2 relative">
                  <button onClick={() => setEducation(p => p.filter((_, j) => j !== i))} className="absolute top-3 right-3 text-gray-300 hover:text-red-500"><Trash2 size={14} /></button>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs text-gray-500 mb-0.5">Institution</label>
                      <input value={edu.institution} onChange={e => setEducation(p => p.map((x, j) => j === i ? { ...x, institution: e.target.value } : x))}
                        className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-0.5">Degree</label>
                      <input value={edu.degree} onChange={e => setEducation(p => p.map((x, j) => j === i ? { ...x, degree: e.target.value } : x))}
                        className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-0.5">Field of Study</label>
                      <input value={edu.field} onChange={e => setEducation(p => p.map((x, j) => j === i ? { ...x, field: e.target.value } : x))}
                        className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-0.5">Year</label>
                      <input value={edu.year} onChange={e => setEducation(p => p.map((x, j) => j === i ? { ...x, year: e.target.value } : x))} placeholder="2023"
                        className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
                    </div>
                  </div>
                </div>
              ))}
              {education.length === 0 && <p className="text-sm text-gray-400">No education entries yet.</p>}
            </div>
          </div>

          {/* Experience */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">Work Experience</h3>
              <button onClick={() => setExperience(p => [...p, { ...emptyExp }])} className="flex items-center gap-1 text-xs text-blue-600 hover:underline"><Plus size={13} />Add</button>
            </div>
            <div className="space-y-4">
              {experience.map((exp, i) => (
                <div key={i} className="border border-gray-100 rounded-lg p-4 space-y-2 relative">
                  <button onClick={() => setExperience(p => p.filter((_, j) => j !== i))} className="absolute top-3 right-3 text-gray-300 hover:text-red-500"><Trash2 size={14} /></button>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs text-gray-500 mb-0.5">Company</label>
                      <input value={exp.company} onChange={e => setExperience(p => p.map((x, j) => j === i ? { ...x, company: e.target.value } : x))}
                        className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-0.5">Role / Title</label>
                      <input value={exp.role} onChange={e => setExperience(p => p.map((x, j) => j === i ? { ...x, role: e.target.value } : x))}
                        className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-0.5">From</label>
                      <input value={exp.from} onChange={e => setExperience(p => p.map((x, j) => j === i ? { ...x, from: e.target.value } : x))} placeholder="Jan 2020"
                        className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-0.5">To</label>
                      <input value={exp.to} onChange={e => setExperience(p => p.map((x, j) => j === i ? { ...x, to: e.target.value } : x))} placeholder="Present"
                        className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-0.5">Description</label>
                    <textarea rows={2} value={exp.description} onChange={e => setExperience(p => p.map((x, j) => j === i ? { ...x, description: e.target.value } : x))}
                      className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none" />
                  </div>
                </div>
              ))}
              {experience.length === 0 && <p className="text-sm text-gray-400">No experience entries yet.</p>}
            </div>
          </div>

          {/* Skills, Certs, Languages */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label: 'Skills', items: skills, setItems: setSkills, input: skillInput, setInput: setSkillInput, placeholder: 'e.g. Python' },
              { label: 'Certifications', items: certifications, setItems: setCertifications, input: certInput, setInput: setCertInput, placeholder: 'e.g. AWS SAA' },
              { label: 'Languages', items: languages, setItems: setLanguages, input: langInput, setInput: setLangInput, placeholder: 'e.g. Malay' },
            ].map(({ label, items, setItems, input, setInput, placeholder }) => (
              <div key={label} className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-900 mb-3 text-sm">{label}</h3>
                <div className="flex gap-2 mb-3">
                  <input value={input} onChange={e => setInput(e.target.value)} placeholder={placeholder}
                    onKeyDown={e => { if (e.key === 'Enter' && input.trim()) { e.preventDefault(); setItems(p => [...p, input.trim()]); setInput('') } }}
                    className="flex-1 border border-gray-300 rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
                  <button onClick={() => { if (input.trim()) { setItems(p => [...p, input.trim()]); setInput('') } }}
                    className="px-2 py-1.5 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"><Plus size={13} /></button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {items.map((item, i) => (
                    <span key={i} className="flex items-center gap-1 bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full">
                      {item}
                      <button onClick={() => setItems(p => p.filter((_, j) => j !== i))} className="hover:text-red-500 ml-0.5"><Trash2 size={10} /></button>
                    </span>
                  ))}
                  {items.length === 0 && <p className="text-xs text-gray-400">None added</p>}
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end">
            <Button onClick={() => updateProfile.mutate()} loading={updateProfile.isPending}>
              <Save size={15} /> Save Experience & Skills
            </Button>
          </div>
        </div>
      )}
    </PortalLayout>
  )
}
