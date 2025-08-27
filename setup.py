#!/usr/bin/env python3
"""Setup script for Telegram Audio Downloader."""

from setuptools import setup, find_packages
import os
import sys

# Add src to path to import version
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from telegram_audio_downloader import __version__
except ImportError:
    # Fallback if module import fails
    __version__ = "1.0.0"

# Read long description from README
def read_readme():
    """Read README file for long description."""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "A powerful Python tool for downloading audio files from Telegram channels and groups."

# Read requirements
def read_requirements(fname='requirements.txt'):
    """
    Read requirements from requirements.txt and return a list of package requirements.
    
    Args:
        fname (str): Path to the requirements file (default: 'requirements.txt')
        
    Returns:
        list: List of package requirements
    """
    requirements_path = os.path.join(os.path.dirname(__file__), fname)
    requirements = []
    
    if not os.path.exists(requirements_path):
        return requirements
        
    with open(requirements_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
                
            # Skip pip options (lines starting with '-') and VCS/URL requirements
            if line.startswith('-') or line.startswith('git+') or '://' in line:
                continue
                
            # Skip development dependencies
            if any(line.startswith(dev_pkg) for dev_pkg in ['pytest', 'black', 'isort', 
                                                          'flake8', 'mypy', 'docker']):
                continue
                
            # Clean up the line (remove comments and whitespace)
            if '#' in line:
                line = line.split('#')[0].strip()
                
            if line:  # Only add non-empty lines
                requirements.append(line)
    
    return requirements

setup(
    name="telegram-audio-downloader",
    version="1.1.0",
    author="Elpablo777",
    author_email="hannover84@msn.com",
    description="🎵 A powerful, asynchronous Python tool for downloading and managing audio files from Telegram groups",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Elpablo777/Telegram-Audio-Downloader",
    project_urls={
        "Bug Reports": "https://github.com/Elpablo777/Telegram-Audio-Downloader/issues",
        "Source": "https://github.com/Elpablo777/Telegram-Audio-Downloader",
        "Documentation": "https://github.com/Elpablo777/Telegram-Audio-Downloader/wiki",
        "Discussions": "https://github.com/Elpablo777/Telegram-Audio-Downloader/discussions",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Communications :: Chat",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Archiving",
        "Topic :: Utilities",
    ],
    python_requires=">=3.11",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.3.1",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.1",
            "black>=23.3.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0",
            "bandit>=1.7.5",
            "safety>=2.3.5",
        ],
        "docker": [
            "docker>=6.1.3",
            "python-multipart>=0.0.6",
        ],
    },
    entry_points={
        "console_scripts": [
            "telegram-audio-downloader=telegram_audio_downloader.cli:main",
        ],
    },
    keywords=[
        "telegram", "audio", "downloader", "asyncio", "cli", 
        "music", "media", "chat", "python", "tool"
    ],
    include_package_data=True,
    package_data={
        "telegram_audio_downloader": [
            "*.md", 
            "config/*.json", 
            "templates/*.html"
        ],
    },
    zip_safe=False,
)