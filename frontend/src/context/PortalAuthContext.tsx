import { createContext, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import portalApi from '@/lib/portalApi'

interface PortalUser {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  role: string
}

interface PortalAuthValue {
  user: PortalUser | null
  login: (username: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  isLoading: boolean
}

interface RegisterData {
  username: string
  email: string
  first_name: string
  last_name: string
  phone: string
  password: string
  password_confirm: string
}

const PortalAuthContext = createContext<PortalAuthValue | null>(null)

export function PortalAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<PortalUser | null>(null)
  const [isLoading, setIsLoading] = useState(() => Boolean(localStorage.getItem('portal_access')))

  useEffect(() => {
    const token = localStorage.getItem('portal_access')
    if (token) {
      portalApi.get('/auth/profile/')
        .then(r => {
          if (r.data.role === 'APPLICANT') setUser(r.data)
          else {
            localStorage.removeItem('portal_access')
            localStorage.removeItem('portal_refresh')
          }
        })
        .catch(() => {
          localStorage.removeItem('portal_access')
          localStorage.removeItem('portal_refresh')
        })
        .finally(() => setIsLoading(false))
    }
  }, [])

  async function login(username: string, password: string) {
    const { data } = await portalApi.post('/auth/login/', { username, password })
    if (data.user.role !== 'APPLICANT') {
      throw new Error('This portal is for applicants only. Use the staff login instead.')
    }
    localStorage.setItem('portal_access', data.access)
    localStorage.setItem('portal_refresh', data.refresh)
    setUser(data.user)
  }

  async function register(body: RegisterData) {
    const { data } = await portalApi.post('/auth/register/', body)
    localStorage.setItem('portal_access', data.access)
    localStorage.setItem('portal_refresh', data.refresh)
    setUser(data.user)
  }

  function logout() {
    const refresh = localStorage.getItem('portal_refresh')
    if (refresh) portalApi.post('/auth/logout/', { refresh }).catch(() => {})
    localStorage.removeItem('portal_access')
    localStorage.removeItem('portal_refresh')
    setUser(null)
  }

  return (
    <PortalAuthContext.Provider value={{ user, login, register, logout, isLoading }}>
      {children}
    </PortalAuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function usePortalAuth() {
  const ctx = useContext(PortalAuthContext)
  if (!ctx) throw new Error('usePortalAuth must be inside PortalAuthProvider')
  return ctx
}
