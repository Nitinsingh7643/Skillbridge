import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q

from core.decorators import recruiter_required
from core.models import Notification
from .models import Company, JobPosting, JobSkillRequirement, Application
from skills.models import Skill
from skills.gap_engine import calculate_skill_gap_and_match
from students.models import StudentProfile

@login_required
@recruiter_required
def recruiter_dashboard(request):
    company, _ = Company.objects.get_or_create(
        user=request.user,
        defaults={'company_name': f"{request.user.first_name or request.user.username}'s Company"}
    )
    
    jobs = company.jobs.all()
    active_jobs = jobs.filter(is_active=True).prefetch_related('skill_requirements__skill', 'applications')
    total_applications = Application.objects.filter(job__company=company)
    total_applications_count = total_applications.count()
    
    applied_count = total_applications.filter(status='APPLIED').count()
    under_review_count = total_applications.filter(status='UNDER_REVIEW').count()
    shortlisted_count = total_applications.filter(status='SHORTLISTED').count()
    interview_count = total_applications.filter(status='INTERVIEW').count()
    selected_count = total_applications.filter(status='SELECTED').count()
    rejected_count = total_applications.filter(status='REJECTED').count()
    
    total_vacancies = sum(j.vacancies for j in active_jobs)
    
    match_scores = [a.match_score_at_application for a in total_applications if a.match_score_at_application]
    avg_match_score = round(sum(match_scores) / len(match_scores)) if match_scores else 0
    
    high_match_count = sum(1 for s in match_scores if s >= 85)
    strong_match_count = sum(1 for s in match_scores if 70 <= s < 85)
    developing_match_count = sum(1 for s in match_scores if s < 70)
    
    next_interview = total_applications.filter(status='INTERVIEW', interview_date__isnull=False).select_related('student__user', 'job').order_by('interview_date').first()
    
    # Enrich active jobs with telemetry
    active_jobs_data = []
    for j in active_jobs:
        job_apps = j.applications.all()
        j_count = job_apps.count()
        j_interview = job_apps.filter(status='INTERVIEW').count()
        j_shortlisted = job_apps.filter(status='SHORTLISTED').count()
        j_selected = job_apps.filter(status='SELECTED').count()
        top_match = max([a.match_score_at_application for a in job_apps] or [0])
        skills_req = [sr.skill.name for sr in j.skill_requirements.all()[:4]]
        active_jobs_data.append({
            'job': j,
            'applicant_count': j_count,
            'interview_count': j_interview,
            'shortlisted_count': j_shortlisted,
            'selected_count': j_selected,
            'top_match': top_match,
            'skills': skills_req,
        })
        
    recent_applications = list(total_applications.select_related('job', 'student__user', 'student__department', 'student__college').order_by('-applied_at')[:8])
    
    avatar_colors = [
        ('#3b82f6', 'rgba(59, 130, 246, 0.15)'),
        ('#10b981', 'rgba(16, 185, 129, 0.15)'),
        ('#f59e0b', 'rgba(245, 158, 11, 0.15)'),
        ('#8b5cf6', 'rgba(139, 92, 246, 0.15)'),
        ('#ec4899', 'rgba(236, 72, 153, 0.15)'),
        ('#06b6d4', 'rgba(6, 182, 212, 0.15)'),
    ]
    for idx, app in enumerate(recent_applications):
        color, bg = avatar_colors[idx % len(avatar_colors)]
        app.avatar_color = color
        app.avatar_bg = bg
        u = app.student.user
        first = u.first_name or u.username or 'S'
        last = u.last_name or ''
        app.initials = (first[0] + (last[0] if last else '')).upper()
    
    # Candidate scout recommendations (students who haven't applied to this company)
    applied_student_ids = total_applications.values_list('student_id', flat=True)
    scout_students = StudentProfile.objects.exclude(id__in=applied_student_ids).select_related('user', 'department', 'college').prefetch_related('skills__skill')[:4]
    
    # Charts data
    funnel_counts = [applied_count, under_review_count, shortlisted_count, interview_count, selected_count]
    funnel_labels = ["1. Applied", "2. Under Review", "3. Shortlisted", "4. Interview", "5. Selected"]
    
    match_tier_labels = ["Tier 1: High Fit (>=85%)", "Tier 2: Strong Fit (70-84%)", "Tier 3: Developing (<70%)"]
    match_tier_counts = [high_match_count, strong_match_count, developing_match_count]
    
    context = {
        'company': company,
        'jobs_count': jobs.count(),
        'active_jobs_count': active_jobs.count(),
        'total_vacancies': total_vacancies,
        'applications_count': total_applications_count,
        'applied_count': applied_count,
        'under_review_count': under_review_count,
        'shortlisted_count': shortlisted_count,
        'interview_count': interview_count,
        'selected_count': selected_count,
        'rejected_count': rejected_count,
        'avg_match_score': avg_match_score,
        'high_match_count': high_match_count,
        'strong_match_count': strong_match_count,
        'developing_match_count': developing_match_count,
        'next_interview': next_interview,
        'active_jobs': active_jobs[:4],
        'active_jobs_data': active_jobs_data,
        'recent_applications': recent_applications,
        'scout_students': scout_students,
        'funnel_labels_json': json.dumps(funnel_labels),
        'funnel_counts_json': json.dumps(funnel_counts),
        'match_tier_labels_json': json.dumps(match_tier_labels),
        'match_tier_counts_json': json.dumps(match_tier_counts),
    }
    return render(request, 'recruiters/dashboard.html', context)


