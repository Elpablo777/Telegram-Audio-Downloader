#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="telegram-audio-downloader",
    version="0.1.0",
    author="Dein Name",
    author_email="deine.email@example.com",
    description="Ein leistungsstarkes Tool zum Herunterladen von Audiodateien aus Telegram-Gruppen",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dein-benutzer/telegram-audio-downloader",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "telethon>=1.29.2",
        "python-dotenv>=1.0.0",
        "tqdm>=4.66.1",
        "mutagen>=1.47.0",
        "pydub>=0.25.1",
        "peewee>=3.16.2",
        "click>=8.1.3",
        "rich>=13.4.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.3.1",
            "pytest-asyncio>=0.21.0",
            "black>=23.3.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "telegram-audio-downloader=telegram_audio_downloader.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
