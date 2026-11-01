// Every role a login can hold — mirrors CustomUser.ROLE_CHOICES on the backend.
export const ALL_ROLES = [
  { code: 'SYSTEM_ADMIN',       label: 'System Admin' },
  { code: 'HR_ADMIN',           label: 'HR Admin' },
  { code: 'HR_MAKER',           label: 'HR Maker' },
  { code: 'HR_CHECKER',         label: 'HR Checker' },
  { code: 'HIRING_MANAGER',     label: 'Hiring Manager' },
  { code: 'INTERVIEWER',        label: 'Interviewer' },
  { code: 'RECRUITER',          label: 'Recruiter' },
  { code: 'FINANCE_CHECKER',    label: 'Finance Checker' },
  { code: 'TALENT_COMMITTEE',   label: 'Talent Committee' },
  { code: 'HR_PERFORMANCE',     label: 'HR Performance' },
  { code: 'LD_OFFICER',         label: 'L&D Officer' },
  { code: 'LD_CHECKER',         label: 'L&D Checker' },
  { code: 'PAYROLL_OFFICER',    label: 'Payroll Officer' },
  { code: 'BENEFITS_ADMIN',     label: 'Benefits Admin' },
  { code: 'HSE_OFFICER',        label: 'HSE Officer' },
  { code: 'SERVICE_DESK_AGENT', label: 'Service Desk Agent' },
  { code: 'ER_OFFICER',         label: 'ER Officer' },
  { code: 'MANAGER',            label: 'Manager' },
  { code: 'EMPLOYEE',           label: 'Employee' },
  { code: 'APPLICANT',          label: 'Applicant' },
]

/** Roles that only these callers may grant (enforced again by the backend). */
const ROLE_GRANTERS: Record<string, string[]> = {
  SYSTEM_ADMIN: ['SYSTEM_ADMIN'],
  HR_ADMIN: ['HR_ADMIN', 'SYSTEM_ADMIN'],
}

/** The roles `userRoles` may hand out to staff — applicants never get a staff login. */
export function grantableStaffRoles(userRoles: string[]) {
  return ALL_ROLES.filter(r =>
    r.code !== 'APPLICANT' && (!ROLE_GRANTERS[r.code] || ROLE_GRANTERS[r.code].some(g => userRoles.includes(g))),
  )
}
