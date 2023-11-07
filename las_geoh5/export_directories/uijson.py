#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#


ui_json = {
    "title": "Drillhole group to LAS file directories",
    "geoh5": None,
    "run_command": "las_geoh5.export_directories.driver",
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
}
