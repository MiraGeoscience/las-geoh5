#  Copyright (c) 2024 Mira Geoscience Ltd.
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
from geoh5py.groups import DrillholeGroup
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile

from las_geoh5.import_files.params import ImportOptions
from las_geoh5.import_las import las_to_drillhole


def run(file: str):
    ifile = InputFile.read_ui_json(file)
    dh_group = ifile.data["drillhole_group"]
    parent_folder = ifile.data["parent_folder"]
    if not parent_folder:
        raise ValueError("No folder specified to read LAS files from.")
    with fetch_active_workspace(ifile.data["geoh5"], mode="a"):
        import_las_directory(dh_group, parent_folder)


def import_las_directory(dh_group: DrillholeGroup, basepath: str | Path):
    """
    Import directory/files from previous export.

    :param workspace: Project workspace.
    :param basepath: Root directory for LAS data.

    :return: New drillhole group containing imported items.
    """

    if isinstance(basepath, str):
        basepath = Path(basepath)

    if not basepath.exists():
        raise OSError(f"Directory does not exist: {basepath}")
    if not basepath.is_dir():
        raise OSError(f"Path is not a directory: {basepath}")

    surveys_path = basepath / "Surveys"
    surveys = list(surveys_path.iterdir()) if surveys_path.exists() else None

    property_group_folders = [
        p for p in basepath.iterdir() if p.is_dir() and p.name != "Surveys"
    ]

    for prop in property_group_folders:
        lasfiles = []
        for file in [k for k in prop.iterdir() if k.suffix == ".las"]:
            lasfiles.append(
                lasio.read(file, mnemonic_case="preserve", encoding="utf-8")
            )
        print(f"Importing property group data from to '{prop.name}'")
        las_to_drillhole(
            lasfiles,
            dh_group,
            prop.name,
            surveys=surveys,
            options=ImportOptions(),
        )

    return dh_group


if __name__ == "__main__":
    run(sys.argv[1])
