
class MockLLM:
    def generate(self, prompt: str, max_tokens: int = 768, temperature: float = 0.6) -> str:
        """Mock LLM that returns a simple response for testing."""
        return """## SUMMARY
Experienced Software Engineer with 3+ years of experience in Python and web development.

## TECHNICAL SKILLS
### Programming Languages
- Python, JavaScript, SQL

### Web Technologies
- Django, Flask, React

## PROFESSIONAL EXPERIENCE
### Software Engineer
Test Company | Remote | 2020 - Present
- Developed and maintained web applications using Python and Django
- Optimized database queries, improving performance by 40%
- Led a team of 3 developers in delivering a major feature

## PROJECTS
### E-commerce Platform
Technologies: Python, Django, PostgreSQL, React
- Built a full-stack e-commerce platform with user authentication and payment processing
- Implemented a recommendation engine that increased sales by 20%

## EDUCATION
B.Tech in Computer Science
Test University | 2020

## RESEARCH PUBLICATIONS
- "Optimizing Web Applications for Performance" (2022)"""
