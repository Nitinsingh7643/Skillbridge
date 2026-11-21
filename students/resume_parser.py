import re
from pypdf import PdfReader
from skills.models import Skill

def parse_resume_pdf(pdf_file):
    """
    AI/Smart Resume Parser:
    Extracts text, email, phone, links, education, projects,
    and matches skills against SkillBridge skill catalog.
    """
    text = ""
    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        return {'success': False, 'error': f"Failed to read PDF: {str(e)}", 'raw_text': ''}

    if not text.strip():
        return {'success': False, 'error': "Could not extract text from the PDF file.", 'raw_text': ''}

    # 1. Email extraction
    email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    email = email_match.group(0) if email_match else ""

    # 2. Phone extraction (Indian and standard formats)
    phone_match = re.search(r'(?:\+?91[\s-]?)?[6789]\d{9}', text)
    phone = phone_match.group(0) if phone_match else ""

    # 3. GitHub & LinkedIn URLs
    github_match = re.search(r'https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+', text, re.IGNORECASE)
    github_url = github_match.group(0) if github_match else ""

    linkedin_match = re.search(r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+', text, re.IGNORECASE)
    linkedin_url = linkedin_match.group(0) if linkedin_match else ""

    # 4. CGPA extraction
    cgpa = 8.0
    cgpa_match = re.search(r'(?:CGPA|GPA|CPI)[\s:=]+([0-9](?:\.[0-9]{1,2})?)', text, re.IGNORECASE)
    if cgpa_match:
        try:
            val = float(cgpa_match.group(1))
            if 0.0 <= val <= 10.0:
                cgpa = val
        except ValueError:
            pass

    # 5. Degree & Branch heuristics
    degree = "B.Tech"
    if re.search(r'\b(M\.Tech|MTech|Master of Technology)\b', text, re.IGNORECASE):
        degree = "M.Tech"
    elif re.search(r'\b(MCA|Master of Computer Applications)\b', text, re.IGNORECASE):
        degree = "MCA"
    elif re.search(r'\b(B\.E\.|B\.E|Bachelor of Engineering)\b', text, re.IGNORECASE):
        degree = "B.E."

    # 6. Skill matching against database
    detected_skills = []
    text_lower = text.lower()
    
    # Skill aliases mapping for common variations
    aliases = {
        'javascript': ['js', 'javascript', 'ecmascript'],
        'react.js': ['react', 'react.js', 'reactjs'],
        'node.js': ['node', 'node.js', 'nodejs'],
        'django': ['django', 'django rest framework', 'drf'],
        'python': ['python', 'py'],
        'postgresql': ['postgres', 'postgresql', 'psql'],
        'mongodb': ['mongo', 'mongodb'],
        'docker': ['docker', 'containerization'],
        'git & github': ['git', 'github', 'version control'],
        'sql': ['sql', 'mysql', 'sqlite', 'rdbms'],
        'c++': ['c++', 'cpp'],
        'rest apis': ['rest api', 'rest apis', 'restful'],
        'machine learning': ['ml', 'machine learning', 'scikit-learn'],
        'data structures': ['dsa', 'data structures', 'algorithms'],
        'system design': ['system design', 'distributed systems'],
    }

    all_db_skills = Skill.objects.select_related('category').all()
    for skill in all_db_skills:
        skill_name_lower = skill.name.lower()
        matched = False
        
        # Check alias dictionary
        if skill_name_lower in aliases:
            for variant in aliases[skill_name_lower]:
                pattern = r'\b' + re.escape(variant) + r'\b'
                if re.search(pattern, text_lower):
                    matched = True
                    break
        else:
            pattern = r'\b' + re.escape(skill_name_lower) + r'\b'
            if re.search(pattern, text_lower):
                matched = True

        if matched:
            detected_skills.append({
                'id': skill.id,
                'name': skill.name,
                'category': skill.category.name,
                'proficiency': 75,  # initial reasonable proficiency
            })

    # 7. Projects section extraction
    projects_found = []
    projects_section_match = re.search(
        r'(?:PROJECTS|ACADEMIC PROJECTS|KEY PROJECTS)\s*[:\n](.*?)(?:EDUCATION|EXPERIENCE|CERTIFICATIONS|SKILLS|ACHIEVEMENTS|$)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if projects_section_match:
        proj_text = projects_section_match.group(1).strip()
        lines = [l.strip() for l in proj_text.split('\n') if len(l.strip()) > 5]
        for l in lines[:3]:
            projects_found.append({
                'title': l[:80],
                'description': l,
            })

    return {
        'success': True,
        'email': email,
        'phone': phone,
        'github_url': github_url,
        'linkedin_url': linkedin_url,
        'degree': degree,
        'cgpa': cgpa,
        'detected_skills': detected_skills,
        'projects_found': projects_found,
        'raw_text_snippet': text[:500] + "...",
    }

