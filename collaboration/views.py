from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count

from .models import SkillDemandReport, WorkshopProposal, LiveProject
from skills.models import Skill
from recruiters.models import Company
from colleges.models import College
from core.models import Notification

def collaboration_hub(request):
    demands = SkillDemandReport.objects.select_related('company').prefetch_related('demanded_skills').all()
    workshops = WorkshopProposal.objects.select_related('company', 'college').prefetch_related('target_skills').all()
    live_projects = LiveProject.objects.select_related('company').prefetch_related('required_skills').filter(is_active=True)

    # Calculate trending demanded skills
    skill_demand_counts = {}
    for d in demands:
        for s in d.demanded_skills.all():
            skill_demand_counts[s.name] = skill_demand_counts.get(s.name, 0) + d.expected_hires

    sorted_demands = sorted(skill_demand_counts.items(), key=lambda x: x[1], reverse=True)[:8]

    context = {
        'demands': demands,
        'workshops': workshops,
        'live_projects': live_projects,
        'sorted_demands': sorted_demands,
        'is_recruiter': request.user.is_authenticated and hasattr(request.user, 'company_profile'),
        'is_college': request.user.is_authenticated and hasattr(request.user, 'college_profile'),
    }
    return render(request, 'collaboration/hub.html', context)


@login_required
def post_skill_demand(request):
    if not hasattr(request.user, 'company_profile'):
        messages.error(request, "Only industry recruiters can submit skill demand forecasts.")
        return redirect('collaboration_hub')

    company = request.user.company_profile
    skills = Skill.objects.all().order_by('name')

    if request.method == 'POST':
        title = request.POST.get('title')
        role = request.POST.get('target_role')
        hires = int(request.POST.get('expected_hires', 10))
        timeline = request.POST.get('target_timeline', 'Next 3-6 Months')
        description = request.POST.get('description')
        skill_ids = request.POST.getlist('demanded_skills')

        demand = SkillDemandReport.objects.create(
            company=company,
            title=title,
            target_role=role,
            expected_hires=hires,
            target_timeline=timeline,
            description=description
        )
        demand.demanded_skills.set(skill_ids)

        # Notify colleges
        colleges = College.objects.all()
        for col in colleges:
            Notification.objects.create(
                user=col.user,
                title=f"New Industry Demand: {company.company_name}",
                message=f"{company.company_name} projected a hiring demand of {hires} candidates for {role}.",
                link="/collaboration/"
            )

        messages.success(request, "Industry skill demand report published to partnering colleges!")
        return redirect('collaboration_hub')

    return render(request, 'collaboration/post_demand.html', {'skills': skills})


@login_required
def propose_workshop(request):
    is_recruiter = hasattr(request.user, 'company_profile')
    is_college = hasattr(request.user, 'college_profile')

    if not (is_recruiter or is_college):
        messages.error(request, "Access restricted to colleges and industry partners.")
        return redirect('collaboration_hub')

    skills = Skill.objects.all().order_by('name')
    colleges = College.objects.all()
    companies = Company.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title')
        proposed_date = request.POST.get('proposed_date')
        duration = int(request.POST.get('duration_hours', 3))
        speaker_name = request.POST.get('speaker_name', '')
        speaker_designation = request.POST.get('speaker_designation', '')
        description = request.POST.get('description')
        skill_ids = request.POST.getlist('target_skills')

        proposer_type = 'INDUSTRY' if is_recruiter else 'COLLEGE'
        company = request.user.company_profile if is_recruiter else None
        college = request.user.college_profile if is_college else None

        if is_recruiter:
            col_id = request.POST.get('target_college')
            if col_id:
                college = College.objects.filter(id=col_id).first()
        elif is_college:
            comp_id = request.POST.get('target_company')
            if comp_id:
                company = Company.objects.filter(id=comp_id).first()

        workshop = WorkshopProposal.objects.create(
            proposer_type=proposer_type,
            company=company,
            college=college,
            title=title,
            proposed_date=proposed_date,
            duration_hours=duration,
            speaker_name=speaker_name,
            speaker_designation=speaker_designation,
            description=description,
            status='PROPOSED'
        )
        workshop.target_skills.set(skill_ids)

        messages.success(request, "Workshop proposal submitted successfully!")
        return redirect('collaboration_hub')

    return render(request, 'collaboration/propose_workshop.html', {
        'skills': skills,
        'colleges': colleges,
        'companies': companies,
        'is_recruiter': is_recruiter,
        'is_college': is_college,
    })


@login_required
def update_workshop_status(request, workshop_id, new_status):
    workshop = get_object_or_404(WorkshopProposal, id=workshop_id)
    workshop.status = new_status
    workshop.save()
    messages.success(request, f"Workshop '{workshop.title}' marked as {workshop.get_status_display()}!")
    return redirect('collaboration_hub')


@login_required
def post_live_project(request):
    if not hasattr(request.user, 'company_profile'):
        messages.error(request, "Only industry recruiters can post live projects.")
        return redirect('collaboration_hub')

    company = request.user.company_profile
    skills = Skill.objects.all().order_by('name')

    if request.method == 'POST':
        title = request.POST.get('title')
        domain = request.POST.get('domain', 'Web Development')
        team_size = int(request.POST.get('team_size_limit', 4))
        deadline = request.POST.get('submission_deadline')
        description = request.POST.get('description')
        skill_ids = request.POST.getlist('required_skills')

        proj = LiveProject.objects.create(
            company=company,
            title=title,
            domain=domain,
            team_size_limit=team_size,
            submission_deadline=deadline,
            description=description
        )
        proj.required_skills.set(skill_ids)

        messages.success(request, f"Live project '{proj.title}' published for student teams!")
        return redirect('collaboration_hub')

    return render(request, 'collaboration/post_live_project.html', {'skills': skills})
