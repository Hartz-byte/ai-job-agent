TAILOR_PROMPT = """
You are an expert resume writer and career coach. Your task is to tailor the provided resume to a specific job description. You must only use the information available in the original resume.

**CRITICAL RULE: Do not invent, add, or exaggerate any skills, experiences, or qualifications that are not explicitly mentioned in the original resume. Your goal is to rephrase, reframe, and highlight the existing information to align with the job description.**

**Resume Content:**
---
{resume_text}
---

**Job Description:**
---
{job_text}
---

**Instructions:**

1.  **Analyze the Job Description:** Carefully read the job description to identify the key requirements, skills, and qualifications the employer is looking for.

2.  **Tailor the Resume Content:** Rewrite the following sections of the resume to align with the job description.

    *   **SUMMARY:** Rewrite the summary to be a concise and impactful statement that highlights the candidate's most relevant qualifications and experiences for this specific job.

    *   **EXPERIENCE:** For each role in the experience section, review the bullet points. Rephrase them to emphasize the accomplishments and responsibilities that are most relevant to the job description. Use action verbs and quantify achievements where possible (using the data from the original resume).

    *   **PROJECTS:** For each project, rewrite the description to highlight the aspects that are most relevant to the job. Emphasize the technologies used and the outcomes achieved that align with the employer's needs.

    *   **SKILLS:** Review the skills list. You can reorder or group the skills to emphasize the ones that are most important for the job. Do not add any skills that are not in the original resume.

3.  **Maintain Professional Tone:** Ensure the language is professional, confident, and tailored to the company and role.

**Output Format:**

Provide the tailored content in the following format, with each section clearly marked.

SUMMARY:
<Your rewritten summary here>

EXPERIENCE:
<Your rewritten experience section here, with each job and its bullet points>

PROJECTS:
<Your rewritten projects section here>

SKILLS:
<Your rewritten skills section here>

"""

COVER_LETTER_PROMPT = """Write a highly personalized cover letter (250-350 words) for the specific job and company below. Research the company's mission, values, and recent developments to create a compelling narrative that shows genuine interest and perfect fit.

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

REQUIREMENTS:
1) Opening paragraph: Hook with specific company knowledge and role interest
2) Body paragraph 1: Highlight 2-3 most relevant achievements/experiences for this role
3) Body paragraph 2: Show knowledge of company/industry and explain mutual fit
4) Closing: Strong call to action and enthusiasm

Use the candidate's authentic voice while demonstrating deep understanding of both the role requirements and company culture. Include specific examples and quantified achievements where possible.

OUTPUT: Professional cover letter body text (no greeting or signature lines)."""
