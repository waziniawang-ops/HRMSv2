# HRMSv2 — Role Access Manual

All demo accounts use password: **Demo1234!**

---

## Role Summary

| Role | Demo Account | Module Access |
|------|-------------|---------------|
| System Admin | `sysadmin` | Everything |
| HR Admin | `hr_norziah` | Everything |
| HR Maker | `hr_fatimah` | Core HR, Recruitment, Onboarding, Workforce, Succession, Workflow, Reports |
| HR Checker | `hr_ahmad` | Core HR (approve), Recruitment (approve), Workforce (approve), Performance (approve outcomes), Workflow |
| Recruiter | `rec_shafiq` | Recruitment (full), Onboarding (read), Workflow |
| Hiring Manager | `mgr_dinesh` | Recruitment (read), Workforce (team), Workflow |
| Interviewer | `int_liwei` | Recruitment interviews + feedback only |
| Finance Checker | `fin_rajan` | Recruitment offers (read), Workflow |
| Talent Committee | `talent_siti` | Succession (full), Reports (succession risk) |
| HR Performance | `perf_azlan` | Performance (full), Reports (performance) |
| LD Officer | `ld_nurul` | Learning (full), Reports (learning compliance) |
| LD Checker | `ldc_hassan` | Learning (publish courses only) |
| Employee | `emp_ali` | Own leave/OT/attendance, own goals/reviews, own learning |

---

## 1. System Admin (`sysadmin`)

Full unrestricted access to every module and every action.

### What they can do:
| Module | Actions |
|--------|---------|
| **Users** | Create, Read, Update, Delete all user accounts. Assign any role. |
| **Workflow Rules** | Create, Read, Update, Delete workflow routing rules. |
| **Core HR** | Full CRUD on Org Units, Positions, Employees, Grades, Jobs, Cost Centers. |
| **Recruitment** | Full access to all requisitions, postings, applicants, applications, interviews, offers. |
| **Onboarding** | Full access to all cases, tasks, documents. |
| **Workforce** | Full access to leave types, leave requests, attendance, overtime, transfers, separations. |
| **Succession** | Full access to plans, nominations, talent pools, talent profiles, development plans. |
| **Performance** | Full access to cycles, competencies, goal plans, reviews, calibration, outcomes, PIPs. |
| **Learning** | Full access to courses, learning paths, assignments, completions, skill gaps. |
| **Workflow** | View all requests. Approve/reject any step. |
| **Reports** | All dashboards and reports. |
| **Audit** | View audit trail. |
| **Notifications** | Own notifications. |

---

## 2. HR Admin (`hr_norziah`)

Same access as System Admin except cannot configure workflow rules or manage system settings.

### What they can do:
| Module | Actions |
|--------|---------|
| **Users** | Create, Read, Update, Delete all user accounts. Assign any role. |
| **Core HR** | Full CRUD on Org Units, Positions, Employees, Grades, Jobs, Cost Centers. |
| **Recruitment** | Full access to all recruitment records. |
| **Onboarding** | Full access to all cases and tasks. |
| **Workforce** | Full access to all workforce records. Approve/reject leave, OT, transfers. |
| **Succession** | Full access to plans, pools, profiles, nominations. |
| **Performance** | Full access to cycles, goals, reviews, calibration, outcomes. |
| **Learning** | Full access to courses, assignments, completions. |
| **Workflow** | View all requests. Approve/reject assigned steps. |
| **Reports** | All dashboards and reports. |
| **Notifications** | Own notifications. |

> **Note:** HR Admin cannot access Workflow Rules configuration (System Admin only).

---

## 3. HR Maker (`hr_fatimah`)

Creates and initiates HR transactions. Cannot approve their own submissions.

### What they can do:
| Module | Actions |
|--------|---------|
| **Core HR — Org Units** | Read only |
| **Core HR — Positions** | Create, Read, Update. Submit position for approval. Cannot approve. |
| **Core HR — Employees** | Read, Update employee records. |
| **Core HR — Grades/Jobs** | Read only |
| **Recruitment — Requisitions** | **Create**, Read, Update, Submit for approval. Cannot approve. |
| **Recruitment — Postings** | Read only |
| **Recruitment — Applicants/Applications** | Read only |
| **Recruitment — Interviews** | Read only |
| **Recruitment — Offers** | Read only |
| **Onboarding — Cases** | Create, Read, Update cases. Submit case for HR review. |
| **Onboarding — Tasks** | Read, mark tasks complete, verify tasks. |
| **Workforce — Leave Types** | Create, Read, Update, Delete |
| **Workforce — Leave Requests** | Read all. Approve/Reject requests. |
| **Workforce — Attendance** | Read all. |
| **Workforce — Overtime** | Read all. Approve OT requests. |
| **Workforce — Transfers** | Create, Read, Update. Cannot approve own transfers. |
| **Workforce — Workforce Plans** | Create, Read, Update. Submit plans for approval. |
| **Succession — Plans** | Create, Read, Update draft plans. Submit for review. |
| **Succession — Talent Pools** | Read only |
| **Succession — Talent Profiles** | Read only |
| **Learning — Assignments** | Create, Read, Update, Delete |
| **Learning — Skill Gaps** | Create, Read, Update, Delete |
| **Workflow — Requests** | View all workflow requests. |
| **Reports** | HR Dashboard, Headcount, Hiring Funnel, Attrition |
| **Notifications** | Own notifications. |

