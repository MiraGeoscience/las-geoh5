.. _import:

Importing LAS Files
===================

Depending on whether you have an existing drillhole group or not, you may need to
create a new group.

.. figure:: /images/import/create_drillhole_group.png
    :align: center
    :width: 60%

Once there's a group to import the data into, the import dialog will guide the
user through the process.

.. figure:: /images/import/import.png
    :align: center
    :width: 100%

For every import operation the user will need to select an existing drillhole
group to import to and LAS files to import from.

.. figure:: /images/import/drillhole_group_and_file_selection.png
    :align: center
    :width: 45%

In order to organize the data by property, the user provides a name to the
``geoh5py.property_group`` and a collocation tolerance that is used by
**geoh5py** to determine if incoming data should be included in existing
property groups with the same name.  ie: if incoming data is not within the
collocation tolerance of an existing property group with the same name - a
new property group will be created.

.. figure:: /images/import/property_group_options.png
    :align: center
    :width: 50%

The next section gives the user the option to give collar location field names
expected to be found in the header of the LAS files being imported.  This is a
necessary step since the LAS format does not include a standard for this
information.  The user may also choose to skip files that do not contain collar
location information as this may lead to many drillholes without location data
being piled up at the origin.

.. figure:: /images/import/collar_options.png
    :align: center
    :width: 50%

Finally, the user may choose to include/exclude warnings which may be helpful
for initial imports, but a nuisance in subsequent import operations.

.. figure:: /images/import/warnings_control.png
    :align: center
    :width: 15%

To learn how to export data from a ``geoh5py.drillhole_group`` continue on to
the :ref:`export` section.
