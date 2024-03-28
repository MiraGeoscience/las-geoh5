.. _getting_started:

Getting Started
===============

I you are a Geoscience ANALYST user, you can skip this section since the installation will be bundled into
your software and using las-geoh5 is as simple as selecting from menu.  Otherwise, read on to learn how to
install and use via ui.json file inside or outside of ANALYST.

.. contents::

.. toctree::
   :maxdepth: 2

Installation
------------

Install Conda
~~~~~~~~~~~~~

Install Conda for Python 3.10 or higher. Follow this link to download its Windows installer (~140 MB of disk space):

`Miniforge <https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe>`_

.. figure:: /images/getting_started/Miniforge3_Setup-1.png
    :align: center
    :width: 200

.. figure:: /images/getting_started/Miniforge3_Setup-3.png
    :align: center
    :width: 200

Registering the Conda distribution as the default Python 3.10 interpreter is totally optional.
Preferably uncheck that box if you already have Python 3 installed on your system.

.. note:: We recommend installing **Miniforge**: beyond being smaller,
    it also installs packages from the conda-forge repository by default,
    which has no restriction for commercial use, while both Miniconda and Anaconda distributions use
    the Anaconda repository by default: see `Anaconda Terms of Service <https://www.anaconda.com/terms-of-service>`_ for details.
    In any case, the installation of **las-geoh5** forces the usage of the conda-forge repository,
    and is thus not affected by the Anaconda Terms of Service.

Install **las-geoh5** from PyPI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The latest release of **las-geoh5** can be installed from the Python package index (`PyPI <https://pypi.org/project/las-geoh5/>`_)
with ``pip install las-geoh5``.  However, because las-geoh5 contains dependencies that will not be
satisfied by the pip installation, we recommend using a conda environment and installing the package
and its few dependencies together.

This is as simple opening a miniforge terminal and running the following commands

.. code-block::

    conda create -n las-geoh5
    conda activate las-geoh5
    pip install las-geoh5 lasio geoh5py tqdm

This way you will have a *las-geoh5* environment that is already encoded into the ui.json files stored
with the package in the assets folder, and can begin running the programs contained within right away.

To learn more about running from ui.json file, proceed to the :ref:`usage` section.
