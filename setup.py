#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="telegram-audio-downloader",
    version="1.0.0",
    author="Elpablo777",
    author_email="hannover84@msn.com",
    description="Ein leistungsstarker, asynchroner Python-Bot zum Herunterladen und Verwalten von Audiodateien aus Telegram-Gruppen",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Elpablo777/Telegram-Audio-Downloader",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "telethon>=1.29.2",
        "python-dotenv>=1.0.0",
        "tqdm>=4.66.1",
        "mutagen>=1.47.0",
        "pydub>=0.25.1",
        "peewee>=3.16.2",
        "click>=8.1.3",
        "rich>=13.4.2",
        "psutil>=5.9.0",
        "aiofiles>=23.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.3.1",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.3.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0",
            "bandit>=1.7.5",
            "safety>=2.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "telegram-audio-downloader=telegram_audio_downloader.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: System :: Archiving",
        "Operating System :: OS Independent",
    ],
    keywords="telegram audio downloader music bot cli async",
    project_urls={
        "Bug Reports": "https://github.com/Elpablo777/Telegram-Audio-Downloader/issues",
        "Source": "https://github.com/Elpablo777/Telegram-Audio-Downloader",
        "Documentation": "https://github.com/Elpablo777/Telegram-Audio-Downloader/wiki",
    },
)
