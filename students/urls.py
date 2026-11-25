from django.urls import path
from . import views

def preview_student_dashboard(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    request.user = User.objects.filter(role='STUDENT').first()
    return views.student_dashboard(request)

def preview_student_skills(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    request.user = User.objects.filter(role='STUDENT').first()
    return views.student_skills_manage(request)

def preview_resume_parser(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    request.user = User.objects.filter(role='STUDENT').first()
    return views.resume_upload_parser(request)

def preview_student_jobs(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    request.user = User.objects.filter(role='STUDENT').first()
    return views.job_browse(request)

def preview_student_applications(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    request.user = User.objects.filter(role='STUDENT').first()
    return views.my_applications(request)

def preview_student_gap_analysis(request, job_id=5):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    request.user = User.objects.filter(role='STUDENT').first()
    return views.job_detail_and_gap_analysis(request, job_id=job_id)

def preview_student_profile(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    request.user = User.objects.filter(role='STUDENT').first()
    return views.student_profile_view(request)

urlpatterns = [
    path('preview/', preview_student_dashboard, name='preview_student_dashboard'),
    path('preview-skills/', preview_student_skills, name='preview_student_skills'),
    path('preview-resume/', preview_resume_parser, name='preview_resume_parser'),
    path('preview-jobs/', preview_student_jobs, name='preview_student_jobs'),
    path('preview-applications/', preview_student_applications, name='preview_student_applications'),
    path('preview-gap-analysis/', preview_student_gap_analysis, name='preview_student_gap_analysis'),
    path('preview-gap-analysis/<int:job_id>/', preview_student_gap_analysis, name='preview_student_gap_analysis_id'),
    path('preview-profile/', preview_student_profile, name='preview_student_profile'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('profile/', views.student_profile_view, name='student_profile_view'),
    path('profile/<int:student_id>/', views.student_profile_view, name='student_profile_detail'),
    path('profile/edit/', views.student_profile_edit, name='student_profile_edit'),
    path('skills/', views.student_skills_manage, name='student_skills_manage'),
    path('projects/', views.student_projects_manage, name='student_projects_manage'),
    path('resume/parser/', views.resume_upload_parser, name='resume_parser'),
    path('jobs/', views.job_browse, name='job_browse'),
    path('jobs/<int:job_id>/gap-analysis/', views.job_detail_and_gap_analysis, name='job_detail'),
    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('applications/', views.my_applications, name='my_applications'),
]

