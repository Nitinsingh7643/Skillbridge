from django.urls import path
from . import views

def preview_collaboration_hub(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    request.user = User.objects.filter(role='COLLEGE').first()
    return views.collaboration_hub(request)

urlpatterns = [
    path('preview/', preview_collaboration_hub, name='preview_collaboration_hub'),
    path('', views.collaboration_hub, name='collaboration_hub'),
    path('post-demand/', views.post_skill_demand, name='post_skill_demand'),
    path('propose-workshop/', views.propose_workshop, name='propose_workshop'),
    path('workshops/<int:workshop_id>/update/<str:new_status>/', views.update_workshop_status, name='update_workshop_status'),
    path('post-live-project/', views.post_live_project, name='post_live_project'),
]

