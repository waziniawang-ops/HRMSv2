"""Full end-to-end HRMS demo seed — uses exact model field names."""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.utils import timezone
from datetime import date, timedelta, datetime
from decimal import Decimal

print("\n" + "="*60)
print("  HRMSv2 END-TO-END DEMO SEED")
print("="*60)

# ── helpers ──────────────────────────────────────────────────
def gc(model, lookup, **defaults):
    obj, created = model.objects.get_or_create(**lookup, defaults=defaults)
    return obj, created

# ── 1. USERS ─────────────────────────────────────────────────
print("\n[1/9] Creating users (13 roles)...")
from apps.accounts.models import CustomUser

def make_user(uname, role, utype='INTERNAL', fname='', lname=''):
    u, _ = CustomUser.objects.get_or_create(username=uname, defaults={
        'email': f'{uname}@hrms.demo', 'role': role, 'user_type': utype,
        'first_name': fname or uname, 'last_name': lname,
    })
    if not u.has_usable_password():
        u.set_password('Demo1234!'); u.save()
    return u

admin_u    = make_user('sysadmin',     'SYSTEM_ADMIN',     fname='Syed', lname='Admin')
hr_maker   = make_user('hr_fatimah',   'HR_MAKER',         fname='Fatimah', lname='Hassan')
hr_checker = make_user('hr_ahmad',     'HR_CHECKER',       fname='Ahmad', lname='Razali')
hr_admin_u = make_user('hr_norziah',   'HR_ADMIN',         fname='Norziah', lname='Kamal')
recruiter  = make_user('rec_shafiq',   'RECRUITER',        fname='Shafiq', lname='Idris')
hiring_mgr = make_user('mgr_dinesh',   'HIRING_MANAGER',   fname='Dinesh', lname='Raj')
interview_u= make_user('int_liwei',    'INTERVIEWER',      fname='Li', lname='Wei')
finance_u  = make_user('fin_rajan',    'FINANCE_CHECKER',  fname='Rajan', lname='Subramaniam')
ld_u       = make_user('ld_nurul',     'LD_OFFICER',       fname='Nurul', lname='Aina')
perf_u     = make_user('perf_azlan',   'HR_PERFORMANCE',   fname='Azlan', lname='Yusof')
talent_u   = make_user('talent_siti',  'TALENT_COMMITTEE', fname='Siti', lname='Rohani')
emp_user   = make_user('emp_ali',      'EMPLOYEE',         fname='Ali', lname='bin Hamid')
ld_checker = make_user('ldc_hassan',   'LD_CHECKER',       fname='Hassan', lname='Osman')

# Make sysadmin a real superuser
sa = CustomUser.objects.get(username='sysadmin')
sa.is_staff = True; sa.is_superuser = True; sa.role = 'SYSTEM_ADMIN'
sa.set_password('Demo1234!'); sa.save()

print(f"  ✓ {CustomUser.objects.count()} users — roles: {', '.join(sorted(set(u.role for u in CustomUser.objects.all())))}")

# ── 2. ORG STRUCTURE ─────────────────────────────────────────
print("\n[2/9] Building org structure (Nexus Corp Berhad)...")
from apps.core_hr.models import OrgUnit, CostCenter, JobFamily, Job, Grade

hq,_       = gc(OrgUnit, {'code':'HQ'},    name='Nexus Corp Berhad',      type='COMPANY',    status='ACTIVE')
it_div,_   = gc(OrgUnit, {'code':'IT'},    name='Information Technology', type='DIVISION',   status='ACTIVE', parent=hq)
hr_div,_   = gc(OrgUnit, {'code':'HR'},    name='Human Resources',        type='DIVISION',   status='ACTIVE', parent=hq)
fin_div,_  = gc(OrgUnit, {'code':'FIN'},   name='Finance',                type='DIVISION',   status='ACTIVE', parent=hq)
sw_dept,_  = gc(OrgUnit, {'code':'SWE'},   name='Software Engineering',   type='DEPARTMENT', status='ACTIVE', parent=it_div)
infra,_    = gc(OrgUnit, {'code':'INFRA'}, name='Infrastructure & Cloud', type='DEPARTMENT', status='ACTIVE', parent=it_div)

cc_it,_ = gc(CostCenter, {'code':'CC-IT-001'}, name='IT Cost Centre',  org_unit=sw_dept)
cc_hr,_ = gc(CostCenter, {'code':'CC-HR-001'}, name='HR Cost Centre',  org_unit=hr_div)

jf_tech,_ = gc(JobFamily, {'code':'TECH'},  name='Technology')
jf_hr,_   = gc(JobFamily, {'code':'HRMGT'}, name='Human Resource Management')

j_swe,_    = gc(Job, {'job_code':'SWE-SNR'},   job_title='Senior Software Engineer', job_family=jf_tech)
j_pm,_     = gc(Job, {'job_code':'PM-001'},    job_title='Product Manager',           job_family=jf_tech)
j_devops,_ = gc(Job, {'job_code':'DEVOPS-001'},job_title='DevOps Engineer',           job_family=jf_tech)
j_hr,_     = gc(Job, {'job_code':'HR-EXEC'},   job_title='HR Executive',              job_family=jf_hr)

g3,_ = gc(Grade, {'grade_code':'G3'}, grade_name='Executive', level=3, pay_band_min=Decimal('3500'), pay_band_max=Decimal('5500'))
g5,_ = gc(Grade, {'grade_code':'G5'}, grade_name='Senior',    level=5, pay_band_min=Decimal('5000'), pay_band_max=Decimal('9000'))
g7,_ = gc(Grade, {'grade_code':'G7'}, grade_name='Manager',   level=7, pay_band_min=Decimal('8000'), pay_band_max=Decimal('14000'))

print(f"  ✓ {OrgUnit.objects.count()} org units | {Grade.objects.count()} grades | {Job.objects.count()} jobs")

# ── 3. POSITIONS ─────────────────────────────────────────────
print("\n[3/9] Creating positions (pre-approved)...")
from apps.core_hr.models import Position

def make_pos(code, title, job, ou, cc, grade, critical=False):
    p,_ = gc(Position, {'position_code': code},
             title=title, job=job, org_unit=ou, cost_center=cc, grade=grade,
             is_critical=critical, status='APPROVED', created_by=hr_maker)
    return p

pos_swe1   = make_pos('POS-SWE-001','Senior Software Engineer (Backend)',   j_swe,   sw_dept, cc_it, g5)
pos_swe2   = make_pos('POS-SWE-002','Senior Software Engineer (Frontend)',  j_swe,   sw_dept, cc_it, g5)
pos_pm     = make_pos('POS-PM-001', 'Product Manager – Digital',            j_pm,    sw_dept, cc_it, g7, critical=True)
pos_devops = make_pos('POS-DEV-001','DevOps Engineer',                      j_devops,infra,   cc_it, g5)
pos_hr     = make_pos('POS-HR-001', 'HR Executive',                         j_hr,    hr_div,  cc_hr, g3)

print(f"  ✓ {Position.objects.count()} positions | {Position.objects.filter(is_critical=True).count()} critical")

# ── 4. EMPLOYEES ─────────────────────────────────────────────
print("\n[4/9] Creating existing employees...")
from apps.core_hr.models import Person, Employee

def make_emp(user, emp_no, pos, grade, days_ago=365):
    person,_ = gc(Person, {'email': user.email},
                  legal_name=f'{user.first_name} {user.last_name}'.strip(),
                  user=user, phone='+601112345678', nationality='Malaysian', gender='M')
    emp,_ = gc(Employee, {'employee_number': emp_no},
               person=person, hire_date=date.today()-timedelta(days=days_ago),
               employment_status='ACTIVE', position=pos, org_unit=pos.org_unit, grade=grade)
    pos.status='OCCUPIED'; pos.incumbent_employee=emp; pos.save()
    return emp

emp_ali = make_emp(emp_user,   'EMP-000001', pos_swe1, g5, days_ago=820)
emp_pm  = make_emp(hiring_mgr, 'EMP-000002', pos_pm,   g7, days_ago=1200)
emp_hr  = make_emp(hr_maker,   'EMP-000003', pos_hr,   g3, days_ago=950)

print(f"  ✓ {Employee.objects.count()} employees in the system")

# ── 5. RECRUITMENT FLOW ──────────────────────────────────────
print("\n[5/9] Running full recruitment cycle...")
from apps.recruitment.models import (
    JobRequisition, JobPosting, Applicant, ApplicantProfile,
    Application, Interview, InterviewFeedback, Offer
)

# pos_swe2 is the vacancy we're filling
pos_swe2.status = 'VACANT'; pos_swe2.incumbent_employee = None; pos_swe2.save()

req,_ = gc(JobRequisition, {'position': pos_swe2},
           hiring_reason='BACKFILL',
           justification='Frontend capacity needed for Platform v3.0 launch.',
           requested_by=hr_maker,
           headcount=1,
           target_start_date=date.today()+timedelta(days=45),
           status='APPROVED')
if not req.requisition_number:
    from django.utils import timezone as tz
    req.requisition_number = f"REQ-{tz.localdate().year}-{str(req.pk)[:8].upper()}"
    req.save()

print(f"  ✓ Requisition: {req.requisition_number} [{req.status}]")

posting,_ = gc(JobPosting, {'requisition': req},
               title='Senior Frontend Engineer',
               description='Join our product team to build high-performance web apps with React/TypeScript.',
               requirements='5+ yrs React, TypeScript, REST APIs. BSc Computer Science preferred.',
               visibility='EXTERNAL', status='POSTED',
               created_by=recruiter,
               opening_date=date.today()-timedelta(days=14),
               closing_date=date.today()+timedelta(days=16))
print(f"  ✓ Job Posting: '{posting.title}' | Visibility: {posting.visibility} | Status: {posting.status}")

# Three applicants — each needs a user account
applicants_data = [
    dict(email='sara.wml@email.com',   full_name='Sara Wong Mei Lin',   phone='+60111001', score=Decimal('88'), username='appl_sara'),
    dict(email='arif.zk@email.com',    full_name='Arif Zulkifli',       phone='+60111002', score=Decimal('72'), username='appl_arif'),
    dict(email='priya.ks@email.com',   full_name='Priya Krishnaswamy',  phone='+60111003', score=Decimal('91'), username='appl_priya'),
]
apps_list = []
for d in applicants_data:
    fname, lname = d['full_name'].split(' ', 1)
    appl_user = make_user(d['username'], 'APPLICANT', utype='EXTERNAL', fname=fname, lname=lname)
    appl_user.email = d['email']; appl_user.save()
    appl,_ = gc(Applicant, {'email': d['email']},
                user=appl_user, full_name=d['full_name'], phone=d['phone'],
                profile_status='ACTIVE', consent_version='2.0')
    ApplicantProfile.objects.get_or_create(applicant=appl, defaults={
        'education':      [{'degree':'BSc Computer Science','institution':'UTM','year':2019}],
        'experience':     [{'company':'TechCo Sdn Bhd','role':'Frontend Developer','years':4}],
        'skills':         ['React','TypeScript','Node.js','GraphQL','AWS'],
    })
    app,_ = gc(Application, {'applicant': appl, 'job_posting': posting},
               stage='OFFER' if d['score']==91 else ('INTERVIEW' if d['score']>=80 else 'SCREENING'),
               score=d['score'])
    apps_list.append((appl, app, d['score']))

print(f"  ✓ {len(apps_list)} applications | shortlisted: {sum(1 for _,_,s in apps_list if s>=80)} | offered: {sum(1 for _,_,s in apps_list if s==91)}")

