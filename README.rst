|coverage| |maintainability| |precommit_ci| |docs| |style| |version| |status| |pyversions|


.. |docs| image:: https://readthedocs.com/projects/mirageoscience-las-geoh5/badge/?version=latest
    :alt: Documentation Status
    :target: https://mirageoscience-las-geoh5.readthedocs-hosted.com/en/latest/?badge=latest

.. |coverage| image:: https://codecov.io/gh/MiraGeoscience/las-geoh5/branch/develop/graph/badge.svg
    :alt: Code coverage
    :target: https://codecov.io/gh/MiraGeoscience/las-geoh5

.. |style| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :alt: Coding style
    :target: https://github.com/pf/black

.. |version| image:: https://img.shields.io/pypi/v/las-geoh5.svg
    :alt: version on PyPI
    :target: https://pypi.python.org/pypi/las-geoh5/

.. |status| image:: https://img.shields.io/pypi/status/las-geoh5.svg
    :alt: version status on PyPI
    :target: https://pypi.python.org/pypi/las-geoh5/

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/las-geoh5.svg
    :alt: Python versions
    :target: https://pypi.python.org/pypi/las-geoh5/

.. |precommit_ci| image:: https://results.pre-commit.ci/badge/github/MiraGeoscience/las-geoh5/develop.svg
    :alt: pre-commit.ci status
    :target: https://results.pre-commit.ci/latest/github/MiraGeoscience/las-geoh5/develop

.. |maintainability| image:: https://api.codeclimate.com/v1/badges/_token_/maintainability
   :target: https://codeclimate.com/github/MiraGeoscience/las-geoh5/maintainability
   :alt: Maintainability


las-geoh5
=========

Import/Export LAS files to/from geoh5 format.

This package allows for import and export of LAS files to and from a drillhole group.
There is a module each for import and export operations.  Each of these includes a driver
and a ui.json that parameterizes the driver and renders a UI for use within `Geoscience ANALYST Pro`_.
Read on to learn how to install las-geoh5 and get started importing and exporting LAS files.

.. contents:: Table of Contents
   :local:
   :depth: 3

Documentation
-------------
`Online documentation <https://mirageoscience-las-geoh5.readthedocs-hosted.com/en/latest/>`_


Installation
------------

Install **las-geoh5** with ``pip`` from PyPI::

    $ pip install las-geoh5


Or from a branch on `github <https://github.com/MiraGeoscience/las-geoh5>`_::

    $ pip install --upgrade --force-reinstall https://github.com/MiraGeoscience/las-geoh5/archive/refs/heads/BRANCH_NAME.zip

(to use a tag rather than a branch, replace ``heads\BRANCH_NAME.zip`` by ``tags\TAG_NAME.zip``)


Or from a local sources, after you have cloned the repository::

    $ git clone https://github.com/MiraGeoscience/las-geoh5 [-b BRANCH_NAME]
    $ pip install -e las-geoh5


Basic Usage
-----------

From Geoscience Analyst
~~~~~~~~~~~~~~~~~~~~~~~
.. _Geoscience ANALYST Pro: https://mirageoscience.com/mining-industry-software/geoscience-analyst-pro/

The most convenient way to use this package is through `Geoscience ANALYST Pro`_
where the import files driver may be run from the **file -> import**
menu.

All drivers may also be run from a ui.json file in `Geoscience ANALYST Pro`_
by either adding to the Python Scripts directory or drag and drop into
the viewport. Defaulted ui.json files can be found in the uijson folder
of the las-geoh5 project.

From command line
~~~~~~~~~~~~~~~~~
To run from command line, prepare first a JSON file with the parameters required for conversion.

Then execute with::

    $ las_to_geoh5 parameters.json [-o output_geoh5]
    $ geoh5_to_las parameters.json [-o output_dir]

where ``parameters.json`` is the path on disk to a JSON file with required input parameters.

If optional ``-o`` (or ``--out``) value is not provided, the program will write out to the location
specified by the JSON file.

License
-------

MIT License

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Third Party Software
--------------------

The curve-apps Software may provide links to third party libraries or code (collectively "Third Party Software")
to implement various functions. Third Party Software does not comprise part of the Software.
The use of Third Party Software is governed by the terms of such software license(s).
Third Party Software notices and/or additional terms and conditions are located in the
`THIRD_PARTY_SOFTWARE.rst`_ file.

.. _THIRD_PARTY_SOFTWARE.rst: ./docs/THIRD_PARTY_SOFTWARE.rst

Copyright
---------

Copyright (c) 2024 Mira Geoscience
