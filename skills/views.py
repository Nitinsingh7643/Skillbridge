from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import Skill, SkillCategory, SkillAssessment, AssessmentQuestion, LearningResource
from students.models import StudentProfile, StudentSkill, AssessmentAttempt
from core.models import Notification

def skill_catalog(request):
    categories = SkillCategory.objects.prefetch_related('skills', 'skills__learning_resources').all()
    search = request.GET.get('search', '').strip()
    
    if search:
        skills = Skill.objects.filter(name__icontains=search).select_related('category')
    else:
        skills = Skill.objects.select_related('category').all()

    return render(request, 'skills/catalog.html', {
        'categories': categories,
        'skills': skills,
        'search': search,
    })
    
@login_required
def assessment_list(request):
    assessments = SkillAssessment.objects.select_related('skill', 'skill__category').prefetch_related('questions').all()
    user_attempts = {}
    if hasattr(request.user, 'student_profile'):
        profile = request.user.student_profile
        for attempt in AssessmentAttempt.objects.filter(student=profile).order_by('completed_at'):
            user_attempts[attempt.assessment_id] = attempt

    assessments_data = []
    for ass in assessments:
        assessments_data.append({
            'assessment': ass,
            'question_count': ass.questions.count(),
            'attempt': user_attempts.get(ass.id)
        })

    total_assessments_count = len(assessments_data)
    total_questions_count = sum(a['question_count'] for a in assessments_data)
    passed_count = sum(1 for a in assessments_data if a['attempt'] and a['attempt'].passed)
    unattempted_count = sum(1 for a in assessments_data if not a['attempt'])
    retake_needed_count = sum(1 for a in assessments_data if a['attempt'] and not a['attempt'].passed)
    pass_rate = round((passed_count / total_assessments_count) * 100) if total_assessments_count > 0 else 0

    # Extract distinct categories
    categories = sorted(list(set(a['assessment'].skill.category.name for a in assessments_data if a['assessment'].skill.category)))

    context = {
        'assessments_data': assessments_data,
        'total_assessments_count': total_assessments_count,
        'total_questions_count': total_questions_count,
        'passed_count': passed_count,
        'unattempted_count': unattempted_count,
        'retake_needed_count': retake_needed_count,
        'pass_rate': pass_rate,
        'categories': categories,
    }
    return render(request, 'skills/assessment_list.html', context)


@login_required
def take_assessment(request, assessment_id):
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can take skill assessments.")
        return redirect('assessment_list')

    assessment = get_object_or_404(SkillAssessment.objects.prefetch_related('questions'), id=assessment_id)
    questions = assessment.questions.all()
    
    if not questions.exists():
        messages.warning(request, "This assessment does not have any questions yet.")
        return redirect('assessment_list')

    return render(request, 'skills/take_assessment.html', {
        'assessment': assessment,
        'questions': questions,
        'time_limit_seconds': assessment.time_limit_minutes * 60,
    })


@login_required
def submit_assessment(request, assessment_id):
    if request.method != 'POST' or not hasattr(request.user, 'student_profile'):
        return redirect('assessment_list')

    assessment = get_object_or_404(SkillAssessment.objects.prefetch_related('questions'), id=assessment_id)
    profile = request.user.student_profile
    questions = assessment.questions.all()
    total_questions = questions.count()

    if total_questions == 0:
        return redirect('assessment_list')

    correct_count = 0
    results_breakdown = []

    for q in questions:
        selected_option = request.POST.get(f'question_{q.id}', '').upper()
        is_correct = (selected_option == q.correct_option)
        if is_correct:
            correct_count += 1
            
        results_breakdown.append({
            'question': q,
            'selected': selected_option,
            'correct': q.correct_option,
            'is_correct': is_correct,
            'explanation': q.explanation,
        })

    score_pct = round((correct_count / total_questions) * 100)
    passed = score_pct >= assessment.passing_score

    # Proctoring security telemetry
    violations_count = int(request.POST.get('proctor_violations', 0) or 0)
    camera_verified = request.POST.get('camera_verified', 'true') == 'true'
    mic_verified = request.POST.get('mic_verified', 'true') == 'true'
    screen_verified = request.POST.get('screen_verified', 'true') == 'true'
    fullscreen_verified = request.POST.get('fullscreen_verified', 'true') == 'true'
    proctored = request.POST.get('proctor_verified', 'true') == 'true'

    attempt = AssessmentAttempt.objects.create(
        student=profile,
        assessment=assessment,
        score=score_pct,
        passed=passed,
        proctored=proctored,
        violations_count=violations_count,
    )

    if passed:
        # Update or verify student skill
        st_skill, _ = StudentSkill.objects.get_or_create(
            student=profile,
            skill=assessment.skill,

            defaults={'proficiency': score_pct}
        )
        st_skill.is_verified = True
        st_skill.verified_score = score_pct
        st_skill.proficiency = max(st_skill.proficiency, score_pct)
        st_skill.verified_at = timezone.now()
        st_skill.save()

        Notification.objects.create(
            user=request.user,
            title=f"Skill Verified: {assessment.skill.name}! 🎯",
            message=f"Congratulations! You scored {score_pct}% on the {assessment.skill.name} assessment. A verified badge was added to your portfolio.",
            link="/student/skills/"
        )
        messages.success(request, f"Congratulations! You passed with {score_pct}% and earned a Verified Skill badge!")
    else:
        messages.warning(request, f"You scored {score_pct}%. Passing score is {assessment.passing_score}%. Review the recommendations below.")

    return render(request, 'skills/assessment_result.html', {
        'assessment': assessment,
        'attempt': attempt,
        'score_pct': score_pct,
        'passed': passed,
        'results_breakdown': results_breakdown,
        'learning_resources': assessment.skill.learning_resources.all()[:4],
        'proctored': proctored,
        'violations_count': violations_count,
        'camera_verified': camera_verified,
        'mic_verified': mic_verified,
        'screen_verified': screen_verified,
        'fullscreen_verified': fullscreen_verified,
    })
