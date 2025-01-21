from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
readme_path = Path(__file__).parent / "README.md"
with readme_path.open("r", encoding="utf-8") as f:
    long_description = f.read()

# Read requirements from requirements.txt
requirements_path = Path(__file__).parent / "requirements.txt"
with requirements_path.open("r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="tender-retrieval-pipeline",
    version="0.1.0",
    description="A robust knowledge graph query pipeline for tender documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/tender-retrieval-pipeline",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.5",
            "pytest-cov>=4.1.0",
            "black>=24.1.1",
            "isort>=5.13.2",
            "mypy>=1.8.0",
            "flake8>=7.0.0",
            "pre-commit>=3.6.0",
        ],
        "docs": [
            "sphinx>=7.2.6",
            "sphinx-rtd-theme>=2.0.0",
            "sphinx-autodoc-typehints>=1.25.2",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        "console_scripts": [
            "tender-pipeline=src.pipeline.cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/tender-retrieval-pipeline/issues",
        "Source": "https://github.com/yourusername/tender-retrieval-pipeline",
        "Documentation": "https://tender-retrieval-pipeline.readthedocs.io/",
    },
    include_package_data=True,
    package_data={
        "tender_retrieval_pipeline": [
            "py.typed",
            "*.pyi",
            "**/*.pyi",
        ],
    },
    zip_safe=False,
    platforms="any",
    license="MIT",
    keywords=[
        "neo4j",
        "knowledge graph",
        "tender",
        "document retrieval",
        "langgraph",
        "langchain",
        "pipeline",
    ],
)