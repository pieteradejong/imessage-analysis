"""
Setup configuration for iMessage Analysis package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="imessage-analysis",
    version="0.1.0",
    description="A tool for analyzing iMessage data from macOS chat.db",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Pieter de Jong",
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=[
        "plotly>=5.0.0",
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.32.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "mypy>=0.991",
        ],
    },
    entry_points={
        "console_scripts": [
            "imessage-analysis=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
)
