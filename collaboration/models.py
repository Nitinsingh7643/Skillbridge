from django.db import models
from skills.models import Skill
from recruiters.models import Company
from colleges.models import College

class SkillDemandReport(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='demand_reports')
    title = models.CharField(max_length=255)
    target_role = models.CharField(max_length=150)
    expected_hires = models.IntegerField(default=10)
    demanded_skills = models.ManyToManyField(Skill, related_name='demand_reports')
    target_timeline = models.CharField(max_length=100, default='Next 3-6 Months')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.company.company_name}: {self.target_role} ({self.expected_hires} hires)"


class WorkshopProposal(models.Model):
    PROPOSER_TYPES = (
        ('INDUSTRY', 'Industry Expert Proposed'),
        ('COLLEGE', 'College Requested'),
    )
    STATUS_CHOICES = (
        ('PROPOSED', 'Proposed'),
        ('ACCEPTED', 'Accepted & Scheduled'),
        ('COMPLETED', 'Completed'),
    )
    proposer_type = models.CharField(max_length=20, choices=PROPOSER_TYPES, default='INDUSTRY')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='workshops')
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True, related_name='workshops')
    title = models.CharField(max_length=255)
    target_skills = models.ManyToManyField(Skill, related_name='workshops')
    proposed_date = models.DateField()
    duration_hours = models.IntegerField(default=3)
    speaker_name = models.CharField(max_length=150, blank=True)
    speaker_designation = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PROPOSED')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} [{self.get_status_display()}]"


class LiveProject(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='live_projects')
    title = models.CharField(max_length=255)
    domain = models.CharField(max_length=150, default='Web Development & Cloud')
    required_skills = models.ManyToManyField(Skill, related_name='live_projects')
    team_size_limit = models.IntegerField(default=4)
    description = models.TextField()
    submission_deadline = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.company.company_name}"
