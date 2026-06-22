import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Users, Building2, Briefcase, UserPlus,
  UserCheck, Calendar, BarChart3, GitBranch, TrendingUp,
  BookOpen, Bell, Shield, ChevronDown, ChevronRight, ScanFace, Settings2,
  DollarSign, Gift, Inbox, HeadphonesIcon, Scale, FileText, LogOut,
  Heart, AlertTriangle, Receipt, Zap, Award
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/context/AuthContext'

type RoleCode = string

interface NavChild {
  label: string
  path: string
  roles?: RoleCode[]
}

interface NavItem {
  label: string
  path?: string
  icon: React.ElementType
  roles?: RoleCode[]
  children?: NavChild[]
}

// Role group shorthands
const ADMIN = ['SYSTEM_ADMIN', 'HR_ADMIN']
const ALL_HR = [...ADMIN, 'HR_MAKER', 'HR_CHECKER']
const PAYROLL = [...ADMIN, 'PAYROLL_OFFICER', 'FINANCE_CHECKER']
const BENEFITS_ROLES = [...ADMIN, 'BENEFITS_ADMIN', 'HR_MAKER']
const ER_ROLES = [...ADMIN, 'ER_OFFICER']
const HSE_ROLES = [...ADMIN, 'HSE_OFFICER']
const SD_ROLES = [...ADMIN, 'SERVICE_DESK_AGENT', 'HR_MAKER', 'EMPLOYEE', 'MANAGER']
const ALL_INTERNAL = [...ALL_HR, 'MANAGER', 'EMPLOYEE', 'RECRUITER', 'HIRING_MANAGER', 'INTERVIEWER', 'FINANCE_CHECKER', 'TALENT_COMMITTEE', 'HR_PERFORMANCE', 'LD_OFFICER', 'LD_CHECKER', 'PAYROLL_OFFICER', 'HSE_OFFICER', 'SERVICE_DESK_AGENT', 'ER_OFFICER', 'BENEFITS_ADMIN']
const RECRUITMENT = [...ALL_HR, 'RECRUITER', 'HIRING_MANAGER', 'INTERVIEWER', 'FINANCE_CHECKER']
const LD = [...ADMIN, 'LD_OFFICER', 'LD_CHECKER']
const SUCCESSION = [...ALL_HR, 'TALENT_COMMITTEE', 'MANAGER']
const PERF = [...ADMIN, 'HR_PERFORMANCE', 'HR_CHECKER', 'MANAGER', 'EMPLOYEE']
const WORKFORCE = [...ALL_HR, 'MANAGER', 'EMPLOYEE', 'RECRUITER', 'HIRING_MANAGER']
const REPORTS = [...ALL_HR, 'HR_PERFORMANCE', 'TALENT_COMMITTEE', 'MANAGER', 'RECRUITER', 'HIRING_MANAGER', 'LD_OFFICER']

