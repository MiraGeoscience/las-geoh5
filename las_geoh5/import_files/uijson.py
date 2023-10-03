#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of my_app project.
#
#  All rights reserved.
#


ui_json = {
    "title": "LAS files to Drillhole group",
    "geoh5": None,
    "run_command": "las_geoh5.import_files.driver",
    "run_command_boolean": {
        "value": False,
        "label": "Run python module",
        "main": True,
        "tooltip": "Warning: launches process to run python model on save",
    },
    "monitoring_directory": None,
    "conda_environment": "las-geoh5",
    "conda_environment_boolean": False,
    "workspace": None,
    "drillhole_group": {
        "main": True,
        "label": "Drillhole group",
        "value": None,
        "groupType": ["{825424fb-c2c6-4fea-9f2b-6cd00023d393}"],
    },
    "name": {
        "main": True,
        "label": "Property group name",
        "value": None,
        "optional": True,
        "enabled": False,
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
