from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-toggle-verify/<str:entity_type>/<int:entity_id>/', views.admin_toggle_verify, name='admin_toggle_verify'),
    path('notifications/', views.notifications_view, name='notifications_view'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]

