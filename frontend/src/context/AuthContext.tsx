import { createContext, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import api from '@/lib/api'

export interface User {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  /** Primary / display role (backward-compat for header label) */
  role: string
  /** All effective roles — use this for access-control checks */
  roles: string[]
  user_type: string
}

interface AuthContextValue {
  user: User | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(() => Boolean(localStorage.getItem('access_token')))

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      api.get('/auth/profile/')
        .then(r => setUser(normalise(r.data)))
        .catch(() => {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        })
        .finally(() => setIsLoading(false))
    }
  }, [])

  async function login(username: string, password: string) {
    const { data } = await api.post('/auth/login/', { username, password })
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    setUser(normalise(data.user))
  }

  function logout() {
    const refresh = localStorage.getItem('refresh_token')
    if (refresh) api.post('/auth/logout/', { refresh }).catch(() => {})
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

/** Guarantee `roles` is always an array, even against old API responses. */
function normalise(raw: Record<string, unknown>): User {
  const roles = Array.isArray(raw.roles)
    ? (raw.roles as string[])
    : raw.role
      ? [raw.role as string]
      : []
  return { ...(raw as User), roles }
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}

/** Returns true if the current user holds at least one of the given roles. */
// eslint-disable-next-line react-refresh/only-export-components
export function useHasRole(...requiredRoles: string[]): boolean {
  const { user } = useAuth()
  if (!user) return false
  return requiredRoles.some(r => user.roles.includes(r))
}
