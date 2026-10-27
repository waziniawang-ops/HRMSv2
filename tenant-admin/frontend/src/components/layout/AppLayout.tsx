import type { ReactNode } from 'react'
import { Sidebar } from './Sidebar'

export function AppLayout({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      <div className="ml-60">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center px-6 sticky top-0 z-20">
          <h1 className="text-lg font-semibold text-slate-900">{title}</h1>
        </header>
        <main className="p-6">{children}</main>
      </div>
    </div>
  )
}
