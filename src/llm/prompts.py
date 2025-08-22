TAILOR_PROMPT = """You are an assistant that tailors a candidate's resume bullets and short summary for a specific AI/ML job.

CANDIDATE_RESUME:
{resume_text}

JOB_POST:
{job_text}

TASK:
1) Write 6-10 bullet points highlighting the most relevant achievements/skills for THIS job (concise, quantifiable where possible).
2) Provide a 2-3 sentence professional summary tailored to this job.
3) Extract a list of top 12 skills/keywords for ATS (comma-separated).

Return as:
## SUMMARY
...
## BULLETS
- ...
## SKILLS
skill1, skill2, ...
"""

COVER_LETTER_PROMPT = """Write a one-page cover letter tailored to the following AI/ML job. Use a confident, genuine tone suitable for an entry-level candidate with MERN experience. Emphasize relevant ML projects, quick learning, and impact. Keep it under 300 words.

CANDIDATE:
Name: {name}
Email: {email}
Phone: {phone}

BASE_COVER_LETTER (optional):
{base_text}

JOB_POST:
{job_text}
"""
