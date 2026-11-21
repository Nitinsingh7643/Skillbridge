# SkillBridge — Academia to Industry Collaboration Portal
> **Intelligent Skill Mapping, Curricula Alignment & Placement Engine**

---

## 📌 Executive Summary
**SkillBridge** is an industry-grade web platform developed with Python and Django. Unlike traditional placement portals that merely post job openings, SkillBridge serves as an intelligent collaborative bridge connecting four key stakeholders:
1. **Students** — Build verifiable digital portfolios, undertake timed skill verification assessments, discover skill deficits against real-world jobs, receive curated learning paths, and track applications.
2. **Colleges / TPOs (Training & Placement Officers)** — Monitor cohort-level skill readiness, run eligibility and skill match checks across departments against company requirements, organize industry workshops, and export placement audit reports.
3. **Industry / Recruiters** — Post internships and full-time jobs with weighted skill requirements ($w_i$), discover candidates ranked by automated match percentage, manage a 5-stage recruitment pipeline, and broadcast future skill demand forecasts.
4. **Platform Administrators** — Verify institutions and companies, manage master skill catalogs, and maintain platform security and role governance.

---

## 📐 Mathematical Skill Gap & Matching Engine
SkillBridge implements a transparent, weighted rule-based gap analysis formula directly addressing the curriculum-to-industry gap:

$$\text{Gap}_i = \max(0, \text{Required}_i - \text{Current}_i)$$

$$\text{GapScore} = \frac{\sum w_i \times \text{Gap}_i}{\sum w_i}$$

$$\text{MatchScore} = \max(0, 100 - \text{GapScore})$$

Where:
- $w_i$ = Recruiter-defined importance weight of skill $i$ (1 to 100)
- $\text{Required}_i$ = Minimum industry proficiency required (1 to 100%)
- $\text{Current}_i$ = Student's verified or self-reported proficiency level (0 if missing)

### Practical Demonstration:
For a *Full Stack Cloud Developer* opening requiring:
- JavaScript (Required: 85%, Weight: 90) $\rightarrow$ Student Level: 90% $\rightarrow$ Gap: 0
- React.js (Required: 80%, Weight: 85) $\rightarrow$ Student Level: 65% $\rightarrow$ Gap: 15
- MongoDB (Required: 75%, Weight: 75) $\rightarrow$ Student Level: 40% $\rightarrow$ Gap: 35
- **Weighted GapScore:** 15.6%
- **MatchScore:** 84%
- **Actionable Output:** Highlights MongoDB and React.js as priority deficits and generates targeted learning modules (e.g. MongoDB CRUD lab, React 18 hooks tutorial).

---

## 🚀 Key Modules & System Features

### Module 1: Role-Based Access Control (RBAC) & Security
- Custom User Model (`CustomUser`) with roles: `STUDENT`, `COLLEGE`, `INDUSTRY`, `ADMIN`.
- Strict view decorators (`@student_required`, `@college_required`, `@recruiter_required`, `@admin_required`) preventing privilege escalation.
- Approval and verification toggles for colleges and corporate partners.

### Module 2: Digital Academic & Professional Portfolio
- Real-time transparent scoring:
  - **Placement Readiness Score (%)** (Composite of CGPA, verified skills count, technical skill avg, and hands-on projects)
  - **Internship Readiness Score (%)**
  - **Technical Proficiency Score (%)**
  - **Soft Skills Index (%)**
- Project portfolios with GitHub and live demo links.

### Module 3 & 4: Skill Mapping & Learning Recommendations
- Centralized Skill Matrix categorized into Web Development, Databases, DevOps & Cloud, Core CS, and Soft Skills.
- Automatically curates online courses, GitHub starter repos, documentation, and practice labs tailored to missing skills.

### Module 5: Internship & Placement Pipeline
- 5-stage recruitment workflow:
  1. `APPLIED` $\rightarrow$ 2. `UNDER_REVIEW` $\rightarrow$ 3. `SHORTLISTED` $\rightarrow$ 4. `INTERVIEW` (with date/time, mode, and virtual meeting link) $\rightarrow$ 5. `SELECTED` / `REJECTED`.
- Recruiter **Candidate Discovery** tool ranking all college students by match score against any posted JD.

### Module 6: College / TPO Command Center
- **Cohort Eligibility & Skill Match Tool**: Select any company opening (e.g. Full Stack Developer) to evaluate all college students across CSE, IT, ECE, identifying eligible candidates and highlighting cohort-wide training deficits.
- Export student placement readiness rosters to **CSV** or print official accreditation reports (NAAC/NBA compliant format).

### Module 7: Academia–Industry Collaboration Hub
- **Industry Skill Demand Forecasts**: Companies submit quarterly hiring demands so colleges can proactively organize bootcamps.
- **Collaborative Workshops**: Industry experts or TPOs propose, schedule, and accept technical training sessions.
- **Live Industry Projects**: Companies post problem statements for collegiate teams with evaluation criteria.

### Module 8: Notifications & Automated Alerts
- In-app notification center alerting students about application updates, interview invites, and newly announced workshops.

---

## 🌟 Enterprise Highlights & Core Capabilities
1. **AI / Smart Resume Parser** (`pypdf` + regex extraction engine):
   - Extracts contact details, degree, detected CGPA, GitHub/LinkedIn links, and matches skills against the SkillBridge catalog.
   - 1-click button to populate student profiles with extracted data.
2. **Skill Verification Engine** (Timed MCQ Assessments):
   - Timed quizzes with real-time countdown timer in JavaScript.
   - Passing threshold (60%) awards a verified skill badge directly to the student portfolio.
3. **Interactive Visual Analytics** (Chart.js):
   - Student skill radar chart.
   - Comparative Bar Chart: Industry Requirement vs Student Proficiency.
   - Aggregate Industry Skill Demand Forecast chart.

---

## 🔑 Pre-Configured Demo Accounts (Ready to Test)

| Role | Username | Default Access | Notes |
| :--- | :--- | :--- | :--- |
| **College / TPO** | `tpo_rvce` | 1-Click Quick-Fill on Login | RV College of Engineering TPO |
| **Industry Recruiter (Google)** | `recruiter_google` | 1-Click Quick-Fill on Login | Google Cloud India |
| **Industry Recruiter (TCS)** | `recruiter_tcs` | 1-Click Quick-Fill on Login | Tata Consultancy Services |
| **Student (High Match)** | `student_rahul` | 1-Click Quick-Fill on Login | 8.85 CGPA, CSE, Full-Stack portfolio |
| **Student (Backend & Data)** | `student_priya` | 1-Click Quick-Fill on Login | 9.15 CGPA, IT, Python & PostgreSQL |
| **Student (Needs Training)** | `student_amit` | 1-Click Quick-Fill on Login | 7.20 CGPA, ECE, Demonstrates gap engine |

> **Note:** Demo account credentials can be loaded directly on the platform [Login Page](/accounts/login/) using the 1-click test buttons, or configured via environment variables (`DEFAULT_SEED_PASSWORD`).

---

## 🛠️ Installation & Quickstart

### 1. Requirements
- Python 3.10+
- Django 5.x / 6.x
- `pypdf` (installed for resume parsing)

### 2. Apply Migrations & Seed Sample Data
```bash
python manage.py migrate
python manage.py seed_data
```

### 3. Run Automated Tests
```bash
python manage.py test
```

### 4. Start the Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

