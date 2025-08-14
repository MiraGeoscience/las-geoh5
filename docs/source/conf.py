# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from datetime import datetime
from importlib.metadata import version
from packaging.version import Version

project = "las-geoh5"
project_copyright = "%Y, Mira Geoscience Ltd"
author = "Mira Geoscience Ltd."

# The full version.
release = version("las-geoh5")
# The base X.Y.Z version.
version = Version(release).base_version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ["_templates"]
exclude_patterns: list[str] = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_theme_options = {
    'description': f"version {release}",
}


def get_copyright_notice():
    return f"Copyright {datetime.now().strftime(project_copyright)}"

rst_epilog = f"""
.. |copyright_notice| replace:: {get_copyright_notice()}.
"""