# Interview for top 2
for appl, app, score in [(a,ap,s) for a,ap,s in apps_list if s >= 80]:
    ivw,c = gc(Interview, {'application': app},
               interview_type='VIDEO',
               scheduled_at=timezone.now()-timedelta(days=5),
               location_or_link='Google Meet — meet.google.com/hrms',
               status='COMPLETED', round_number=1, created_by=recruiter)
    if c:
        ivw.panel.set([interview_u])
    InterviewFeedback.objects.get_or_create(
        interview=ivw, interviewer=interview_u,
        defaults={
            'overall_score': score,
            'section_scores': {'technical': float(score-3), 'communication': float(score+2), 'culture_fit': float(score)},
            'strengths': 'Strong React expertise. Clear communicator. Good system design awareness.',
            'areas_for_improvement': 'Can improve on backend integration patterns.',
            'recommendation': 'STRONG_YES' if score >= 90 else 'YES',
            'is_locked': True,
        }
    )

# Select Priya (score 91) and make her an offer
winner_appl = next(a for a,_,s in apps_list if s==91)
winner_app  = next(ap for _,ap,s in apps_list if s==91)

offer,_ = gc(Offer, {'application': winner_app},
             position=pos_swe2,
             grade=g5,
             basic_salary=Decimal('8500'),
             allowances={'housing': 500, 'transport': 300},
             total_package=Decimal('9300'),
             employment_type='PERMANENT',
             start_date=date.today()+timedelta(days=45),
             status='ACCEPTED',
             created_by=recruiter,
             expiry_date=date.today()+timedelta(days=14),
             accepted_at=timezone.now()-timedelta(days=1))
if not offer.offer_number:
    offer.offer_number = f"OFF-{timezone.localdate().year}-{str(offer.pk)[:8].upper()}"
    offer.save()

print(f"  ✓ Offer {offer.offer_number}: {winner_appl.full_name} | RM {offer.basic_salary:,.0f}/mo | {offer.status}")

# ── 6. ONBOARDING → EMPLOYEE ─────────────────────────────────
print("\n[6/9] Onboarding → converting to employee...")
from apps.onboarding.models import OnboardingCase, OnboardingTask

onb,_ = gc(OnboardingCase, {'offer': offer},
           target_start_date=offer.start_date,
           assigned_hr=hr_maker,
           status='COMPLETED',
           completed_at=timezone.now())

tasks_spec = [
    ('PERSONAL_INFO','Personal Information Verification',True,1),
    ('RESUME','Resume Verification',True,2),
    ('ACADEMIC_CERTS','Academic Certificates',True,3),
    ('BANK_DETAILS','Bank Account Details',True,4),
    ('EMERGENCY_CONTACT','Emergency Contact',True,5),
    ('CONTRACT_SIGNING','Employment Contract Signing',True,6),
    ('ACCESS_REQUEST','Access Provisioning Request',False,7),
    ('PAYROLL_SETUP','Payroll Setup',True,8),
]
for code, title, req_f, order in tasks_spec:
    t,_ = gc(OnboardingTask,
             {'onboarding_case': onb, 'task_code': code},
             title=title, is_required=req_f, order=order,
             status='COMPLETED', completed_by=hr_maker,
             completed_at=timezone.now()-timedelta(hours=3),
             hr_verified=True)
    if t.status != 'COMPLETED':
        t.status='COMPLETED'; t.completed_by=hr_maker
        t.completed_at=timezone.now()-timedelta(hours=3); t.hr_verified=True; t.save()

person_new,_ = gc(Person, {'email': winner_appl.email},
                  legal_name=winner_appl.full_name, phone=winner_appl.phone,
                  nationality='Malaysian', gender='F')

last_emp = Employee.objects.order_by('-created_at').first()
next_no  = int(last_emp.employee_number.split('-')[-1]) + 1 if last_emp else 4
new_emp,emp_created = gc(Employee, {'person': person_new},
                         employee_number=f'EMP-{next_no:06d}',
                         hire_date=offer.start_date,
                         employment_status='PROBATION',
                         position=pos_swe2, org_unit=pos_swe2.org_unit, grade=g5,
                         source_onboarding=onb)

pos_swe2.status='OCCUPIED'; pos_swe2.incumbent_employee=new_emp; pos_swe2.save()
onb.candidate_person=person_new; onb.save()

print(f"  ✓ Employee: {new_emp.employee_number} — {person_new.legal_name}")
print(f"  ✓ Position: {pos_swe2.title} → OCCUPIED")
print(f"  ✓ Onboarding tasks: {onb.completion_percentage}% | {onb.status}")

# ── 7. WORKFORCE ─────────────────────────────────────────────
print("\n[7/9] Workforce: leave, attendance, overtime, transfer...")
from apps.workforce.models import (
    LeaveType, LeaveBalance, LeaveRequest,
    AttendanceLog, OvertimeRequest, Transfer
)

annual,_ = gc(LeaveType, {'code':'AL'}, name='Annual Leave',   days_per_year=Decimal('20'), is_paid=True)
mc_lt,_  = gc(LeaveType, {'code':'MC'}, name='Medical Leave',  days_per_year=Decimal('14'), is_paid=True)
mat_lt,_ = gc(LeaveType, {'code':'ML'}, name='Maternity Leave',days_per_year=Decimal('98'), is_paid=True)

yr = date.today().year
for emp in [emp_ali, emp_pm, emp_hr, new_emp]:
    gc(LeaveBalance,{'employee':emp,'leave_type':annual,'year':yr},
       entitled_days=Decimal('20'), used_days=Decimal('0'))
    gc(LeaveBalance,{'employee':emp,'leave_type':mc_lt,'year':yr},
       entitled_days=Decimal('14'), used_days=Decimal('0'))

lr,_ = gc(LeaveRequest,
          {'employee':emp_ali,'leave_type':annual,
           'start_date':date.today()+timedelta(days=7)},
          end_date=date.today()+timedelta(days=9),
          days_requested=Decimal('3'),
          reason='Family vacation to Langkawi',
          status='APPROVED',
          reviewed_by=hr_maker,
          reviewed_at=timezone.now()-timedelta(hours=2))
bal,_ = LeaveBalance.objects.get_or_create(employee=emp_ali,leave_type=annual,year=yr,
    defaults={'entitled_days':Decimal('20'),'used_days':Decimal('0')})
if bal.used_days == 0: bal.used_days=Decimal('3'); bal.save()

# 5 days attendance for emp_ali
for i in range(1,6):
    day = date.today()-timedelta(days=i)
    if day.weekday()<5:
        AttendanceLog.objects.get_or_create(employee=emp_ali, date=day, defaults={
            'clock_in':  timezone.make_aware(datetime.combine(day,datetime.min.time().replace(hour=8,minute=45))),
            'clock_out': timezone.make_aware(datetime.combine(day,datetime.min.time().replace(hour=17,minute=30))),
            'hours_worked': Decimal('8.75'), 'is_present': True,
            'is_late': (i==2), 'source': 'BIOMETRIC',
        })

ot,_ = gc(OvertimeRequest,
          {'employee':emp_ali,'date':date.today()-timedelta(days=3)},
          hours_requested=Decimal('3'), hours_approved=Decimal('3'),
          reason='Critical production release deployment',
          status='APPROVED', approved_by=hiring_mgr,
          approved_at=timezone.now()-timedelta(days=2))

# Transfer emp_ali from Backend to DevOps team (pending approval)
pos_devops.status = 'VACANT'; pos_devops.save()
xfer,_ = gc(Transfer,
            {'employee':emp_ali,'from_position':pos_swe1,'to_position':pos_devops},
            movement_type='LATERAL',
            from_grade=g5, to_grade=g5,
            effective_date=date.today()+timedelta(days=30),
            reason='Ali requested move to DevOps to broaden cloud infrastructure expertise.',
            status='APPROVED',
            initiated_by=hr_maker, approved_by=hr_checker,
            approved_at=timezone.now()-timedelta(hours=1))

print(f"  ✓ Leave: {lr.employee.person.legal_name} — {lr.days_requested}d {annual.name} [{lr.status}]")
print(f"  ✓ Attendance: {AttendanceLog.objects.count()} logs")
print(f"  ✓ OT: {ot.hours_approved}h on {ot.date} [{ot.status}]")
print(f"  ✓ Transfer: {xfer.employee.person.legal_name} → {pos_devops.title} [{xfer.status}]")

# ── 8. PERFORMANCE ───────────────────────────────────────────
print("\n[8/9] Performance management: cycle, goals, reviews, outcomes...")
from apps.performance.models import (
    PerformanceCycle, CompetencyModel, Competency,
    GoalPlan, Goal, ReviewForm, FinalOutcome
)

cycle,_ = gc(PerformanceCycle, {'name':'FY2026 Annual Performance Review'},
             cycle_year=2026, status='YEAR_END',
             goal_setting_start=date(2026,1,1), goal_setting_end=date(2026,1,31),
             year_end_start=date(2026,11,1),    year_end_end=date(2026,11,30))

cm,_ = gc(CompetencyModel, {'name':'Core Engineering Competencies'},
          description='Applied to all Engineering roles.', is_active=True)
for cname, wt in [('Technical Excellence','2.0'),('Problem Solving','1.5'),('Delivery','1.5'),('Collaboration','1.0')]:
    gc(Competency, {'model':cm,'name':cname}, max_level=5, weight=Decimal(wt))

gp,_ = gc(GoalPlan, {'employee':emp_ali,'cycle':cycle},
          status='HR_APPROVED', overall_weight_total=Decimal('5.0'))

for gtitle, cat, wt, tgt in [
    ('Deliver Platform v3.0 — on-time & on-budget', 'KPI',         '2.0', '100% delivery by Q3'),
    ('Reduce API P95 latency to <150ms',             'KPI',         '1.5', 'P95 latency <150ms'),
    ('Achieve AWS Solutions Architect certification', 'DEVELOPMENT','0.5', 'Certified by Q3 2026'),
    ('Mentor 2 junior engineers',                    'BEHAVIORAL',  '1.0', '2 mentees progressing'),
]:
    gc(Goal, {'goal_plan':gp,'title':gtitle},
       category=cat, weight=Decimal(wt), target_value=tgt,
       status='COMPLETED', completion_percentage=100)

# Self + Manager reviews
self_rev,_ = gc(ReviewForm, {'cycle':cycle,'employee':emp_ali,'review_type':'SELF'},
                reviewer=emp_user, status='SUBMITTED',
                overall_rating=Decimal('4.2'),
                strengths_comments='Led Platform v3.0 end-to-end. API latency target exceeded.',
                improvement_comments='Can improve delegation. Tends to over-engineer.',
                overall_comments='Proud of the team impact this year.',
                submitted_at=timezone.now()-timedelta(days=7))

mgr_rev,_ = gc(ReviewForm, {'cycle':cycle,'employee':emp_ali,'review_type':'MANAGER'},
               reviewer=hiring_mgr, status='SUBMITTED',
               overall_rating=Decimal('4.5'),
               strengths_comments='Ali is our most reliable engineer. Delivery is impeccable.',
               improvement_comments='Encourage broader cross-functional collaboration.',
               overall_comments='Exceeds all expectations. Ready for G7 consideration.',
               submitted_at=timezone.now()-timedelta(days=4))

outcome,_ = gc(FinalOutcome, {'cycle':cycle,'employee':emp_ali},
               final_rating=Decimal('4.4'),
               outcome_label='EXCEEDS',
               eligible_for_increment=True, eligible_for_bonus=True,
               increment_percentage=Decimal('8.0'),
               bonus_amount=Decimal('5100.00'),
               notes='Exceptional year. Fast-track for Grade 7 promotion in H1 2027.',
               approved_by=hr_checker)

print(f"  ✓ Cycle: {cycle.name} [{cycle.status}]")
print(f"  ✓ Goals: {Goal.objects.count()} | Reviews: {ReviewForm.objects.count()}")
print(f"  ✓ Outcome: {emp_ali.person.legal_name} → {outcome.outcome_label} | Rating: {outcome.final_rating} | Bonus: RM{outcome.bonus_amount:,.0f} | Increment: {outcome.increment_percentage}%")

# ── 9. LEARNING ──────────────────────────────────────────────
print("\n[9/9] Learning management: courses, assignments, completions, certs...")
from apps.learning.models import (
    Course, LearningAssignment, CourseCompletion, Certificate, SkillGap
)

