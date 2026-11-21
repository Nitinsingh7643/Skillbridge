from django.db import models
from django.conf import settings

class College(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='college_profile')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    university = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    tpo_name = models.CharField(max_length=150, blank=True)
    tpo_email = models.EmailField(blank=True)
    tpo_phone = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20)

    class Meta:
        unique_together = ('college', 'code')

    def __str__(self):
        return f"{self.name} ({self.code})"
