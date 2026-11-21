def calculate_skill_gap_and_match(student, job):
    """
    Implements the SkillBridge Gap Analysis & Match Engine:
    Gap_i = max(0, Required_i - Current_i)
    GapScore = sum(w_i * Gap_i) / sum(w_i)
    MatchScore = round(max(0, 100 - GapScore))
    """
    requirements = job.skill_requirements.select_related('skill').all()
    if not requirements.exists():
        return {
            'match_score': 100,
            'gap_score': 0.0,
            'skill_breakdown': [],
            'gap_skills': [],
            'matching_skills': [],
            'top_recommendations': [],
        }

    # Map student skills by skill id
    student_skills_map = {ss.skill_id: ss for ss in student.skills.select_related('skill').all()}

    total_weighted_gap = 0.0
    total_weight = 0.0
    breakdown = []
    gap_skills = []
    matching_skills = []

    for req in requirements:
        w_i = float(req.importance_weight)
        req_level = float(req.min_proficiency)
        student_skill = student_skills_map.get(req.skill_id)
        current_level = float(student_skill.proficiency) if student_skill else 0.0
        is_verified = student_skill.is_verified if student_skill else False

        gap_i = max(0.0, req_level - current_level)
        total_weighted_gap += (w_i * gap_i)
        total_weight += w_i

        # Fetch top learning resources for this skill
        resources = list(req.skill.learning_resources.all()[:3])

        item = {
            'skill': req.skill,
            'skill_id': req.skill.id,
            'skill_name': req.skill.name,
            'required': int(req_level),
            'current': int(current_level),
            'gap': int(gap_i),
            'weight': int(w_i),
            'is_verified': is_verified,
            'has_skill': student_skill is not None,
            'surplus': int(max(0.0, current_level - req_level)),
            'resources': resources,
        }
        breakdown.append(item)

        if gap_i > 0:
            gap_skills.append(item)
        else:
            matching_skills.append(item)

    # Sort gaps by importance weight descending (highest weight gaps first)
    gap_skills.sort(key=lambda x: (x['gap'] > 0, x['weight'], x['gap']), reverse=True)

    if total_weight > 0:
        gap_score = total_weighted_gap / total_weight
        match_score = round(max(0.0, 100.0 - gap_score))
    else:
        gap_score = 0.0
        match_score = 100

    # Collect curated recommendations from the top skill gaps
    top_recommendations = []
    for g in gap_skills[:4]:
        for res in g['resources']:
            top_recommendations.append({
                'skill_name': g['skill_name'],
                'gap': g['gap'],
                'importance': g['weight'],
                'resource': res,
            })

    return {
        'match_score': match_score,
        'gap_score': round(gap_score, 1),
        'skill_breakdown': breakdown,
        'gap_skills': gap_skills,
        'matching_skills': matching_skills,
        'top_recommendations': top_recommendations,
    }