c_induct,_  = gc(Course, {'code':'INDUCTION-001'},
                 title='New Employee Induction Program', course_type='ELEARNING',
                 duration_hours=Decimal('4'), passing_score=80, is_mandatory=True,
                 status='PUBLISHED', created_by=ld_u)
c_aws,_     = gc(Course, {'code':'AWS-SAA-001'},
                 title='AWS Solutions Architect Associate Prep', course_type='VIRTUAL',
                 duration_hours=Decimal('40'), passing_score=72, is_mandatory=False,
                 status='PUBLISHED', created_by=ld_u)
c_react,_   = gc(Course, {'code':'REACT-ADV-001'},
                 title='Advanced React & TypeScript', course_type='ELEARNING',
                 duration_hours=Decimal('12'), passing_score=75, is_mandatory=False,
                 status='PUBLISHED', created_by=ld_u)
c_pdpa,_    = gc(Course, {'code':'PDPA-001'},
                 title='PDPA & Data Privacy Compliance', course_type='ELEARNING',
                 duration_hours=Decimal('2'), passing_score=85, is_mandatory=True,
                 status='PUBLISHED', created_by=ld_u)
c_agile,_   = gc(Course, {'code':'AGILE-001'},
                 title='Agile & Scrum Fundamentals', course_type='ELEARNING',
                 duration_hours=Decimal('6'), passing_score=75, is_mandatory=False,
                 status='PUBLISHED', created_by=ld_u)

for emp, course, st, due_offset in [
    (emp_ali,  c_aws,    'COMPLETED',    0),
    (emp_ali,  c_pdpa,   'COMPLETED',    0),
    (emp_ali,  c_react,  'COMPLETED',    0),
    (new_emp,  c_induct, 'IN_PROGRESS',  14),
    (new_emp,  c_pdpa,   'ASSIGNED',     30),
    (emp_pm,   c_pdpa,   'COMPLETED',    0),
    (emp_pm,   c_agile,  'COMPLETED',    0),
    (emp_hr,   c_pdpa,   'COMPLETED',    0),
]:
    gc(LearningAssignment,
       {'employee': emp, 'course': course},
       status=st, assigned_by=ld_u,
       due_date=date.today()+timedelta(days=due_offset) if due_offset else date.today()+timedelta(days=30))

# Completions + auto-issue certs
for emp, course, score in [
    (emp_ali, c_aws,   Decimal('88')),
    (emp_ali, c_pdpa,  Decimal('94')),
    (emp_ali, c_react, Decimal('82')),
    (emp_pm,  c_pdpa,  Decimal('90')),
    (emp_pm,  c_agile, Decimal('85')),
    (emp_hr,  c_pdpa,  Decimal('88')),
]:
    comp,cr = gc(CourseCompletion,
                 {'employee':emp,'course':course},
                 completed_at=timezone.now()-timedelta(days=30+int(score)%10),
                 score=score, hours_completed=course.duration_hours, is_valid=True)
    if cr:
        cnum = f"CERT-{course.code}-{emp.employee_number}-{date.today().year}"
        Certificate.objects.get_or_create(completion=comp, defaults={
            'certificate_number': cnum,
            'expiry_date': date.today()+timedelta(days=730),
        })

gc(SkillGap,
   {'employee':emp_ali,'skill_name':'Kubernetes & Container Orchestration'},
   required_level=4, current_level=2, recommended_course=c_aws, is_closed=False)
gc(SkillGap,
   {'employee':new_emp,'skill_name':'TypeScript Advanced Patterns'},
   required_level=3, current_level=1, recommended_course=c_react, is_closed=False)

print(f"  ✓ Courses: {Course.objects.filter(status='PUBLISHED').count()} published")
print(f"  ✓ Assignments: {LearningAssignment.objects.count()} | Completions: {CourseCompletion.objects.count()} | Certs: {Certificate.objects.count()}")

# ── 10. PAYROLL ───────────────────────────────────────────────
print("\n[10/21] Payroll: calendar, elements, profiles, run, payslips...")
from apps.payroll.models import (
    PayrollCalendar, PayrollElement, EmployeePayrollProfile,
    PayrollRun, PayslipLine, Payslip, PayrollAdjustment, PayrollGLPosting
)

cal_monthly,_ = gc(PayrollCalendar, {'code':'CAL-MY-001'},
    name='Nexus Corp Monthly Payroll', pay_group='MONTHLY',
    frequency='Processed on 25th of each month, paid on last working day', created_by=admin_u)

el_basic,_    = gc(PayrollElement, {'code':'BASIC'},      name='Basic Salary',        category='EARNING',    is_taxable=True,  is_pensionable=True,  formula={'type':'fixed','value':0}, display_order=1)
el_housing,_  = gc(PayrollElement, {'code':'ALLOW-HSNG'}, name='Housing Allowance',   category='ALLOWANCE',  is_taxable=False, is_pensionable=False, formula={'type':'fixed','value':500}, display_order=2)
el_transport,_= gc(PayrollElement, {'code':'ALLOW-TRNSP'},name='Transport Allowance', category='ALLOWANCE',  is_taxable=False, is_pensionable=False, formula={'type':'fixed','value':300}, display_order=3)
el_epf,_      = gc(PayrollElement, {'code':'DED-EPF-EE'}, name='EPF (Employee 9%)',   category='DEDUCTION',  is_taxable=False, is_pensionable=False, formula={'type':'percentage','value':9,'base':'BASIC'}, display_order=10)
el_socso,_    = gc(PayrollElement, {'code':'DED-SOCSO'},  name='SOCSO',               category='DEDUCTION',  is_taxable=False, is_pensionable=False, formula={'type':'fixed','value':69.05}, display_order=11)
el_bonus,_    = gc(PayrollElement, {'code':'BONUS-PERF'}, name='Performance Bonus',   category='EARNING',    is_taxable=True,  is_pensionable=True,  formula={'type':'fixed','value':0}, display_order=5)

# Payroll profiles — linked to employees and their real bank details
for emp, bank, acc in [
    (emp_ali,  'Maybank Berhad', '5621-1234-5678'),
    (emp_pm,   'CIMB Bank',      '8012-9876-5432'),
    (emp_hr,   'RHB Bank',       '2125-4567-8901'),
    (new_emp,  'Public Bank',    '3198-2345-6789'),
]:
    gc(EmployeePayrollProfile, {'employee': emp},
       calendar=cal_monthly, bank_name=bank, bank_account_number=acc,
       is_active=True, created_by=admin_u)

# May 2026 — CLOSED payroll run
period_start = date(2026, 5, 1)
period_end   = date(2026, 5, 31)
run_may,_ = gc(PayrollRun, {'calendar': cal_monthly, 'period_start': period_start},
    period_end=period_end, status='CLOSED',
    pay_date=date(2026, 5, 30),
    total_gross=Decimal('40900'), total_deductions=Decimal('4248.05'), total_net=Decimal('36651.95'),
    employee_count=4, processed_by=admin_u, approved_by=finance_u,
    approved_at=timezone.now()-timedelta(days=22),
    locked_at=timezone.now()-timedelta(days=22), created_by=admin_u)

# Salary data: (employee, basic, housing, transport) matching their grades
emp_salaries = [
    (emp_ali,  Decimal('8200'), Decimal('500'), Decimal('300')),
    (emp_pm,   Decimal('12500'),Decimal('800'), Decimal('500')),
    (emp_hr,   Decimal('4200'), Decimal('400'), Decimal('200')),
    (new_emp,  Decimal('8500'), Decimal('500'), Decimal('300')),
]
for emp, basic, housing, transport in emp_salaries:
    epf_ded  = (basic * Decimal('0.09')).quantize(Decimal('0.01'))
    gross    = basic + housing + transport
    ded_tot  = epf_ded + Decimal('69.05')
    net      = gross - ded_tot
    for el, amt, is_ded in [(el_basic, basic, False),(el_housing, housing, False),(el_transport, transport, False),(el_epf, -epf_ded, True),(el_socso, Decimal('-69.05'), True)]:
        gc(PayslipLine, {'payroll_run':run_may,'employee':emp,'element':el},
           amount=abs(amt), taxable_amount=basic if el==el_basic else Decimal('0'), is_deduction=is_ded)
    gc(Payslip, {'payroll_run':run_may,'employee':emp},
       basic_pay=basic, total_allowances=housing+transport,
       gross_pay=gross, total_deductions=ded_tot,
       tax_amount=Decimal('0'), pension_amount=epf_ded,
       net_pay=net, payslip_date=date(2026,5,30), is_locked=True,
       generated_at=timezone.now()-timedelta(days=22))

# Performance bonus adjustment for emp_ali (from FY2026 outcome: RM5100)
gc(PayrollAdjustment,
   {'payroll_run': run_may, 'employee': emp_ali, 'element': el_bonus},
   amount=Decimal('5100'), reason='FY2026 Annual Performance Bonus — EXCEEDS rating (4.4). Approved per HR-FIN-2026-001.',
   status='APPROVED', approved_by=finance_u, created_by=admin_u)

# GL posting for May run
gc(PayrollGLPosting, {'payroll_run': run_may, 'gl_account': '5100-001'},
   description='Payroll — Basic Salaries May 2026', amount=Decimal('33400'),
   cost_center=cc_it, posting_date=date(2026,5,30), is_posted=True,
   posted_at=timezone.now()-timedelta(days=22))
gc(PayrollGLPosting, {'payroll_run': run_may, 'gl_account': '5100-002'},
   description='Payroll — Allowances May 2026', amount=Decimal('3800'),
   cost_center=cc_it, posting_date=date(2026,5,30), is_posted=True,
   posted_at=timezone.now()-timedelta(days=22))

print(f"  ✓ Calendar: {cal_monthly.name}")
print(f"  ✓ {PayrollElement.objects.count()} payroll elements | Run: May 2026 [{run_may.status}]")
print(f"  ✓ {Payslip.objects.count()} payslips | {PayslipLine.objects.count()} lines | GL postings: {PayrollGLPosting.objects.count()}")

# ── 11. COMPENSATION ──────────────────────────────────────────
print("\n[11/21] Compensation: packages, grade bands, bonus cycle...")
from apps.compensation.models import (
    SalaryComponent, GradeBand, EmployeePackage,
    CompensationChange, BonusCycle, BonusAllocation
)

sc_basic,_  = gc(SalaryComponent, {'code':'SC-BASIC'},  name='Basic Salary',      category='BASIC',     is_pensionable=True,  is_taxable=True)
sc_house,_  = gc(SalaryComponent, {'code':'SC-HSNG'},   name='Housing Allowance', category='ALLOWANCE', is_pensionable=False, is_taxable=False)
sc_trnsp,_  = gc(SalaryComponent, {'code':'SC-TRNSP'},  name='Transport Allowance',category='ALLOWANCE',is_pensionable=False, is_taxable=False)

for grade, sc, mn, mid, mx in [
    (g3, sc_basic,  Decimal('3500'), Decimal('4000'), Decimal('5500')),
    (g3, sc_house,  Decimal('300'),  Decimal('400'),  Decimal('500')),
    (g3, sc_trnsp,  Decimal('150'),  Decimal('200'),  Decimal('300')),
    (g5, sc_basic,  Decimal('6500'), Decimal('7500'), Decimal('9500')),
    (g5, sc_house,  Decimal('400'),  Decimal('500'),  Decimal('700')),
    (g5, sc_trnsp,  Decimal('250'),  Decimal('300'),  Decimal('400')),
    (g7, sc_basic,  Decimal('10000'),Decimal('12000'),Decimal('16000')),
    (g7, sc_house,  Decimal('600'),  Decimal('800'),  Decimal('1000')),
    (g7, sc_trnsp,  Decimal('400'),  Decimal('500'),  Decimal('600')),
]:
    gc(GradeBand, {'grade':grade,'component':sc}, min_amount=mn, mid_amount=mid, max_amount=mx)

