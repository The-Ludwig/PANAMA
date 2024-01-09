# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "PANAMA"
copyright = "2023, Ludwig Neste"
author = "Ludwig Neste"
# release = "v0.3.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "nbsphinx",
    "myst_parser",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx_click",
    "pydata_sphinx_theme",
]

# templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = [".rst", ".md"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_theme_options = {
    #     "logo": {
    #         "text": "My awesome documentation",
    #     },
    "collapse_navigation": False,
    "show_nav_level": 3,
    "show_toc_level": 3,
    "secondary_sidebar_items": [],
}
# html_static_path = ["_static"]
html_sidebars = {"**": ["page-toc", "sidebar-nav-bs", "sidebar-ethical-ads"]}


# -- Autodoc options
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}
