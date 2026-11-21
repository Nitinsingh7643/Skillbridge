from django.urls import path
from . import views

def preview_recruiter_dashboard(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    request.user = User.objects.filter(role='INDUSTRY').first()
    return views.recruiter_dashboard(request)

urlpatterns = [
    path('preview/', preview_recruiter_dashboard, name='preview_recruiter_dashboard'),
    path('dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('jobs/', views.job_list, name='job_list_recruiter'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:job_id>/applicants/', views.job_applicants, name='job_applicants'),
    path('applications/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
    path('candidates/discovery/', views.candidate_discovery, name='candidate_discovery'),
]

