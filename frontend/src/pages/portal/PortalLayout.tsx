import type { ReactNode } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { Briefcase, LogOut, User, FileText, LayoutDashboard, LogIn } from 'lucide-react'
import { usePortalAuth } from '@/context/PortalAuthContext'
import { cn } from '@/lib/utils'

export function PortalLayout({ children }: { children: ReactNode }) {
  const { user, logout } = usePortalAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/portal/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Top nav */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/portal" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <Briefcase size={16} className="text-white" />
            </div>
            <div>
              <p className="text-sm font-bold text-gray-900 leading-none">HRMSv2 Careers</p>
              <p className="text-[10px] text-gray-400">Nexus Corp Berhad</p>
            </div>
          </Link>

          <nav className="flex items-center gap-1">
            <NavLink
              to="/portal"
              end
              className={({ isActive }) => cn(
                'flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              )}
            >
              <Briefcase size={15} /> Jobs
            </NavLink>

            {user ? (
              <>
                <NavLink
                  to="/portal/dashboard"
                  className={({ isActive }) => cn(
                    'flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  )}
                >
                  <LayoutDashboard size={15} /> My Applications
                </NavLink>
                <NavLink
                  to="/portal/profile"
                  className={({ isActive }) => cn(
                    'flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  )}
                >
                  <User size={15} /> Profile
                </NavLink>
                <NavLink
                  to="/portal/documents"
                  className={({ isActive }) => cn(
                    'flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  )}
                >
                  <FileText size={15} /> Documents
                </NavLink>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-red-600 hover:bg-red-50 transition-colors ml-1"
                >
                  <LogOut size={15} /> Sign Out
                </button>
              </>
            ) : (
              <>
                <NavLink
                  to="/portal/login"
                  className={({ isActive }) => cn(
                    'flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  )}
                >
                  <LogIn size={15} /> Sign In
                </NavLink>
                <Link
                  to="/portal/register"
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold bg-blue-600 text-white hover:bg-blue-700 transition-colors ml-1"
                >
                  Register
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-8">
        {children}
      </main>

      <footer className="border-t border-gray-200 py-4 text-center text-xs text-gray-400">
        Nexus Corp Berhad © 2026 — Careers Portal
      </footer>
    </div>
  )
}
