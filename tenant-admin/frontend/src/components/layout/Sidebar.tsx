import { NavLink } from 'react-router-dom'
import { Building2, Package, LayoutGrid, LogOut } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { label: 'Tenants', path: '/tenants', icon: Building2 },
  { label: 'Plans', path: '/plans', icon: Package },
]

export function Sidebar() {
  const { user, logout } = useAuth()

  return (
    <aside className="fixed inset-y-0 left-0 w-60 bg-gradient-to-b from-slate-900 via-orange-950 to-slate-900 flex flex-col z-30">
      <div className="px-4 py-5 border-b border-slate-800 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center shrink-0">
          <LayoutGrid size={16} className="text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-white leading-none">Tenant Admin</p>
          <p className="text-[10px] text-slate-400 mt-0.5">Visionaries Ent. Control Plane</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => cn(
              'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
              isActive
                ? 'bg-primary-600 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            )}
          >
            <item.icon size={16} />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="px-3 py-3 border-t border-slate-800 space-y-2">
        {user && (
          <div className="px-3 py-2 rounded-lg bg-slate-900">
            <p className="text-xs font-medium text-white truncate">{user.username}</p>
            <p className="text-[10px] text-slate-500 truncate">{user.email}</p>
          </div>
        )}
        <button
          onClick={logout}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </div>
    </aside>
  )
}
