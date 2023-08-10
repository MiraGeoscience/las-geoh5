#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  All rights reserved.
#

from __future__ import annotations

import argparse
import sys
from copy import deepcopy
from pathlib import Path

from geoh5py.ui_json import InputFile
from geoh5py.ui_json.constants import default_ui_json
from geoh5py.ui_json.templates import group_parameter, string_parameter


def write_uijson(basepath: str | Path, mode: str = "export"):
    """
    Write a ui.json file for either import or export or las files.

    :param basepath: Root directory for las data.
    :param mode: Switch for 'import' or 'export' behaviour.

    :return: Input file for the written data.
    """

    ui_json = deepcopy(default_ui_json)
    name_parameter = string_parameter(label="Name", value="", optional="enabled")

    if mode == "export":
        drillhole_group = group_parameter(
            label="Drillhole group",
            group_type=("{825424fb-c2c6-4fea-9f2b-6cd00023d393}",),
        )
    elif mode == "import":
        name_parameter["group"] = "Simple"
        name_parameter["enabled"] = False
        drillhole_group = string_parameter(label="Drillhole group", value="")
        drillhole_group["group"] = "Simple"

    else:
        raise ValueError("Mode argument must be 'import' or 'export'.")

    ui_json.update(
        dict(
            {
                "title": f"{mode.capitalize()} drillhole group",
                "run_command": "las_geoh5.main",
                "conda_environment": "las-geoh5",
                "drillhole_group": drillhole_group,
                "name": name_parameter,
            },
        )
    )
    ifile = InputFile(ui_json=ui_json, validate=False)
    ifile.path = str(basepath)
    ifile.write_ui_json(f"{mode}_to_las.ui.json", basepath)

    return ifile


def main(args):
    print(args)
    parser = argparse.ArgumentParser(description="Write ui.json files.")
    parser.add_argument(
        "path", type=Path, help="Path to folder where ui.json files will be written."
    )
    parser.add_argument(
        "mode",
        type=str,
        choices={"import", "export", "all"},
        help="Mode switching between 'import', 'export', and 'all' behaviour.",
    )
    args = parser.parse_args(args)
    if args.mode == "all":
        for m in ["import", "export"]:  # pylint: disable=invalid-name
            write_uijson(args.path, m)
    else:
        write_uijson(args.path, args.mode)


if __name__ == "__main__":
    main(sys.argv[1:])
