from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.tpo_dashboard, name='tpo_dashboard'),
    path('cohort-filter/', views.cohort_eligibility_filter, name='cohort_eligibility_filter'),
    path('export/csv/', views.export_placement_report_csv, name='export_placement_report_csv'),
    path('report/print/', views.print_placement_report, name='print_placement_report'),
]

