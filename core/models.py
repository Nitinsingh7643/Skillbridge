from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('COLLEGE', 'College / TPO'),
        ('INDUSTRY', 'Industry / Recruiter'),
        ('ADMIN', 'Platform Administrator'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    phone = models.CharField(max_length=20, blank=True)
    is_approved = models.BooleanField(default=True, help_text="TPO/Company accounts can be verified by admin.")
    profile_image = models.FileField(upload_to='profiles/', blank=True, null=True)

    def is_student(self):
        return self.role == 'STUDENT'

    def is_college(self):
        return self.role == 'COLLEGE'

    def is_industry(self):
        return self.role == 'INDUSTRY'

    def is_platform_admin(self):
        return self.role == 'ADMIN' or self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
