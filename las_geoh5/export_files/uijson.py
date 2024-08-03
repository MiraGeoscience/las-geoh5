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
        "title": "Drillhole group to LAS file directories",
        "run_command": "las_geoh5.export_files.driver",
        "conda_environment": "las-geoh5",
        "drillhole_group": {
            "main": True,
            "label": "Drillhole group",
            "value": None,
            "groupType": ["{825424fb-c2c6-4fea-9f2b-6cd00023d393}"],
        },
        "rootpath": {
            "main": True,
            "label": "Directory",
            "fileDescription": ["Directory"],
            "fileType": ["directory"],
            "value": None,
            "directoryOnly": True,
        },
        "use_directories": {
            "main": True,
            "label": "Use directories",
            "tooltip": "Organize LAS files by property group directories",
            "value": True,
        },
    },
)
