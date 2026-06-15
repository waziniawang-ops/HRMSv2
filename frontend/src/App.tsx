import { type ReactNode } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from '@/context/AuthContext'
import { PortalAuthProvider, usePortalAuth } from '@/context/PortalAuthContext'
import { Spinner } from '@/components/ui/Spinner'

// Portal pages
import PortalJobs from '@/pages/portal/Jobs'
import PortalJobDetail from '@/pages/portal/JobDetail'
import PortalLogin from '@/pages/portal/Login'
import PortalRegister from '@/pages/portal/Register'
import PortalDashboard from '@/pages/portal/Dashboard'
import PortalProfile from '@/pages/portal/Profile'
import PortalDocuments from '@/pages/portal/Documents'

import Login from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'

// Core HR
import OrgUnits from '@/pages/core/OrgUnits'
import Positions from '@/pages/core/Positions'
import Employees from '@/pages/core/Employees'
import Grades from '@/pages/core/Grades'
import Jobs from '@/pages/core/Jobs'
import EmployeeAssignments from '@/pages/core/EmployeeAssignments'

// Recruitment
import Requisitions from '@/pages/recruitment/Requisitions'
import Postings from '@/pages/recruitment/Postings'
import Applicants from '@/pages/recruitment/Applicants'
import Applications from '@/pages/recruitment/Applications'
import Interviews from '@/pages/recruitment/Interviews'
import Offers from '@/pages/recruitment/Offers'

// Onboarding
import Cases from '@/pages/onboarding/Cases'

// Workforce
import LeaveTypes from '@/pages/workforce/LeaveTypes'
import LeaveRequests from '@/pages/workforce/LeaveRequests'
import Attendance from '@/pages/workforce/Attendance'
import Overtime from '@/pages/workforce/Overtime'
import Transfers from '@/pages/workforce/Transfers'

// Succession
import SuccessionPlans from '@/pages/succession/Plans'
import TalentPools from '@/pages/succession/TalentPools'
import TalentProfiles from '@/pages/succession/TalentProfiles'

// Performance
import Cycles from '@/pages/performance/Cycles'
import Goals from '@/pages/performance/Goals'
import Reviews from '@/pages/performance/Reviews'
import Outcomes from '@/pages/performance/Outcomes'

// Learning
import Courses from '@/pages/learning/Courses'
import Assignments from '@/pages/learning/Assignments'
import Completions from '@/pages/learning/Completions'
import SkillGaps from '@/pages/learning/SkillGaps'

// Workflow
import WorkflowRules from '@/pages/workflow/Rules'
import WorkflowRequests from '@/pages/workflow/Requests'

// Other
import Notifications from '@/pages/Notifications'
import UsersPage from '@/pages/Users'
import Audit from '@/pages/Audit'
import Settings from '@/pages/Settings'

// Attendance / Kiosk
import FaceEnroll from '@/pages/attendance/FaceEnroll'
import AttendanceRecords from '@/pages/attendance/AttendanceRecords'
import Kiosk from '@/pages/attendance/Kiosk'

// Reports
import HeadcountReport from '@/pages/reports/Headcount'
import HiringFunnel from '@/pages/reports/HiringFunnel'
import PerformanceReport from '@/pages/reports/PerformanceReport'
import LearningReport from '@/pages/reports/LearningReport'

