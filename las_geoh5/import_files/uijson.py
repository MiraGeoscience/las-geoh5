#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

from copy import deepcopy

from geoh5py.ui_json.constants import default_ui_json


# pylint: disable=duplicate-code

ui_json = dict(
    deepcopy(default_ui_json),
    **{
        "title": "LAS files to Drillhole group",
        "run_command": "las_geoh5.import_files.driver",
        "conda_environment": "las-geoh5",
        "drillhole_group": {
            "main": True,
            "label": "Drillhole group",
            "value": None,
            "groupType": ["{825424fb-c2c6-4fea-9f2b-6cd00023d393}"],
        },
        "files": {
            "main": True,
            "label": "Files",
            "value": None,
            "fileDescription": ["LAS files"],
            "fileType": ["las"],
            "fileMulti": True,
        },
        "name": {
            "main": True,
            "label": "Property group name",
            "group": "Property group",
            "value": "",
        },
        "collocation_tolerance": {
            "main": True,
            "label": "Collocation tolerance",
            "group": "Property group",
            "value": 0.01,
            "tooltip": (
                "Tolerance for determining collocation of data locations "
                "and ultimately deciding if incoming data should belong to "
                "an existing property group.",
            ),
        },
        "collar_x_name": {
            "main": True,
            "label": "Easting",
            "tooltip": "Name of header field containing the collar easting.",
            "value": "X",
            "group": "Collar",
            "optional": True,
            "enabled": False,
        },
        "collar_y_name": {
            "main": True,
            "label": "Northing",
            "tooltip": "Name of header field containing the collar northing.",
            "value": "Y",
            "group": "Collar",
            "optional": True,
            "enabled": False,
        },
        "collar_z_name": {
            "main": True,
            "tooltip": "Name of header field containing the collar elevation.",
            "label": "Elevation",
            "value": "ELEV",
            "group": "Collar",
            "optional": True,
            "enabled": False,
        },
        "skip_empty_header": {
            "main": True,
            "label": "Skip empty header",
            "value": False,
            "tooltip": (
                "Importing files without collar information "
                "results in drillholes placed at the origin. "
                "Check this box to skip these files."
            ),
        },
        "warnings": {
            "main": True,
            "label": "Warnings",
            "value": True,
            "tooltip": "Show warnings during import.",
        },
    },
)