# Current packages for all employees
pkg_specs = [
    (emp_ali,  Decimal('9000'),  [{'code':'SC-BASIC','amount':8200},{'code':'SC-HSNG','amount':500},{'code':'SC-TRNSP','amount':300}], date(2025,7,1)),
    (emp_pm,   Decimal('13800'), [{'code':'SC-BASIC','amount':12500},{'code':'SC-HSNG','amount':800},{'code':'SC-TRNSP','amount':500}], date(2023,6,1)),
    (emp_hr,   Decimal('4800'),  [{'code':'SC-BASIC','amount':4200},{'code':'SC-HSNG','amount':400},{'code':'SC-TRNSP','amount':200}], date(2023,9,1)),
    (new_emp,  Decimal('9300'),  [{'code':'SC-BASIC','amount':8500},{'code':'SC-HSNG','amount':500},{'code':'SC-TRNSP','amount':300}], date.today()+timedelta(days=45)),
]
pkgs = {}
for emp, ctc, comps, eff in pkg_specs:
    pkg,_ = gc(EmployeePackage, {'employee':emp,'effective_date':eff},
               total_ctc=ctc, currency='MYR', status='ACTIVE',
               components=comps, approved_by=finance_u,
               approved_at=timezone.now()-timedelta(days=10), created_by=admin_u)
    pkgs[emp.employee_number] = pkg

# emp_ali's 8% increment from FY2026 performance — salary was RM7593 → now RM8200 (post-increment)
old_pkg,_ = gc(EmployeePackage, {'employee':emp_ali,'effective_date':date(2024,7,1)},
    total_ctc=Decimal('8335'), currency='MYR', status='SUPERSEDED',
    components=[{'code':'SC-BASIC','amount':7593},{'code':'SC-HSNG','amount':500},{'code':'SC-TRNSP','amount':242}],
    approved_by=finance_u, approved_at=timezone.now()-timedelta(days=380), created_by=admin_u)
gc(CompensationChange, {'employee':emp_ali,'effective_date':date(2025,7,1)},
   change_type='INCREMENT', previous_package=old_pkg,
   new_package=pkgs['EMP-000001'],
   reason='FY2025 Annual Increment — 8% based on EXCEEDS performance rating and manager recommendation for G7 fast-track.',
   status='APPROVED', created_by=admin_u)

# FY2026 Bonus cycle
bonus_cycle,_ = gc(BonusCycle, {'name':'FY2026 Annual Performance Bonus','year':2026},
    bonus_type='ANNUAL', budget_pool=Decimal('85000'), currency='MYR', status='PAID',
    created_by=admin_u)

for emp, amt, rating in [
    (emp_ali, Decimal('5100'), 'EXCEEDS'),
    (emp_pm,  Decimal('7500'), 'EXCEEDS'),
    (emp_hr,  Decimal('2100'), 'MEETS'),
]:
    gc(BonusAllocation, {'cycle':bonus_cycle,'employee':emp},
       recommended_amount=amt, approved_amount=amt,
       performance_rating=rating, status='PAID',
       notes=f"Based on FY2026 performance outcome. Rating: {rating}.",
       recommended_by=hr_admin_u, approved_by=finance_u)

print(f"  ✓ {SalaryComponent.objects.count()} salary components | {GradeBand.objects.count()} grade bands")
print(f"  ✓ {EmployeePackage.objects.count()} packages | Bonus cycle: {bonus_cycle.name} [{bonus_cycle.status}]")
print(f"  ✓ {BonusAllocation.objects.count()} bonus allocations | Total pool: MYR {bonus_cycle.budget_pool:,.0f}")

# ── 12. BENEFITS ──────────────────────────────────────────────
print("\n[12/21] Benefits: plans, enrollments, dependents, claims...")
from apps.benefits.models import (
    BenefitPlan, EligibilityRule, BenefitEnrollment, BenefitDependent, BenefitClaimReference
)

bp_medical,_ = gc(BenefitPlan, {'code':'BP-MED-001'},
    name='Group Medical (Panel)', category='MEDICAL',
    provider='Allianz Malaysia Berhad',
    coverage_details={'outpatient_limit':1500,'specialist_limit':3000,'emergency':True},
    employee_contribution_rate=Decimal('0.005'), employer_contribution_rate=Decimal('0.995'),
    max_dependents=5, is_active=True)
bp_hosp,_ = gc(BenefitPlan, {'code':'BP-HOSP-001'},
    name='Hospitalisation & Surgical', category='HOSPITALISATION',
    provider='Allianz Malaysia Berhad',
    coverage_details={'annual_limit':50000,'room_board_per_day':250,'intensive_care':5000},
    employee_contribution_rate=Decimal('0.20'), employer_contribution_rate=Decimal('0.80'),
    max_dependents=5, is_active=True)
bp_life,_ = gc(BenefitPlan, {'code':'BP-GTL-001'},
    name='Group Term Life Insurance', category='INSURANCE',
    provider='AIA Berhad',
    coverage_details={'sum_assured_multiplier':24,'accidental_death':True},
    employee_contribution_rate=Decimal('0'), employer_contribution_rate=Decimal('1'),
    max_dependents=0, is_active=True)

for plan, grade in [(bp_medical,g3),(bp_medical,g5),(bp_medical,g7),(bp_hosp,g5),(bp_hosp,g7),(bp_life,g3),(bp_life,g5),(bp_life,g7)]:
    gc(EligibilityRule, {'plan':plan,'grade':grade}, employment_type='', min_service_months=0, is_active=True)

enroll_specs = [
    (emp_ali, bp_medical, Decimal('0'), Decimal('75'), date(emp_ali.hire_date.year, emp_ali.hire_date.month, 1)),
    (emp_ali, bp_hosp,   Decimal('120'),Decimal('480'),date(emp_ali.hire_date.year, emp_ali.hire_date.month, 1)),
    (emp_ali, bp_life,   Decimal('0'), Decimal('210'), date(emp_ali.hire_date.year, emp_ali.hire_date.month, 1)),
    (emp_pm,  bp_medical, Decimal('0'), Decimal('75'), date(emp_pm.hire_date.year,  emp_pm.hire_date.month,  1)),
    (emp_pm,  bp_hosp,   Decimal('120'),Decimal('480'),date(emp_pm.hire_date.year,  emp_pm.hire_date.month,  1)),
    (emp_pm,  bp_life,   Decimal('0'), Decimal('210'), date(emp_pm.hire_date.year,  emp_pm.hire_date.month,  1)),
    (emp_hr,  bp_medical, Decimal('0'), Decimal('75'), date(emp_hr.hire_date.year,  emp_hr.hire_date.month,  1)),
    (emp_hr,  bp_life,   Decimal('0'), Decimal('210'), date(emp_hr.hire_date.year,  emp_hr.hire_date.month,  1)),
    (new_emp, bp_medical, Decimal('0'), Decimal('75'), date.today()+timedelta(days=45)),
    (new_emp, bp_life,   Decimal('0'), Decimal('210'), date.today()+timedelta(days=45)),
]
enrollments = {}
for emp, plan, ee_contrib, er_contrib, eff in enroll_specs:
    enr,_ = gc(BenefitEnrollment, {'employee':emp,'plan':plan},
               enrollment_date=eff, status='ACTIVE',
               employee_contribution=ee_contrib, employer_contribution=er_contrib,
               approved_by=hr_admin_u, approved_at=timezone.now()-timedelta(days=30))
    enrollments[(emp.employee_number, plan.code)] = enr

# emp_pm's spouse as dependent on hospitalisation
hosp_enr = enrollments.get(('EMP-000002','BP-HOSP-001'))
if hosp_enr:
    gc(BenefitDependent, {'enrollment':hosp_enr,'name':'Kavitha Raj'},
       relationship='SPOUSE', date_of_birth=date(1983,7,14), id_number='830714-10-1234', is_active=True)

# emp_ali's dental claim against medical plan
med_enr = enrollments.get(('EMP-000001','BP-MED-001'))
if med_enr:
    gc(BenefitClaimReference, {'enrollment':med_enr,'claim_date':date(2026,5,15)},
       claim_reference='ALZ-2026-05-0041',
       amount_claimed=Decimal('380'), amount_approved=Decimal('350'),
       status='APPROVED',
       description='Dental treatment — scaling and root canal (Panel Clinic KL)',
       approved_by=hr_admin_u)

print(f"  ✓ {BenefitPlan.objects.count()} benefit plans | {BenefitEnrollment.objects.count()} enrollments")
print(f"  ✓ {BenefitDependent.objects.count()} dependents | {BenefitClaimReference.objects.count()} benefit claims")

# ── 13. CLAIMS (EXPENSE & TRAVEL) ─────────────────────────────
print("\n[13/21] Claims: types, policies, travel requests, expense claims...")
from apps.claims.models import (
    ClaimType, ExpensePolicy, ClaimRequest, ClaimLine, TravelRequest
)

ct_travel,_  = gc(ClaimType, {'code':'CT-TRV'}, name='Travel & Accommodation', category='TRAVEL',
    max_amount_per_claim=Decimal('5000'), requires_receipt=True, requires_approval=True)
ct_meal,_    = gc(ClaimType, {'code':'CT-MEAL'},name='Meal Allowance',          category='MEAL',
    max_amount_per_claim=Decimal('80'), requires_receipt=True, requires_approval=False)
ct_conf,_    = gc(ClaimType, {'code':'CT-CONF'},name='Conference & Training Fee',category='TRAINING',
    max_amount_per_claim=Decimal('3000'), requires_receipt=True, requires_approval=True)
ct_mile,_    = gc(ClaimType, {'code':'CT-MILE'},name='Mileage Reimbursement',   category='MILEAGE',
    max_amount_per_claim=Decimal('500'), requires_receipt=False, requires_approval=False)

exp_policy,_ = gc(ExpensePolicy, {'name':'Nexus Corp Standard Expense Policy 2026'},
    description='Governs all employee expense reimbursements effective 1 Jan 2026.',
    effective_date=date(2026,1,1), is_active=True,
    mileage_rate_per_km=Decimal('0.45'), per_diem_domestic=Decimal('120'),
    per_diem_international=Decimal('350'),
    meal_allowance_breakfast=Decimal('20'), meal_allowance_lunch=Decimal('30'), meal_allowance_dinner=Decimal('40'),
    rules={'max_hotel_rate_domestic':250,'max_hotel_rate_international':500},
    created_by=admin_u)

# emp_ali's KL Tech Conference (AWS re:Invent KL) — connected to his AWS certification goal
kl_conf_start = date(2026, 4, 14)
kl_conf_end   = date(2026, 4, 16)
tr,_ = gc(TravelRequest, {'employee':emp_ali,'departure_date':kl_conf_start},
    title='AWS re:Invent KL 2026 — KL Travel',
    destination='Kuala Lumpur Convention Centre, KL',
    return_date=kl_conf_end, purpose='Attend AWS re:Invent KL 2026 — aligned to Q2 certification goal.',
    travel_type='DOMESTIC', estimated_cost=Decimal('1950'), currency='MYR',
    status='APPROVED', approved_by=hiring_mgr,
    approved_at=timezone.now()-timedelta(days=70))

cr_ali,_ = gc(ClaimRequest, {'employee':emp_ali,'period_start':kl_conf_start},
    claim_number='CLM-2026-0012',
    claim_title='AWS re:Invent KL 2026 — Conference Expenses',
    period_end=kl_conf_end, total_amount=Decimal('1930'),
    currency='MYR', status='PAID',
    submitted_at=timezone.now()-timedelta(days=62),
    approved_by=hiring_mgr, approved_at=timezone.now()-timedelta(days=60),
    paid_by=finance_u, paid_at=timezone.now()-timedelta(days=55))

