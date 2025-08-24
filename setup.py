from setuptools import setup, find_packages

setup(
    name="ai-job-agent",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # Add your project's dependencies here
        "python-docx",
        "pdfminer.six",
        "python-dotenv",
        "pydantic",
    ],
    python_requires=">=3.8",
)
