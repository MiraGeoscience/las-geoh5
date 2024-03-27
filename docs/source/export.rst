.. _export:

Exporting LAS Files
===================

The export of LAS files is done through the export dialog. The user will choose
among a small number of options controlling the process.

.. figure:: /images/export/export.png
    :align: center
    :width: 100%

    *Export Dialog.*

To export a drillhole group to LAS files, the user chooses the drillhole group
to export and pick a directory under which the files will be saved.

.. figure:: /images/export/drillhole_group_and_directory.png
    :align: center
    :width: 40%

    *Choosing drillhole group and directory for export.*

The files can be exported to a single directory or to a set of sub-directories
organized by property group.

.. figure:: /images/export/directories_control.png
    :align: center
    :width: 15%

    *Choosing a directory tree structure vs. a flat structure.*

If the user chooses to export to a directory tree structure, the files will be
organized into sub-directories for each property group

.. figure:: /images/export/use_directories_true.png
    :align: center
    :width: 100%

    *Example of directory tree structure.*

Otherwise, a flat structure will be used with filenames augmented with property
group names to avoid conflicts.

.. figure:: /images/export/use_directories_false.png
    :align: center
    :width: 100%

    *Example of flat structure.*