> **Maker-Checker Rule:** HR Maker submits transactions but cannot approve them. An HR Checker or HR Admin must approve.

---

## 4. HR Checker (`hr_ahmad`)

Reviews and approves submissions made by HR Makers.

### What they can do:
| Module | Actions |
|--------|---------|
| **Core HR — Org Units** | Read only |
| **Core HR — Positions** | Read. **Approve or Reject** submitted positions. |
| **Core HR — Employees** | Read all records. |
| **Core HR — Grades/Jobs** | Read only |
| **Recruitment — Requisitions** | Read. **Approve or Reject** submitted requisitions. |
| **Recruitment — Postings** | Read. **Approve and Publish** or Reject submitted postings. |
| **Recruitment — Applicants/Applications** | Read only |
| **Recruitment — Interviews** | Read only |
| **Recruitment — Offers** | Read. **Approve or Reject** submitted offers. |
| **Onboarding — Cases** | Read. **Complete and Convert** approved cases to Employee records. |
| **Onboarding — Tasks** | Read. Verify tasks. |
| **Workforce — Leave Requests** | Read all. **Approve/Reject** |
| **Workforce — Attendance** | Read all |
| **Workforce — Overtime** | Read all. Approve OT. |
| **Workforce — Transfers** | Read. **Approve/Reject** and **Complete** transfers. |
| **Workforce — Separations** | Read. **Approve** and **Complete** separations. |
| **Workforce — Workforce Plans** | Read. **Approve** submitted plans. |
| **Performance — Outcomes** | Read. **Approve** final performance outcomes. |
| **Succession** | Read only |
| **Workflow — Requests** | View all requests. Approve/Reject assigned steps. |
| **Reports** | HR Dashboard, Headcount, Hiring Funnel, Attrition |
| **Notifications** | Own notifications. |

> **Checker cannot create** new transactions — only review and approve/reject what Makers have submitted.

---

## 5. Recruiter (`rec_shafiq`)

Manages the full recruitment pipeline from posting to offer.

