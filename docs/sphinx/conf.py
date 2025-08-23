# Configuration file for the Sphinx documentation builder

import os
import sys
from pathlib import Path

# Add source path
sys.path.insert(0, os.path.abspath('../../src'))

# -- Project information -----------------------------------------------------

project = 'Telegram Audio Downloader'
copyright = '2024, Pablo'
author = 'Pablo'
version = '1.0.0'
release = '1.0.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.githubpages',
    'myst_parser',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The suffix(es) of source filenames.
source_suffix = {
    '.rst': None,
    '.md': 'myst_parser',
}

# The master toctree document.
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_theme_options = {
    'analytics_id': '',
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

html_context = {
    "display_github": True,
    "github_user": "Elpablo777",
    "github_repo": "Telegram-Audio-Downloader",
    "github_version": "main",
    "conf_py_path": "/docs/sphinx/",
}

# Custom CSS
html_css_files = [
    'custom.css',
]

# -- Extension configuration -------------------------------------------------

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'telethon': ('https://docs.telethon.dev/en/stable/', None),
}

# Todo extension
todo_include_todos = True

# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
    'preamble': '',
    'figure_align': 'htbp',
}

latex_documents = [
    (master_doc, 'TelegramAudioDownloader.tex', 'Telegram Audio Downloader Documentation',
     'Pablo', 'manual'),
]

# -- Options for manual page output ------------------------------------------

man_pages = [
    (master_doc, 'telegram-audio-downloader', 'Telegram Audio Downloader Documentation',
     [author], 1)
]

# -- Options for Texinfo output ----------------------------------------------

texinfo_documents = [
    (master_doc, 'TelegramAudioDownloader', 'Telegram Audio Downloader Documentation',
     author, 'TelegramAudioDownloader', 'Download audio files from Telegram groups.',
     'Miscellaneous'),
]

# -- Custom configuration ----------------------------------------------------

# MyST Parser configuration
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

myst_url_schemes = ("http", "https", "mailto")