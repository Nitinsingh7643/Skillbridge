import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Avg

from core.decorators import college_required
from .models import College, Department
from students.models import StudentProfile, StudentSkill
from recruiters.models import JobPosting, Application
from skills.models import Skill
from skills.gap_engine import calculate_skill_gap_and_match
from collaboration.models import SkillDemandReport, WorkshopProposal

@login_required
@college_required
def tpo_dashboard(request):
    college, _ = College.objects.get_or_create(
        user=request.user,
        defaults={'name': f"{request.user.first_name or request.user.username}'s Institution"}
    )
    
    students = StudentProfile.objects.filter(college=college).select_related('user', 'department').prefetch_related('skills', 'applications')
    total_students = students.count()
    
    # Department breakdown
    dept_stats = Department.objects.filter(college=college).annotate(student_count=Count('students'))

    # Placement metrics
    placed_students_count = Application.objects.filter(student__college=college, status='SELECTED').values('student').distinct().count()
    interviewing_count = Application.objects.filter(student__college=college, status='INTERVIEW').values('student').distinct().count()

    # Calculate average cohort readiness
    readiness_scores = [s.placement_readiness() for s in students]
    avg_readiness = round(sum(readiness_scores) / len(readiness_scores)) if readiness_scores else 0
    needing_training_count = sum(1 for score in readiness_scores if score < 60)

    # Recent industry skill demands
    recent_demands = SkillDemandReport.objects.select_related('company').prefetch_related('demanded_skills')[:5]

    context = {
        'college': college,
        'total_students': total_students,
        'dept_stats': dept_stats,
        'placed_students_count': placed_students_count,
        'interviewing_count': interviewing_count,
        'avg_readiness': avg_readiness,
        'needing_training_count': needing_training_count,
        'students': students[:10],
        'recent_demands': recent_demands,
    }
    return render(request, 'colleges/dashboard.html', context)


@login_required
@college_required
def cohort_eligibility_filter(request):
    """
    Cohort Match Feature:
    TPO selects a company job requirement, and system maps and ranks
    which college students meet criteria and identifies training gaps!
    """
    college, _ = College.objects.get_or_create(user=request.user)
    students = StudentProfile.objects.filter(college=college).select_related('user', 'department').prefetch_related('skills__skill')
    
    active_jobs = JobPosting.objects.filter(is_active=True).select_related('company').prefetch_related('skill_requirements__skill')
    selected_job_id = request.GET.get('job_id')
    selected_job = None
    evaluated_students = []
    cohort_gap_counts = {}

    if selected_job_id:
        selected_job = active_jobs.filter(id=selected_job_id).first()

    if selected_job:
        for s in students:
            # Check eligibility: CGPA & Department
            cgpa_pass = s.cgpa >= selected_job.min_cgpa
            dept_pass = True
            if s.department and selected_job.eligible_departments:
                dept_pass = (s.department.code.lower() in selected_job.eligible_departments.lower())

            analysis = calculate_skill_gap_and_match(s, selected_job)
            match_score = analysis['match_score']

            # Aggregate common cohort skill gaps
            for gap_item in analysis['gap_skills']:
                s_name = gap_item['skill_name']
                cohort_gap_counts[s_name] = cohort_gap_counts.get(s_name, 0) + 1

            evaluated_students.append({
                'student': s,
                'cgpa_pass': cgpa_pass,
                'dept_pass': dept_pass,
                'is_eligible': cgpa_pass and dept_pass,
                'match_score': match_score,
                'gap_score': analysis['gap_score'],
                'gap_skills': analysis['gap_skills'][:3],
                'matching_skills': analysis['matching_skills'][:3],
            })

        # Sort: eligible first, then highest match score
        evaluated_students.sort(key=lambda x: (x['is_eligible'], x['match_score']), reverse=True)

    # Sort common cohort gaps
    sorted_cohort_gaps = sorted(cohort_gap_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    context = {
        'college': college,
        'active_jobs': active_jobs,
        'selected_job': selected_job,
        'evaluated_students': evaluated_students,
        'sorted_cohort_gaps': sorted_cohort_gaps,
        'total_evaluated': len(evaluated_students),
        'total_eligible': sum(1 for e in evaluated_students if e['is_eligible']),
    }
    return render(request, 'colleges/cohort_filter.html', context)


@login_required
@college_required
def export_placement_report_csv(request):
    college, _ = College.objects.get_or_create(user=request.user)
    students = StudentProfile.objects.filter(college=college).select_related('user', 'department')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="SkillBridge_{college.code or "College"}_Placement_Report.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Student Name', 'Roll Number', 'Email', 'Department',
        'Semester', 'CGPA', 'Placement Readiness (%)', 'Technical Score (%)',
        'Verified Skills Count', 'Projects Count'
    ])

    for s in students:
        verified_count = s.skills.filter(is_verified=True).count()
        writer.writerow([
            s.user.get_full_name() or s.user.username,
            s.roll_number,
            s.user.email,
            s.department.code if s.department else 'N/A',
            s.semester,
            s.cgpa,
            s.placement_readiness(),
            s.technical_score(),
            verified_count,
            s.projects.count()
        ])

    return response


@login_required
@college_required
def print_placement_report(request):
    college, _ = College.objects.get_or_create(user=request.user)
    students = StudentProfile.objects.filter(college=college).select_related('user', 'department').prefetch_related('skills', 'projects')
    departments = Department.objects.filter(college=college)

    total_students = students.count()
    placed_student_ids = set(
        Application.objects.filter(student__college=college, status='SELECTED').values_list('student_id', flat=True)
    )
    placed_count = len(placed_student_ids)

    student_rows = []
    readiness_list = []
    total_verified_skills = 0
    total_projects = 0

    for s in students:
        readiness = s.placement_readiness()
        readiness_list.append(readiness)
        total_skills = s.skills.count()
        verified_skills = s.skills.filter(is_verified=True).count()
        proj_count = s.projects.count()
        total_verified_skills += verified_skills
        total_projects += proj_count

        student_rows.append({
            'student': s,
            'readiness': readiness,
            'tech_score': s.technical_score(),
            'total_skills': total_skills,
            'verified_skills': verified_skills,
            'projects_count': proj_count,
            'is_placed': s.id in placed_student_ids,
        })

    avg_readiness = round(sum(readiness_list) / len(readiness_list)) if readiness_list else 0
    placement_rate = round((placed_count / total_students) * 100) if total_students > 0 else 0

    return render(request, 'colleges/print_report.html', {
        'college': college,
        'students': students,
        'student_rows': student_rows,
        'departments': departments,
        'total_students': total_students,
        'placed_count': placed_count,
        'placement_rate': placement_rate,
        'avg_readiness': avg_readiness,
        'total_verified_skills': total_verified_skills,
        'total_projects': total_projects,
    })
