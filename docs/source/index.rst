About
=====

.. figure:: /images/index.png
    :align: center
    :width: 100%

The LAS file format is a public file format for the exchange of well log data.
The format includes a large header section followed by a block of depth indexed
data columns.  The irregular structure of the format poses a challenge for most
text parsing tools.  The goal of the las-geoh5 package is to leverage the
existing `lasio <https://lasio.readthedocs.io/en/latest/>`_ python package for
reading and writing LAS files in order to convert in and out of the
`hdf5 <https://docs.h5py.org/en/stable/>`_ format using
`geoh5py <https://mirageoscience-geoh5py.readthedocs-hosted.com/en/latest/>`_.

The recommended usage of the las-geoh5 package for most users is through the
`Geoscience ANALYST <https://mirageoscience.com/geoscience-analyst/>`_ software.
Within ANALYST, the import and export routines can be executed through menu system
or a `ui.json <https://mirageoscience-geoh5py.readthedocs-hosted.com/en/latest/content/uijson_format/index.html>`_
interface.  To learn more about importing and exporting drillhole data with
**las-geoh5**, see the :ref:`import` and :ref:`export` pages.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   getting_started
   usage
   import
   export


License
^^^^^^^
las-geoh5 is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

las-geoh5 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with las-geoh5.  If not, see `<https://www.gnu.org/licenses/>`_.


Third Party Software
^^^^^^^^^^^^^^^^^^^^
The las-geoh5 Software may provide links to third party libraries or code (collectively “Third Party Software”)
to implement various functions. Third Party Software does not comprise part of the Software.
The use of Third Party Software is governed by the terms of such software license(s).
Third Party Software notices and/or additional terms and conditions are located in the
`THIRD_PARTY_SOFTWARE`_ file.

.. _THIRD_PARTY_SOFTWARE: THIRD_PARTY_SOFTWARE.rst

Copyright
^^^^^^^^^
Copyright (c) 2024 Mira Geoscience Ltd.
