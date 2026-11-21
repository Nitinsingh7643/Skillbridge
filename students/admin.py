from django.contrib import admin
from .models import (
    StudentProfile, StudentSkill, AssessmentAttempt,
    StudentProject, StudentCertification, StudentExperience
)

admin.site.register(StudentProfile)
admin.site.register(StudentSkill)
admin.site.register(AssessmentAttempt)
admin.site.register(StudentProject)
admin.site.register(StudentCertification)
admin.site.register(StudentExperience)
