#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

from __future__ import annotations

import sys
from pathlib import Path

import lasio
from geoh5py import Workspace
from geoh5py.groups import DrillholeGroup
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile

from las_geoh5.import_las import las_to_drillhole


def run(file: str):
    ifile = InputFile.read_ui_json(file)
    dh_group = ifile.data["drillhole_group"]
    name = ifile.data["name"]
    with fetch_active_workspace(ifile.data["geoh5"], mode="a") as workspace:
        basepath = Path(ifile.path) / dh_group
        import_las_directory(workspace, basepath, name)


def import_las_directory(
    workspace: Workspace, basepath: str | Path, name: str | None = None
):
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
        for file in [k for k in prop.iterdir() if k.suffix == ".las"]:
            lasfiles.append(lasio.read(file, mnemonic_case="preserve"))
        print(f"Importing property group data from to {prop.name}")
        las_to_drillhole(workspace, lasfiles, dh_group, prop.name, surveys)

    return dh_group


if __name__ == "__main__":
    run(sys.argv[1])