for ct, desc, amt, edate, upr in [
    (ct_conf, 'AWS re:Invent KL 2026 conference registration fee', Decimal('750'),  kl_conf_start, Decimal('750')),
    (ct_travel,'AirAsia KUL-KUL return (KUB → KLIA)',              Decimal('380'),  kl_conf_start, Decimal('380')),
    (ct_travel,'Hotel — Regalia KL (2 nights × RM230)',            Decimal('460'),  kl_conf_start, Decimal('230')),
    (ct_meal,  'Meal allowance — 3 days per diem (RM110/day)',     Decimal('330'),  kl_conf_start, Decimal('110')),
]:
    qty = amt / upr
    gc(ClaimLine, {'claim':cr_ali,'claim_type':ct,'description':desc},
       expense_date=edate, quantity=qty, unit_price=upr, amount=amt, currency='MYR')

# emp_pm's ad-hoc client meeting expenses
cr_pm,_ = gc(ClaimRequest, {'employee':emp_pm,'period_start':date(2026,6,1)},
    claim_number='CLM-2026-0019',
    claim_title='Client Stakeholder Meeting — Petaling Jaya',
    period_end=date(2026,6,1), total_amount=Decimal('87'),
    currency='MYR', status='APPROVED',
    submitted_at=timezone.now()-timedelta(days=20),
    approved_by=finance_u, approved_at=timezone.now()-timedelta(days=18))
gc(ClaimLine, {'claim':cr_pm,'claim_type':ct_meal,'description':'Business lunch — 3 pax, Hilton PJ'},
   expense_date=date(2026,6,1), quantity=Decimal('1'), unit_price=Decimal('87'), amount=Decimal('87'), currency='MYR')

print(f"  ✓ {ClaimType.objects.count()} claim types | Expense policy active")
print(f"  ✓ {ClaimRequest.objects.count()} claim requests | {ClaimLine.objects.count()} claim lines | Travel requests: {TravelRequest.objects.count()}")

# ── 14. ESS ───────────────────────────────────────────────────
print("\n[14/21] Employee Self-Service: request types, requests, profile changes...")
from apps.ess.models import ESSRequestType, ESSRequest, ProfileChangeRequest, ManagerDelegation

ess_letter,_ = gc(ESSRequestType, {'code':'ESS-DOC-001'},
    name='Employment Verification Letter', category='DOCUMENT_REQUEST',
    requires_approval=False,
    description='Request an official letter confirming employment status, position, and salary.')
ess_payslip,_= gc(ESSRequestType, {'code':'ESS-DOC-002'},
    name='Payslip Re-print / Duplicate', category='DOCUMENT_REQUEST',
    requires_approval=False, description='Request a reprint of payslip for specified period.')
ess_bank,_   = gc(ESSRequestType, {'code':'ESS-PROF-001'},
    name='Bank Account Change', category='PROFILE_UPDATE',
    requires_approval=True, description='Update bank account for salary disbursement. Requires HR approval.')
ess_cert,_   = gc(ESSRequestType, {'code':'ESS-CERT-001'},
    name='Training Completion Certificate', category='TRAINING',
    requires_approval=False, description='Request an official training completion certificate for a completed course.')

# emp_ali: requested employment verification letter (for Maybank home loan application)
req_letter,_ = gc(ESSRequest, {'employee':emp_ali,'request_type':ess_letter,'subject':'Employment Verification Letter — Maybank Home Loan'},
    description='Require an employment letter confirming my current position, grade G5, and monthly salary RM8,200 for a Maybank home loan application.',
    payload={'purpose':'home_loan','bank':'Maybank Berhad','amount_requested':'480000'},
    status='COMPLETED',
    resolved_by=hr_admin_u, resolved_at=timezone.now()-timedelta(days=10),
    resolution_notes='Employment verification letter (EMP-VL-2026-0033) issued and emailed to employee.')

# new_emp: bank account change (Public Bank → CIMB Bank)
req_bank,_ = gc(ESSRequest, {'employee':new_emp,'request_type':ess_bank,'subject':'Salary Account Change — Public Bank to CIMB'},
    description='Please update my salary disbursement to CIMB Bank, Account No: 8012-0099-7766.',
    payload={'new_bank':'CIMB Bank','new_account':'8012-0099-7766'},
    status='SUBMITTED')

# emp_ali: profile change request — phone number
gc(ProfileChangeRequest, {'employee':emp_ali,'field_name':'phone'},
   field_label='Mobile Phone Number',
   old_value='+601112345678', new_value='+60123456789',
   reason='Changed mobile service provider, new number effective 1 Jun 2026.',
   status='APPROVED', reviewed_by=hr_maker,
   review_notes='Verified via email and employee IC copy.')

# emp_pm delegates leave approval to emp_ali during his conference absence
gc(ManagerDelegation, {'delegator':emp_pm,'delegate':emp_ali,'delegation_type':'LEAVE_APPROVAL'},
   valid_from=kl_conf_start, valid_to=kl_conf_end, is_active=False,
   reason='Dinesh attending AWS conference KL, delegating leave approvals to Ali bin Hamid.',
   created_by=hr_admin_u)

print(f"  ✓ {ESSRequestType.objects.count()} ESS request types | {ESSRequest.objects.count()} requests")
print(f"  ✓ {ProfileChangeRequest.objects.count()} profile change requests | {ManagerDelegation.objects.count()} delegations")

# ── 15. SERVICE DESK ──────────────────────────────────────────
print("\n[15/21] Service Desk: categories, tickets, knowledge base...")
from apps.service_desk.models import (
    TicketCategory, HRTicket, TicketComment, KnowledgeCategory, KnowledgeArticle
)

sd_u = make_user('sd_farah', 'SERVICE_DESK_AGENT', fname='Farah', lname='Amiruddin')

cat_it,_   = gc(TicketCategory, {'code':'CAT-IT'},   name='IT Access & Hardware',      sla_hours=24, is_confidential=False)
cat_pay,_  = gc(TicketCategory, {'code':'CAT-PAY'},  name='Payroll & Compensation',     sla_hours=8,  is_confidential=True)
cat_leave,_= gc(TicketCategory, {'code':'CAT-LV'},   name='Leave & Attendance',         sla_hours=24, is_confidential=False)
cat_ben,_  = gc(TicketCategory, {'code':'CAT-BEN'},  name='Benefits & Insurance',       sla_hours=48, is_confidential=False)
cat_gen,_  = gc(TicketCategory, {'code':'CAT-GEN'},  name='General HR Queries',         sla_hours=48, is_confidential=False)

# Ticket 1: new_emp — access provisioning (connected to onboarding)
t1,_ = gc(HRTicket, {'ticket_number':'TKT-2026-0041'},
    category=cat_it,
    subject='New Employee System Access — Priya Krishnaswamy (EMP-000004)',
    description='Please provision access to: Jira, Confluence, GitLab, AWS Dev, HR Portal, Office 365. New employee starting ' + str(date.today()+timedelta(days=45)) + '.',
    raised_by=hr_maker, on_behalf_of=new_emp,
    status='IN_PROGRESS', priority='HIGH',
    assigned_to=sd_u,
    due_at=timezone.now()+timedelta(days=3))
gc(TicketComment, {'ticket':t1,'author':sd_u,'content':'Jira, Confluence and GitLab access provisioned. AWS and Office 365 pending IT Security approval.'},
   is_internal=False if hasattr(TicketComment,'is_internal') else True)

# Ticket 2: emp_ali — payslip discrepancy (RESOLVED)
t2,_ = gc(HRTicket, {'ticket_number':'TKT-2026-0031'},
    category=cat_pay,
    subject='May 2026 Payslip — EPF deduction seems incorrect',
    description='My May 2026 payslip shows EPF deduction of RM738. Should be 9% of basic RM8,200 = RM738. Appears correct but I want confirmation.',
    raised_by=emp_user, status='RESOLVED', priority='MEDIUM',
    assigned_to=hr_admin_u,
    resolved_at=timezone.now()-timedelta(days=15),
    resolution_notes='Confirmed: EPF calculated correctly at 9% of basic RM8,200 = RM738. Employee acknowledged.', satisfaction_score=5)

# Ticket 3: emp_pm — annual leave balance query
t3,_ = gc(HRTicket, {'ticket_number':'TKT-2026-0025'},
    category=cat_leave,
    subject='Annual Leave Balance — Q2 2026',
    description='Can you please confirm my current annual leave balance and how many days I have remaining for H2 2026?',
    raised_by=hiring_mgr, status='CLOSED', priority='LOW',
    assigned_to=hr_maker,
    resolved_at=timezone.now()-timedelta(days=30), closed_at=timezone.now()-timedelta(days=29),
    resolution_notes='Leave balance confirmed: 17 days remaining as of 30 Jun 2026.', satisfaction_score=4)

# Knowledge base
kc_hr,_  = gc(KnowledgeCategory, {'name':'HR Policies & Procedures'})
kc_it,_  = gc(KnowledgeCategory, {'name':'IT & Systems'})
kc_pay,_ = gc(KnowledgeCategory, {'name':'Payroll & Benefits'})

_kc_map = {'HR': kc_hr, 'IT': kc_it, 'PAY': kc_pay}

for slug, title, cat_key, content, views in [
    ('how-to-apply-annual-leave','How to Apply for Annual Leave','HR',
     'Log into the HR Portal → Workforce → Leave Requests → New Request. Select leave type "Annual Leave", enter dates, and submit. Your line manager will receive an approval notification.',
     142),
    ('employee-expense-claim-process','Employee Expense Claim Process','PAY',
     'All expense claims must be submitted within 30 days of incurrence. Attach original receipts. Claims above RM500 require manager pre-approval via a Travel Request before travel. Submit via HR Portal → Claims.',
     89),
    ('vpn-access-setup-guide','VPN Access Setup Guide','IT',
     'Download Cisco AnyConnect from the IT portal. Use your company email and LDAP password. Server: vpn.nexuscorp.my. Contact IT Help Desk (ext 200) for first-time setup assistance.',
     213),
    ('medical-panel-clinics-list','Medical Panel Clinics List','PAY',
     'Allianz panel clinics are accessible via the Allianz Smart Health app. Present your staff ID and Allianz card. Outpatient limit: RM1,500/year. Dental covered up to RM500/year at designated panel dentists.',
     67),
    ('understanding-your-payslip','Understanding Your Payslip','PAY',
     'Your payslip is generated on the 25th each month. Basic Salary × 9% = EPF (Employee). SOCSO is flat rate based on salary band. Housing (RM500) and Transport (RM300) allowances are tax-exempt.',
     198),
]:
    gc(KnowledgeArticle, {'slug':slug},
       title=title, category=_kc_map[cat_key], content=content,
       status='PUBLISHED', is_featured=(views>150),
       views_count=views, author=hr_admin_u,
       published_at=timezone.now()-timedelta(days=90))

print(f"  ✓ {TicketCategory.objects.count()} ticket categories | {HRTicket.objects.count()} tickets")
print(f"  ✓ {KnowledgeArticle.objects.count()} knowledge articles")

# ── 16. EMPLOYEE RELATIONS ────────────────────────────────────
print("\n[16/21] Employee Relations: case categories, ER case, parties, outcome...")
from apps.employee_relations.models import (
    ERCaseCategory, ERCase, CaseParty, CaseHearing, CaseOutcome
)

er_u = make_user('er_norhaida', 'ER_OFFICER', fname='Norhaida', lname='Zakaria')

cat_attend,_ = gc(ERCaseCategory, {'code':'ERC-ATT'}, name='Attendance & Punctuality', is_grievance=False, is_disciplinary=True, is_confidential=True)
cat_conduct,_ = gc(ERCaseCategory, {'code':'ERC-CON'},name='Conduct & Professionalism',is_grievance=False, is_disciplinary=True, is_confidential=True)
cat_griev,_   = gc(ERCaseCategory, {'code':'ERC-GRV'},name='Grievance',                is_grievance=True,  is_disciplinary=False,is_confidential=True)
cat_perf,_    = gc(ERCaseCategory, {'code':'ERC-PIP'}, name='Performance Improvement', is_grievance=False, is_disciplinary=True, is_confidential=True)

