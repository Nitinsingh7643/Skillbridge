from django.db import models
from django.conf import settings
from colleges.models import College, Department
from skills.models import Skill, SkillAssessment

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    roll_number = models.CharField(max_length=50, blank=True)
    degree = models.CharField(max_length=100, default='B.Tech')
    semester = models.IntegerField(default=7)
    graduation_year = models.IntegerField(default=2026)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=7.50)
    bio = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.roll_number or 'Student'})"

    def technical_score(self):
        skills = self.skills.filter(skill__category__name__icontains='Soft').all()
        tech_skills = self.skills.exclude(id__in=[s.id for s in skills])
        if not tech_skills.exists():
            return 0
        total = sum(s.proficiency for s in tech_skills)
        return round(total / tech_skills.count())

    def soft_score(self):
        soft_skills = self.skills.filter(skill__category__name__icontains='Soft')
        if not soft_skills.exists():
            return 70  # baseline default
        total = sum(s.proficiency for s in soft_skills)
        return round(total / soft_skills.count())

    def overall_skill_score(self):
        all_skills = self.skills.all()
        if not all_skills.exists():
            return 0
        total = sum(s.proficiency for s in all_skills)
        return round(total / all_skills.count())

    def placement_readiness(self):
        """
        Transparent placement readiness score (0 - 100%):
        - CGPA factor (max 25 pts, scaled from 10.0 CGPA)
        - Technical skill average (max 35 pts)
        - Verified skills bonus (max 20 pts: up to 4 verified skills = 5 pts each)
        - Projects count (max 20 pts: up to 4 projects = 5 pts each)
        """
        cgpa_pts = min(25.0, (float(self.cgpa) / 10.0) * 25.0)
        tech_pts = (self.technical_score() / 100.0) * 35.0
        verified_count = self.skills.filter(is_verified=True).count()
        verified_pts = min(20.0, verified_count * 5.0)
        projects_count = self.projects.count()
        project_pts = min(20.0, projects_count * 5.0)

        total = cgpa_pts + tech_pts + verified_pts + project_pts
        return min(100, round(total))

    def internship_readiness(self):
        """
        Transparent internship readiness score (0 - 100%):
        Prioritizes foundational skills and projects.
        """
        cgpa_pts = min(20.0, (float(self.cgpa) / 10.0) * 20.0)
        tech_pts = (self.technical_score() / 100.0) * 40.0
        project_pts = min(25.0, self.projects.count() * 8.0)
        skill_count_pts = min(15.0, self.skills.count() * 3.0)
        return min(100, round(cgpa_pts + tech_pts + project_pts + skill_count_pts))


class StudentSkill(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency = models.IntegerField(default=60)  # 1 to 100
    is_verified = models.BooleanField(default=False)
    verified_score = models.IntegerField(default=0)  # 0 to 100
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'skill')

    def __str__(self):
        return f"{self.student.user.username} - {self.skill.name} ({self.proficiency}%)"


class AssessmentAttempt(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='assessment_attempts')
    assessment = models.ForeignKey(SkillAssessment, on_delete=models.CASCADE, related_name='attempts')
    score = models.IntegerField()  # percentage
    passed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        status = "PASSED" if self.passed else "FAILED"
        return f"{self.student.user.username} - {self.assessment.skill.name}: {self.score}% ({status})"


class StudentProject(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField()
    technologies = models.CharField(max_length=255, help_text="Comma-separated e.g. Django, React, PostgreSQL")
    github_link = models.URLField(blank=True)
    live_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.student.user.username})"


class StudentCertification(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='certifications')
    title = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField(null=True, blank=True)
    credential_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.title} - {self.issuing_organization}"


class StudentExperience(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='experiences')
    company_name = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    duration = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.role} at {self.company_name}"
