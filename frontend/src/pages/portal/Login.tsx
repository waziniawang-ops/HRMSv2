import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Briefcase } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { usePortalAuth } from '@/context/PortalAuthContext'

export default function PortalLogin() {
  const { login } = usePortalAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await login(username, password)
      navigate('/portal/dashboard')
    } catch (err: unknown) {
      const error = err as { message?: string; response?: { data?: { detail?: string; non_field_errors?: string[] } } }
      if (error.message && !error.response) {
        toast.error(error.message)
      } else {
        const detail = error.response?.data?.detail || error.response?.data?.non_field_errors?.[0] || 'Invalid credentials'
        toast.error(detail)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center mx-auto mb-3">
            <Briefcase size={22} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Applicant Portal</h1>
          <p className="text-sm text-gray-500 mt-1">Sign in to manage your applications</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Username</label>
            <input
              required autoFocus value={username} onChange={e => setUsername(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password" required value={password} onChange={e => setPassword(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <Button type="submit" loading={loading} className="w-full justify-center mt-2">
            Sign In
          </Button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-4">
          Don't have an account?{' '}
          <Link to="/portal/register" className="text-blue-600 hover:underline font-medium">Register here</Link>
        </p>
        <p className="text-center text-xs text-gray-400 mt-2">
          <Link to="/portal" className="hover:underline">← Browse open positions</Link>
        </p>
      </div>
    </div>
  )
}
