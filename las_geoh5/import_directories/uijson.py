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
        "title": "LAS file directories to Drillhole group",
        "run_command": "las_geoh5.import_directories.driver",
    }
)
