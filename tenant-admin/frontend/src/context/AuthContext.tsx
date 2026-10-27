import { createContext, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

interface AuthUser {
  username: string
  email: string
  is_superuser: boolean
}

interface AuthValue {
  user: AuthUser | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(() => Boolean(localStorage.getItem('ta_access_token')))

  useEffect(() => {
    const token = localStorage.getItem('ta_access_token')
    // isLoading already initialized to false above when there's no token
    // (lazy useState initializer), so there's nothing to do here in that case.
    if (!token) return
    api.get('/auth/me/')
      .then(r => setUser(r.data))
      .catch(() => {
        localStorage.removeItem('ta_access_token')
        localStorage.removeItem('ta_refresh_token')
      })
      .finally(() => setIsLoading(false))
  }, [])

  async function login(username: string, password: string) {
    qc.clear()
    const { data } = await api.post('/auth/login/', { username, password })
    localStorage.setItem('ta_access_token', data.access)
    localStorage.setItem('ta_refresh_token', data.refresh)
    setUser(data.user)
  }

  function logout() {
    localStorage.removeItem('ta_access_token')
    localStorage.removeItem('ta_refresh_token')
    setUser(null)
    qc.clear()
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
