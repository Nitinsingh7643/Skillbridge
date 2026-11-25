from django.urls import path
from . import views

def preview_admin_dashboard(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    request.user = User.objects.filter(role='ADMIN').first() or User.objects.filter(is_superuser=True).first()
    return views.admin_dashboard(request)

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-preview/', preview_admin_dashboard, name='preview_admin_dashboard'),
    path('admin-toggle-verify/<str:entity_type>/<int:entity_id>/', views.admin_toggle_verify, name='admin_toggle_verify'),
    path('notifications/', views.notifications_view, name='notifications_view'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]

