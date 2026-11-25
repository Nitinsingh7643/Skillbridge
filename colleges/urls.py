from django.urls import path
from . import views

def preview_print_report(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    request.user = User.objects.filter(role='COLLEGE').first()
    return views.print_placement_report(request)

urlpatterns = [
    path('dashboard/', views.tpo_dashboard, name='tpo_dashboard'),
    path('cohort-filter/', views.cohort_eligibility_filter, name='cohort_eligibility_filter'),
    path('export/csv/', views.export_placement_report_csv, name='export_placement_report_csv'),
    path('report/print/', views.print_placement_report, name='print_placement_report'),
    path('report/preview/', preview_print_report, name='preview_print_report'),
]