# emp_pm raised a concern about a subordinate's repeated late attendance
# (Based on attendance log showing emp_ali was late on day i==2)
er_case,_ = gc(ERCase, {'case_number':'ER-2026-00003'},
    category=cat_attend,
    subject='Repeated Late Arrival — ' + emp_ali.person.legal_name,
    description='Line manager reported employee arrived 47 minutes late on 19 May 2026 without prior notification. Employee has had 2 prior informal warnings regarding tardiness in Q1 2026. Formal ER case opened per HR policy clause 8.2.',
    case_type='DISCIPLINARY', status='CLOSED', severity='MINOR',
    subject_employee=emp_ali, opened_by=hiring_mgr,
    assigned_investigator=er_u, confidential=True)

gc(CaseParty, {'case':er_case,'employee':emp_ali}, role='SUBJECT', notes='Employee acknowledged the late arrival.')
gc(CaseParty, {'case':er_case,'employee':emp_pm},  role='COMPLAINANT', notes='Line manager who initiated the case.')

gc(CaseHearing, {'case':er_case,'hearing_date':timezone.now()-timedelta(days=28)},
   hearing_type='SHOW_CAUSE', location='HR Conference Room 2A',
   outcome_summary='Employee provided explanation — delayed due to traffic accident on Kesas Highway. Supporting evidence: Waze screenshot, police report reference.',
   status='COMPLETED', panel_members=[er_u.get_full_name()])

gc(CaseOutcome, {'case':er_case},
   outcome_type='VERBAL_WARNING',
   effective_date=date.today()-timedelta(days=25),
   outcome_details='Verbal warning issued. Employee acknowledged lateness and presented mitigating circumstances (road accident). No further action required. Case closed.',
   letter_issued=True)

print(f"  ✓ {ERCaseCategory.objects.count()} ER categories | {ERCase.objects.count()} ER case [{er_case.status}]")
print(f"  ✓ {CaseParty.objects.count()} parties | {CaseHearing.objects.count()} hearings | {CaseOutcome.objects.count()} outcomes")

# ── 17. DOCUMENTS ─────────────────────────────────────────────
print("\n[17/21] Documents: categories, templates, policies, acknowledgements...")
from apps.documents.models import (
    DocCategory, DocTemplate, DocPolicy, DocAcknowledgement, RetentionRule
)

dc_hr,_       = gc(DocCategory, {'code':'DC-HR'},    name='HR Records',           is_confidential=True,  retention_years=7)
dc_contract,_ = gc(DocCategory, {'code':'DC-CNT'},   name='Employment Contracts', is_confidential=True,  retention_years=7)
dc_policy,_   = gc(DocCategory, {'code':'DC-POL'},   name='Company Policies',     is_confidential=False, retention_years=5)
dc_cert,_     = gc(DocCategory, {'code':'DC-CERT'},  name='Certificates',         is_confidential=False, retention_years=5)

gc(DocTemplate, {'code':'TPL-EMP-CONTRACT'},
   name='Employment Contract — Permanent Staff', category=dc_contract,
   description='Standard permanent employment contract for Malaysian staff.',
   variables=['employee_name','position','grade','basic_salary','start_date','reporting_manager'],
   version='3.1', is_active=True, created_by=hr_admin_u)
gc(DocTemplate, {'code':'TPL-OFFER-LETTER'},
   name='Offer Letter Template', category=dc_hr,
   description='Standard offer letter to be countersigned by candidate.',
   variables=['candidate_name','position','grade','package','start_date'],
   version='2.0', is_active=True, created_by=hr_admin_u)
gc(DocTemplate, {'code':'TPL-WARN-VERBAL'},
   name='Verbal Warning Acknowledgement', category=dc_hr,
   description='Used for formalising verbal warnings under ER cases.',
   variables=['employee_name','case_number','date','nature_of_issue'],
   version='1.2', is_active=True, created_by=hr_admin_u)

# HR Policies with acknowledgement requirements
policies = []
for code, name, ver, content in [
    ('POL-001','Employee Handbook 2026',        '4.0','Comprehensive guide covering employment terms, code of conduct, benefits, and grievance procedures for all Nexus Corp employees.'),
    ('POL-002','IT Security & Acceptable Use',  '2.1','Policy governing use of company IT assets, software, internet access, and data classification requirements.'),
    ('POL-003','Leave Management Policy',        '3.0','Entitlements, application procedures and approval workflows for all leave categories including annual, medical, and emergency leave.'),
    ('POL-004','Expense Reimbursement Policy',   '2.0','Guidelines for submitting and approving employee expense claims and travel requests. All claims must be submitted within 30 days.'),
    ('POL-005','Anti-Harassment & Dignity at Work','1.0','Zero-tolerance stance on harassment, bullying, and discrimination in all forms. All violations must be reported immediately.'),
]:
    pol,_ = gc(DocPolicy, {'code':code},
               name=name, category=dc_policy,
               version=ver, content=content,
               status='ACTIVE', effective_date=date(2026,1,1),
               requires_acknowledgement=True,
               acknowledgement_deadline=date(2026,1,31),
               published_at=timezone.now()-timedelta(days=171),
               published_by=hr_admin_u, created_by=hr_admin_u)
    policies.append(pol)

emp_handbook = policies[0]
it_policy    = policies[1]

# Acknowledgements: all 3 existing employees have acknowledged handbook and IT policy
for emp_obj in [emp_ali, emp_pm, emp_hr]:
    for pol in [emp_handbook, it_policy]:
        gc(DocAcknowledgement, {'employee':emp_obj,'policy':pol},
           version_acknowledged=pol.version,
           ip_address='10.0.0.' + str(10 + [emp_ali,emp_pm,emp_hr].index(emp_obj)))

# Retention rules
gc(RetentionRule, {'category':dc_contract}, retention_years=7, disposal_action='ARCHIVE',        legal_hold_applicable=True,  notes='Employment Act 1955 s.61')
gc(RetentionRule, {'category':dc_hr},       retention_years=7, disposal_action='SECURE_DELETE',  legal_hold_applicable=True,  notes='Employment Act 1955 s.61')
gc(RetentionRule, {'category':dc_policy},   retention_years=5, disposal_action='ARCHIVE',        legal_hold_applicable=False, notes='Company Records Policy 2024')

print(f"  ✓ {DocCategory.objects.count()} doc categories | {DocTemplate.objects.count()} templates | {DocPolicy.objects.count()} policies")
print(f"  ✓ {DocAcknowledgement.objects.count()} policy acknowledgements | {RetentionRule.objects.count()} retention rules")

# ── 18. OFFBOARDING ───────────────────────────────────────────
print("\n[18/21] Offboarding: separation, clearance tasks, exit interview...")
from apps.workforce.models import Separation
from apps.offboarding.models import (
    OffboardingCase, ClearanceTask, AssetClearance, AccessRevocation, ExitInterview, FinalSettlement
)

# Create a departed employee (contract expired — realistic for a consultant)
dep_user = make_user('dep_khairul', 'EMPLOYEE', fname='Khairul', lname='Hisham')
dep_person,_ = gc(Person, {'email': dep_user.email},
    legal_name='Khairul Hisham', phone='+60112233445', nationality='Malaysian', gender='M', user=dep_user)
emp_khairul,_ = gc(Employee, {'employee_number':'EMP-000005'},
    person=dep_person, hire_date=date(2025,1,2),
    employment_status='TERMINATED', position=pos_devops, org_unit=infra, grade=g5,
    employment_type='CONTRACT')

sep,_ = gc(Separation, {'employee':emp_khairul},
    separation_type='END_OF_CONTRACT',
    notice_date=date(2026,4,1), last_working_date=date(2026,5,31),
    reason='Fixed-term contract (12 months) concluded. Role absorbed into permanent headcount per Q3 hiring plan.',
    status='COMPLETED', clearance_completed=True, exit_interview_done=True,
    initiated_by=hr_maker, approved_by=hr_checker,
    approved_at=timezone.now()-timedelta(days=30))

ofb,_ = gc(OffboardingCase, {'employee':emp_khairul},
    separation=sep, status='COMPLETED',
    notice_period_days=30, last_working_date=date(2026,5,31),
    exit_interview_scheduled_date=date(2026,5,28),
    knowledge_handover_due=date(2026,5,25),
    rehire_eligible=True, rehire_notes='Excellent contractor. Rehire recommended if permanent role opens.',
    final_settlement_amount=Decimal('3500'), settlement_status='PAID',
    settlement_paid_at=date(2026,6,10),
    initiated_by=hr_maker, hr_owner=hr_maker,
    completed_at=timezone.now()-timedelta(days=20))

for task_name, dept, ttype in [
    ('Return company laptop (ThinkPad X1)', 'IT',      'ASSET_RETURN'),
    ('Return access card & parking pass',   'Admin',   'ACCESS_REVOCATION'),
    ('Handover DevOps runbooks & docs',     'IT',      'KNOWLEDGE_TRANSFER'),
    ('Exit interview completed',            'HR',      'INTERVIEW'),
    ('Final payroll computation',           'Finance', 'PAYROLL'),
]:
    gc(ClearanceTask, {'case':ofb,'task_name':task_name},
       department=dept, task_type=ttype,
       assigned_to=hr_maker, status='COMPLETED',
       completed_by=hr_maker, completed_at=timezone.now()-timedelta(days=22))

gc(AssetClearance, {'case':ofb,'asset_name':'ThinkPad X1 Carbon (14") — Laptop'},
   asset_code='IT-ASSET-0334', asset_type='LAPTOP',
   issued_date=date(2025,1,2), return_date=date(2026,5,31),
   condition_on_return='GOOD', return_status='RETURNED')

gc(ExitInterview, {'case':ofb},
   interview_date=date(2026,5,28), conducted_by=hr_maker,
   format='IN_PERSON',
   reason_for_leaving='Fixed-term contract concluded. Was a great experience overall.',
   overall_experience='POSITIVE', would_return=True, would_recommend=True,
   responses={
       'management':'5/5 — Supportive, clear expectations.',
       'work_environment':'4/5 — Great team culture.',
       'compensation':'4/5 — Competitive for contract role.',
       'strengths':'Team culture, learning environment.',
       'improvements':'Earlier communication on contract renewal timeline.',
   },
   overall_sentiment='POSITIVE',
   is_confidential=True,
   additional_comments='Would welcome a permanent role if one opens. Very positive experience overall.')

gc(FinalSettlement, {'case':ofb},
   basic_pay_balance=Decimal('8500'),
   leave_encashment=Decimal('1618'),
   gratuity_amount=Decimal('0'),
   notice_pay_deduction=Decimal('0'),
   asset_deductions=Decimal('0'),
   other_deductions=Decimal('0'),
   other_additions=Decimal('0'),
   total_settlement=Decimal('10118'),
   settlement_date=date(2026,6,10),
   payment_method='BANK_TRANSFER',
   status='PAID', approved_by=finance_u,
   notes='End-of-contract settlement: 31 days basic + 5 days unused leave encashed.')

print(f"  ✓ Offboarding: {emp_khairul.person.legal_name} [{sep.separation_type}] — {ofb.status}")
print(f"  ✓ {ClearanceTask.objects.count()} clearance tasks | 1 exit interview | 1 final settlement")

# ── 19. ENGAGEMENT ────────────────────────────────────────────
print("\n[19/21] Engagement: recognition types, awards, nominations, survey, action plan...")
from apps.engagement.models import (
    RecognitionType, RecognitionAward, RecognitionNomination,
    SurveyTemplate, EngagementSurvey, SurveyResponse, ActionPlan, EmployeePoints
)

rec_star,_ = gc(RecognitionType, {'code':'REC-STAR'},
    name='Star Performer', recognition_category='PERFORMANCE', points_value=150,
    badge_icon='star', requires_approval=True, is_active=True)
rec_above,_ = gc(RecognitionType, {'code':'REC-ABV'},
    name='Going Above & Beyond', recognition_category='VALUES', points_value=100,
    badge_icon='award', requires_approval=False, is_active=True)