@login_required
@recruiter_required
def job_list(request):
    company, _ = Company.objects.get_or_create(user=request.user)
    jobs = company.jobs.annotate(applicant_count=Count('applications')).order_by('-created_at')
    return render(request, 'recruiters/job_list.html', {'company': company, 'jobs': jobs})


@login_required
@recruiter_required
def job_create(request):
    company, _ = Company.objects.get_or_create(user=request.user)
    skills = Skill.objects.select_related('category').all().order_by('category__name', 'name')

    if request.method == 'POST':
        title = request.POST.get('title')
        job_type = request.POST.get('job_type')
        description = request.POST.get('description')
        min_cgpa = request.POST.get('min_cgpa', 6.0)
        eligible_depts = request.POST.get('eligible_departments', 'CSE, IT, ECE')
        stipend_salary = request.POST.get('stipend_salary', '₹8 - 12 LPA')
        location_type = request.POST.get('location_type', 'HYBRID')
        location_city = request.POST.get('location_city', 'Bengaluru')
        vacancies = int(request.POST.get('vacancies', 5))
        deadline = request.POST.get('deadline')

        job = JobPosting.objects.create(
            company=company,
            title=title,
            job_type=job_type,
            description=description,
            min_cgpa=min_cgpa,
            eligible_departments=eligible_depts,
            stipend_salary=stipend_salary,
            location_type=location_type,
            location_city=location_city,
            vacancies=vacancies,
            deadline=deadline
        )

        # Handle skill requirements (Skill IDs, Proficiencies, Weights)
        skill_ids = request.POST.getlist('skill_ids')
        for sid in skill_ids:
            weight = request.POST.get(f'weight_{sid}', 80)
            min_prof = request.POST.get(f'min_prof_{sid}', 70)
            skill = Skill.objects.filter(id=sid).first()
            if skill:
                JobSkillRequirement.objects.create(
                    job=job,
                    skill=skill,
                    importance_weight=int(weight),
                    min_proficiency=int(min_prof)
                )

        messages.success(request, f"Opportunity '{job.title}' posted successfully with industry skill mapping!")
        return redirect('job_list_recruiter')

    return render(request, 'recruiters/job_form.html', {'skills': skills})


