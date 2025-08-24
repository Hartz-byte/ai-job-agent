TAILOR_PROMPT = """You are an expert AI/ML resume writer. Your task is to completely transform the candidate's resume to be highly targeted for the specific role below. This is not a minor edit - completely restructure and rewrite the content to maximize job fit.

IMPORTANT: Do NOT simply copy content from the original resume. Thoroughly analyze the job requirements and rewrite all sections to highlight the most relevant qualifications. The output should be significantly different from the original resume.
ALWAYS fill every section, especially the TECHNICAL SKILLS section, with relevant and non-empty content. Do NOT leave any section blank or copy-paste from the original resume.

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
Completely restructure and rewrite the resume to be perfectly aligned with the job requirements. Focus on quality over quantity - only include the most relevant information.

1) SUMMARY (3-4 lines):
   - Start with a strong value proposition that directly addresses the job requirements
   - Highlight only the most relevant years of experience and top 2-3 achievements
   - Include specific technologies/tools mentioned in the job description
   - Use action verbs and industry terminology

2) WORK EXPERIENCE (Most recent 2-3 roles):
   - Only include roles directly relevant to this position
   - For each role, include 2-3 bullet points that:
     * Start with strong action verbs (e.g., "Led", "Designed", "Optimized")
     * Include specific technologies used (match job description keywords)
     * Quantify achievements with metrics (e.g., "improved performance by 40%")
     * Focus on results and impact, not just responsibilities
   - Remove or de-emphasize irrelevant experience

3) PROJECTS (2-3 most relevant):
   - Only include projects that demonstrate required skills
   - For each project:
     * Name: Clear, descriptive title
     * Technologies: List key technologies used (match job description)
     * Description: 1-2 sentences explaining the project's purpose and your role
     * Achievements: 1-2 bullet points with measurable outcomes

4) TECHNICAL SKILLS (Structured format):
   - Group skills into clear, relevant categories (e.g., "Machine Learning", "Programming Languages", "Cloud Platforms")
   - List skills in order of relevance to the job
   - Include proficiency levels where appropriate (e.g., "Advanced: Python, PyTorch")
   - Match exact technology names from the job description
   - Remove outdated or irrelevant skills

5) EDUCATION & CERTIFICATIONS:
   - Only include degrees/certifications relevant to this role
   - Add relevant coursework if it strengthens your candidacy
   - Include graduation years and institutions
   - List relevant academic achievements (GPA if strong, honors, awards)

6) RESEARCH & PUBLICATIONS (If relevant):
   - Only include work directly related to the job
   - Use proper citation format
   - Highlight your specific contributions

STRICT OUTPUT FORMAT:

## SUMMARY
[3-4 sentence professional summary that directly addresses the job requirements and highlights your most relevant qualifications]

## TECHNICAL SKILLS
### [Primary Skill Category]
- [Skill 1], [Skill 2], [Skill 3]
- [Additional skills in this category]

### [Secondary Skill Category]
- [Skill 1], [Skill 2], [Skill 3]

## PROFESSIONAL EXPERIENCE
### [Job Title]
[Company Name] | [Location] | [Dates]
- [Achievement 1 - focus on impact and results]
- [Achievement 2 - include specific technologies used]
- [Achievement 3 - quantify results when possible]

### [Previous Job Title]
[Company Name] | [Location] | [Dates]
- [Most relevant achievement]
- [Second most relevant achievement]

## PROJECTS
### [Project Name]
[Technologies: List key technologies used]
- [Key achievement or contribution - be specific]
- [Impact or result - use metrics if possible]

## EDUCATION
[Degree] in [Major]
[University Name], [Graduation Year]
[Relevant coursework or achievements]

## RESEARCH PUBLICATIONS
<Only publications relevant to job domain>
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