rec_innov,_ = gc(RecognitionType, {'code':'REC-INNOV'},
    name='Innovation Champion', recognition_category='INNOVATION', points_value=120,
    badge_icon='lightbulb', requires_approval=True, is_active=True)
rec_team,_  = gc(RecognitionType, {'code':'REC-TEAM'},
    name='Team Player', recognition_category='TEAMWORK', points_value=75,
    badge_icon='users', requires_approval=False, is_active=True)

# emp_pm nominates emp_ali for "Going Above & Beyond" (Platform v3.0 delivery)
nom,_ = gc(RecognitionNomination, {'nominator':emp_pm,'nominee':emp_ali,'recognition_type':rec_above},
    justification='Ali led the Platform v3.0 backend delivery single-handedly while onboarding a new team member. His dedication during the critical 3-week sprint — including weekend work — was exceptional.',
    supporting_evidence='Platform v3.0 launched 4 days ahead of schedule (15 Mar 2026). API P95 latency: 118ms vs 150ms target.',
    status='APPROVED')

award,_ = gc(RecognitionAward, {'nominated_by':emp_pm,'recipient':emp_ali,'recognition_type':rec_above},
    message='Ali — your ownership of Platform v3.0 and the incredible speed and quality you delivered sets the standard for all of us. Thank you for going above and beyond!',
    is_public=True, points_awarded=100, status='APPROVED',
    reviewed_by=hr_admin_u, reviewed_at=timezone.now()-timedelta(days=45))

# emp_hr nominating emp_pm for Team Player
gc(RecognitionAward, {'nominated_by':emp_hr,'recipient':emp_pm,'recognition_type':rec_team},
    message='Dinesh consistently makes time for the team despite his demanding schedule. Always willing to unblock issues and provide guidance.',
    is_public=True, points_awarded=75, status='APPROVED',
    reviewed_by=hr_admin_u, reviewed_at=timezone.now()-timedelta(days=60))

# Points ledger
gc(EmployeePoints, {'employee':emp_ali},  total_earned=100, total_redeemed=0)
gc(EmployeePoints, {'employee':emp_pm},   total_earned=75,  total_redeemed=0)
gc(EmployeePoints, {'employee':emp_hr},   total_earned=50,  total_redeemed=0)

# H1 2026 Engagement Survey
survey_tmpl,_ = gc(SurveyTemplate, {'code':'TMPL-ENG-H1'},
    name='H1 Employee Engagement Pulse Survey',
    survey_type='ENGAGEMENT',
    questions=[
        {'id':'q1','text':'I feel proud to work at Nexus Corp.','type':'likert','scale':5},
        {'id':'q2','text':'My manager provides clear direction and feedback.','type':'likert','scale':5},
        {'id':'q3','text':'I have the tools and resources to do my job effectively.','type':'likert','scale':5},
        {'id':'q4','text':'How likely are you to recommend Nexus Corp as a place to work? (0-10)','type':'nps','scale':10},
        {'id':'q5','text':'What one thing would you change to improve your work experience?','type':'open','scale':None},
    ],
    is_active=True, created_by=hr_admin_u)

survey,_ = gc(EngagementSurvey, {'title':'H1 2026 Employee Pulse Survey'},
    template=survey_tmpl,
    description='Anonymous pulse survey to assess H1 2026 employee engagement levels.',
    target_audience='ALL', is_anonymous=True, anonymity_threshold=3,
    open_date=timezone.now()-timedelta(days=20),
    close_date=timezone.now()-timedelta(days=6),
    status='CLOSED', response_count=3, launched_by=hr_admin_u)

import uuid as uuid_mod
for emp, resp_data, enps in [
    (emp_ali,  {'q1':5,'q2':4,'q3':5,'q4':9,'q5':'Better coffee machine in the pantry.'}, 9),
    (emp_pm,   {'q1':4,'q2':5,'q3':4,'q4':9,'q5':'More cross-department collaboration events.'}, 9),
    (emp_hr,   {'q1':4,'q2':4,'q3':3,'q4':7,'q5':'HR tools need modernising — too much manual work.'}, 7),
]:
    gc(SurveyResponse, {'survey':survey,'employee':emp},
       response_token=str(uuid_mod.uuid4()),
       responses=resp_data, enps_score=enps,
       submitted_at=timezone.now()-timedelta(days=10), is_complete=True)

gc(ActionPlan, {'survey':survey,'title':'Upgrade HR Systems & Automation'},
    description='Invest in modernising HR tools to reduce manual work and improve employee experience.',
    focus_area='Tools & Technology',
    assigned_to=hr_admin_u,
    target_date=date(2026,12,31), status='IN_PROGRESS',
    progress_notes='HRIS upgrade RFP issued. Shortlisting vendors.',
    completion_percentage=20, created_by=hr_admin_u)

print(f"  ✓ {RecognitionType.objects.count()} recognition types | {RecognitionAward.objects.count()} awards | {RecognitionNomination.objects.count()} nominations")
print(f"  ✓ Survey '{survey.title}' [{survey.status}] | {SurveyResponse.objects.count()} responses | {ActionPlan.objects.count()} action plan")

# ── 20. HSE ───────────────────────────────────────────────────
print("\n[20/21] HSE: incident types, incident, investigation, wellbeing programs...")
from apps.hse.models import (
    HSEIncidentType, HSEIncident, IncidentInvestigation, CorrectiveAction,
    WellbeingProgram, WellbeingEnrollment, MedicalFitnessRecord
)

hse_u = make_user('hse_azhar', 'HSE_OFFICER', fname='Azhar', lname='Mohd Noor')

it_near,_  = gc(HSEIncidentType, {'code':'HSE-NM'},  name='Near Miss',          default_severity='MINOR',   requires_investigation=True,  notification_required=False)
it_injury,_= gc(HSEIncidentType, {'code':'HSE-MI'},  name='Minor Injury',        default_severity='MODERATE',requires_investigation=True,  notification_required=True)
it_ergo,_  = gc(HSEIncidentType, {'code':'HSE-ERG'}, name='Ergonomic Issue',     default_severity='MINOR',   requires_investigation=False, notification_required=False)
it_fire,_  = gc(HSEIncidentType, {'code':'HSE-FD'},  name='Fire Drill',          default_severity='NONE',    requires_investigation=False, notification_required=False)

# Near-miss: wet floor in server room — emp_ali reported it
inc,_ = gc(HSEIncident, {'incident_number':'HSE-2026-0007'},
    incident_type=it_near,
    title='Wet Floor Near-Miss — Server Room Level 3',
    description='Employee slipped on wet floor near server rack B-07 due to a leaking air-conditioning condensate pipe. No injury sustained. Incident reported immediately.',
    incident_date=timezone.now()-timedelta(days=35),
    location='Level 3 — Server Room, Block A',
    severity='MINOR', status='CLOSED',
    reported_by=emp_user,
    employees_involved=[emp_ali.employee_number],
    witness_names=['Li Wei (Interviewer)', 'Dinesh Raj (PM)'],
    immediate_action_taken='Warning signs placed. Maintenance called immediately. Area cordoned off until pipe repaired.',
    is_work_related=True, is_notifiable=False, root_cause_identified=True)

inv,_ = gc(IncidentInvestigation, {'incident':inc},
    lead_investigator=hse_u,
    investigation_start=date.today()-timedelta(days=34),
    target_close_date=date.today()-timedelta(days=25),
    root_cause='Failure to schedule preventive maintenance on AC condensate drain. Last inspection was 8 months ago (overdue).',
    contributing_factors='No scheduled inspection regime for AC units in server room. Condensate pan overflow not detected until puddle formed.',
    findings='AC unit condenser pipe cracked due to scale build-up. Condensate overflowed onto floor. No drip tray installed.',
    recommendations='1. Install drip trays under all AC units in server rooms. 2. Quarterly AC maintenance schedule. 3. Anti-slip mats in server room.',
    status='COMPLETED', completed_at=timezone.now()-timedelta(days=28))

for desc, due_offset, status in [
    ('Install anti-slip mats in all server room areas', -20, 'CLOSED'),
    ('Install drip trays under all 8 AC units — Server Room Level 3', -15, 'CLOSED'),
    ('Schedule quarterly preventive maintenance for all AC units', -10, 'OPEN'),
    ('Update HSE inspection checklist to include AC condensate systems', -5, 'OPEN'),
]:
    gc(CorrectiveAction, {'incident':inc,'action_description':desc},
       investigation=inv, assigned_to=hse_u,
       due_date=date.today()+timedelta(days=due_offset),
       status=status, priority='MEDIUM',
       completed_at=timezone.now()+timedelta(days=due_offset) if status=='CLOSED' else None)

# Wellbeing programs (facilitator is a User FK)
wb_ergo,_ = gc(WellbeingProgram, {'name':'Ergonomics & Workstation Setup Workshop'},
    description='2-hour guided session on proper workstation ergonomics to prevent RSI and back pain. Includes desk assessment.',
    program_type='WORKSHOP',
    start_date=date(2026,6,10), end_date=date(2026,6,10),
    max_participants=20, facilitator=hse_u,
    status='COMPLETED', is_mandatory=False, created_by=hse_u)
wb_sports,_ = gc(WellbeingProgram, {'name':'Nexus Corp Sports Day 2026'},
    description='Annual company sports day — badminton, futsal, and athletics. All departments welcome.',
    program_type='SPORTS',
    start_date=date(2026,7,12), end_date=date(2026,7,12),
    max_participants=100, facilitator=hr_admin_u,
    status='PLANNED', is_mandatory=False, created_by=hr_admin_u)
wb_mental,_ = gc(WellbeingProgram, {'name':'Mental Health Awareness & Resilience'},
    description='4-session mental health workshop covering stress management, mindfulness, and resilience.',
    program_type='COUNSELLING',
    start_date=date(2026,6,3), end_date=date(2026,6,24),
    max_participants=15, facilitator=hse_u,
    status='COMPLETED', is_mandatory=False, created_by=hse_u)

for emp, prog, stat, comp_date in [
    (emp_ali, wb_ergo,   'COMPLETED', date(2026,6,10)),
    (emp_ali, wb_sports, 'ACTIVE',    None),
    (emp_pm,  wb_sports, 'ACTIVE',    None),
    (emp_hr,  wb_mental, 'COMPLETED', date(2026,6,24)),
    (emp_hr,  wb_ergo,   'COMPLETED', date(2026,6,10)),
    (new_emp, wb_ergo,   'ACTIVE',    None),
]:
    gc(WellbeingEnrollment, {'employee':emp,'program':prog},
       status=stat, completion_date=comp_date,
       attendance_percentage=100 if stat=='COMPLETED' else None)

gc(MedicalFitnessRecord, {'employee':emp_ali,'assessment_date':date(2026,3,15)},
    fitness_status='FIT',
    assessed_by='Dr. Amirul Hakim (Klinik Kesihatan Nexus)',
    medical_facility='Klinik Kesihatan Nexus, Level 1',
    next_review_date=date(2027,3,15),
    notes='Annual health screening: BMI 22.4, BP 118/76, Cholesterol 4.8 mmol/L, Glucose 5.1 mmol/L. All within normal range.',
    is_confidential=True)

print(f"  ✓ {HSEIncidentType.objects.count()} incident types | {HSEIncident.objects.count()} incident [{inc.status}]")
print(f"  ✓ {CorrectiveAction.objects.count()} corrective actions | {WellbeingProgram.objects.count()} wellbeing programs | {WellbeingEnrollment.objects.count()} enrollments")

# ── 21. SKILLS ────────────────────────────────────────────────
print("\n[21/21] Skills: categories, proficiency scales, job requirements, employee skills...")
from apps.skills.models import (
    SkillCategory, Skill, ProficiencyScale, JobSkillRequirement,
    EmployeeSkill, SkillEvidence, SkillGapAnalysis, SkillGap
)

