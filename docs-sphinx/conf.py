# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Repopulation-With-Elite-Set'
copyright = '2025, Pedro'
author = 'Pedro'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os
import sys

# Adiciona o diretório do projeto ao sys.path para o Sphinx encontrar os módulos
sys.path.insert(0, os.path.abspath('..'))

extensions = [
    'sphinx.ext.autodoc', # Para gerar docs de docstrings
    'myst_parser'         # Para usar arquivos Markdown
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown'
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'pt_BR'

# -- Theme switcher ----------------------------------------------------------
# 1: Sphinx Book Theme
# 2: Furo
# 3: PyData Sphinx Theme

theme_choice = 1  # <-- Mude este número para trocar o tema

if theme_choice == 1:
    html_theme = 'sphinx_book_theme'
    html_theme_options = {
        "repository_url": "https://github.com/PedroVic12/Repopulation-With-Elite-Set",
        "use_repository_button": True,
        "home_page_in_toc": True,
        "logo": {
            "text": "Repopulation-With-Elite-Set",
        }
    }
elif theme_choice == 2:
    html_theme = 'furo'
    html_theme_options = {
        "light_css_variables": {
            "color_primary": "#003366",
            "color_accent": "#007acc",
        },
        "dark_css_variables": {
            "color_primary": "#007acc",
            "color_accent": "#0099ff",
        },
    }
else:
    html_theme = 'pydata_sphinx_theme'
    html_theme_options = {
        "logo": {
            "text": "Repopulation-With-Elite-Set",
        },
        "icon_links": [
            {
                "name": "GitHub",
                "url": "https://github.com/PedroVic12/Repopulation-With-Elite-Set",
                "icon": "fa-brands fa-github",
            }
        ],
        "primary_sidebar_end": ["sidebar-ethical-ads.html"],
    }


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = ['_static']
