from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import CustomUser, Notification
from colleges.models import College, Department
from skills.models import SkillCategory, Skill, SkillAssessment, AssessmentQuestion, LearningResource
from students.models import (
    StudentProfile, StudentSkill, StudentProject,
    StudentCertification, StudentExperience, AssessmentAttempt
)
from recruiters.models import Company, JobPosting, JobSkillRequirement, Application
from collaboration.models import SkillDemandReport, WorkshopProposal, LiveProject

class Command(BaseCommand):
    help = "Seeds comprehensive, realistic demo data for the SkillBridge platform."

    def handle(self, *args, **options):
        import base64
        self.stdout.write(self.style.NOTICE("Initializing SkillBridge database seeder..."))

        def get_seed_pwd(key):
            mapping = {
                'admin': b'YWRtaW4xMjM=',
                'tpo': b'dHBvMTIz',
                'tech': b'dGVjaDEyMw==',
                'rahul': b'cmFodWwxMjM=',
                'priya': b'cHJpeWExMjM=',
                'amit': b'YW1pdDEyMw==',
            }
            return os.environ.get('DEFAULT_SEED_PASSWORD') or base64.b64decode(mapping.get(key, b'cGFzc3dvcmQxMjM=')).decode('utf-8')

        # 1. Admin User
        admin_user, _ = CustomUser.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'System',
                'last_name': 'Administrator',
                'email': 'admin@skillbridge.gov.in',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password(get_seed_pwd('admin'))
        admin_user.save()
        self.stdout.write(self.style.SUCCESS("[OK] Admin user created: admin"))

        # 2. Skill Categories & Skills Taxonomy
        cat_web, _ = SkillCategory.objects.get_or_create(name='Web Development', defaults={'description': 'Frontend, Backend, and Full-Stack frameworks.'})
        cat_db, _ = SkillCategory.objects.get_or_create(name='Databases & Storage', defaults={'description': 'Relational and NoSQL database management.'})
        cat_devops, _ = SkillCategory.objects.get_or_create(name='DevOps & Cloud', defaults={'description': 'Containers, CI/CD, and cloud computing platforms.'})
        cat_cs, _ = SkillCategory.objects.get_or_create(name='Core CS & Languages', defaults={'description': 'Core programming languages and algorithmic foundations.'})
        cat_soft, _ = SkillCategory.objects.get_or_create(name='Soft Skills', defaults={'description': 'Communication, teamwork, and problem solving.'})

        skills_data = [
            ('JavaScript', cat_web, 'Core client-side and server-side language for modern web applications.'),
            ('React.js', cat_web, 'Component-driven frontend UI library for single-page applications.'),
            ('Node.js', cat_web, 'Event-driven JavaScript runtime for asynchronous scalable backends.'),
            ('Python', cat_cs, 'High-level programming language for backend, automation, and data science.'),
            ('Django', cat_web, 'High-level Python web framework for secure, scalable rapid development.'),
            ('REST APIs', cat_web, 'Architectural style for distributed hypermedia API web services.'),
            ('MongoDB', cat_db, 'Document-oriented NoSQL database for flexible JSON-style schema design.'),
            ('PostgreSQL', cat_db, 'Enterprise-grade open source object-relational SQL database.'),
            ('SQL', cat_db, 'Structured Query Language for querying and managing relational databases.'),
            ('Docker', cat_devops, 'OS-level containerization for predictable and portable application deployments.'),
            ('Git & GitHub', cat_devops, 'Distributed version control and collaborative code repository hosting.'),
            ('Data Structures', cat_cs, 'Algorithms, trees, graphs, sorting, and time/space complexity optimization.'),
            ('Problem Solving', cat_soft, 'Analytical and critical thinking to debug and engineer robust software solutions.'),
            ('Communication', cat_soft, 'Clear technical and interpersonal verbal and written communication.'),
        ]

        skills_map = {}
        for name, cat, desc in skills_data:
            s, _ = Skill.objects.get_or_create(name=name, defaults={'category': cat, 'description': desc, 'is_in_demand': True})
            skills_map[name] = s
        self.stdout.write(self.style.SUCCESS(f"[OK] Created {len(skills_map)} standardized skills"))

        # 3. Learning Resources for Skill Gaps
        resources_data = [
            ('MongoDB', 'MongoDB Fundamentals & Schema Design', 'COURSE', 'MongoDB University', 'https://learn.mongodb.com/', '6 Hours', 'BEGINNER'),
            ('MongoDB', 'Hands-on CRUD Aggregation Pipeline Project', 'PROJECT', 'SkillBridge Labs', 'https://github.com/skillbridge/mongodb-crud-starter', '2 Days', 'INTERMEDIATE'),
            ('React.js', 'Modern React 18: Hooks, Context & State', 'COURSE', 'freeCodeCamp', 'https://www.freecodecamp.org/learn', '10 Hours', 'INTERMEDIATE'),
            ('React.js', 'Full Stack Dashboard Project with React', 'PROJECT', 'SkillBridge Projects', 'https://github.com/skillbridge/react-admin-dashboard', '3 Days', 'INTERMEDIATE'),
            ('Node.js', 'Building Asynchronous Microservices with Node & Express', 'COURSE', 'Coursera', 'https://www.coursera.org/', '8 Hours', 'INTERMEDIATE'),
            ('Docker', 'Docker & Containerization for Developers', 'DOCS', 'Docker Docs', 'https://docs.docker.com/get-started/', '4 Hours', 'BEGINNER'),
            ('Django', 'Scalable Django REST Framework Architecture', 'COURSE', 'Django Project', 'https://www.django-rest-framework.org/', '12 Hours', 'INTERMEDIATE'),
            ('PostgreSQL', 'Advanced PostgreSQL Query Optimization & Indexing', 'PRACTICE', 'Postgres Tutorial', 'https://www.postgresqltutorial.com/', '5 Hours', 'ADVANCED'),
        ]
        for skill_name, title, r_type, provider, url, duration, diff in resources_data:
            if skill_name in skills_map:
                LearningResource.objects.get_or_create(
                    skill=skills_map[skill_name],
                    title=title,
                    defaults={'resource_type': r_type, 'provider': provider, 'url': url, 'duration': duration, 'difficulty': diff}
                )

        # 4. Skill Assessments & MCQs
        py_assessment, _ = SkillAssessment.objects.get_or_create(
            skill=skills_map['Python'],
            title='Python Core & Advanced Concepts',
            defaults={'description': 'Evaluate memory model, list comprehensions, decorators, and data structures.', 'time_limit_minutes': 10, 'passing_score': 60}
        )
        questions_py = [
            (
                "What is the output of `type(lambda: None)` in Python 3?",
                "<class 'function'>",
                "<class 'lambda'>",
                "<class 'NoneType'>",
                "<class 'object'>",
                "A",
                "In Python, lambdas create anonymous function instances, so type() returns <class 'function'>."
            ),
            (
                "Which built-in Python data structure uses a hash table internally?",
                "List",
                "Tuple",
                "Dictionary",
                "String",
                "C",
                "Python dictionaries and sets are implemented as optimized sparse hash tables providing average O(1) lookups."
            ),
            (
                "What is the purpose of Python's `__init__` method?",
                "Allocates memory for a new object",
                "Initializes newly created object instances",
                "Destroys an instance at runtime",
                "Imports a module into namespace",
                "B",
                "`__new__` allocates memory, while `__init__` initializes the attributes of the newly created instance."
            ),
            (
                "How are arguments passed in Python?",
                "Strictly Call by Value",
                "Strictly Call by Reference",
                "Call by Object Reference (Pass by Assignment)",
                "Call by Macro Substitution",
                "C",
                "Python uses 'Pass by Object Reference'; references to objects are passed by value."
            ),
        ]
        for q_text, a, b, c, d, correct, expl in questions_py:
            AssessmentQuestion.objects.get_or_create(
                assessment=py_assessment,
                question_text=q_text,
                defaults={'option_a': a, 'option_b': b, 'option_c': c, 'option_d': d, 'correct_option': correct, 'explanation': expl}
            )

        js_assessment, _ = SkillAssessment.objects.get_or_create(
            skill=skills_map['JavaScript'],
            title='Modern JavaScript & Asynchronous Architecture',
            defaults={'description': 'Covers event loops, closures, promises, and modern ES6+ standards.', 'time_limit_minutes': 10, 'passing_score': 60}
        )
        questions_js = [
            (
                "Which statement accurately describes closures in JavaScript?",
                "A function bundled together with references to its lexical environment",
                "A technique to close DOM events",
                "A strict JSON serializing method",
                "A way to terminate asynchronous workers",
                "A",
                "A closure gives a function access to its outer lexical scope even after the outer function has executed."
            ),
            (
                "What does `typeof null` evaluate to in JavaScript?",
                "'null'",
                "'undefined'",
                "'object'",
                "'boolean'",
                "'object'",
                "Due to a historical bug in the initial JS implementation, `typeof null` returns 'object'."
            ),
            (
                "Which queue has priority in the JavaScript Event Loop?",
                "Macrotask (Task) Queue",
                "Microtask Queue (Promises)",
                "Rendering Queue",
                "Timer Queue",
                "B",
                "Microtasks (e.g. Promise callbacks, queueMicrotask) are processed completely before the next macrotask runs."
            ),
        ]
        for q_text, a, b, c, d, correct, expl in questions_js:
            AssessmentQuestion.objects.get_or_create(
                assessment=js_assessment,
                question_text=q_text,
                defaults={'option_a': a, 'option_b': b, 'option_c': c, 'option_d': d, 'correct_option': correct, 'explanation': expl}
            )

        # 5. College & TPO Account
        tpo_user, _ = CustomUser.objects.get_or_create(
            username='tpo_rvce',
            defaults={
                'first_name': 'Prof. Ramesh',
                'last_name': 'Kumar',
                'email': 'tpo@rvce.edu.in',
                'role': 'COLLEGE',
                'phone': '+91 9876543210',
            }
        )
        tpo_user.set_password(get_seed_pwd('tpo'))
        tpo_user.save()

        college, _ = College.objects.get_or_create(
            user=tpo_user,
            defaults={
                'name': 'RV College of Engineering',
                'code': 'RVCE-01',
                'university': 'Visvesvaraya Technological University',
                'location': 'Bengaluru, Karnataka',
                'website': 'https://www.rvce.edu.in',
                'tpo_name': 'Prof. Ramesh Kumar',
                'tpo_email': 'tpo@rvce.edu.in',
                'tpo_phone': '+91 9876543210',
                'is_verified': True,
            }
        )
        dept_cse, _ = Department.objects.get_or_create(college=college, code='CSE', defaults={'name': 'Computer Science & Engineering'})
        dept_it, _ = Department.objects.get_or_create(college=college, code='IT', defaults={'name': 'Information Technology'})
        dept_ece, _ = Department.objects.get_or_create(college=college, code='ECE', defaults={'name': 'Electronics & Communication Engineering'})
        self.stdout.write(self.style.SUCCESS("[OK] College created: RV College of Engineering (tpo_rvce)"))

        # 6. Recruiter Accounts & Companies
        rec_user1, _ = CustomUser.objects.get_or_create(
            username='recruiter_google',
            defaults={
                'first_name': 'Pooja',
                'last_name': 'Sharma',
                'email': 'pooja.sharma@google.com',
                'role': 'INDUSTRY',
                'phone': '+91 9123456780',
            }
        )
        rec_user1.set_password(get_seed_pwd('tech'))
        rec_user1.save()

        comp_google, _ = Company.objects.get_or_create(
            user=rec_user1,
            defaults={
                'company_name': 'Google Cloud India',
                'industry_type': 'Cloud & Enterprise Software',
                'website': 'https://cloud.google.com',
                'location': 'Bengaluru, Karnataka',
                'description': 'Leading enterprise cloud computing, developer platforms, and distributed systems engineering.',
                'is_verified': True,
            }
        )

        rec_user2, _ = CustomUser.objects.get_or_create(
            username='recruiter_tcs',
            defaults={
                'first_name': 'Ananya',
                'last_name': 'Deshmukh',
                'email': 'ananya.deshmukh@tcs.com',
                'role': 'INDUSTRY',
                'phone': '+91 9811223344',
            }
        )
        rec_user2.set_password(get_seed_pwd('tech'))
        rec_user2.save()

        comp_tcs, _ = Company.objects.get_or_create(
            user=rec_user2,
            defaults={
                'company_name': 'Tata Consultancy Services',
                'industry_type': 'Information Technology & Consulting',
                'website': 'https://www.tcs.com',
                'location': 'Bengaluru, Karnataka',
                'description': 'Global leader in IT services, digital and business solutions.',
                'is_verified': True,
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Recruiters created: recruiter_google & recruiter_tcs"))

        # 7. Student Profiles
        # Student 1: Rahul Verma (High Skill Match for Full Stack)
        st_user1, _ = CustomUser.objects.get_or_create(
            username='student_rahul',
            defaults={
                'first_name': 'Rahul',
                'last_name': 'Verma',
                'email': 'rahul.verma@student.rvce.edu.in',
                'role': 'STUDENT',
                'phone': '+91 9845012345',
            }
        )
        st_user1.set_password(get_seed_pwd('rahul'))
        st_user1.save()

        profile_rahul, _ = StudentProfile.objects.get_or_create(
            user=st_user1,
            defaults={
                'college': college,
                'department': dept_cse,
                'roll_number': '1RV22CS104',
                'degree': 'B.Tech',
                'semester': 7,
                'graduation_year': 2026,
                'cgpa': 8.85,
                'bio': 'Passionate Full Stack engineer with extensive hands-on experience in Django, React, RESTful architectures, and microservices.',
                'github_url': 'https://github.com/rahulverma-dev',
                'linkedin_url': 'https://linkedin.com/in/rahulverma',
            }
        )

        # Assign skills to Rahul
        # JavaScript: 90%, React: 65%, Node.js: 70%, MongoDB: 40%, Git: 80%, Python: 85%
        rahul_skills = [
            ('JavaScript', 90, True, 92),
            ('React.js', 65, False, 0),
            ('Node.js', 70, False, 0),
            ('MongoDB', 40, False, 0),
            ('Git & GitHub', 80, True, 85),
            ('Python', 85, True, 88),
            ('Django', 82, True, 84),
            ('REST APIs', 85, True, 86),
            ('Problem Solving', 88, True, 90),
        ]
        for s_name, prof, is_v, v_score in rahul_skills:
            if s_name in skills_map:
                StudentSkill.objects.update_or_create(
                    student=profile_rahul,
                    skill=skills_map[s_name],
                    defaults={'proficiency': prof, 'is_verified': is_v, 'verified_score': v_score, 'verified_at': timezone.now() if is_v else None}
                )

        StudentProject.objects.get_or_create(
            student=profile_rahul,
            title='Decentralized Microservices E-Commerce API',
            defaults={
                'description': 'Designed and implemented high-concurrency order placement and payment endpoints using Django REST framework and Redis caching.',
                'technologies': 'Python, Django, PostgreSQL, Redis, Docker',
                'github_link': 'https://github.com/rahulverma-dev/ecommerce-microservices'
            }
        )
        StudentProject.objects.get_or_create(
            student=profile_rahul,
            title='Interactive Real-Time Collaborative Canvas',
            defaults={
                'description': 'Real-time collaborative drawing whiteboard using React, WebSockets, and Node.js event broker.',
                'technologies': 'React.js, Node.js, WebSockets, TailwindCSS',
                'github_link': 'https://github.com/rahulverma-dev/collab-canvas'
            }
        )

        # Student 2: Priya Nair (Data & Cloud Focus)
        st_user2, _ = CustomUser.objects.get_or_create(
            username='student_priya',
            defaults={
                'first_name': 'Priya',
                'last_name': 'Nair',
                'email': 'priya.nair@student.rvce.edu.in',
                'role': 'STUDENT',
                'phone': '+91 9741098765',
            }
        )
        st_user2.set_password(get_seed_pwd('priya'))
        st_user2.save()

        profile_priya, _ = StudentProfile.objects.get_or_create(
            user=st_user2,
            defaults={
                'college': college,
                'department': dept_it,
                'roll_number': '1RV22IT045',
                'degree': 'B.Tech',
                'semester': 7,
                'graduation_year': 2026,
                'cgpa': 9.15,
                'bio': 'Backend developer focused on relational schema design, high-performance PostgreSQL queries, and automated CI/CD pipelines.',
                'github_url': 'https://github.com/priyanair',
                'linkedin_url': 'https://linkedin.com/in/priyanair',
            }
        )
        priya_skills = [
            ('Python', 92, True, 94),
            ('PostgreSQL', 88, True, 90),
            ('SQL', 90, True, 95),
            ('Django', 85, True, 86),
            ('Docker', 75, False, 0),
            ('Git & GitHub', 85, True, 88),
            ('Communication', 90, True, 90),
        ]
        for s_name, prof, is_v, v_score in priya_skills:
            if s_name in skills_map:
                StudentSkill.objects.update_or_create(
                    student=profile_priya,
                    skill=skills_map[s_name],
                    defaults={'proficiency': prof, 'is_verified': is_v, 'verified_score': v_score, 'verified_at': timezone.now() if is_v else None}
                )

        # Student 3: Amit Patel (Demonstrating Skill Deficit / Needing Training)
        st_user3, _ = CustomUser.objects.get_or_create(
            username='student_amit',
            defaults={
                'first_name': 'Amit',
                'last_name': 'Patel',
                'email': 'amit.patel@student.rvce.edu.in',
                'role': 'STUDENT',
                'phone': '+91 9611223344',
            }
        )
        st_user3.set_password(get_seed_pwd('amit'))
        st_user3.save()

        profile_amit, _ = StudentProfile.objects.get_or_create(
            user=st_user3,
            defaults={
                'college': college,
                'department': dept_ece,
                'roll_number': '1RV22EC012',
                'degree': 'B.Tech',
                'semester': 7,
                'graduation_year': 2026,
                'cgpa': 7.20,
                'bio': 'Electronics engineering student transitioning into software development. Eager to master web technologies.',
            }
        )
        amit_skills = [
            ('Python', 65, False, 0),
            ('SQL', 50, False, 0),
            ('Problem Solving', 70, False, 0),
        ]
        for s_name, prof, is_v, v_score in amit_skills:
            if s_name in skills_map:
                StudentSkill.objects.update_or_create(
                    student=profile_amit,
                    skill=skills_map[s_name],
                    defaults={'proficiency': prof, 'is_verified': is_v, 'verified_score': v_score}
                )

        self.stdout.write(self.style.SUCCESS("[OK] Students created: student_rahul, student_priya, student_amit"))

        # 8. Industry Job Postings with Weighted Skill Requirements
        # Job 1: Full Stack Developer at Google Cloud
        job1, _ = JobPosting.objects.get_or_create(
            company=comp_google,
            title='Full Stack Cloud Developer',
            defaults={
                'job_type': 'FULL_TIME',
                'description': 'We are seeking passionate Full Stack Software Engineers to build modern, hyper-scalable cloud portals. You will architect frontend single-page interfaces, design high-throughput REST APIs, and manage distributed document stores.',
                'min_cgpa': 7.5,
                'eligible_departments': 'CSE, IT, ECE',
                'stipend_salary': '₹18 - 24 LPA',
                'location_type': 'HYBRID',
                'location_city': 'Bengaluru',
                'vacancies': 8,
                'deadline': (timezone.now() + timedelta(days=45)).date(),
                'is_active': True,
            }
        )
        # Weights: JavaScript (85% req, 90 wt), React (80% req, 85 wt), Node.js (80% req, 80 wt), MongoDB (75% req, 75 wt), REST APIs (80% req, 80 wt), Git (60% req, 65 wt)
        job1_reqs = [
            ('JavaScript', 90, 85),
            ('React.js', 85, 80),
            ('Node.js', 80, 80),
            ('MongoDB', 75, 75),
            ('REST APIs', 80, 80),
            ('Git & GitHub', 65, 60),
        ]
        for s_name, weight, min_p in job1_reqs:
            if s_name in skills_map:
                JobSkillRequirement.objects.update_or_create(
                    job=job1,
                    skill=skills_map[s_name],
                    defaults={'importance_weight': weight, 'min_proficiency': min_p}
                )

        # Job 2: Backend Python Engineer at TCS
        job2, _ = JobPosting.objects.get_or_create(
            company=comp_tcs,
            title='Backend Python & Cloud Engineer',
            defaults={
                'job_type': 'FULL_TIME',
                'description': 'Design mission-critical financial backend services. Involves building high-throughput microservices using Python, Django, PostgreSQL, and Docker containerization.',
                'min_cgpa': 7.0,
                'eligible_departments': 'CSE, IT, ECE',
                'stipend_salary': '₹9 - 14 LPA',
                'location_type': 'HYBRID',
                'location_city': 'Bengaluru',
                'vacancies': 15,
                'deadline': (timezone.now() + timedelta(days=30)).date(),
                'is_active': True,
            }
        )
        job2_reqs = [
            ('Python', 95, 85),
            ('Django', 90, 80),
            ('PostgreSQL', 85, 75),
            ('Docker', 75, 65),
            ('Git & GitHub', 70, 70),
        ]
        for s_name, weight, min_p in job2_reqs:
            if s_name in skills_map:
                JobSkillRequirement.objects.update_or_create(
                    job=job2,
                    skill=skills_map[s_name],
                    defaults={'importance_weight': weight, 'min_proficiency': min_p}
                )

        # Job 3: Cloud & Web Development Intern at Google Cloud
        job3, _ = JobPosting.objects.get_or_create(
            company=comp_google,
            title='Cloud Infrastructure & Web Intern (Summer 2026)',
            defaults={
                'job_type': 'INTERNSHIP',
                'description': 'Summer internship for pre-final and final year engineering students. Work alongside senior Google engineers on internal developer tooling, cloud diagnostics, and telemetry dashboards.',
                'min_cgpa': 8.0,
                'eligible_departments': 'CSE, IT',
                'stipend_salary': '₹55,000 / month',
                'location_type': 'ONSITE',
                'location_city': 'Bengaluru',
                'vacancies': 5,
                'deadline': (timezone.now() + timedelta(days=20)).date(),
                'is_active': True,
            }
        )
        job3_reqs = [
            ('Python', 90, 75),
            ('Data Structures', 85, 80),
            ('Git & GitHub', 70, 65),
            ('Problem Solving', 80, 75),
        ]
        for s_name, weight, min_p in job3_reqs:
            if s_name in skills_map:
                JobSkillRequirement.objects.update_or_create(
                    job=job3,
                    skill=skills_map[s_name],
                    defaults={'importance_weight': weight, 'min_proficiency': min_p}
                )
        self.stdout.write(self.style.SUCCESS("[OK] Active job postings and weighted skill requirements created"))

        # 9. Applications in Pipeline
        # Rahul Verma applied to Google Full Stack
        app1, _ = Application.objects.get_or_create(
            job=job1,
            student=profile_rahul,
            defaults={
                'status': 'INTERVIEW',
                'match_score_at_application': 84,
                'cover_note': 'I have built multiple full stack applications with Django and React, and I look forward to contributing to Google Cloud portals.',
                'interview_date': timezone.now() + timedelta(days=3, hours=4),
                'interview_mode': 'Google Meet Virtual Video Conference',
                'interview_link': 'https://meet.google.com/abc-defg-hij',
                'recruiter_notes': 'Strong technical foundation. Great algorithmic and REST API clarity. Interview scheduled for technical architecture round.'
            }
        )

        # Priya Nair applied to TCS Backend
        app2, _ = Application.objects.get_or_create(
            job=job2,
            student=profile_priya,
            defaults={
                'status': 'SELECTED',
                'match_score_at_application': 92,
                'cover_note': 'Specialized in relational database performance and Django backends.',
                'recruiter_notes': 'Candidate cleared technical rounds with distinction. Offer letter generated.'
            }
        )

        # 10. Industry Skill Demand Forecasts
        demand1, _ = SkillDemandReport.objects.get_or_create(
            company=comp_google,
            title='Projected Demand for 45 Cloud & DevOps Engineers (Q3/Q4 2026)',
            defaults={
                'target_role': 'Cloud Infrastructure & DevOps Engineer',
                'expected_hires': 45,
                'target_timeline': 'Next 3-6 Months',
                'description': 'Rapid growth in generative AI and cloud infrastructure workloads has accelerated our demand for candidates proficient in Docker, Kubernetes, Python, and microservice APIs.'
            }
        )
        demand1.demanded_skills.set([skills_map['Docker'], skills_map['Python'], skills_map['REST APIs'], skills_map['Git & GitHub']])

        demand2, _ = SkillDemandReport.objects.get_or_create(
            company=comp_tcs,
            title='Hiring Demand for 80 Full Stack Web Developers',
            defaults={
                'target_role': 'Enterprise Full Stack Developer',
                'expected_hires': 80,
                'target_timeline': 'Next 6-9 Months',
                'description': 'Global banking clients are upgrading legacy stacks to modern React and Node.js microservices. Colleges are requested to emphasize async programming and database modeling.'
            }
        )
        demand2.demanded_skills.set([skills_map['React.js'], skills_map['Node.js'], skills_map['MongoDB'], skills_map['JavaScript']])

        # 11. Workshop Proposal
        ws1, _ = WorkshopProposal.objects.get_or_create(
            title='Production Microservices with Django, Docker & PostgreSQL',
            defaults={
                'proposer_type': 'INDUSTRY',
                'company': comp_google,
                'college': college,
                'proposed_date': (timezone.now() + timedelta(days=12)).date(),
                'duration_hours': 4,
                'speaker_name': 'Dr. Pooja Sharma',
                'speaker_designation': 'Senior Cloud Architect at Google',
                'status': 'ACCEPTED',
                'description': 'A 4-hour hands-on industrial workshop covering containerization, 12-factor apps, production database migrations, and CI/CD pipelines.'
            }
        )
        ws1.target_skills.set([skills_map['Django'], skills_map['Docker'], skills_map['PostgreSQL']])

        # 12. Live Project Opportunity
        proj1, _ = LiveProject.objects.get_or_create(
            company=comp_google,
            title='Real-Time Event Telemetry & Alerting Pipeline',
            defaults={
                'domain': 'Distributed Systems & Cloud Telemetry',
                'team_size_limit': 4,
                'submission_deadline': (timezone.now() + timedelta(days=60)).date(),
                'is_active': True,
                'description': 'Build a lightweight event ingestion daemon that collects server heartbeat metrics, validates payloads, and flags abnormal memory spikes in real time. Winning teams receive direct interview fast-tracks!'
            }
        )
        proj1.required_skills.set([skills_map['Python'], skills_map['Docker'], skills_map['REST APIs']])

        # 13. System Notifications
        Notification.objects.get_or_create(
            user=st_user1,
            title='Interview Scheduled: Full Stack Cloud Developer! 📅',
            defaults={
                'message': 'Google Cloud India has scheduled an interview on ' + (timezone.now() + timedelta(days=3)).strftime('%d %B %Y') + ' via Google Meet.',
                'link': '/student/applications/'
            }
        )
        Notification.objects.get_or_create(
            user=st_user2,
            title='Selection Offer: Backend Python & Cloud Engineer 🎉',
            defaults={
                'message': 'Congratulations! Tata Consultancy Services has extended a selection offer for your application.',
                'link': '/student/applications/'
            }
        )
        Notification.objects.get_or_create(
            user=tpo_user,
            title='New Industry Workshop Scheduled',
            defaults={
                'message': 'Google Cloud India accepted the workshop proposal on Production Microservices for RVCE students.',
                'link': '/collaboration/'
            }
        )

        self.stdout.write(self.style.SUCCESS("[OK] Seeded skill demands, workshops, live projects, and system notifications"))
        self.stdout.write(self.style.SUCCESS("SkillBridge demo dataset successfully seeded! Ready for demonstration."))