sc_prog,_ = gc(SkillCategory, {'code':'SK-PROG'},  name='Programming Languages')
sc_cloud,_= gc(SkillCategory, {'code':'SK-CLD'},   name='Cloud & Infrastructure')
sc_devops,_=gc(SkillCategory, {'code':'SK-DOPS'},  name='DevOps & Automation')
sc_soft,_ = gc(SkillCategory, {'code':'SK-SOFT'},  name='Soft Skills')
sc_hr,_   = gc(SkillCategory, {'code':'SK-HR'},    name='HR & People Management')

for code, name, cat, desc in [
    ('SK-PY',   'Python',              sc_prog,  'General-purpose scripting and backend development.'),
    ('SK-JS',   'JavaScript / ES2024', sc_prog,  'Frontend and Node.js development.'),
    ('SK-TS',   'TypeScript',          sc_prog,  'Typed JavaScript for large-scale applications.'),
    ('SK-REACT','React',               sc_prog,  'Component-based UI framework.'),
    ('SK-AWS',  'Amazon Web Services', sc_cloud, 'Cloud infrastructure, services and serverless.'),
    ('SK-AZURE','Microsoft Azure',     sc_cloud, 'Azure cloud platform and services.'),
    ('SK-K8S',  'Kubernetes',          sc_devops,'Container orchestration at scale.'),
    ('SK-DOCK', 'Docker',              sc_devops,'Containerisation and image management.'),
    ('SK-CICD', 'CI/CD Pipelines',    sc_devops,'Automated build, test and deploy pipelines.'),
    ('SK-COMM', 'Communication',       sc_soft,  'Verbal and written professional communication.'),
    ('SK-LEAD', 'Leadership',          sc_soft,  'Team leadership and people management.'),
    ('SK-HRIS', 'HRIS Systems',        sc_hr,    'HR Information Systems — configuration, data management, reporting.'),
]:
    gc(Skill, {'code':code}, name=name, category=cat, description=desc, is_active=True)

# Load all skills into a dict for easy reference
skills = {s.code: s for s in Skill.objects.all()}

for lvl, name, desc in [
    (1, 'Novice',      'Foundational awareness. Can perform basic tasks with guidance.'),
    (2, 'Developing',  'Growing competency. Can perform tasks independently with occasional support.'),
    (3, 'Proficient',  'Solid working knowledge. Delivers quality output independently.'),
    (4, 'Advanced',    'Deep expertise. Can mentor others and handle complex scenarios.'),
    (5, 'Expert',      'Recognised authority. Shapes strategy and drives best practice adoption.'),
]:
    gc(ProficiencyScale, {'level':lvl}, code=f'PROF-{lvl}', name=name, description=desc)

profs = {p.level: p for p in ProficiencyScale.objects.all()}

# Job skill requirements — j_swe (Senior Software Engineer)
for sk_code, req_level, mandatory in [
    ('SK-TS',  4, True), ('SK-REACT',4, True), ('SK-AWS', 3, True),
    ('SK-PY',  3, False),('SK-JS',   4, True),
]:
    gc(JobSkillRequirement, {'job':j_swe,'skill':skills[sk_code]},
       required_level=profs[req_level], is_mandatory=mandatory)

# j_devops (DevOps Engineer) — target of Ali's transfer
for sk_code, req_level, mandatory in [
    ('SK-K8S', 4, True), ('SK-DOCK',4, True), ('SK-AWS', 4, True),
    ('SK-CICD',4, True), ('SK-PY',  3, False),
]:
    gc(JobSkillRequirement, {'job':j_devops,'skill':skills[sk_code]},
       required_level=profs[req_level], is_mandatory=mandatory)

# emp_ali's skill profile (based on his career history and completed courses)
ali_skills = [
    ('SK-TS',   4, True,  True),   # TypeScript — advanced, endorsed by manager
    ('SK-REACT',4, True,  True),   # React — advanced, endorsed
    ('SK-JS',   4, True,  True),   # JavaScript — advanced, endorsed
    ('SK-PY',   3, True,  False),  # Python — proficient, self-assessed
    ('SK-AWS',  3, False, True),   # AWS — proficient, evidenced by cert
    ('SK-K8S',  2, True,  False),  # Kubernetes — developing, self-assessed (gap for DevOps)
    ('SK-DOCK', 3, True,  False),  # Docker — proficient, self-assessed
    ('SK-COMM', 4, False, True),   # Communication — endorsed by manager
]
for sk_code, lvl, self_assessed, endorsed in ali_skills:
    gc(EmployeeSkill, {'employee':emp_ali,'skill':skills[sk_code]},
       proficiency=profs[lvl], is_self_assessed=self_assessed,
       is_endorsed=endorsed,
       endorsed_by=hiring_mgr if endorsed else None,
       endorsed_at=timezone.now()-timedelta(days=30) if endorsed else None)

# emp_pm's skills
for sk_code, lvl in [('SK-AWS',4),('SK-LEAD',5),('SK-COMM',5),('SK-CICD',3)]:
    gc(EmployeeSkill, {'employee':emp_pm,'skill':skills[sk_code]},
       proficiency=profs[lvl], is_self_assessed=False, is_endorsed=True,
       endorsed_by=hr_admin_u, endorsed_at=timezone.now()-timedelta(days=60))

# Skill evidence: Ali's AWS cert — linked to his EmployeeSkill record
from apps.learning.models import CourseCompletion
aws_emp_skill = EmployeeSkill.objects.filter(employee=emp_ali, skill=skills['SK-AWS']).first()
if aws_emp_skill:
    gc(SkillEvidence, {'employee_skill':aws_emp_skill,'evidence_type':'CERTIFICATION'},
       title='AWS Solutions Architect Associate — Passed (Score 88%)',
       description='Passed AWS SAA-C03 exam at AWS re:Invent KL, April 2026.',
       url='https://aws.amazon.com/verification',
       verified=True, verified_by=hr_admin_u)

# Skill gap analysis: Ali vs DevOps role (transfer target from workforce section)
sga,_ = gc(SkillGapAnalysis, {'employee':emp_ali,'job':j_devops},
    overall_match_percentage=Decimal('62.5'),
    notes='Ali meets 5 of 8 criteria. Key gaps: Kubernetes (L2 vs L4 required) and CI/CD (not assessed). Recommend 6-month development plan before transfer.',
    gaps_summary=[
        {'skill':'Kubernetes','current':2,'required':4,'gap':2},
        {'skill':'CI/CD Pipelines','current':1,'required':4,'gap':3},
    ],
    recommended_training=['Kubernetes CKA Certification','GitLab CI/CD Advanced'])

for sk_code, current, required in [
    ('SK-K8S', 2, 4), ('SK-CICD', 1, 4),
]:
    gc(SkillGap, {'employee':emp_ali,'skill':skills[sk_code]},
       current_level=profs[current], required_level=profs[required],
       gap_size=required-current, status='OPEN')

print(f"  ✓ {SkillCategory.objects.count()} skill categories | {Skill.objects.count()} skills | {ProficiencyScale.objects.count()} proficiency levels")
print(f"  ✓ {JobSkillRequirement.objects.count()} job requirements | {EmployeeSkill.objects.count()} employee skills | {SkillEvidence.objects.count()} evidence")
print(f"  ✓ Skill gap analysis: Ali vs DevOps — readiness: {sga.overall_match_percentage}%")

# ── FINAL SUMMARY ─────────────────────────────────────────────
print("\n" + "="*60)
print("  FINAL DATABASE SNAPSHOT")
print("="*60)

from apps.workflow.models import WorkflowRule, WorkflowRequest
from apps.notification.models import NotificationTemplate
from apps.succession.models import TalentPool
from apps.payroll.models import Payslip as PayslipModel, PayrollRun as PayrollRunModel
from apps.compensation.models import EmployeePackage as EmpPkg, BonusAllocation as BonusAlloc
from apps.benefits.models import BenefitEnrollment as BenEnroll, BenefitClaimReference as BenClaim
from apps.claims.models import ClaimRequest as ClaimReq, TravelRequest as TravelReq
from apps.ess.models import ESSRequest as ESSReq
from apps.service_desk.models import HRTicket, KnowledgeArticle
from apps.employee_relations.models import ERCase
from apps.documents.models import DocPolicy, DocAcknowledgement as DocAck
from apps.offboarding.models import OffboardingCase as OffbCase
from apps.engagement.models import RecognitionAward, EngagementSurvey as EngSurvey
from apps.hse.models import HSEIncident, WellbeingProgram as WbProg
from apps.skills.models import EmployeeSkill as EmpSkill

rows = [
    ("── CORE HR ──────────────────────────",""),
    ("Users (all roles)",                   CustomUser.objects.count()),
    ("Org Units",                           OrgUnit.objects.count()),
    ("Positions (occupied)",                Position.objects.filter(status='OCCUPIED').count()),
    ("Employees active",                    Employee.objects.filter(employment_status__in=['ACTIVE','PROBATION']).count()),
    ("Employees separated",                 Employee.objects.filter(employment_status='TERMINATED').count()),
    ("── RECRUITMENT & ONBOARDING ────────",""),
    ("Job Postings",                        JobPosting.objects.count()),
    ("Applications",                        Application.objects.count()),
    ("Offers accepted",                     Offer.objects.filter(status='ACCEPTED').count()),
    ("Onboarding cases completed",          OnboardingCase.objects.filter(status='COMPLETED').count()),
    ("── WORKFORCE ────────────────────────",""),
    ("Leave requests",                      LeaveRequest.objects.count()),
    ("Attendance logs",                     AttendanceLog.objects.count()),
    ("Overtime requests",                   OvertimeRequest.objects.count()),
    ("Transfers",                           Transfer.objects.count()),
    ("── PERFORMANCE & LEARNING ──────────",""),
    ("Performance cycles",                  PerformanceCycle.objects.count()),
    ("Goals",                               Goal.objects.count()),
    ("Review forms",                        ReviewForm.objects.count()),
    ("Final outcomes",                      FinalOutcome.objects.count()),
    ("Courses published",                   Course.objects.filter(status='PUBLISHED').count()),
    ("Learning assignments",                LearningAssignment.objects.count()),
    ("Certificates issued",                 Certificate.objects.count()),
    ("── PAYROLL & COMPENSATION ──────────",""),
    ("Payroll runs",                        PayrollRunModel.objects.count()),
    ("Payslips generated",                  PayslipModel.objects.count()),
    ("Employee packages",                   EmpPkg.objects.count()),
    ("Bonus allocations",                   BonusAlloc.objects.count()),
    ("── BENEFITS & CLAIMS ───────────────",""),
    ("Benefit enrollments",                 BenEnroll.objects.count()),
    ("Benefit claims",                      BenClaim.objects.count()),
    ("Expense claims",                      ClaimReq.objects.count()),
    ("Travel requests",                     TravelReq.objects.count()),
    ("── ESS & SERVICE DESK ──────────────",""),
    ("ESS requests",                        ESSReq.objects.count()),
    ("HR tickets",                          HRTicket.objects.count()),
    ("Knowledge articles",                  KnowledgeArticle.objects.count()),
    ("── ER, DOCUMENTS & OFFBOARDING ─────",""),
    ("ER cases",                            ERCase.objects.count()),
    ("HR policies",                         DocPolicy.objects.count()),
    ("Policy acknowledgements",             DocAck.objects.count()),
    ("Offboarding cases",                   OffbCase.objects.count()),
    ("── ENGAGEMENT, HSE & SKILLS ────────",""),
    ("Recognition awards",                  RecognitionAward.objects.count()),
    ("Engagement surveys",                  EngSurvey.objects.count()),
    ("HSE incidents",                       HSEIncident.objects.count()),
    ("Wellbeing programs",                  WbProg.objects.count()),
    ("Employee skills on record",           EmpSkill.objects.count()),
]

for label, count in rows:
    if count == "":
        print(f"\n  {label}")
    else:
        bar = '█' * min(count, 20) if isinstance(count, int) and count > 0 else ''
        print(f"  {label:<38} {str(count):>4}  {bar}")

print(f"\n  ✅ SEED COMPLETE — all 21 modules seeded with interconnected production-like data")
print("="*60 + "\n")
