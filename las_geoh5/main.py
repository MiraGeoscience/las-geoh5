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
from geoh5py import Workspace
from geoh5py.groups.drillhole_group import DrillholeGroup
from geoh5py.objects import Drillhole
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile
from geoh5py.ui_json.constants import default_ui_json
from geoh5py.ui_json.templates import group_parameter, string_parameter
from tqdm import tqdm

from las_geoh5.export_las import drillhole_to_las
from las_geoh5.import_las import las_to_drillhole


def export_las(group: DrillholeGroup, basepath: str | Path, name: str | None = None):
    """
    Export contents of drillhole group to las files organized by directories.

    :param group: Drillhole group container.
    :param basepath: Base path where directories/files will be created.
    :param name: Alternate name of root directory to be created.
    """

    if isinstance(basepath, str):
        basepath = Path(basepath)

    drillholes = [k for k in group.children if isinstance(k, Drillhole)]

    name = name if name is not None else group.name
    subpath = basepath / name
    if not subpath.exists():
        subpath.mkdir()

    print(f"Exporting drillhole surveys and property group data to {str(subpath)}")
    for drillhole in tqdm(drillholes):
        drillhole_to_las(drillhole, subpath)


def import_las(workspace: Workspace, basepath: str | Path, name: str | None = None):
    """
    Import directory/files from previous export.

    :param workspace: Project workspace.
    :param basepath: Root directory for las data.
    :param name: Alternate name for property group to create.

    :return: New drillhole group containing imported items.
    """

    if isinstance(basepath, str):
        basepath = Path(basepath)

    if not basepath.exists():
        raise OSError(f"Path {str(basepath)} does not exist.")

    name = name if name is not None else basepath.name
    dh_group = DrillholeGroup.create(workspace, name=name)

    surveys_path = basepath / "Surveys"
    surveys = list(surveys_path.iterdir()) if surveys_path.exists() else None

    property_group_folders = [
        p for p in basepath.iterdir() if p.is_dir() and p.name != "Surveys"
    ]

    for prop in property_group_folders:
        lasfiles = []
        print("Importing property group data from {prop.name}")
        for file in tqdm([k for k in prop.iterdir() if k.suffix == ".las"]):
            lasfiles.append(lasio.read(file, mnemonic_case="preserve"))

        las_to_drillhole(workspace, lasfiles, dh_group, prop.name, surveys)

    return dh_group


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
        drillhole_group = string_parameter(label="Drillhole group", value="")
        drillhole_group["groupOptional"] = True
        drillhole_group["enabled"] = False
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


def main(file: str):
    """
    Driver for import or export of las data.

    :param file: Path to ui.json file.
    """

    ifile = InputFile.read_ui_json(file)
    dh_group = ifile.data["drillhole_group"]
    name = ifile.data["name"]
    if ifile.data["title"].split()[0].lower() == "export":
        with fetch_active_workspace(ifile.data["geoh5"]):
            export_las(dh_group, Path(ifile.path), name)
    elif ifile.data["title"].split()[0].lower() == "import":
        with fetch_active_workspace(ifile.data["geoh5"], mode="a") as workspace:
            basepath = Path(ifile.path) / dh_group
            import_las(workspace, basepath, name)


if __name__ == "__main__":  # pragma: no cover
    FILE = sys.argv[1]
    main(FILE)
