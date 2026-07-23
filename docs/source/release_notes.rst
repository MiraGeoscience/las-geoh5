Release Notes
=============

Release 0.3.3 (2026-07-04)
--------------------------

- Remove and fix pylint and mypy disables
- Update to Python 3.12

Release 0.3.2 (2025-12-18)
--------------------------

- Review changes made to ui.json coming from release
- Remove depth name from import-files ui.json


Release 0.3.1 (2025-06-18)
--------------------------

- Build conda package faster with rattler-build
- For pypi, use dedicated package.rst as long description (readme field) instead of README.rst
- Relock on latest git dev revisions
- Re-versioned
- Adjust ui.json
- Update ui.json file as per latest adjustment in Analyst


Release 0.3.0 (2025-02-07)
--------------------------

- Clean out "workspace" field in UI.json
- Improve tooltips and label in title for MNEM field for collar
- Fixes for using geoh5 v0.10.0
- LAS importer - vertical colocation
- Check that utf-8 characters are supported
- Do not include top level files in wheels



Release 0.2.0 (2024-04-15)
--------------------------

- Add Documentation.
- Drillhole name first in exported LAS files.
- Suffix exported .las files with property group name.
- Move all parameters in import ui.json to main tab.
- Expose collocation tolerance in import ui.json file
- Improve logging
- Increment property group and data names for existing non-collocated objects.

Release 0.1.0 (2023-11-02)
--------------------------

- Introduce a generalized .las importer.
- Introduce import/export in and out of directory structure.
