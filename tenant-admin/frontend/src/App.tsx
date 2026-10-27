import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from '@/context/AuthContext'
import { PageSpinner } from '@/components/ui/Spinner'
import Login from '@/pages/Login'
import Tenants from '@/pages/Tenants'
import Plans from '@/pages/Plans'

const qc = new QueryClient({ defaultOptions: { queries: { staleTime: 30000, retry: 1 } } })

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()
  if (isLoading) return <div className="min-h-screen flex items-center justify-center"><PageSpinner /></div>
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function Routed() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/tenants" element={<RequireAuth><Tenants /></RequireAuth>} />
      <Route path="/plans" element={<RequireAuth><Plans /></RequireAuth>} />
      <Route path="/" element={<Navigate to="/tenants" replace />} />
      <Route path="*" element={<Navigate to="/tenants" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <AuthProvider>
          <Toaster position="top-right" />
          <Routed />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
