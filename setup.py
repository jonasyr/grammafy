"""Setup configuration for Grammafy."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="grammafy",
    version="2.0.0",
    author="Grammafy Contributors",
    description="Convert LaTeX files to clean text for grammar checking",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/grammafy",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Markup :: LaTeX",
    ],
    python_requires=">=3.10",
    install_requires=[
        "uni-curses>=1.5",
    ],
    entry_points={
        "console_scripts": [
            "grammafy=scr.grammafy:main",
        ],
    },
)
