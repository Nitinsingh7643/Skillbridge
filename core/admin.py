from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Notification

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Roles & Approvals', {'fields': ('role', 'phone', 'is_approved', 'profile_image')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_approved', 'is_staff')
    list_filter = ('role', 'is_approved', 'is_staff', 'is_superuser')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Notification)