const ALL_NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  {
    label: 'Core HR', icon: Building2, roles: ALL_HR,
    children: [
      { label: 'Org Units', path: '/core/org-units' },
      { label: 'Positions', path: '/core/positions' },
      { label: 'Employees', path: '/core/employees' },
      { label: 'Assignments', path: '/core/assignments' },
      { label: 'Job Grades', path: '/core/grades' },
      { label: 'Jobs', path: '/core/jobs' },
    ],
  },
  {
    label: 'Recruitment', icon: UserPlus, roles: RECRUITMENT,
    children: [
      { label: 'Requisitions', path: '/recruitment/requisitions', roles: [...ALL_HR, 'RECRUITER', 'HIRING_MANAGER'] },
      { label: 'Job Postings', path: '/recruitment/postings', roles: [...ALL_HR, 'RECRUITER', 'HIRING_MANAGER'] },
      { label: 'Applicants', path: '/recruitment/applicants', roles: [...ALL_HR, 'RECRUITER', 'HIRING_MANAGER', 'INTERVIEWER'] },
      { label: 'Applications', path: '/recruitment/applications', roles: [...ALL_HR, 'RECRUITER', 'HIRING_MANAGER', 'INTERVIEWER'] },
      { label: 'Interviews', path: '/recruitment/interviews', roles: [...ALL_HR, 'RECRUITER', 'HIRING_MANAGER', 'INTERVIEWER'] },
      { label: 'Offers', path: '/recruitment/offers', roles: [...ALL_HR, 'RECRUITER', 'FINANCE_CHECKER'] },
    ],
  },
  {
    label: 'Onboarding', icon: UserCheck, roles: [...ALL_HR, 'RECRUITER'],
    children: [
      { label: 'Cases', path: '/onboarding/cases' },
    ],
  },
  {
    label: 'Attendance', icon: ScanFace, roles: ALL_HR,
    children: [
      { label: 'Face Enrolment', path: '/attendance/enroll', roles: ALL_HR },
      { label: 'Records', path: '/attendance/records', roles: ALL_HR },
    ],
  },
  {
    label: 'Workforce', icon: Calendar, roles: WORKFORCE,
    children: [
      { label: 'Leave Types', path: '/workforce/leave-types', roles: ALL_HR },
      { label: 'Leave Requests', path: '/workforce/leave-requests' },
      { label: 'Attendance', path: '/workforce/attendance' },
      { label: 'Overtime', path: '/workforce/overtime' },
      { label: 'Transfers', path: '/workforce/transfers', roles: [...ALL_HR, 'MANAGER'] },
    ],
  },
  {
    label: 'Succession', icon: GitBranch, roles: SUCCESSION,
    children: [
      { label: 'Plans', path: '/succession/plans' },
      { label: 'Talent Pools', path: '/succession/talent-pools', roles: [...ALL_HR, 'TALENT_COMMITTEE'] },
      { label: 'Talent Profiles', path: '/succession/talent-profiles', roles: [...ALL_HR, 'TALENT_COMMITTEE', 'MANAGER'] },
    ],
  },
  {
    label: 'Performance', icon: TrendingUp, roles: PERF,
    children: [
      { label: 'Cycles', path: '/performance/cycles', roles: [...ADMIN, 'HR_PERFORMANCE'] },
      { label: 'Goal Plans', path: '/performance/goals' },
      { label: 'Reviews', path: '/performance/reviews' },
      { label: 'Outcomes', path: '/performance/outcomes', roles: [...ADMIN, 'HR_PERFORMANCE', 'HR_CHECKER'] },
    ],
  },
  {
    label: 'Learning', icon: BookOpen, roles: [...LD, 'HR_MAKER', 'MANAGER', 'EMPLOYEE'],
    children: [
      { label: 'Courses', path: '/learning/courses', roles: LD },
      { label: 'Assignments', path: '/learning/assignments', roles: [...LD, 'HR_MAKER', 'MANAGER', 'EMPLOYEE'] },
      { label: 'Completions', path: '/learning/completions', roles: LD },
      { label: 'Skill Gaps', path: '/learning/skill-gaps', roles: ALL_HR },
    ],
  },
  {
    label: 'Workflow', icon: GitBranch,
    children: [
      { label: 'Rules', path: '/workflow/rules', roles: ADMIN },
      { label: 'Requests', path: '/workflow/requests' },
    ],
  },
  { label: 'Notifications', path: '/notifications', icon: Bell },
  {
    label: 'Reports', icon: BarChart3, roles: REPORTS,
    children: [
      { label: 'HR Dashboard', path: '/reports/dashboard', roles: ALL_HR },
      { label: 'Headcount', path: '/reports/headcount', roles: ALL_HR },
      { label: 'Hiring Funnel', path: '/reports/hiring-funnel', roles: [...ALL_HR, 'RECRUITER', 'HIRING_MANAGER'] },
      { label: 'Performance', path: '/reports/performance', roles: [...ADMIN, 'HR_PERFORMANCE'] },
      { label: 'Learning', path: '/reports/learning', roles: LD },
    ],
  },
  {
    label: 'Payroll', icon: DollarSign, roles: PAYROLL,
    children: [
      { label: 'Calendars', path: '/payroll/calendars', roles: PAYROLL },
      { label: 'Payroll Runs', path: '/payroll/runs', roles: PAYROLL },
      { label: 'Payslips', path: '/payroll/payslips', roles: PAYROLL },
      { label: 'Elements', path: '/payroll/elements', roles: PAYROLL },
    ],
  },
  {
    label: 'Compensation', icon: BarChart3, roles: [...ADMIN, 'PAYROLL_OFFICER', 'FINANCE_CHECKER'],
    children: [
      { label: 'Packages', path: '/compensation/packages' },
      { label: 'Bonus Cycles', path: '/compensation/bonus-cycles' },
    ],
  },
  {
    label: 'Benefits', icon: Gift, roles: BENEFITS_ROLES,
    children: [
      { label: 'Benefit Plans', path: '/benefits/plans' },
      { label: 'Enrollments', path: '/benefits/enrollments' },
    ],
  },
  {
    label: 'ESS', icon: Inbox, roles: ALL_INTERNAL,
    children: [
      { label: 'All Requests', path: '/ess/requests', roles: ALL_HR },
      { label: 'My Requests', path: '/ess/my-requests' },
      { label: 'Profile Changes', path: '/ess/profile-changes' },
    ],
  },
  {
    label: 'Service Desk', icon: HeadphonesIcon, roles: SD_ROLES,
    children: [
      { label: 'Tickets', path: '/service-desk/tickets' },
      { label: 'Knowledge Base', path: '/service-desk/knowledge-base' },
    ],
  },
  {
    label: 'Employee Relations', icon: Scale, roles: ER_ROLES,
    children: [
      { label: 'ER Cases', path: '/er/cases' },
    ],
  },
  {
    label: 'Documents', icon: FileText, roles: ALL_HR,
    children: [
      { label: 'Records', path: '/documents/records' },
      { label: 'Policies', path: '/documents/policies' },
    ],
  },
  {
    label: 'Offboarding', icon: LogOut, roles: ALL_HR,
    children: [
      { label: 'Cases', path: '/offboarding/cases' },
    ],
  },
  {
    label: 'Engagement', icon: Award, roles: ALL_HR,
    children: [
      { label: 'Recognition', path: '/engagement/nominations' },
      { label: 'Surveys', path: '/engagement/surveys' },
    ],
  },
  {
    label: 'HSE', icon: AlertTriangle, roles: HSE_ROLES,
    children: [
      { label: 'Incidents', path: '/hse/incidents' },
      { label: 'Wellbeing', path: '/hse/wellbeing' },
    ],
  },
  {
    label: 'Claims', icon: Receipt, roles: [...ALL_HR, 'MANAGER', 'EMPLOYEE'],
    children: [
      { label: 'Claim Requests', path: '/claims/requests' },
    ],
  },
  {
    label: 'Skills', icon: Zap, roles: [...ALL_HR, 'MANAGER'],
    children: [
      { label: 'Skill Inventory', path: '/skills/inventory', roles: ALL_HR },
      { label: 'Employee Skills', path: '/skills/employee-skills' },
    ],
  },
  { label: 'Users', path: '/users', icon: Users, roles: ADMIN },
  { label: 'Audit', path: '/audit', icon: Shield, roles: ADMIN },
  { label: 'Settings', path: '/settings', icon: Settings2, roles: ['SYSTEM_ADMIN'] },
]

