from django.db import models

class SkillCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Skill Categories"

    def __str__(self):
        return self.name


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(SkillCategory, on_delete=models.CASCADE, related_name='skills')
    description = models.TextField(blank=True)
    is_in_demand = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SkillAssessment(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='assessments')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    time_limit_minutes = models.IntegerField(default=10)
    passing_score = models.IntegerField(default=60)  # percentage

    def __str__(self):
        return f"{self.skill.name} Assessment - {self.title}"


class AssessmentQuestion(models.Model):
    OPTION_CHOICES = (
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    )
    assessment = models.ForeignKey(SkillAssessment, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    explanation = models.TextField(blank=True)

    def __str__(self):
        return f"Q: {self.question_text[:50]}..."


class LearningResource(models.Model):
    RESOURCE_TYPES = (
        ('COURSE', 'Online Course'),
        ('PROJECT', 'Hands-on Project'),
        ('DOCS', 'Documentation & Tutorial'),
        ('PRACTICE', 'Coding & Practice Exercise'),
    )
    DIFFICULTY_LEVELS = (
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
    )
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='learning_resources')
    title = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default='COURSE')
    provider = models.CharField(max_length=100)
    url = models.URLField()
    duration = models.CharField(max_length=50, blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='BEGINNER')

    def __str__(self):
        return f"{self.title} ({self.skill.name})"
