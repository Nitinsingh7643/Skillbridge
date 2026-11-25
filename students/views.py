from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from core.decorators import student_required
from core.models import Notification
from .models import (
    StudentProfile, StudentSkill, StudentProject,
    StudentCertification, StudentExperience, AssessmentAttempt
)
from colleges.models import College, Department
from skills.models import Skill, SkillCategory, LearningResource, SkillAssessment
from skills.gap_engine import calculate_skill_gap_and_match
from recruiters.models import JobPosting, Application
from .resume_parser import parse_resume_pdf

@login_required
@student_required
def student_dashboard(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    
    # Calculate readiness metrics
    tech_score = profile.technical_score()
    soft_score = profile.soft_score()
    overall_score = profile.overall_skill_score()
    placement_readiness = profile.placement_readiness()
    internship_readiness = profile.internship_readiness()

    student_skills = profile.skills.select_related('skill', 'skill__category').all()
    verified_skills_count = student_skills.filter(is_verified=True).count()
    projects = profile.projects.all()
    applications = profile.applications.select_related('job', 'job__company').order_by('-applied_at')[:5]

    # Calculate match scores for active jobs
    active_jobs = JobPosting.objects.filter(is_active=True).select_related('company').prefetch_related('skill_requirements__skill')
    matched_jobs = []
    all_gaps_for_recommendations = []

    for job in active_jobs:
        analysis = calculate_skill_gap_and_match(profile, job)
        matched_jobs.append({
            'job': job,
            'match_score': analysis['match_score'],
            'gap_score': analysis['gap_score'],
            'gap_skills': analysis['gap_skills'][:3],
            'matching_skills': analysis['matching_skills'][:3],
        })
        if analysis['gap_skills']:
            all_gaps_for_recommendations.extend(analysis['gap_skills'][:2])

    # Sort jobs by highest match score
    matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
    top_recommended_jobs = matched_jobs[:4]

    # Curate unique learning recommendations
    recommended_resources = []
    seen_skills = set()
    for g in all_gaps_for_recommendations:
        if g['skill_name'] not in seen_skills:
            seen_skills.add(g['skill_name'])
            res_list = LearningResource.objects.filter(skill_id=g['skill_id'])[:2]
            for r in res_list:
                recommended_resources.append({
                    'skill_name': g['skill_name'],
                    'gap': g['gap'],
                    'resource': r
                })

    context = {
        'profile': profile,
        'tech_score': tech_score,
        'soft_score': soft_score,
        'overall_score': overall_score,
        'placement_readiness': placement_readiness,
        'internship_readiness': internship_readiness,
        'student_skills': student_skills,
        'verified_skills_count': verified_skills_count,
        'projects_count': projects.count(),
        'applications': applications,
        'applications_count': profile.applications.count(),
        'top_recommended_jobs': top_recommended_jobs,
        'recommended_resources': recommended_resources[:6],
    }
    return render(request, 'students/dashboard.html', context)


@login_required
def student_profile_view(request, student_id=None):
    if student_id:
        profile = get_object_or_404(StudentProfile, id=student_id)
    else:
        profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    student_skills = profile.skills.select_related('skill', 'skill__category').all()
    projects = profile.projects.all()
    certifications = profile.certifications.all()
    experiences = profile.experiences.all()

    total_skills = student_skills.count()
    verified_skills_count = student_skills.filter(is_verified=True).count()
    verification_rate = round((verified_skills_count / total_skills) * 100) if total_skills > 0 else 0
    technical_score = profile.technical_score()
    soft_score = profile.soft_score()
    placement_readiness = profile.placement_readiness()
    internship_readiness = profile.internship_readiness()
    applications_count = profile.applications.count()

    # Categorize skills for grouping tabs
    category_map = {}
    for ss in student_skills:
        cname = ss.skill.category.name if ss.skill.category else 'General'
        if cname not in category_map:
            category_map[cname] = []
        category_map[cname].append(ss)

    context = {
        'profile': profile,
        'student_skills': student_skills,
        'total_skills': total_skills,
        'verified_skills_count': verified_skills_count,
        'verification_rate': verification_rate,
        'technical_score': technical_score,
        'soft_score': soft_score,
        'projects': projects,
        'projects_count': projects.count(),
        'certifications': certifications,
        'experiences': experiences,
        'applications_count': applications_count,
        'category_map': category_map,
        'is_owner': request.user == profile.user,
        'placement_readiness': placement_readiness,
        'internship_readiness': internship_readiness,
    }
    return render(request, 'students/profile_view.html', context)


@login_required
@student_required
def student_profile_edit(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    colleges = College.objects.all()
    departments = Department.objects.all()

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.phone = request.POST.get('phone', '').strip()
        user.save()

        college_id = request.POST.get('college')
        dept_id = request.POST.get('department')
        profile.college = College.objects.filter(id=college_id).first() if college_id else None
        profile.department = Department.objects.filter(id=dept_id).first() if dept_id else None

        profile.roll_number = request.POST.get('roll_number', '').strip()
        profile.degree = request.POST.get('degree', 'B.Tech').strip()
        profile.semester = int(request.POST.get('semester', 7))
        profile.graduation_year = int(request.POST.get('graduation_year', 2026))
        
        cgpa_str = request.POST.get('cgpa', '7.5').strip()
        try:
            profile.cgpa = float(cgpa_str)
        except ValueError:
            pass

        profile.bio = request.POST.get('bio', '').strip()
        profile.github_url = request.POST.get('github_url', '').strip()
        profile.linkedin_url = request.POST.get('linkedin_url', '').strip()
        profile.portfolio_url = request.POST.get('portfolio_url', '').strip()
        
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
            user.save()

        profile.save()
        messages.success(request, "Your academic portfolio has been updated successfully!")
        return redirect('student_profile_view')

    context = {
        'profile': profile,
        'colleges': colleges,
        'departments': departments,
    }
    return render(request, 'students/profile_edit.html', context)


@login_required
@student_required
def student_skills_manage(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    all_skills = Skill.objects.select_related('category').all().order_by('category__name', 'name')
    existing_skills = profile.skills.select_related('skill', 'skill__category').order_by('-is_verified', '-proficiency')
    existing_skill_ids = [es.skill_id for es in existing_skills]

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            skill_id = request.POST.get('skill_id')
            proficiency = int(request.POST.get('proficiency', 60))
            skill = get_object_or_404(Skill, id=skill_id)
            StudentSkill.objects.update_or_create(
                student=profile,
                skill=skill,
                defaults={'proficiency': min(100, max(10, proficiency))}
            )
            messages.success(request, f"Added {skill.name} ({proficiency}%) to your profile!")
        elif action == 'update':
            skill_id = request.POST.get('skill_id')
            proficiency = int(request.POST.get('proficiency', 60))
            ss = get_object_or_404(StudentSkill, student=profile, skill_id=skill_id)
            ss.proficiency = min(100, max(10, proficiency))
            ss.save()
            messages.success(request, f"Updated proficiency for {ss.skill.name} to {proficiency}%.")
        elif action == 'delete':
            skill_id = request.POST.get('skill_id')
            StudentSkill.objects.filter(student=profile, skill_id=skill_id).delete()
            messages.info(request, "Skill removed from profile.")

        return redirect('student_skills_manage')

    total_skills_count = existing_skills.count()
    verified_skills_count = existing_skills.filter(is_verified=True).count()
    avg_proficiency = round(sum(s.proficiency for s in existing_skills) / total_skills_count) if total_skills_count > 0 else 0
    verification_rate = round((verified_skills_count / total_skills_count) * 100) if total_skills_count > 0 else 0

    category_breakdown = {}
    for es in existing_skills:
        cat = es.skill.category.name if es.skill.category else 'General'
        if cat not in category_breakdown:
            category_breakdown[cat] = {'name': cat, 'count': 0, 'sum_prof': 0, 'verified_count': 0}
        category_breakdown[cat]['count'] += 1
        category_breakdown[cat]['sum_prof'] += es.proficiency
        if es.is_verified:
            category_breakdown[cat]['verified_count'] += 1
    for cat in category_breakdown.values():
        cat['avg_prof'] = round(cat['sum_prof'] / cat['count']) if cat['count'] > 0 else 0

    import json
    radar_labels = list(category_breakdown.keys())
    radar_scores = [category_breakdown[k]['avg_prof'] for k in radar_labels]

    context = {
        'profile': profile,
        'existing_skills': existing_skills,
        'existing_skill_ids': existing_skill_ids,
        'all_skills': all_skills,
        'total_skills_count': total_skills_count,
        'verified_skills_count': verified_skills_count,
        'avg_proficiency': avg_proficiency,
        'verification_rate': verification_rate,
        'category_breakdown': category_breakdown,
        'radar_labels_json': json.dumps(radar_labels),
        'radar_scores_json': json.dumps(radar_scores),
    }
    return render(request, 'students/skills_manage.html', context)


@login_required
@student_required
def student_projects_manage(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            StudentProject.objects.create(
                student=profile,
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                technologies=request.POST.get('technologies'),
                github_link=request.POST.get('github_link', ''),
                live_link=request.POST.get('live_link', '')
            )
            messages.success(request, "Project added successfully! This boosts your placement readiness score.")
        elif action == 'delete':
            proj_id = request.POST.get('project_id')
            StudentProject.objects.filter(student=profile, id=proj_id).delete()
            messages.info(request, "Project removed.")

        return redirect('student_projects_manage')

    projects = profile.projects.all()
    return render(request, 'students/projects_manage.html', {'profile': profile, 'projects': projects})


@login_required
@student_required
def resume_upload_parser(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    parsed_data = None

    if request.method == 'POST':
        if 'resume_file' in request.FILES:
            resume_file = request.FILES['resume_file']
            profile.resume = resume_file
            profile.save()

            parsed = parse_resume_pdf(profile.resume.path)
            if parsed['success']:
                parsed_data = parsed
                request.session['parsed_resume_data'] = {
                    'email': parsed['email'],
                    'phone': parsed['phone'],
                    'degree': parsed['degree'],
                    'cgpa': parsed['cgpa'],
                    'github_url': parsed['github_url'],
                    'linkedin_url': parsed['linkedin_url'],
                    'skills': [s['id'] for s in parsed['detected_skills']],
                    'projects': parsed['projects_found'],
                }
                messages.success(request, f"Resume parsed successfully! Extracted {len(parsed['detected_skills'])} skills.")
            else:
                messages.error(request, parsed.get('error', 'Could not parse resume.'))

        elif request.POST.get('action') == 'reparse_saved_resume' and profile.resume:
            parsed = parse_resume_pdf(profile.resume.path)
            if parsed['success']:
                parsed_data = parsed
                request.session['parsed_resume_data'] = {
                    'email': parsed['email'],
                    'phone': parsed['phone'],
                    'degree': parsed['degree'],
                    'cgpa': parsed['cgpa'],
                    'github_url': parsed['github_url'],
                    'linkedin_url': parsed['linkedin_url'],
                    'skills': [s['id'] for s in parsed['detected_skills']],
                    'projects': parsed['projects_found'],
                }
                messages.success(request, f"Saved resume re-scanned successfully! Extracted {len(parsed['detected_skills'])} skills.")
            else:
                messages.error(request, parsed.get('error', 'Could not parse resume.'))
        
        elif request.POST.get('action') == 'apply_parsed_data':
            saved_data = request.session.get('parsed_resume_data', {})
            if saved_data:
                user = request.user
                if saved_data.get('phone'):
                    user.phone = saved_data['phone']
                    user.save()
                
                if saved_data.get('cgpa'):
                    profile.cgpa = saved_data['cgpa']
                if saved_data.get('degree'):
                    profile.degree = saved_data['degree']
                if saved_data.get('github_url'):
                    profile.github_url = saved_data['github_url']
                if saved_data.get('linkedin_url'):
                    profile.linkedin_url = saved_data['linkedin_url']
                profile.save()

                # Add detected skills
                skills_added_count = 0
                for skill_id in saved_data.get('skills', []):
                    skill = Skill.objects.filter(id=skill_id).first()
                    if skill:
                        StudentSkill.objects.get_or_create(
                            student=profile,
                            skill=skill,
                            defaults={'proficiency': 75}
                        )
                        skills_added_count += 1

                # Add detected projects
                for p in saved_data.get('projects', []):
                    StudentProject.objects.create(
                        student=profile,
                        title=p['title'],
                        description=p['description'],
                        technologies="Extracted from Resume"
                    )

                del request.session['parsed_resume_data']
                messages.success(request, f"Profile updated! Added {skills_added_count} detected skills & updated academic details.")
                return redirect('student_profile_view')

    return render(request, 'students/resume_parser.html', {
        'profile': profile,
        'parsed_data': parsed_data,
    })


@login_required
@student_required
def job_browse(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    job_type = request.GET.get('job_type', '')
    location_type = request.GET.get('location_type', '')
    search = request.GET.get('search', '').strip()

    jobs = JobPosting.objects.filter(is_active=True).select_related('company').prefetch_related('skill_requirements__skill')

    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if location_type:
        jobs = jobs.filter(location_type=location_type)
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) |
            Q(company__company_name__icontains=search) |
            Q(description__icontains=search)
        )

    # Calculate dynamic match scores for every job
    job_cards = []
    applied_job_ids = set(profile.applications.values_list('job_id', flat=True))

    for job in jobs:
        analysis = calculate_skill_gap_and_match(profile, job)
        job_cards.append({
            'job': job,
            'match_score': analysis['match_score'],
            'gap_score': analysis['gap_score'],
            'has_applied': job.id in applied_job_ids,
            'gap_skills': analysis['gap_skills'][:3],
            'matching_skills': analysis['matching_skills'][:3],
        })

    # Sort primarily by Match Score descending
    job_cards.sort(key=lambda x: x['match_score'], reverse=True)

    total_jobs_count = len(job_cards)
    high_match_count = sum(1 for j in job_cards if j['match_score'] >= 80)
    internships_count = sum(1 for j in job_cards if j['job'].job_type == 'INTERNSHIP')
    fulltime_count = sum(1 for j in job_cards if j['job'].job_type == 'FULL_TIME')
    ppo_count = sum(1 for j in job_cards if j['job'].job_type == 'PPO')
    applied_count = len(applied_job_ids)
    avg_match_score = round(sum(j['match_score'] for j in job_cards) / total_jobs_count) if total_jobs_count > 0 else 0

    context = {
        'profile': profile,
        'job_cards': job_cards,
        'job_type': job_type,
        'location_type': location_type,
        'search': search,
        'total_jobs_count': total_jobs_count,
        'high_match_count': high_match_count,
        'internships_count': internships_count,
        'fulltime_count': fulltime_count,
        'ppo_count': ppo_count,
        'applied_count': applied_count,
        'avg_match_score': avg_match_score,
    }
    return render(request, 'students/job_browse.html', context)


@login_required
@student_required
def job_detail_and_gap_analysis(request, job_id):
    import json
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    job = get_object_or_404(JobPosting.objects.select_related('company'), id=job_id)
    analysis = calculate_skill_gap_and_match(profile, job)
    
    has_applied = Application.objects.filter(job=job, student=profile).exists()
    application = Application.objects.filter(job=job, student=profile).first()

    # Eligibility check
    cgpa_eligible = profile.cgpa >= job.min_cgpa
    dept_eligible = True
    if profile.department and job.eligible_departments:
        dept_eligible = (profile.department.code.lower() in job.eligible_departments.lower())

    # Company branding metadata
    cname = job.company.company_name.lower()
    if 'google' in cname:
        brand_color = '#4285F4'
        brand_bg = 'rgba(66, 133, 244, 0.15)'
        brand_icon = 'fa-brands fa-google'
    elif 'microsoft' in cname:
        brand_color = '#00A4EF'
        brand_bg = 'rgba(0, 164, 239, 0.15)'
        brand_icon = 'fa-brands fa-microsoft'
    elif 'amazon' in cname or 'aws' in cname:
        brand_color = '#FF9900'
        brand_bg = 'rgba(255, 153, 0, 0.15)'
        brand_icon = 'fa-brands fa-aws'
    elif 'atlassian' in cname:
        brand_color = '#0052CC'
        brand_bg = 'rgba(0, 82, 204, 0.15)'
        brand_icon = 'fa-brands fa-atlassian'
    elif 'cisco' in cname:
        brand_color = '#049fd9'
        brand_bg = 'rgba(4, 159, 217, 0.15)'
        brand_icon = 'fa-solid fa-network-wired'
    elif 'flipkart' in cname:
        brand_color = '#2874F0'
        brand_bg = 'rgba(40, 116, 240, 0.15)'
        brand_icon = 'fa-solid fa-bolt'
    elif 'tata' in cname or 'tcs' in cname:
        brand_color = '#0070BA'
        brand_bg = 'rgba(0, 112, 186, 0.15)'
        brand_icon = 'fa-solid fa-building'
    else:
        brand_color = '#6366f1'
        brand_bg = 'rgba(99, 102, 241, 0.15)'
        brand_icon = 'fa-solid fa-briefcase'

    chart_labels = [item['skill_name'] for item in analysis['skill_breakdown']]
    chart_req = [item['required'] for item in analysis['skill_breakdown']]
    chart_cur = [item['current'] for item in analysis['skill_breakdown']]

    context = {
        'profile': profile,
        'job': job,
        'analysis': analysis,
        'has_applied': has_applied,
        'application': application,
        'cgpa_eligible': cgpa_eligible,
        'dept_eligible': dept_eligible,
        'brand_color': brand_color,
        'brand_bg': brand_bg,
        'brand_icon': brand_icon,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_req_json': json.dumps(chart_req),
        'chart_cur_json': json.dumps(chart_cur),
    }
    return render(request, 'students/job_gap_analysis.html', context)


@login_required
@student_required
def apply_job(request, job_id):
    if request.method == 'POST':
        profile, _ = StudentProfile.objects.get_or_create(user=request.user)
        job = get_object_or_404(JobPosting, id=job_id, is_active=True)

        if Application.objects.filter(job=job, student=profile).exists():
            messages.warning(request, "You have already applied for this opening.")
            return redirect('job_detail', job_id=job.id)

        cover_note = request.POST.get('cover_note', '')
        analysis = calculate_skill_gap_and_match(profile, job)
        match_score = analysis['match_score']

        app = Application.objects.create(
            job=job,
            student=profile,
            cover_note=cover_note,
            match_score_at_application=match_score,
            status='APPLIED'
        )

        # Notify the recruiter
        Notification.objects.create(
            user=job.company.user,
            title=f"New Candidate Application: {job.title}",
            message=f"{request.user.get_full_name() or request.user.username} applied with a {match_score}% skill match score.",
            link=f"/recruiters/jobs/{job.id}/applicants/"
        )

        # Notify the student
        Notification.objects.create(
            user=request.user,
            title="Application Submitted",
            message=f"Your application for {job.title} at {job.company.company_name} was submitted ({match_score}% Match).",
            link="/student/applications/"
        )

        messages.success(request, f"Application submitted successfully with a {match_score}% skill match score!")
        return redirect('my_applications')

    return redirect('job_browse')


@login_required
@student_required
def my_applications(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    all_apps = list(profile.applications.select_related('job', 'job__company').order_by('-applied_at'))
    
    total_count = len(all_apps)
    interview_count = sum(1 for a in all_apps if a.status == 'INTERVIEW')
    shortlisted_count = sum(1 for a in all_apps if a.status == 'SHORTLISTED')
    under_review_count = sum(1 for a in all_apps if a.status == 'UNDER_REVIEW')
    selected_count = sum(1 for a in all_apps if a.status == 'SELECTED')
    applied_count = sum(1 for a in all_apps if a.status == 'APPLIED')
    rejected_count = sum(1 for a in all_apps if a.status == 'REJECTED')
    avg_match_score = round(sum(a.match_score_at_application for a in all_apps) / total_count) if total_count > 0 else 0
    next_interview = next((a for a in all_apps if a.status == 'INTERVIEW' and a.interview_date), None)
    
    selected_status = request.GET.get('status', '').strip().upper()
    search = request.GET.get('search', '').strip().lower()
    
    filtered_apps = all_apps
    if selected_status and selected_status != 'ALL':
        filtered_apps = [a for a in filtered_apps if a.status == selected_status]
    if search:
        filtered_apps = [
            a for a in filtered_apps
            if search in a.job.title.lower() or
               search in a.job.company.company_name.lower() or
               search in (a.job.location_city or '').lower()
        ]
        
    stage_map = {
        'APPLIED': {'num': 1, 'percent': 20, 'badge': 'secondary', 'label': '1. Application Received'},
        'UNDER_REVIEW': {'num': 2, 'percent': 40, 'badge': 'info', 'label': '2. Skill & Resume Audit'},
        'SHORTLISTED': {'num': 3, 'percent': 60, 'badge': 'primary', 'label': '3. Shortlisted for Rounds'},
        'INTERVIEW': {'num': 4, 'percent': 80, 'badge': 'warning', 'label': '4. Technical Interview'},
        'SELECTED': {'num': 5, 'percent': 100, 'badge': 'success', 'label': '5. Offer Extended 🎉'},
        'REJECTED': {'num': 0, 'percent': 0, 'badge': 'danger', 'label': 'Not Selected'},
    }
    
    for app in filtered_apps:
        app.stage_info = stage_map.get(app.status, stage_map['APPLIED'])
        cname = app.job.company.company_name.lower()
        if 'google' in cname:
            app.brand_color = '#4285F4'
            app.brand_bg = 'rgba(66, 133, 244, 0.15)'
            app.brand_icon = 'fa-brands fa-google'
            app.brand_code = 'GOOG'
        elif 'microsoft' in cname:
            app.brand_color = '#00A4EF'
            app.brand_bg = 'rgba(0, 164, 239, 0.15)'
            app.brand_icon = 'fa-brands fa-microsoft'
            app.brand_code = 'MSFT'
        elif 'amazon' in cname or 'aws' in cname:
            app.brand_color = '#FF9900'
            app.brand_bg = 'rgba(255, 153, 0, 0.15)'
            app.brand_icon = 'fa-brands fa-aws'
            app.brand_code = 'AMZN'
        elif 'atlassian' in cname:
            app.brand_color = '#0052CC'
            app.brand_bg = 'rgba(0, 82, 204, 0.15)'
            app.brand_icon = 'fa-brands fa-atlassian'
            app.brand_code = 'ATLS'
        elif 'cisco' in cname:
            app.brand_color = '#049fd9'
            app.brand_bg = 'rgba(4, 159, 217, 0.15)'
            app.brand_icon = 'fa-solid fa-network-wired'
            app.brand_code = 'CSCO'
        elif 'flipkart' in cname:
            app.brand_color = '#2874F0'
            app.brand_bg = 'rgba(40, 116, 240, 0.15)'
            app.brand_icon = 'fa-solid fa-bolt'
            app.brand_code = 'FLPK'
        elif 'tata' in cname or 'tcs' in cname:
            app.brand_color = '#0070BA'
            app.brand_bg = 'rgba(0, 112, 186, 0.15)'
            app.brand_icon = 'fa-solid fa-building'
            app.brand_code = 'TCS'
        else:
            app.brand_color = '#6366f1'
            app.brand_bg = 'rgba(99, 102, 241, 0.15)'
            app.brand_icon = 'fa-solid fa-briefcase'
            app.brand_code = app.job.company.company_name[:2].upper()

    context = {
        'profile': profile,
        'applications': filtered_apps,
        'all_apps_count': total_count,
        'total_applications_count': total_count,
        'interview_count': interview_count,
        'shortlisted_count': shortlisted_count,
        'under_review_count': under_review_count,
        'selected_count': selected_count,
        'applied_count': applied_count,
        'rejected_count': rejected_count,
        'avg_match_score': avg_match_score,
        'next_interview': next_interview,
        'selected_status': selected_status,
        'search': search,
    }
    return render(request, 'students/my_applications.html', context)
