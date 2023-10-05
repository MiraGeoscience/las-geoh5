#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of my_app project.
#
#  All rights reserved.
#

from copy import deepcopy

from las_geoh5.export_directories.uijson import ui_json

ui_json = dict(
    deepcopy(ui_json),
    **{
        "title": "LAS files to Drillhole group",
        "run_command": "las_geoh5.import_files.driver",
        "files": {
            "main": True,
            "label": "Files",
            "value": None,
            "fileDescription": ["LAS files"],
            "fileType": ["las"],
            "fileMulti": True,
        },
        "depths_name": {
            "main": True,
            "label": "Depths",
            "value": "DEPTH",
        },
        "collar_x_name": {
            "main": True,
            "label": "Collar x",
            "value": "X",
            "group": "Import fields",
            "optional": True,
            "enabled": False,
        },
        "collar_y_name": {
            "main": True,
            "label": "Collar y",
            "value": "Y",
            "group": "Import fields",
            "optional": True,
            "enabled": False,
        },
        "collar_z_name": {
            "main": True,
            "label": "Collar z",
            "value": "ELEV",
            "group": "Import fields",
            "optional": True,
            "enabled": False,
        },
    }
)
