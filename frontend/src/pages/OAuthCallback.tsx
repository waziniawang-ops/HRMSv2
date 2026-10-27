import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuth } from '@/context/AuthContext'

/**
 * Where the backend's OAuth callback (apps.accounts.views.OAuthCallbackView)
 * redirects after a successful IdP login. The JWT pair arrives in the URL
 * fragment (`#access=...&refresh=...`), which browsers never send to a server.
 */
export default function OAuthCallback() {
  const { loginWithTokens } = useAuth()
  const navigate = useNavigate()
  const ran = useRef(false)

  useEffect(() => {
    if (ran.current) return
    ran.current = true

    const params = new URLSearchParams(window.location.hash.slice(1))
    const access = params.get('access')
    const refresh = params.get('refresh')
    // Clear the tokens out of the address bar/history straight away.
    window.history.replaceState(null, '', window.location.pathname)

    if (!access || !refresh) {
      navigate('/login?oauth_error=oauth_failed', { replace: true })
      return
    }

    loginWithTokens(access, refresh)
      .then(() => {
        toast.success('Welcome back!')
        navigate('/', { replace: true })
      })
      .catch(() => navigate('/login?oauth_error=oauth_failed', { replace: true }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-orange-950 to-slate-900 flex items-center justify-center">
      <div className="text-center text-white">
        <svg className="animate-spin h-8 w-8 mx-auto mb-3" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p className="text-sm text-slate-300">Signing you in…</p>
      </div>
    </div>
  )
}
