TAILOR_PROMPT = """You are an expert AI/ML resume writer. Tailor the candidate's resume for the specific role below.

CONTEXT:
Job Title: {job_title}
Company: {company}
Location: {location}
Job URL: {job_url}

CANDIDATE RESUME (raw text):
{resume_text}

JOB DESCRIPTION (raw text):
{job_text}

TASK:
1) Provide a 2-3 sentence professional SUMMARY tailored to this job (avoid buzzwords, include concrete domains/tools).
2) Write 6-8 BULLETS with quantified impact where possible, prioritize role-relevant items, use active verbs, avoid duplicates.
3) Provide 10-14 SKILLS/KEYWORDS for ATS (comma-separated, no duplicates, lowercase).

STRICT OUTPUT FORMAT:
## SUMMARY
<2-3 sentences>
## BULLETS
- <concise bullet>
- <concise bullet>
## SKILLS
skill1, skill2, ...
"""

COVER_LETTER_PROMPT = """Write a concise (220-320 words) cover letter tailored to the job below. Preserve the candidate's voice if BASE_COVER_LETTER is provided, but tailor details to the company and role. Prefer 2-3 compact paragraphs. Avoid generic fluff.

JOB:
Title: {job_title}
Company: {company}
Location: {location}
URL: {job_url}

CANDIDATE:
Name: {name}
Email: {email}
Phone: {phone}

BASE_COVER_LETTER (optional):
{base_text}

JOB DESCRIPTION (raw text):
{job_text}

OUTPUT: Body text only (no greeting or signature lines)."""
