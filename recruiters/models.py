from django.db import models
from django.conf import settings
from skills.models import Skill
from students.models import StudentProfile

class Company(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=255)
    industry_type = models.CharField(max_length=150, default='Information Technology')
    website = models.URLField(blank=True)
    location = models.CharField(max_length=255, default='Bengaluru, India')
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.company_name


class JobPosting(models.Model):
    JOB_TYPE_CHOICES = (
        ('INTERNSHIP', 'Internship'),
        ('FULL_TIME', 'Full-Time Placement'),
        ('PPO', 'Pre-Placement Offer (PPO)'),
    )
    LOCATION_TYPE_CHOICES = (
        ('REMOTE', 'Remote'),
        ('HYBRID', 'Hybrid'),
        ('ONSITE', 'On-site'),
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=200)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='FULL_TIME')
    description = models.TextField()
    min_cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=6.5)
    eligible_departments = models.CharField(max_length=255, default='CSE, IT, ECE, EEE', help_text="Comma-separated codes")
    stipend_salary = models.CharField(max_length=100, default='₹8 - 12 LPA')
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPE_CHOICES, default='HYBRID')
    location_city = models.CharField(max_length=100, default='Bengaluru')
    vacancies = models.IntegerField(default=5)
    deadline = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.company.company_name} ({self.get_job_type_display()})"


class JobSkillRequirement(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='skill_requirements')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    importance_weight = models.IntegerField(default=80, help_text="Weight w_i from 1 to 100")
    min_proficiency = models.IntegerField(default=70, help_text="Required proficiency from 1 to 100")

    class Meta:
        unique_together = ('job', 'skill')

    def __str__(self):
        return f"{self.job.title} requires {self.skill.name} (Min: {self.min_proficiency}%, Weight: {self.importance_weight})"


class Application(models.Model):
    STATUS_CHOICES = (
        ('APPLIED', 'Applied'),
        ('UNDER_REVIEW', 'Under Review'),
        ('SHORTLISTED', 'Shortlisted'),
        ('INTERVIEW', 'Interview Scheduled'),
        ('SELECTED', 'Selected'),
        ('REJECTED', 'Rejected'),
    )
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPLIED')
    applied_at = models.DateTimeField(auto_now_add=True)
    cover_note = models.TextField(blank=True)
    match_score_at_application = models.IntegerField(default=0)
    interview_date = models.DateTimeField(null=True, blank=True)
    interview_mode = models.CharField(max_length=100, blank=True, help_text="e.g. Google Meet, On-Campus")
    interview_link = models.URLField(blank=True)
    recruiter_notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('job', 'student')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.student.user.username} -> {self.job.title} [{self.get_status_display()}]"
