# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os

from datetime import datetime
from importlib.metadata import version as get_version

from packaging.version import Version

project = "las-geoh5"
project_copyright = "%Y, Mira Geoscience Ltd"
author = "Mira Geoscience Ltd."

# The full version.
package_name = "las-geoh5"

full_version = Version(get_version(package_name))
# The full public version, including alpha/beta/rc tags
release = full_version.public
# remove the post release segment, if any
if full_version.is_postrelease:
    release = release.rsplit(".post", 1)[0]
# The base X.Y.Z version.
version = full_version.base_version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

nitpicky = True

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_issues",
    "sphinxcontrib.googleanalytics",
]
intersphinx_mapping = {
    # use None to auto-fetch objects.inv
    "numpy": ("https://numpy.org/doc/1.26/", None),
    "python": ("http://docs.python.org/3", None),
}

templates_path = ["_templates"]
exclude_patterns: list[str] = []

googleanalytics_id = os.environ.get("GOOGLE_ANALYTICS_ID", "")
if not googleanalytics_id:
    googleanalytics_enabled = False

issues_github_path = f"mirageoscience/{package_name}"

# -- Options for auto-doc ----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#module-sphinx.ext.autodoc

autodoc_typehints = "signature"

autodoc_mock_imports = [
    "geoapps_utils",
    "geoh5py",
    "numpy",
    "pydantic",
    "scipy",
    "skimage",
    "tqdm",
]

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