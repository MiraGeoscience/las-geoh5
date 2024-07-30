#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

from copy import deepcopy

from geoh5py.ui_json.constants import default_ui_json


ui_json = dict(
    deepcopy(default_ui_json),
    **{
        "title": "LAS file directories to Drillhole group",
        "run_command": "las_geoh5.import_directories.driver",
        "conda_environment": "las-geoh5",
        "drillhole_group": {
            "main": True,
            "label": "Drillhole group",
            "value": None,
            "groupType": ["{825424fb-c2c6-4fea-9f2b-6cd00023d393}"],
        },
        "parent_folder": {
            "main": True,
            "label": "Directory",
            "value": None,
            "fileDescription": ["Directory"],
            "fileType": ["directory"],
            "directoryOnly": True,
            "fileMulti": False,
        },
    },
)
