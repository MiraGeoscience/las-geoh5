.. _import:

Importing LAS Files
===================

Depending on whether you have an existing drillhole group or not, you may need to
create a new group.

.. figure:: /images/create_drillhole_group.png
    :align: center
    :width: 60%

Once there's a group to import the data into, the ui can be used to import the
data.

.. figure:: /images/import.png
    :align: center
    :width: 100%

The ui will guide the user to select a drillhole group and select LAS
files to import.

.. figure:: /images/drillhole_group_and_file_selection.png
    :align: center
    :width: 100%

In order to organize the data by property, the user can then give a name to the
``geoh5py.property_group`` and give a collocation tolerance that is used by
geoh5py to determine if incoming data should be included in existing property
groups with the same name.  ie: if incoming data is not within the collocation
tolerance of an existing property group with the same name - a new property
group will be created.

.. figure:: /images/property_group_options.png
    :align: center
    :width: 100%

The next section gives the user the option to give collar location field names
expected to be found in the header of the LAS files being imported.  This is a
necessary step since the LAS format does not include a standard for this
information.  The user may also choose to skip files that do not contain collar
location information as this may lead to many drillholes being piled up at the
origin.

.. figure:: /images/collar_options.png
    :align: center
    :width: 100%

Finally, the user may choose to include/exclude warnings which may be helpful
for initial imports, but a nuisance in subsequent import operations.

.. figure:: /images/warnings_checkbox.png
    :align: center
    :width: 100%
