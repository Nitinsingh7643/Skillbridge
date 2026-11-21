from django.test import TestCase, Client
from django.urls import reverse
from core.models import CustomUser
from colleges.models import College, Department
from skills.models import SkillCategory, Skill, SkillAssessment, AssessmentQuestion
from students.models import StudentProfile, StudentSkill
from recruiters.models import Company, JobPosting, JobSkillRequirement, Application
from skills.gap_engine import calculate_skill_gap_and_match

class SkillBridgeTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.auth_secret = 'AuthTest' + 'Pass2026!'

        # Skill Categories & Skills
        self.cat_web = SkillCategory.objects.create(name='Web Development')
        self.cat_db = SkillCategory.objects.create(name='Databases')

        self.skill_js = Skill.objects.create(name='JavaScript', category=self.cat_web)
        self.skill_react = Skill.objects.create(name='React.js', category=self.cat_web)
        self.skill_mongo = Skill.objects.create(name='MongoDB', category=self.cat_db)

        # College & TPO
        self.tpo_user = CustomUser.objects.create_user(username='test_tpo', password=self.auth_secret, role='COLLEGE')
        self.college = College.objects.create(user=self.tpo_user, name='National Institute of Technology', code='NIT')
        self.dept_cse = Department.objects.create(college=self.college, name='CSE', code='CSE')

        # Student User
        self.student_user = CustomUser.objects.create_user(username='test_student', password=self.auth_secret, role='STUDENT')
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            college=self.college,
            department=self.dept_cse,
            cgpa=8.5,
            degree='B.Tech',
            semester=7
        )

        # Assign student skills:
        # JS: 90%, React: 65%, Mongo: 40%
        StudentSkill.objects.create(student=self.student, skill=self.skill_js, proficiency=90)
        StudentSkill.objects.create(student=self.student, skill=self.skill_react, proficiency=65)
        StudentSkill.objects.create(student=self.student, skill=self.skill_mongo, proficiency=40)

        # Recruiter & Company
        self.rec_user = CustomUser.objects.create_user(username='test_recruiter', password=self.auth_secret, role='INDUSTRY')
        self.company = Company.objects.create(user=self.rec_user, company_name='TechCorp Solutions')

        # Job Opening: Full Stack
        self.job = JobPosting.objects.create(
            company=self.company,
            title='Full Stack Developer',
            min_cgpa=7.0,
            eligible_departments='CSE, IT',
            deadline='2026-12-31'
        )

        # Requirements:
        # JS: Req 85%, Weight 90
        # React: Req 80%, Weight 85
        # Mongo: Req 75%, Weight 75
        JobSkillRequirement.objects.create(job=self.job, skill=self.skill_js, min_proficiency=85, importance_weight=90)
        JobSkillRequirement.objects.create(job=self.job, skill=self.skill_react, min_proficiency=80, importance_weight=85)
        JobSkillRequirement.objects.create(job=self.job, skill=self.skill_mongo, min_proficiency=75, importance_weight=75)

    def test_mathematical_skill_gap_formula(self):
        """
        Verify the exact mathematical formula:
        JS: Curr 90 >= Req 85 => Gap = 0. Weighted gap = 90 * 0 = 0
        React: Curr 65 < Req 80 => Gap = 15. Weighted gap = 85 * 15 = 1275
        Mongo: Curr 40 < Req 75 => Gap = 35. Weighted gap = 75 * 35 = 2625
        Total Weight = 90 + 85 + 75 = 250
        Total Weighted Gap = 0 + 1275 + 2625 = 3900
        GapScore = 3900 / 250 = 15.6
        MatchScore = round(100 - 15.6) = 84%
        """
        analysis = calculate_skill_gap_and_match(self.student, self.job)
        self.assertEqual(analysis['match_score'], 84)
        self.assertEqual(analysis['gap_score'], 15.6)
        self.assertEqual(len(analysis['gap_skills']), 2)  # React & Mongo
        self.assertEqual(len(analysis['matching_skills']), 1)  # JS

    def test_role_based_access_security(self):
        """Test that students cannot access recruiter or college pages."""
        self.client.login(username='test_student', password=self.auth_secret)
        
        # Accessing recruiter dashboard as student should redirect
        response = self.client.get(reverse('recruiter_dashboard'), follow=True)
        self.assertRedirects(response, reverse('student_dashboard'))

        # Accessing TPO dashboard as student should redirect
        response = self.client.get(reverse('tpo_dashboard'), follow=True)
        self.assertRedirects(response, reverse('student_dashboard'))

    def test_skill_assessment_verification(self):
        """Test MCQ assessment scoring and automatic badge verification."""
        assessment = SkillAssessment.objects.create(
            skill=self.skill_js,
            title='JavaScript Test',
            time_limit_minutes=10,
            passing_score=60
        )
        q1 = AssessmentQuestion.objects.create(
            assessment=assessment,
            question_text='What is 2+2 in JS?',
            option_a='4', option_b='22', option_c='NaN', option_d='0',
            correct_option='A'
        )
        q2 = AssessmentQuestion.objects.create(
            assessment=assessment,
            question_text='Is JS single-threaded?',
            option_a='No', option_b='Yes', option_c='Sometimes', option_d='Never',
            correct_option='B'
        )

        self.client.login(username='test_student', password=self.auth_secret)
        # Submit correct answers for both questions (100% score)
        response = self.client.post(reverse('submit_assessment', args=[assessment.id]), {
            f'question_{q1.id}': 'A',
            f'question_{q2.id}': 'B',
        })
        self.assertEqual(response.status_code, 200)

        # Student's JS skill should now be verified
        st_skill = StudentSkill.objects.get(student=self.student, skill=self.skill_js)
        self.assertTrue(st_skill.is_verified)
        self.assertEqual(st_skill.verified_score, 100)
