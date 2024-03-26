.. _introduction:

Introduction
============

.. figure:: /images/intro.png
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
Within ANALYST, the import and export routines can be executed through the
`ui.json <https://mirageoscience-geoh5py.readthedocs-hosted.com/en/latest/content/uijson_format/index.html>`_
interface.  To learn more about importing and exporting drillhole data with
**las-geoh5**, see the :ref:`import` and :ref:`export` pages.
