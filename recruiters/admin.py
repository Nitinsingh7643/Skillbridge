from django.contrib import admin
from .models import Company, JobPosting, JobSkillRequirement, Application

admin.site.register(Company)
admin.site.register(JobPosting)
admin.site.register(JobSkillRequirement)
admin.site.register(Application)