const qc = new QueryClient({ defaultOptions: { queries: { staleTime: 30000, retry: 1 } } })

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth()
  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Spinner className="h-8 w-8" />
    </div>
  )
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function RequirePortalAuth({ children }: { children: ReactNode }) {
  const { user, isLoading } = usePortalAuth()
  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Spinner className="h-8 w-8" />
    </div>
  )
  if (!user) return <Navigate to="/portal/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <PortalAuthProvider>
        <BrowserRouter basename={import.meta.env.BASE_URL}>
          <Routes>
            <Route path="/login" element={<Login />} />
            {/* Kiosk is public — no auth required */}
            <Route path="/kiosk" element={<Kiosk />} />

            {/* Applicant Portal — public + protected */}
            <Route path="/portal" element={<PortalJobs />} />
            <Route path="/portal/jobs/:id" element={<PortalJobDetail />} />
            <Route path="/portal/login" element={<PortalLogin />} />
            <Route path="/portal/register" element={<PortalRegister />} />
            <Route path="/portal/dashboard" element={<RequirePortalAuth><PortalDashboard /></RequirePortalAuth>} />
            <Route path="/portal/profile" element={<RequirePortalAuth><PortalProfile /></RequirePortalAuth>} />
            <Route path="/portal/documents" element={<RequirePortalAuth><PortalDocuments /></RequirePortalAuth>} />
            <Route path="/*" element={
              <RequireAuth>
                <Routes>
                  <Route path="/" element={<Dashboard />} />

                  <Route path="/core/org-units" element={<OrgUnits />} />
                  <Route path="/core/positions" element={<Positions />} />
                  <Route path="/core/employees" element={<Employees />} />
                  <Route path="/core/grades" element={<Grades />} />
                  <Route path="/core/jobs" element={<Jobs />} />
                  <Route path="/core/assignments" element={<EmployeeAssignments />} />

                  <Route path="/recruitment/requisitions" element={<Requisitions />} />
                  <Route path="/recruitment/postings" element={<Postings />} />
                  <Route path="/recruitment/applicants" element={<Applicants />} />
                  <Route path="/recruitment/applications" element={<Applications />} />
                  <Route path="/recruitment/interviews" element={<Interviews />} />
                  <Route path="/recruitment/offers" element={<Offers />} />

                  <Route path="/onboarding/cases" element={<Cases />} />

                  <Route path="/attendance/enroll" element={<FaceEnroll />} />
                  <Route path="/attendance/records" element={<AttendanceRecords />} />

                  <Route path="/workforce/leave-types" element={<LeaveTypes />} />
                  <Route path="/workforce/leave-requests" element={<LeaveRequests />} />
                  <Route path="/workforce/attendance" element={<Attendance />} />
                  <Route path="/workforce/overtime" element={<Overtime />} />
                  <Route path="/workforce/transfers" element={<Transfers />} />

                  <Route path="/succession/plans" element={<SuccessionPlans />} />
                  <Route path="/succession/talent-pools" element={<TalentPools />} />
                  <Route path="/succession/talent-profiles" element={<TalentProfiles />} />

                  <Route path="/performance/cycles" element={<Cycles />} />
                  <Route path="/performance/goals" element={<Goals />} />
                  <Route path="/performance/reviews" element={<Reviews />} />
                  <Route path="/performance/outcomes" element={<Outcomes />} />

                  <Route path="/learning/courses" element={<Courses />} />
                  <Route path="/learning/assignments" element={<Assignments />} />
                  <Route path="/learning/completions" element={<Completions />} />
                  <Route path="/learning/skill-gaps" element={<SkillGaps />} />

                  <Route path="/workflow/rules" element={<WorkflowRules />} />
                  <Route path="/workflow/requests" element={<WorkflowRequests />} />

                  <Route path="/notifications" element={<Notifications />} />
                  <Route path="/users" element={<UsersPage />} />
                  <Route path="/audit" element={<Audit />} />
                  <Route path="/settings" element={<Settings />} />

                  <Route path="/reports/dashboard" element={<Dashboard />} />
                  <Route path="/reports/headcount" element={<HeadcountReport />} />
                  <Route path="/reports/hiring-funnel" element={<HiringFunnel />} />
                  <Route path="/reports/performance" element={<PerformanceReport />} />
                  <Route path="/reports/learning" element={<LearningReport />} />

                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </RequireAuth>
            } />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" toastOptions={{ duration: 3000 }} />
        </PortalAuthProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
