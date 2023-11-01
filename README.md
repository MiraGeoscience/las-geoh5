# las-geoh5

Import/Export LAS files to/from geoh5 format.

This package contains three modules for import/export of LAS
files in and out of a geoh5 file.  the import/export directories
modules allow export and subsequent re-import of LAS files from
a drillhole group saved in a geoh5 file to a structured set of 
directories on disk.  The import files module is intended for the
more general case of LAS file import to an existing drillhole
group.


### Basic Usage

The most convenient way to use this package is through 
[Geoscience ANALYST Pro](https://mirageoscience.com/mining-industry-software/geoscience-analyst-pro/) where the import files driver may be
run from the **file -> import** menu.

All drivers may also be run from a ui.json file in 
[Geoscience ANALYST Pro](https://mirageoscience.com/mining-industry-software/geoscience-analyst-pro/) by either adding to the Python Scripts
directory or drag and drop into the viewport.  Defaulted ui.json
files can be found in the uijson folder of the las-geoh5 project.

Finally, the drivers can be run from CLI using the following

```bash
python -m las_geoh5.module.driver some_file.ui.json
```

Where module is one of `import_files`, `export_files`, or `import_las`.