/** A user with ANY of the required roles may access the item. */
function canAccess(requiredRoles: RoleCode[] | undefined, userRoles: RoleCode[]): boolean {
  return !requiredRoles || requiredRoles.some(r => userRoles.includes(r))
}

function filterNavItems(items: NavItem[], userRoles: RoleCode[]): NavItem[] {
  return items
    .filter(item => canAccess(item.roles, userRoles))
    .map(item => {
      if (!item.children) return item
      const children = item.children.filter(c => canAccess(c.roles, userRoles))
      return { ...item, children }
    })
    .filter(item => !item.children || item.children.length > 0)
}

function NavGroup({ item }: { item: NavItem }) {
  const location = useLocation()
  const isActive = item.children?.some(c => location.pathname.startsWith(c.path))
  const [open, setOpen] = useState(isActive ?? false)

  return (
    <div>
      <button
        onClick={() => setOpen(o => !o)}
        className={cn(
          'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors text-left',
          isActive ? 'text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
        )}
      >
        <item.icon size={18} className="shrink-0" />
        <span className="flex-1">{item.label}</span>
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      {open && (
        <div className="ml-7 mt-1 space-y-0.5">
          {item.children!.map(child => (
            <NavLink
              key={child.path}
              to={child.path}
              className={({ isActive }) => cn(
                'block px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )}
            >
              {child.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  )
}

export function Sidebar() {
  const { user } = useAuth()
  // user.roles is the full effective set; fall back to [primary role] if missing
  const userRoles = user?.roles?.length ? user.roles : (user?.role ? [user.role] : [])
  const navItems = filterNavItems(ALL_NAV_ITEMS, userRoles)

  return (
    <aside className="fixed inset-y-0 left-0 w-60 bg-slate-900 flex flex-col z-30">
      <div className="px-4 py-5 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shrink-0">
            <Briefcase size={16} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-white leading-none">HRMSv2</p>
            <p className="text-[10px] text-slate-400 mt-0.5">Enterprise HR Platform</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-0.5">
        {navItems.map(item =>
          item.children ? (
            <NavGroup key={item.label} item={item} />
          ) : (
            <NavLink
              key={item.path}
              to={item.path!}
              end
              className={({ isActive }) => cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )}
            >
              <item.icon size={18} className="shrink-0" />
              {item.label}
            </NavLink>
          )
        )}
      </nav>

      <div className="px-3 py-3 border-t border-slate-800">
        <p className="text-[10px] text-slate-500 text-center">Visionaries Sdn Bhd © 2026</p>
      </div>
    </aside>
  )
}
