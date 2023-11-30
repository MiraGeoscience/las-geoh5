#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

from copy import deepcopy

from las_geoh5.export_directories.uijson import ui_json

ui_json = dict(
    deepcopy(ui_json),
    **{
        "title": "LAS files to Drillhole group",
        "run_command": "las_geoh5.import_files.driver",
        "name": {
            "main": True,
            "label": "Name",
            "value": "",
        },
        "files": {
            "main": True,
            "label": "Files",
            "value": None,
            "fileDescription": ["LAS files"],
            "fileType": ["las"],
            "fileMulti": True,
        },
        "depths_name": {
            "label": "Depths",
            "value": "DEPTH",
            "group": "Import fields",
            "optional": True,
            "enabled": False,
        },
        "collar_x_name": {
            "label": "Collar x",
            "value": "X",
            "group": "Import fields",
            "optional": True,
            "enabled": False,
        },
        "collar_y_name": {
            "label": "Collar y",
            "value": "Y",
            "group": "Import fields",
            "optional": True,
            "enabled": False,
        },
        "collar_z_name": {
            "label": "Collar z",
            "value": "ELEV",
            "group": "Import fields",
            "optional": True,
            "enabled": False,
        },
        "skip_empty_header": {
            "label": "Skip empty header",
            "value": False,
            "tooltip": (
                "Importing files without collar information "
                "results in drillholes placed at the origin. "
                "Check this box to skip these files."
                ""
            ),
        },
    }
)
