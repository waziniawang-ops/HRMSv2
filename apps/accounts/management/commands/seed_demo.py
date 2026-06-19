from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta, datetime
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed the database with demo users and full HRMS sample data'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Flush all data before seeding')

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing database...'))
            from django.core.management import call_command
            call_command('flush', '--no-input')

        self.stdout.write('\n' + '='*60)
        self.stdout.write('  HRMSv2 DEMO SEED')
        self.stdout.write('='*60)

        def gc(model, lookup, **defaults):
            obj, created = model.objects.get_or_create(**lookup, defaults=defaults)
            return obj, created

        # ── 1. USERS ─────────────────────────────────────────────
        self.stdout.write('\n[1/9] Creating users (13 roles)...')
        from apps.accounts.models import CustomUser

        def make_user(uname, role, utype='INTERNAL', fname='', lname=''):
            u, _ = CustomUser.objects.get_or_create(username=uname, defaults={
                'email': f'{uname}@hrms.demo', 'role': role, 'user_type': utype,
                'first_name': fname or uname, 'last_name': lname,
            })
            u.set_password('Demo1234!')
            u.save()
            return u

        admin_u    = make_user('sysadmin',    'SYSTEM_ADMIN',    fname='Syed',    lname='Admin')
        hr_maker   = make_user('hr_fatimah',  'HR_MAKER',        fname='Fatimah', lname='Hassan')
        hr_checker = make_user('hr_ahmad',    'HR_CHECKER',      fname='Ahmad',   lname='Razali')
        hr_admin_u = make_user('hr_norziah',  'HR_ADMIN',        fname='Norziah', lname='Kamal')
        recruiter  = make_user('rec_shafiq',  'RECRUITER',       fname='Shafiq',  lname='Idris')
        hiring_mgr = make_user('mgr_dinesh',  'HIRING_MANAGER',  fname='Dinesh',  lname='Raj')
        interview_u= make_user('int_liwei',   'INTERVIEWER',     fname='Li',      lname='Wei')
        finance_u  = make_user('fin_rajan',   'FINANCE_CHECKER', fname='Rajan',   lname='Subramaniam')
        ld_u       = make_user('ld_nurul',    'LD_OFFICER',      fname='Nurul',   lname='Aina')
        perf_u     = make_user('perf_azlan',  'HR_PERFORMANCE',  fname='Azlan',   lname='Yusof')
        talent_u   = make_user('talent_siti', 'TALENT_COMMITTEE',fname='Siti',    lname='Rohani')
        emp_user   = make_user('emp_ali',     'EMPLOYEE',        fname='Ali',     lname='bin Hamid')
        ld_checker = make_user('ldc_hassan',  'LD_CHECKER',      fname='Hassan',  lname='Osman')

        sa = CustomUser.objects.get(username='sysadmin')
        sa.is_staff = True; sa.is_superuser = True; sa.role = 'SYSTEM_ADMIN'
        sa.set_password('Demo1234!'); sa.save()

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {CustomUser.objects.count()} users created'
        ))

        # ── 2. ORG STRUCTURE ─────────────────────────────────────
        self.stdout.write('\n[2/9] Building org structure (Visionaries Sdn Bhd)...')
        from apps.core_hr.models import OrgUnit, CostCenter, JobFamily, Job, Grade

        hq,_      = gc(OrgUnit, {'code':'HQ'},    name='Visionaries Sdn Bhd',      type='COMPANY',    status='ACTIVE')
        it_div,_  = gc(OrgUnit, {'code':'IT'},    name='Information Technology', type='DIVISION',   status='ACTIVE', parent=hq)
        hr_div,_  = gc(OrgUnit, {'code':'HR'},    name='Human Resources',        type='DIVISION',   status='ACTIVE', parent=hq)
        fin_div,_ = gc(OrgUnit, {'code':'FIN'},   name='Finance',                type='DIVISION',   status='ACTIVE', parent=hq)
        sw_dept,_ = gc(OrgUnit, {'code':'SWE'},   name='Software Engineering',   type='DEPARTMENT', status='ACTIVE', parent=it_div)
        infra,_   = gc(OrgUnit, {'code':'INFRA'}, name='Infrastructure & Cloud', type='DEPARTMENT', status='ACTIVE', parent=it_div)

        cc_it,_ = gc(CostCenter, {'code':'CC-IT-001'}, name='IT Cost Centre',  org_unit=sw_dept)
        cc_hr,_ = gc(CostCenter, {'code':'CC-HR-001'}, name='HR Cost Centre',  org_unit=hr_div)

        jf_tech,_ = gc(JobFamily, {'code':'TECH'},  name='Technology')
        jf_hr,_   = gc(JobFamily, {'code':'HRMGT'}, name='Human Resource Management')

        j_swe,_    = gc(Job, {'job_code':'SWE-SNR'},    job_title='Senior Software Engineer', job_family=jf_tech)
        j_pm,_     = gc(Job, {'job_code':'PM-001'},     job_title='Product Manager',           job_family=jf_tech)
        j_devops,_ = gc(Job, {'job_code':'DEVOPS-001'}, job_title='DevOps Engineer',           job_family=jf_tech)
        j_hr,_     = gc(Job, {'job_code':'HR-EXEC'},    job_title='HR Executive',              job_family=jf_hr)

        g3,_ = gc(Grade, {'grade_code':'G3'}, grade_name='Executive', level=3, pay_band_min=Decimal('3500'), pay_band_max=Decimal('5500'))
        g5,_ = gc(Grade, {'grade_code':'G5'}, grade_name='Senior',    level=5, pay_band_min=Decimal('5000'), pay_band_max=Decimal('9000'))
        g7,_ = gc(Grade, {'grade_code':'G7'}, grade_name='Manager',   level=7, pay_band_min=Decimal('8000'), pay_band_max=Decimal('14000'))

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {OrgUnit.objects.count()} org units | {Grade.objects.count()} grades | {Job.objects.count()} jobs'
        ))

        # ── 3. POSITIONS ─────────────────────────────────────────
        self.stdout.write('\n[3/9] Creating positions...')
        from apps.core_hr.models import Position

        def make_pos(code, title, job, ou, cc, grade, critical=False):
            p, _ = gc(Position, {'position_code': code},
                      title=title, job=job, org_unit=ou, cost_center=cc, grade=grade,
                      is_critical=critical, status='APPROVED', created_by=hr_maker)
            return p

        pos_swe1   = make_pos('POS-SWE-001', 'Senior Software Engineer (Backend)',  j_swe,    sw_dept, cc_it, g5)
        pos_swe2   = make_pos('POS-SWE-002', 'Senior Software Engineer (Frontend)', j_swe,    sw_dept, cc_it, g5)
        pos_pm     = make_pos('POS-PM-001',  'Product Manager – Digital',           j_pm,     sw_dept, cc_it, g7, critical=True)
        pos_devops = make_pos('POS-DEV-001', 'DevOps Engineer',                     j_devops, infra,   cc_it, g5)
        pos_hr     = make_pos('POS-HR-001',  'HR Executive',                        j_hr,     hr_div,  cc_hr, g3)

        self.stdout.write(self.style.SUCCESS(f'  ✓ {Position.objects.count()} positions'))

        # ── 4. EMPLOYEES ─────────────────────────────────────────
        self.stdout.write('\n[4/9] Creating employees...')
        from apps.core_hr.models import Person, Employee

        def make_emp(user, emp_no, pos, grade, days_ago=365):
            person, _ = gc(Person, {'email': user.email},
                           legal_name=f'{user.first_name} {user.last_name}'.strip(),
                           user=user, phone='+601112345678', nationality='Malaysian', gender='M')
            emp, _ = gc(Employee, {'employee_number': emp_no},
                        person=person, hire_date=date.today()-timedelta(days=days_ago),
                        employment_status='ACTIVE', position=pos, org_unit=pos.org_unit, grade=grade)
            pos.status = 'OCCUPIED'; pos.incumbent_employee = emp; pos.save()
            return emp

        emp_ali = make_emp(emp_user,   'EMP-000001', pos_swe1, g5, days_ago=820)
        emp_pm  = make_emp(hiring_mgr, 'EMP-000002', pos_pm,   g7, days_ago=1200)
        emp_hr  = make_emp(hr_maker,   'EMP-000003', pos_hr,   g3, days_ago=950)

        self.stdout.write(self.style.SUCCESS(f'  ✓ {Employee.objects.count()} employees'))

        # ── 5. RECRUITMENT ───────────────────────────────────────
        self.stdout.write('\n[5/9] Running full recruitment cycle...')
        from apps.recruitment.models import (
            JobRequisition, JobPosting, Applicant, ApplicantProfile,
            Application, Interview, InterviewFeedback, Offer
        )

        pos_swe2.status = 'VACANT'; pos_swe2.incumbent_employee = None; pos_swe2.save()

        req, _ = gc(JobRequisition, {'position': pos_swe2},
                    hiring_reason='BACKFILL',
                    justification='Frontend capacity needed for Platform v3.0 launch.',
                    requested_by=hr_maker, headcount=1,
                    target_start_date=date.today()+timedelta(days=45),
                    status='APPROVED')
        if not req.requisition_number:
            req.requisition_number = f"REQ-{date.today().year}-{str(req.pk)[:8].upper()}"
            req.save()

        posting, _ = gc(JobPosting, {'requisition': req},
                        title='Senior Frontend Engineer',
                        description='Join our product team to build high-performance web apps with React/TypeScript.',
                        requirements='5+ yrs React, TypeScript, REST APIs. BSc Computer Science preferred.',
                        visibility='EXTERNAL', status='POSTED', created_by=recruiter,
                        opening_date=date.today()-timedelta(days=14),
                        closing_date=date.today()+timedelta(days=16))

        applicants_data = [
            dict(email='sara.wml@email.com',  full_name='Sara Wong Mei Lin',  phone='+60111001', score=Decimal('88'), username='appl_sara'),
            dict(email='arif.zk@email.com',   full_name='Arif Zulkifli',      phone='+60111002', score=Decimal('72'), username='appl_arif'),
            dict(email='priya.ks@email.com',  full_name='Priya Krishnaswamy', phone='+60111003', score=Decimal('91'), username='appl_priya'),
        ]
        apps_list = []
        for d in applicants_data:
            fname, lname = d['full_name'].split(' ', 1)
            appl_user = make_user(d['username'], 'APPLICANT', utype='EXTERNAL', fname=fname, lname=lname)
            appl_user.email = d['email']; appl_user.save()
            appl, _ = gc(Applicant, {'email': d['email']},
                         user=appl_user, full_name=d['full_name'], phone=d['phone'],
                         profile_status='ACTIVE', consent_version='2.0')
            ApplicantProfile.objects.get_or_create(applicant=appl, defaults={
                'education':  [{'degree':'BSc Computer Science','institution':'UTM','year':2019}],
                'experience': [{'company':'TechCo Sdn Bhd','role':'Frontend Developer','years':4}],
                'skills':     ['React','TypeScript','Node.js','GraphQL','AWS'],
            })
            app, _ = gc(Application, {'applicant': appl, 'job_posting': posting},
                        stage='OFFER' if d['score']==91 else ('INTERVIEW' if d['score']>=80 else 'SCREENING'),
                        score=d['score'])
            apps_list.append((appl, app, d['score']))

        for appl, app, score in [(a, ap, s) for a, ap, s in apps_list if s >= 80]:
            ivw, c = gc(Interview, {'application': app},
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
                    'strengths': 'Strong React expertise. Clear communicator.',
                    'areas_for_improvement': 'Can improve on backend integration patterns.',
                    'recommendation': 'STRONG_YES' if score >= 90 else 'YES',
                    'is_locked': True,
                }
            )

        winner_appl = next(a for a, _, s in apps_list if s == 91)
        winner_app  = next(ap for _, ap, s in apps_list if s == 91)

        offer, _ = gc(Offer, {'application': winner_app},
                      position=pos_swe2, grade=g5,
                      basic_salary=Decimal('8500'),
                      allowances={'housing': 500, 'transport': 300},
                      total_package=Decimal('9300'),
                      employment_type='PERMANENT',
                      start_date=date.today()+timedelta(days=45),
                      status='ACCEPTED', created_by=recruiter,
                      expiry_date=date.today()+timedelta(days=14),
                      accepted_at=timezone.now()-timedelta(days=1))
        if not offer.offer_number:
            offer.offer_number = f"OFF-{date.today().year}-{str(offer.pk)[:8].upper()}"
            offer.save()

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {len(apps_list)} applications | Offer: {offer.offer_number} [{offer.status}]'
        ))

        # ── 6. ONBOARDING ────────────────────────────────────────
        self.stdout.write('\n[6/9] Onboarding → converting to employee...')
        from apps.onboarding.models import OnboardingCase, OnboardingTask

        onb, _ = gc(OnboardingCase, {'offer': offer},
                    target_start_date=offer.start_date, assigned_hr=hr_maker,
                    status='COMPLETED', completed_at=timezone.now())

        for code, title, req_f, order in [
            ('PERSONAL_INFO',    'Personal Information Verification', True,  1),
            ('RESUME',           'Resume Verification',               True,  2),
            ('ACADEMIC_CERTS',   'Academic Certificates',             True,  3),
            ('BANK_DETAILS',     'Bank Account Details',              True,  4),
            ('EMERGENCY_CONTACT','Emergency Contact',                 True,  5),
            ('CONTRACT_SIGNING', 'Employment Contract Signing',       True,  6),
            ('ACCESS_REQUEST',   'Access Provisioning Request',       False, 7),
            ('PAYROLL_SETUP',    'Payroll Setup',                     True,  8),
        ]:
            gc(OnboardingTask,
               {'onboarding_case': onb, 'task_code': code},
               title=title, is_required=req_f, order=order,
               status='COMPLETED', completed_by=hr_maker,
               completed_at=timezone.now()-timedelta(hours=3), hr_verified=True)

        person_new, _ = gc(Person, {'email': winner_appl.email},
                           legal_name=winner_appl.full_name, phone=winner_appl.phone,
                           nationality='Malaysian', gender='F')
        last_emp = Employee.objects.order_by('-created_at').first()
        next_no  = int(last_emp.employee_number.split('-')[-1]) + 1 if last_emp else 4
        new_emp, _ = gc(Employee, {'person': person_new},
                        employee_number=f'EMP-{next_no:06d}',
                        hire_date=offer.start_date,
                        employment_status='PROBATION',
                        position=pos_swe2, org_unit=pos_swe2.org_unit, grade=g5,
                        source_onboarding=onb)
        pos_swe2.status = 'OCCUPIED'; pos_swe2.incumbent_employee = new_emp; pos_swe2.save()
        onb.candidate_person = person_new; onb.save()

        self.stdout.write(self.style.SUCCESS(f'  ✓ Employee: {new_emp.employee_number} — {person_new.legal_name}'))

        # ── 7. WORKFORCE ─────────────────────────────────────────
        self.stdout.write('\n[7/9] Workforce: leave, attendance, overtime, transfer...')
        from apps.workforce.models import (
            LeaveType, LeaveBalance, LeaveRequest,
            AttendanceLog, OvertimeRequest, Transfer
        )

        annual, _ = gc(LeaveType, {'code':'AL'}, name='Annual Leave',    days_per_year=Decimal('20'), is_paid=True)
        mc_lt,  _ = gc(LeaveType, {'code':'MC'}, name='Medical Leave',   days_per_year=Decimal('14'), is_paid=True)
        mat_lt, _ = gc(LeaveType, {'code':'ML'}, name='Maternity Leave', days_per_year=Decimal('98'), is_paid=True)

        yr = date.today().year
        for emp in [emp_ali, emp_pm, emp_hr, new_emp]:
            gc(LeaveBalance, {'employee':emp,'leave_type':annual,'year':yr},
               entitled_days=Decimal('20'), used_days=Decimal('0'))
            gc(LeaveBalance, {'employee':emp,'leave_type':mc_lt,'year':yr},
               entitled_days=Decimal('14'), used_days=Decimal('0'))

        lr, _ = gc(LeaveRequest,
                   {'employee':emp_ali,'leave_type':annual,'start_date':date.today()+timedelta(days=7)},
                   end_date=date.today()+timedelta(days=9),
                   days_requested=Decimal('3'),
                   reason='Family vacation to Langkawi',
                   status='APPROVED', reviewed_by=hr_maker,
                   reviewed_at=timezone.now()-timedelta(hours=2))
        bal, _ = LeaveBalance.objects.get_or_create(
            employee=emp_ali, leave_type=annual, year=yr,
            defaults={'entitled_days':Decimal('20'), 'used_days':Decimal('0')})
        if bal.used_days == 0:
            bal.used_days = Decimal('3'); bal.save()

        for i in range(1, 6):
            day = date.today()-timedelta(days=i)
            if day.weekday() < 5:
                AttendanceLog.objects.get_or_create(employee=emp_ali, date=day, defaults={
                    'clock_in':  timezone.make_aware(datetime.combine(day, datetime.min.time().replace(hour=8,  minute=45))),
                    'clock_out': timezone.make_aware(datetime.combine(day, datetime.min.time().replace(hour=17, minute=30))),
                    'hours_worked': Decimal('8.75'), 'is_present': True,
                    'is_late': (i == 2), 'source': 'BIOMETRIC',
                })

        ot, _ = gc(OvertimeRequest,
                   {'employee':emp_ali,'date':date.today()-timedelta(days=3)},
                   hours_requested=Decimal('3'), hours_approved=Decimal('3'),
                   reason='Critical production release deployment',
                   status='APPROVED', approved_by=hiring_mgr,
                   approved_at=timezone.now()-timedelta(days=2))

        pos_devops.status = 'VACANT'; pos_devops.save()
        gc(Transfer,
           {'employee':emp_ali,'from_position':pos_swe1,'to_position':pos_devops},
           movement_type='LATERAL', from_grade=g5, to_grade=g5,
           effective_date=date.today()+timedelta(days=30),
           reason='Ali requested move to DevOps to broaden cloud infrastructure expertise.',
           status='APPROVED', initiated_by=hr_maker, approved_by=hr_checker,
           approved_at=timezone.now()-timedelta(hours=1))

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ Leave | {AttendanceLog.objects.count()} attendance logs | OT | Transfer'
        ))

        # ── 8. PERFORMANCE ───────────────────────────────────────
        self.stdout.write('\n[8/9] Performance management...')
        from apps.performance.models import (
            PerformanceCycle, CompetencyModel, Competency,
            GoalPlan, Goal, ReviewForm, FinalOutcome
        )

        cycle, _ = gc(PerformanceCycle, {'name':'FY2026 Annual Performance Review'},
                      cycle_year=2026, status='YEAR_END',
                      goal_setting_start=date(2026,1,1), goal_setting_end=date(2026,1,31),
                      year_end_start=date(2026,11,1),    year_end_end=date(2026,11,30))

        cm, _ = gc(CompetencyModel, {'name':'Core Engineering Competencies'},
                   description='Applied to all Engineering roles.', is_active=True)
        for cname, wt in [('Technical Excellence','2.0'),('Problem Solving','1.5'),('Delivery','1.5'),('Collaboration','1.0')]:
            gc(Competency, {'model':cm,'name':cname}, max_level=5, weight=Decimal(wt))

        gp, _ = gc(GoalPlan, {'employee':emp_ali,'cycle':cycle},
                   status='HR_APPROVED', overall_weight_total=Decimal('5.0'))

        for gtitle, cat, wt, tgt in [
            ('Deliver Platform v3.0 — on-time & on-budget', 'KPI',         '2.0', '100% delivery by Q3'),
            ('Reduce API P95 latency to <150ms',             'KPI',         '1.5', 'P95 latency <150ms'),
            ('Achieve AWS Solutions Architect certification', 'DEVELOPMENT', '0.5', 'Certified by Q3 2026'),
            ('Mentor 2 junior engineers',                    'BEHAVIORAL',  '1.0', '2 mentees progressing'),
        ]:
            gc(Goal, {'goal_plan':gp,'title':gtitle},
               category=cat, weight=Decimal(wt), target_value=tgt,
               status='COMPLETED', completion_percentage=100)

        gc(ReviewForm, {'cycle':cycle,'employee':emp_ali,'review_type':'SELF'},
           reviewer=emp_user, status='SUBMITTED', overall_rating=Decimal('4.2'),
           strengths_comments='Led Platform v3.0 end-to-end. API latency target exceeded.',
           improvement_comments='Can improve delegation.',
           overall_comments='Proud of the team impact this year.',
           submitted_at=timezone.now()-timedelta(days=7))

        gc(ReviewForm, {'cycle':cycle,'employee':emp_ali,'review_type':'MANAGER'},
           reviewer=hiring_mgr, status='SUBMITTED', overall_rating=Decimal('4.5'),
           strengths_comments='Ali is our most reliable engineer. Delivery is impeccable.',
           improvement_comments='Encourage broader cross-functional collaboration.',
           overall_comments='Exceeds all expectations. Ready for G7 consideration.',
           submitted_at=timezone.now()-timedelta(days=4))

        gc(FinalOutcome, {'cycle':cycle,'employee':emp_ali},
           final_rating=Decimal('4.4'), outcome_label='EXCEEDS',
           eligible_for_increment=True, eligible_for_bonus=True,
           increment_percentage=Decimal('8.0'), bonus_amount=Decimal('5100.00'),
           notes='Exceptional year. Fast-track for Grade 7 promotion in H1 2027.',
           approved_by=hr_checker)

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ Cycle | {Goal.objects.count()} goals | {ReviewForm.objects.count()} reviews | outcome'
        ))

        # ── 9. LEARNING ──────────────────────────────────────────
        self.stdout.write('\n[9/9] Learning management...')
        from apps.learning.models import (
            Course, LearningAssignment, CourseCompletion, Certificate, SkillGap
        )

        c_induct, _ = gc(Course, {'code':'INDUCTION-001'}, title='New Employee Induction Program',
                         course_type='ELEARNING', duration_hours=Decimal('4'),
                         passing_score=80, is_mandatory=True, status='PUBLISHED', created_by=ld_u)
        c_aws, _    = gc(Course, {'code':'AWS-SAA-001'}, title='AWS Solutions Architect Associate Prep',
                         course_type='VIRTUAL', duration_hours=Decimal('40'),
                         passing_score=72, is_mandatory=False, status='PUBLISHED', created_by=ld_u)
        c_react, _  = gc(Course, {'code':'REACT-ADV-001'}, title='Advanced React & TypeScript',
                         course_type='ELEARNING', duration_hours=Decimal('12'),
                         passing_score=75, is_mandatory=False, status='PUBLISHED', created_by=ld_u)
        c_pdpa, _   = gc(Course, {'code':'PDPA-001'}, title='PDPA & Data Privacy Compliance',
                         course_type='ELEARNING', duration_hours=Decimal('2'),
                         passing_score=85, is_mandatory=True, status='PUBLISHED', created_by=ld_u)
        c_agile, _  = gc(Course, {'code':'AGILE-001'}, title='Agile & Scrum Fundamentals',
                         course_type='ELEARNING', duration_hours=Decimal('6'),
                         passing_score=75, is_mandatory=False, status='PUBLISHED', created_by=ld_u)

        for emp, course, st, due_offset in [
            (emp_ali, c_aws,    'COMPLETED',   0),
            (emp_ali, c_pdpa,   'COMPLETED',   0),
            (emp_ali, c_react,  'COMPLETED',   0),
            (new_emp, c_induct, 'IN_PROGRESS', 14),
            (new_emp, c_pdpa,   'ASSIGNED',    30),
            (emp_pm,  c_pdpa,   'COMPLETED',   0),
            (emp_pm,  c_agile,  'COMPLETED',   0),
            (emp_hr,  c_pdpa,   'COMPLETED',   0),
        ]:
            gc(LearningAssignment,
               {'employee': emp, 'course': course},
               status=st, assigned_by=ld_u,
               due_date=date.today()+timedelta(days=due_offset if due_offset else 30))

        for emp, course, score in [
            (emp_ali, c_aws,   Decimal('88')),
            (emp_ali, c_pdpa,  Decimal('94')),
            (emp_ali, c_react, Decimal('82')),
            (emp_pm,  c_pdpa,  Decimal('90')),
            (emp_pm,  c_agile, Decimal('85')),
            (emp_hr,  c_pdpa,  Decimal('88')),
        ]:
            comp, cr = gc(CourseCompletion,
                          {'employee': emp, 'course': course},
                          completed_at=timezone.now()-timedelta(days=30+int(score)%10),
                          score=score, hours_completed=course.duration_hours, is_valid=True)
            if cr:
                Certificate.objects.get_or_create(completion=comp, defaults={
                    'certificate_number': f"CERT-{course.code}-{emp.employee_number}-{date.today().year}",
                    'expiry_date': date.today()+timedelta(days=730),
                })

        gc(SkillGap, {'employee':emp_ali,'skill_name':'Kubernetes & Container Orchestration'},
           required_level=4, current_level=2, recommended_course=c_aws, is_closed=False)
        gc(SkillGap, {'employee':new_emp,'skill_name':'TypeScript Advanced Patterns'},
           required_level=3, current_level=1, recommended_course=c_react, is_closed=False)

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {Course.objects.filter(status="PUBLISHED").count()} courses | '
            f'{CourseCompletion.objects.count()} completions | '
            f'{Certificate.objects.count()} certs'
        ))

        # ── SUMMARY ──────────────────────────────────────────────
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('  ✅ SEED COMPLETE — all demo data loaded'))
        self.stdout.write('='*60)
        self.stdout.write('\n  Demo credentials (password: Demo1234!)')
        self.stdout.write('  ─────────────────────────────────────')
        for uname, label in [
            ('sysadmin',    'Sys Admin'),
            ('hr_norziah',  'HR Admin'),
            ('hr_fatimah',  'HR Maker'),
            ('hr_ahmad',    'HR Checker'),
            ('rec_shafiq',  'Recruiter'),
            ('mgr_dinesh',  'Hiring Mgr'),
            ('int_liwei',   'Interviewer'),
            ('fin_rajan',   'Finance'),
            ('talent_siti', 'Talent Cmt'),
            ('perf_azlan',  'HR Perf'),
            ('ld_nurul',    'LD Officer'),
            ('ldc_hassan',  'LD Checker'),
            ('emp_ali',     'Employee'),
        ]:
            self.stdout.write(f'  {uname:<15} — {label}')
        self.stdout.write('')
