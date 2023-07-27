#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of las_geoh5 project.
#
#  All rights reserved.

from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

import lasio
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.groups.drillhole_group import DrillholeGroup
from geoh5py.shared.concatenation import ConcatenatedDrillhole
from geoh5py.ui_json import InputFile
from geoh5py.ui_json.constants import default_ui_json
from geoh5py.ui_json.templates import (
    file_parameter, group_parameter, string_parameter
)

from las_geoh5.export_las import drillhole_to_las
from las_geoh5.import_las import las_to_drillhole



def export_las(group, basepath, name=None):

    drillholes = [
        k for k in group.children if isinstance(k, ConcatenatedDrillhole)
    ]

    name = name if name is not None else group.name
    subpath = Path(basepath / name)
    if not subpath.exists():
        subpath.mkdir()

    for drillhole in drillholes:
        drillhole_to_las(drillhole, subpath)

def import_las(workspace, basepath, name=None):

    if not basepath.exists():
        raise OSError(f"Path {str(basepath)} does not exist.")

    name = name if name is not None else basepath.name
    dh_group = DrillholeGroup.create(workspace, name=name)

    surveys_path = Path(basepath / "Surveys")
    surveys = [f for f in surveys_path.iterdir()]
    property_group_folders = [
        p for p in basepath.iterdir() if p.is_dir()
        and p.name != "Surveys"
    ]

    for p in property_group_folders:
        lasfiles = [
            lasio.read(f, mnemonic_case="preserve") for f in p.iterdir() if f.suffix == ".las"
        ]
        las_to_drillhole(workspace, lasfiles, dh_group, p.name, surveys)


def write_uijson(basepath, mode="export"):
    ui_json = deepcopy(default_ui_json)
    update = {}
    if mode == "export":
        drillhole_group = group_parameter(
            label="Drillhole group",
            group_type="{825424fb-c2c6-4fea-9f2b-6cd00023d393}"
        )
    elif mode == "import":
        drillhole_group = string_parameter(
            label="Drillhole group", value=""

        )
        name_parameter = string_parameter(
            label="Name", value="", optional="enabled"
        )
        drillhole_group["groupOptional"] = True
        drillhole_group["enabled"] = False
        drillhole_group["group"] = "Simple"
        name_parameter["group"] = "Simple"

        update["name_parameter"] = name_parameter
        update["data_files_parameter"] = file_parameter(
            label="Data files",
            file_type=["las"],
            optional="disabled",
        )
    else:
        raise ValueError("Mode argument must be 'import' or 'export'.")

    ui_json.update(
        dict(
            {
                "title": f"{mode.capitalize()} drillhole group",
                "run_command": "las_geoh5.main",
                "conda_environment": "las-geoh5",
                "drillhole_group": drillhole_group,
            },
            **update
        )
    )
    ifile = InputFile(ui_json=ui_json, validate=False)
    ifile.path = basepath
    ifile.write_ui_json(f"{mode}_to_las.ui.json", basepath)

    return ifile


def main(file):
    ifile = InputFile.read_ui_json(file)
    dh_group = ifile.data["drillhole_group"]
    name = ifile.data["name"]
    if ifile.data["title"].split()[0].lower() == "export":
        with fetch_active_workspace(ifile.data["geoh5"]):
            export_las(dh_group, Path(ifile.path), name)
    elif ifile.data["title"].split()[0].lower() == "import":
        with fetch_active_workspace(
                ifile.data["geoh5"], mode='a'
        ) as workspace:
            basepath = Path(ifile.path) / dh_group
            import_las(workspace, basepath, name)

if __name__ == "__main__":  # pragma: no cover
    file = sys.argv[1]
    main(file)


