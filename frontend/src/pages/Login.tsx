import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Briefcase } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import { ORG_NAME, PLATFORM_NAME, APP_NAME, CURRENT_YEAR, SHOW_DEMO_CREDENTIALS } from '@/lib/branding'

const OAUTH_ERROR_MESSAGES: Record<string, string> = {
  oauth_no_account: 'No account here uses that email — ask an admin to create one for you first, then try SSO again.',
  oauth_email_unverified: "Your identity provider hasn't verified that email address.",
  oauth_denied: 'Sign-in was cancelled.',
  oauth_invalid_state: 'That sign-in link expired or was already used — please try again.',
  oauth_not_configured: 'SSO is not available for this organization.',
  oauth_failed: 'Something went wrong contacting the identity provider — please try again.',
}

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [searchParams] = useSearchParams()
  const [oauth, setOauth] = useState<{ enabled: boolean; button_label?: string }>({ enabled: false })

  useEffect(() => {
    api.get('/auth/oauth/status/').then(r => setOauth(r.data)).catch(() => setOauth({ enabled: false }))
  }, [])

  useEffect(() => {
    const error = searchParams.get('oauth_error')
    if (error) toast.error(OAUTH_ERROR_MESSAGES[error] ?? 'Sign-in failed — please try again.')
  }, [searchParams])

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

  function handleOAuthLogin() {
    // A real browser navigation, not a fetch — the browser must leave the SPA for the IdP.
    window.location.href = `${api.defaults.baseURL}/auth/oauth/login/`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-orange-950 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-orange-600 mb-4">
            <Briefcase size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">{APP_NAME}</h1>
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
                className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
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
                className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-orange-600 hover:bg-orange-700 text-white font-medium py-2.5 rounded-lg text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-2"
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

          {oauth.enabled && (
            <>
              <div className="flex items-center gap-3 my-4">
                <div className="flex-1 h-px bg-gray-200" />
                <span className="text-xs text-gray-400">or</span>
                <div className="flex-1 h-px bg-gray-200" />
              </div>
              <button
                type="button"
                onClick={handleOAuthLogin}
                className="w-full bg-white hover:bg-gray-50 text-gray-700 font-medium py-2.5 rounded-lg text-sm transition-colors border border-gray-300"
              >
                {oauth.button_label || 'Sign in with SSO'}
              </button>
            </>
          )}

          {SHOW_DEMO_CREDENTIALS && (
            <div className="mt-6 p-4 bg-orange-50 rounded-xl">
              <p className="text-xs font-medium text-orange-800 mb-2">Demo Credentials <span className="font-normal text-orange-600">(all use Demo1234!)</span></p>
              <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-xs text-orange-700">
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
          )}
        </div>

        <p className="text-center text-slate-500 text-xs mt-6">
          {ORG_NAME} · {APP_NAME} © {CURRENT_YEAR}
          {ORG_NAME !== PLATFORM_NAME && <span className="block mt-1">Powered by {PLATFORM_NAME}</span>}
        </p>
      </div>
    </div>
  )
}
