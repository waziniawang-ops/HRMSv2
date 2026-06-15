import { Bell, LogOut, User } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import api from '@/lib/api'

interface HeaderProps {
  title: string
}

export function Header({ title }: HeaderProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  const { data: unreadData } = useQuery({
    queryKey: ['notif-unread-count'],
    queryFn: () => api.get('/notifications/inbox/unread_count/').then(r => r.data),
    refetchInterval: 30000,
  })

  function handleLogout() {
    logout()
    navigate('/login')
    toast.success('Logged out successfully')
  }

  const extraRoles = (user?.roles?.filter(r => r !== user.role) ?? []).length
  const roleLabel = user?.role
    ? `${user.role.replace(/_/g, ' ')}${extraRoles > 0 ? ` +${extraRoles}` : ''}`
    : ''

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6 sticky top-0 z-20">
      <h1 className="text-base font-semibold text-gray-900">{title}</h1>

      <div className="flex items-center gap-3">
        <button
          className="relative p-2 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
          onClick={() => navigate('/notifications')}
        >
          <Bell size={18} />
          {(unreadData?.unread_count ?? 0) > 0 && (
            <span className="absolute top-1 right-1 min-w-[16px] h-4 px-0.5 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center leading-none">
              {unreadData.unread_count > 99 ? '99+' : unreadData.unread_count}
            </span>
          )}
        </button>

        <div className="relative">
          <button
            onClick={() => setMenuOpen(o => !o)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center">
              <User size={14} className="text-white" />
            </div>
            <div className="text-left">
              <p className="text-sm font-medium text-gray-900 leading-none">
                {user?.first_name} {user?.last_name}
              </p>
              <p className="text-[11px] text-gray-500 mt-0.5">{roleLabel}</p>
            </div>
          </button>

          {menuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
              <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-xl shadow-lg border border-gray-200 py-1 z-20">
                <div className="px-4 py-2 border-b border-gray-100">
                  <p className="text-xs font-medium text-gray-900">{user?.username}</p>
                  <p className="text-xs text-gray-500">{user?.email}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  <LogOut size={15} /> Sign out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
