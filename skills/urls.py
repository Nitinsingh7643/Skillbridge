from django.urls import path
from . import views

def preview_assessment_list(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    request.user = User.objects.filter(role='STUDENT').first()
    return views.assessment_list(request)

urlpatterns = [
    path('preview/', preview_assessment_list, name='preview_assessment_list'),
    path('catalog/', views.skill_catalog, name='skill_catalog'),
    path('assessments/', views.assessment_list, name='assessment_list'),
    path('assessments/<int:assessment_id>/take/', views.take_assessment, name='take_assessment'),
    path('assessments/<int:assessment_id>/submit/', views.submit_assessment, name='submit_assessment'),
]