### What they can do:
| Module | Actions |
|--------|---------|
| **Recruitment — Requisitions** | Read only (cannot create — that's HR Maker) |
| **Recruitment — Job Postings** | **Create**, Read, Update, Delete. Submit posting for approval. |
| **Recruitment — Applicants** | Read all applicant profiles. |
| **Recruitment — Applications** | Read all. **Shortlist** or **Reject** applications. |
| **Recruitment — Interviews** | **Create**, Read, Update, Delete interviews. Mark interviews complete. |
| **Recruitment — Interview Feedback** | Read feedback submitted by interviewers. |
| **Recruitment — Offers** | **Create**, Read, Update. Submit offer for approval. **Send** approved offers to candidates. |
| **Onboarding — Cases** | Read only |
| **Workflow — Requests** | View own workflow requests. |
| **Notifications** | Own notifications. |

> **Recruiter cannot approve** job postings or offers — those go to HR Checker.

---

## 6. Hiring Manager (`mgr_dinesh`)

Reviews candidates for positions they manage. Has team workforce visibility.

### What they can do:
| Module | Actions |
|--------|---------|
| **Recruitment — Requisitions** | Read only |
| **Recruitment — Job Postings** | Read only |
| **Recruitment — Applications** | Read only |
| **Recruitment — Interviews** | Read only. Submit interview feedback. |
| **Recruitment — Offers** | Read only |
| **Workforce — Leave Requests** | Read all (team visibility) |
| **Workforce — Attendance** | Read all (team visibility) |
| **Workforce — Overtime** | Read all (team visibility) |
| **Workforce — Transfers** | Read only |
| **Succession — Talent Profiles** | Read (their people) |
| **Succession — Nominations** | Create successor nominations for their org. |
| **Performance — Goal Plans** | Read (team) |
| **Performance — Reviews** | Read (team) |
| **Workflow — Requests** | View own requests. Approve assigned team workflow steps. |
| **Notifications** | Own notifications. |

---

## 7. Interviewer (`int_liwei`)

Participates in interviews and submits structured feedback.

### What they can do:
| Module | Actions |
|--------|---------|
| **Recruitment — Interviews** | Read interviews they are part of. |
| **Recruitment — Interview Feedback** | **Create** and **Update** own feedback. |
| **Workflow — Requests** | View own requests. |
| **Notifications** | Own notifications. |

> Interviewers have no access to applicant personal data beyond what is in the interview record.

---

## 8. Finance Checker (`fin_rajan`)

Reviews compensation and budget elements in recruitment and approves finance workflow steps.

### What they can do:
| Module | Actions |
|--------|---------|
| **Recruitment — Offers** | Read (for budget/salary review) |
| **Workflow — Requests** | View own requests. **Approve/Reject** assigned finance workflow steps. |
| **Notifications** | Own notifications. |

> Finance Checker has no write access to HR records. Their role is purely approval of finance-tagged workflow steps.

---

## 9. Talent Committee (`talent_siti`)

Manages the succession planning process from nominations to final approval.

### What they can do:
| Module | Actions |
|--------|---------|
| **Succession — Plans** | Create, Read, Update. **Approve** submitted succession plans. |
| **Succession — Nominations** | Create, Read, Update, Delete successor nominations. |
| **Succession — Talent Pools** | Read, Update talent pools. |
| **Succession — Talent Profiles** | Read, Update talent profiles. View 9-box grid. View flight risk report. |
| **Workflow — Requests** | View own requests. Approve assigned committee workflow steps. |
| **Reports — Succession Risk** | View succession risk dashboard. |
| **Notifications** | Own notifications. |

---

## 10. HR Performance Officer (`perf_azlan`)

Manages the full performance management cycle.

### What they can do:
| Module | Actions |
|--------|---------|
| **Performance — Cycles** | **Create**, Read, Update. **Advance cycle status** (Draft → Active → Goal Setting → Mid-Year → Year-End → Calibration → Completed → Closed). |
| **Performance — Competency Models** | Create, Read, Update, Delete. |
| **Performance — Competencies** | Create, Read, Update, Delete. |
| **Performance — Goal Plans** | Read all. **Approve** submitted goal plans. |
| **Performance — Goals** | Read all. |
| **Performance — Reviews** | Read all. |
| **Performance — Calibration Sessions** | **Create**, Read, Update. **Mark Complete**. |
| **Performance — Calibrated Ratings** | Create, Read, Update, Delete. |
| **Performance — Final Outcomes** | **Create**, Read, Update. |
| **Performance — Improvement Plans (PIPs)** | Create, Read, Update, Delete. |
| **Workflow — Requests** | View own requests. |
| **Reports — Performance Distribution** | View performance distribution report. |
| **Notifications** | Own notifications. |

---

## 11. L&D Officer (`ld_nurul`)

Creates and manages the full learning catalogue and assignments.

### What they can do:
| Module | Actions |
|--------|---------|
| **Learning — Courses** | **Create**, Read, Update. **Archive** courses. Cannot publish (that is LD Checker). |
| **Learning — Learning Paths** | Create, Read, Update, Delete. |
| **Learning — Assignment Rules** | Create, Read, Update, Delete. |
| **Learning — Assignments** | Read all assignments. |
| **Learning — Course Sessions** | **Create**, Read, Update. **Mark session complete**. |
| **Learning — Enrollments** | Read all. **Mark attendance**. |
| **Learning — Completions** | **Create**, Read (record course completions, auto-generates certificate). |
| **Learning — Training Requests** | Read all. **Approve** or **Reject** training requests. |
| **Learning — Skill Gaps** | Read all. **Close** skill gaps. |
| **Workflow — Requests** | View own requests. |
| **Reports — Learning Compliance** | View learning compliance report. |
| **Notifications** | Own notifications. |

---

## 12. L&D Checker (`ldc_hassan`)

Reviews and publishes courses created by L&D Officers.

### What they can do:
| Module | Actions |
|--------|---------|
| **Learning — Courses** | Read all. **Publish** draft courses (approves and makes live). |
| **Learning — Learning Paths** | Read only |
| **Learning — Assignments** | Read only |
| **Learning — Completions** | Read only |
| **Workflow — Requests** | View own requests. |
| **Notifications** | Own notifications. |

> **Checker cannot create** courses — only publish what the L&D Officer has prepared.

---

## 13. Manager (`mgr_dinesh` is Hiring Manager — there is no pure MANAGER demo user)

A Manager has team-level read access and can nominate successors.

### What they can do:
| Module | Actions |
|--------|---------|
| **Workforce — Leave Requests** | Read (own team) |
| **Workforce — Attendance** | Read (own team) |
| **Workforce — Overtime** | Read (own team) |
| **Workforce — Transfers** | Read only |
| **Succession — Plans** | Read only |
| **Succession — Nominations** | **Create** successor nominations for positions in their org. |
| **Succession — Talent Profiles** | Read (their people) |
| **Performance — Goal Plans** | Read (own team) |
| **Performance — Reviews** | Read (own team) |
| **Learning — Assignments** | Read (own team) |
| **Workflow — Requests** | View own requests. Approve assigned team workflow steps. |
| **Notifications** | Own notifications. |

---

## 14. Employee (`emp_ali`)

Self-service access to own HR data.

### What they can do:
| Module | Actions |
|--------|---------|
| **Workforce — Leave Requests** | **Create** own requests. Submit for approval. View own request status. |
| **Workforce — Attendance** | **Create** own attendance log entries. View own attendance history. |
| **Workforce — Overtime** | **Create** own OT requests. View own request status. |
| **Performance — Goal Plans** | **Create** own goal plans. Submit for approval. View own plans. |
| **Performance — Goals** | **Create** own goals within their goal plan. Update progress. |
| **Performance — Reviews** | View own reviews. **Submit** own self-review form. **Acknowledge** completed reviews. |
| **Learning — Assignments** | View own assignments. **Start** assigned courses. |
| **Learning — Enrollments** | **Create** own session enrollments. |
| **Learning — Assessments** | **Submit** course assessments. |
| **Learning — Training Requests** | **Create** own training requests. |
| **Workflow — Requests** | View own submitted workflow requests and their status. |
| **Notifications** | Own notifications. Mark as read. |

> **Employees cannot see** other employees' leave, attendance, OT, goals, or reviews — all lists are scoped to their own records only.

---

## 15. Applicant (External — `appl_sara`, `appl_arif`, `appl_priya`)

External portal access only. Cannot access any internal pages.

### What they can do:
| Module | Actions |
|--------|---------|
| **Public Job Board** | Browse all publicly posted jobs (no login required). |
| **Applicant Profile** | **Create and update** own profile (education, experience, skills). |
| **Applications** | **Submit** applications to open postings. View own application status. **Withdraw** own application. |
| **Offers** | **Accept** or **Decline** offers sent to them. |

> Applicants log in at the external portal (separate from the internal HRMS). They have no access to any internal navigation or HR data.

---

## CRUD Matrix Quick Reference

| Action | SYS_ADMIN | HR_ADMIN | HR_MAKER | HR_CHECKER | RECRUITER | HIRING_MGR | INTERVIEWER | FINANCE | TALENT_CMT | HR_PERF | LD_OFFICER | LD_CHECKER | MANAGER | EMPLOYEE |
|--------|-----------|----------|----------|------------|-----------|------------|-------------|---------|------------|---------|------------|------------|---------|----------|
| Manage Users | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Workflow Rules | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Create Positions | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Approve Positions | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Create Requisition | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Approve Requisition | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage Job Postings | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Approve Postings | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Schedule Interviews | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Submit Interview Feedback | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Create Offers | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Approve Offers | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage Onboarding | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Convert Onboarding→Employee | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Submit Leave Request | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Approve Leave | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Submit OT Request | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Approve OT | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Log Attendance | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Initiate Transfer | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Approve Transfer | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage Succession Plans | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Approve Succession Plans | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Nominate Successors | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Manage Perf Cycles | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Create/Submit Goal Plan | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Approve Goal Plan | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Submit Review Form | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Approve Final Outcome | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Create Courses | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Publish Courses | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Submit Training Request | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Approve Training Request | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| View HR Dashboard | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| View Perf Reports | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View Learning Reports | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| View Succession Risk | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## Key Business Rules

1. **Maker-Checker Segregation**: HR Maker submits transactions. HR Checker approves them. The same person cannot submit and approve the same record.

2. **Data Isolation**: Employees only see their own leave, attendance, overtime, goal plans, and reviews. HR Staff see all records.

3. **Workflow Engine**: Position approvals, requisitions, job postings, and offers all flow through the workflow engine. Records must be submitted before they can be approved.

4. **Onboarding → Employee Conversion**: Completing an onboarding case automatically creates an Employee record in the system (HR Checker only).

5. **Course Publication**: L&D Officer creates courses. L&D Checker publishes them. A course must be published before employees can be enrolled.

6. **Succession Approval**: HR Maker or HR Staff creates succession plan drafts. The Talent Committee reviews and approves them.

7. **Performance Cycle Flow**: HR Performance Officer advances the cycle through stages: Draft → Active → Goal Setting → Mid-Year → Year-End → Calibration → Completed → Closed.
