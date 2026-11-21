from django.urls import path
from . import views

urlpatterns = [
    path('', views.collaboration_hub, name='collaboration_hub'),
    path('post-demand/', views.post_skill_demand, name='post_skill_demand'),
    path('propose-workshop/', views.propose_workshop, name='propose_workshop'),
    path('workshops/<int:workshop_id>/update/<str:new_status>/', views.update_workshop_status, name='update_workshop_status'),
    path('post-live-project/', views.post_live_project, name='post_live_project'),
]

