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

from geoh5py.groups import DrillholeGroup
from geoh5py.objects import Drillhole
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile
from tqdm import tqdm

from las_geoh5.export_las import drillhole_to_las


def run(file: str | Path):
    ifile = InputFile.read_ui_json(file)
    dh_group = ifile.data["drillhole_group"]
    name = ifile.data["name"]
    with fetch_active_workspace(ifile.data["geoh5"]):
        export_las_directory(dh_group, Path(ifile.path), name)


def export_las_directory(
    group: DrillholeGroup, basepath: str | Path, name: str | None = None
):
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


if __name__ == "__main__":
    run(sys.argv[1])
