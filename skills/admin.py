from django.contrib import admin
from .models import SkillCategory, Skill, SkillAssessment, AssessmentQuestion, LearningResource

admin.site.register(SkillCategory)
admin.site.register(Skill)
admin.site.register(SkillAssessment)
admin.site.register(AssessmentQuestion)
admin.site.register(LearningResource)