@login_required
@recruiter_required
def job_applicants(request, job_id):
    company, _ = Company.objects.get_or_create(user=request.user)
    job = get_object_or_404(JobPosting, id=job_id, company=company)
    
    status_filter = request.GET.get('status', '')
    applicants = job.applications.select_related('student__user', 'student__department', 'student__college')

    if status_filter:
        applicants = applicants.filter(status=status_filter)

    # Calculate real-time match analysis for each applicant
    applicant_cards = []
    for app in applicants:
        analysis = calculate_skill_gap_and_match(app.student, job)
        applicant_cards.append({
            'application': app,
            'student': app.student,
            'match_score': analysis['match_score'],
            'gap_score': analysis['gap_score'],
            'gap_skills': analysis['gap_skills'][:3],
            'matching_skills': analysis['matching_skills'],
        })

    # Sort applicants primarily by Match Score descending
    applicant_cards.sort(key=lambda x: x['match_score'], reverse=True)

    return render(request, 'recruiters/job_applicants.html', {
        'job': job,
        'applicant_cards': applicant_cards,
        'status_filter': status_filter,
    })


@login_required
@recruiter_required
def update_application_status(request, application_id):
    company, _ = Company.objects.get_or_create(user=request.user)
    application = get_object_or_404(Application, id=application_id, job__company=company)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        interview_date = request.POST.get('interview_date')
        interview_mode = request.POST.get('interview_mode', '')
        interview_link = request.POST.get('interview_link', '')
        notes = request.POST.get('recruiter_notes', '')

        application.status = new_status
        if interview_date:
            application.interview_date = interview_date
        application.interview_mode = interview_mode
        application.interview_link = interview_link
        application.recruiter_notes = notes
        application.save()

        # Notify the candidate
        student_user = application.student.user
        notif_msg = f"Your application status for {application.job.title} was updated to: {application.get_status_display()}."
        if new_status == 'INTERVIEW':
            notif_msg += f" Interview scheduled via {interview_mode}."
        elif new_status == 'SELECTED':
            notif_msg += f" Congratulations! You have received a selection offer."

        Notification.objects.create(
            user=student_user,
            title=f"Application Update: {application.get_status_display()}",
            message=notif_msg,
            link="/student/applications/"
        )

        messages.success(request, f"Updated application status for {student_user.get_full_name() or student_user.username} to '{application.get_status_display()}'.")
        return redirect('job_applicants', job_id=application.job.id)

    return redirect('job_applicants', job_id=application.job.id)


@login_required
@recruiter_required
def candidate_discovery(request):
    company, _ = Company.objects.get_or_create(user=request.user)
    jobs = company.jobs.filter(is_active=True)
    selected_job_id = request.GET.get('job_id')
    selected_job = None

    students = StudentProfile.objects.select_related('user', 'college', 'department').prefetch_related('skills__skill', 'projects')

    # Optional department filter
    dept_filter = request.GET.get('dept', '')
    if dept_filter:
        students = students.filter(department__code__iexact=dept_filter)

    # Optional min CGPA filter
    min_cgpa = request.GET.get('min_cgpa', '')
    if min_cgpa:
        try:
            students = students.filter(cgpa__gte=float(min_cgpa))
        except ValueError:
            pass

    ranked_candidates = []
    if selected_job_id:
        selected_job = jobs.filter(id=selected_job_id).first()

    for s in students:
        if selected_job:
            analysis = calculate_skill_gap_and_match(s, selected_job)
            match_score = analysis['match_score']
            gap_skills = analysis['gap_skills'][:3]
        else:
            match_score = s.placement_readiness()
            gap_skills = []

        ranked_candidates.append({
            'student': s,
            'match_score': match_score,
            'gap_skills': gap_skills,
            'tech_score': s.technical_score(),
            'readiness': s.placement_readiness(),
            'skills': s.skills.select_related('skill').all()[:6]
        })

    # Sort candidates by match score
    ranked_candidates.sort(key=lambda x: x['match_score'], reverse=True)

    return render(request, 'recruiters/candidate_discovery.html', {
        'company': company,
        'jobs': jobs,
        'selected_job': selected_job,
        'ranked_candidates': ranked_candidates,
        'dept_filter': dept_filter,
        'min_cgpa': min_cgpa,
    })
