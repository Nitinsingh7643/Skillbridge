from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg

from .models import CustomUser, Notification
from .forms import RegisterForm, LoginForm
from .decorators import admin_required
from students.models import StudentProfile, StudentSkill
from colleges.models import College, Department
from recruiters.models import Company, JobPosting, Application
from skills.models import Skill
from collaboration.models import SkillDemandReport, WorkshopProposal, LiveProject

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    stats = {
        'total_students': StudentProfile.objects.count(),
        'total_colleges': College.objects.count(),
        'total_companies': Company.objects.count(),
        'total_jobs': JobPosting.objects.filter(is_active=True).count(),
        'demanded_skills_count': Skill.objects.filter(is_in_demand=True).count(),
    }
    recent_jobs = JobPosting.objects.filter(is_active=True).select_related('company').order_by('-created_at')[:4]

    # Build dynamic candidate data for the simulation card
    import json
    candidates = []
    avatar_gradients = [
        'linear-gradient(135deg, #6366f1, #06b6d4)',
        'linear-gradient(135deg, #a855f7, #ec4899)',
        'linear-gradient(135deg, #10b981, #06b6d4)',
        'linear-gradient(135deg, #f59e0b, #ef4444)',
        'linear-gradient(135deg, #3b82f6, #8b5cf6)',
        'linear-gradient(135deg, #ec4899, #f43f5e)',
        'linear-gradient(135deg, #14b8a6, #22d3ee)',
        'linear-gradient(135deg, #8b5cf6, #6366f1)',
    ]

    all_students = StudentProfile.objects.select_related(
        'user', 'college', 'department'
    ).prefetch_related('skills__skill').all()

    for idx, sp in enumerate(all_students):
        full_name = sp.user.get_full_name() or sp.user.username
        initial = full_name[0].upper() if full_name else '?'
        college_name = sp.college.name if sp.college else 'College'
        dept_code = sp.department.code if sp.department else 'CSE'
        cgpa = str(sp.cgpa)
        overall = sp.overall_skill_score()

        # Determine badge based on score
        if overall >= 80:
            badge_text = 'Elite Fit'
            badge_color = '#06b6d4'
        elif overall >= 60:
            badge_text = 'High Fit'
            badge_color = '#10b981'
        elif overall >= 40:
            badge_text = 'Moderate'
            badge_color = '#f59e0b'
        else:
            badge_text = 'Developing'
            badge_color = '#ef4444'

        # Top 3 skills by proficiency
        top_skills = sp.skills.select_related('skill').order_by('-proficiency')[:3]
        skills_data = []
        for sk in top_skills:
            prof = sk.proficiency
            if prof >= 75:
                fill_class = 'clean-fill fill-emerald'
                status_icon = 'fa-circle-check'
                status_label = f'{prof}% • Compliant'
                status_bg = 'rgba(16, 185, 129, 0.16)'
                status_color = '#34d399'
                status_border = 'rgba(16, 185, 129, 0.35)'
            elif prof >= 50:
                fill_class = 'clean-fill fill-amber'
                status_icon = 'fa-circle-exclamation'
                deficit = 75 - prof
                status_label = f'{prof}% • {deficit}% Deficit'
                status_bg = 'rgba(245, 158, 11, 0.16)'
                status_color = '#fbbf24'
                status_border = 'rgba(245, 158, 11, 0.35)'
            else:
                fill_class = 'clean-fill fill-crimson'
                status_icon = 'fa-triangle-exclamation'
                deficit = 75 - prof
                status_label = f'{prof}% • {deficit}% Deficit'
                status_bg = 'rgba(239, 68, 68, 0.16)'
                status_color = '#f87171'
                status_border = 'rgba(239, 68, 68, 0.35)'

            skills_data.append({
                'name': sk.skill.name,
                'prof': prof,
                'fillClass': fill_class,
                'icon': status_icon,
                'label': status_label,
                'bg': status_bg,
                'color': status_color,
                'border': status_border,
            })

        candidates.append({
            'initial': initial,
            'avatarBg': avatar_gradients[idx % len(avatar_gradients)],
            'name': full_name,
            'college': college_name,
            'dept': dept_code,
            'cgpa': cgpa,
            'score': overall,
            'badgeText': badge_text,
            'badgeColor': badge_color,
            'skills': skills_data,
        })

    candidates_json = json.dumps(candidates)

    trending_skills = Skill.objects.filter(is_in_demand=True).select_related('category')[:8]
    featured_companies = Company.objects.all()[:6]
    live_projects = LiveProject.objects.select_related('company').prefetch_related('required_skills')[:3]

    return render(request, 'core/index.html', {
        'stats': stats,
        'recent_jobs': recent_jobs,
        'candidates_json': candidates_json,
        'candidates_count': len(candidates),
        'trending_skills': trending_skills,
        'featured_companies': featured_companies,
        'live_projects': live_projects,
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            role = form.cleaned_data.get('role')
            org_name = form.cleaned_data.get('organization_name', '').strip()
            user.role = role
            user.save()

            # Create corresponding profile
            if role == 'STUDENT':
                StudentProfile.objects.create(user=user)
                Notification.objects.create(
                    user=user,
                    title="Welcome to SkillBridge!",
                    message="Complete your student portfolio and take skill assessments to unlock top job matches.",
                    link="/student/profile/edit/"
                )
            elif role == 'COLLEGE':
                college_name = org_name if org_name else f"{user.first_name}'s Institution"
                college = College.objects.create(
                    user=user,
                    name=college_name,
                    tpo_name=f"{user.first_name} {user.last_name}",
                    tpo_email=user.email,
                    tpo_phone=user.phone
                )
                # Create standard departments
                Department.objects.create(college=college, name="Computer Science & Engineering", code="CSE")
                Department.objects.create(college=college, name="Information Technology", code="IT")
                Department.objects.create(college=college, name="Electronics & Communication", code="ECE")
                Notification.objects.create(
                    user=user,
                    title="College Account Created",
                    message="Welcome to SkillBridge TPO portal. Manage your students and explore industry skill requirements.",
                    link="/colleges/dashboard/"
                )
            elif role == 'INDUSTRY':
                comp_name = org_name if org_name else f"{user.first_name}'s Tech Corp"
                Company.objects.create(
                    user=user,
                    company_name=comp_name,
                    location="Bengaluru, India"
                )
                Notification.objects.create(
                    user=user,
                    title="Recruiter Account Created",
                    message="Welcome to SkillBridge Recruiter portal. Post internships and jobs with skill mapping.",
                    link="/recruiters/dashboard/"
                )

            login(request, user)
            messages.success(request, f"Welcome to SkillBridge, {user.first_name or user.username}!")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Please fix the errors below to register.")
    else:
        form = RegisterForm()

    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def dashboard_redirect(request):
    """Directs authenticated users to their corresponding dashboard."""
    role = request.user.role
    if role == 'STUDENT':
        return redirect('student_dashboard')
    elif role == 'COLLEGE':
        return redirect('tpo_dashboard')
    elif role == 'INDUSTRY':
        return redirect('recruiter_dashboard')
    elif role == 'ADMIN' or request.user.is_superuser:
        return redirect('admin_dashboard')
    else:
        return redirect('index')


@login_required
@admin_required
def admin_dashboard(request):
    total_users = CustomUser.objects.count()
    total_students = StudentProfile.objects.count()
    total_colleges = College.objects.count()
    total_companies = Company.objects.count()
    total_jobs = JobPosting.objects.count()
    total_applications = Application.objects.count()

    colleges = College.objects.select_related('user').all()
    companies = Company.objects.select_related('user').all()
    recent_jobs = JobPosting.objects.select_related('company').order_by('-created_at')[:6]
    recent_applications = Application.objects.select_related('student__user', 'job__company').order_by('-applied_at')[:8]

    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_colleges': total_colleges,
        'total_companies': total_companies,
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'colleges': colleges,
        'companies': companies,
        'recent_jobs': recent_jobs,
        'recent_applications': recent_applications,
    }
    return render(request, 'core/admin_dashboard.html', context)


@login_required
@admin_required
def admin_toggle_verify(request, entity_type, entity_id):
    if entity_type == 'college':
        college = get_object_or_404(College, id=entity_id)
        college.is_verified = not college.is_verified
        college.save()
        messages.success(request, f"Updated verification status for {college.name}.")
    elif entity_type == 'company':
        company = get_object_or_404(Company, id=entity_id)
        company.is_verified = not company.is_verified
        company.save()
        messages.success(request, f"Updated verification status for {company.company_name}.")
    return redirect('admin_dashboard')


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/notifications.html', {'notifications': notifications})


@login_required
def mark_notification_read(request, notification_id):
    notif = get_object_or_404(Notification, id=notification_id, user=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('notifications_view')


@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications_view')
