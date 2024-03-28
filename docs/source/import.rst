.. _import:

Importing LAS Files
===================

Depending on whether you have an existing drillhole group or not, you may need to
create a new group by right clicking in the object tree of ANALYST.

.. figure:: /images/import/create_drillhole_group.png
    :align: center
    :width: 60%

    *Creating a new drillhole group.*

Once there's a group to import the data into, the import dialog will guide the
user through the process.

.. figure:: /images/import/import.png
    :align: center
    :width: 100%

    *Import dialog.*

For every import operation the user will need to select an existing drillhole
group to import to and LAS files to import from.

.. figure:: /images/import/drillhole_group_and_file_selection.png
    :align: center
    :width: 45%

    *Choosing drillhole group and files for import.*

In order to organize the data by property, the user provides a name to the
``geoh5py.property_group`` and a collocation tolerance that is used by
`geoh5py <https://mirageoscience-geoh5py.readthedocs-hosted.com/en/stable/index.html>`_ to determine if incoming data should be included in existing
property groups with the same name.  A new property group is
created if the incoming depth sampling is outside of the collocation tolerance.

.. figure:: /images/import/property_group_options.png
    :align: center
    :width: 50%

    *Choosing a name for the property group being imported and setting a tolerance for assigning to existing groups.*

The next section gives the user the option to provide collar location field names
expected to be found in the header of the LAS files being imported.  This is a
necessary step since the LAS format does not include a standard for this
information.  It may be necessary to scan the files to find field names that apply
to all (or most) of the files.  Just open the files in an editor and look in the
``Well`` section of the header for something that looks like easting/northing/elevation
data.

.. figure:: /images/import/las_collar_locations.png
    :align: center
    :width: 50%

    *Scanning LAS file headers for collar location data.*

The user may also choose to ``skip_empty_header`` to ignore files that do not contain
collar location information as this may lead to many drillholes without location data
being piled up at the origin.

.. figure:: /images/import/collar_options.png
    :align: center
    :width: 50%

    *Collar location options including a checkbox to skip files without location data.*

Finally, the user may choose to include/exclude warnings which may be helpful
for initial imports, but a nuisance in subsequent import operations.

.. figure:: /images/import/warnings_control.png
    :align: center
    :width: 15%

    *Setting warnings preference.*

To learn how to export data from a ``geoh5py.drillhole_group`` continue on to
the :ref:`export` section.
