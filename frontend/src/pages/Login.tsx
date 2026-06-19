import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Briefcase } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await login(username, password)
      navigate('/')
      toast.success('Welcome back!')
    } catch {
      toast.error('Invalid credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-600 mb-4">
            <Briefcase size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">HRMSv2</h1>
          <p className="text-slate-400 text-sm mt-1">Enterprise Human Resource Management</p>
        </div>

        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Sign in to your account</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
                autoFocus
                className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Signing in...
                </>
              ) : 'Sign in'}
            </button>
          </form>

          <div className="mt-6 p-4 bg-blue-50 rounded-xl">
            <p className="text-xs font-medium text-blue-800 mb-2">Demo Credentials <span className="font-normal text-blue-600">(all use Demo1234!)</span></p>
            <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-xs text-blue-700">
              <p><span className="font-mono font-semibold">sysadmin</span> — Sys Admin</p>
              <p><span className="font-mono font-semibold">hr_norziah</span> — HR Admin</p>
              <p><span className="font-mono font-semibold">hr_fatimah</span> — HR Maker</p>
              <p><span className="font-mono font-semibold">hr_ahmad</span> — HR Checker</p>
              <p><span className="font-mono font-semibold">rec_shafiq</span> — Recruiter</p>
              <p><span className="font-mono font-semibold">mgr_dinesh</span> — Hiring Mgr</p>
              <p><span className="font-mono font-semibold">int_liwei</span> — Interviewer</p>
              <p><span className="font-mono font-semibold">fin_rajan</span> — Finance</p>
              <p><span className="font-mono font-semibold">talent_siti</span> — Talent Cmt</p>
              <p><span className="font-mono font-semibold">perf_azlan</span> — HR Perf</p>
              <p><span className="font-mono font-semibold">ld_nurul</span> — LD Officer</p>
              <p><span className="font-mono font-semibold">ldc_hassan</span> — LD Checker</p>
              <p><span className="font-mono font-semibold">emp_ali</span> — Employee</p>
            </div>
          </div>
        </div>

        <p className="text-center text-slate-500 text-xs mt-6">
          Visionaries Sdn Bhd · HRMSv2 © 2026
        </p>
      </div>
    </div>
  )
}
