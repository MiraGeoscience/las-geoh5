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

from geoh5py.groups import DrillholeGroup
from geoh5py.objects import Drillhole
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile
from tqdm import tqdm

from las_geoh5.export_las import drillhole_to_las


def run(params_json: str | Path, output_dir: str | Path | None = None):
    """
    Export drillhole data from GEOH5 to LAS.

    :param params_json: The JSON file with export parameters, with references to the input
        GEOH5 file, and an output directory for LAS.
    :param output_dir: if specified, use this path as the directory to write out the resulting
        LAS files, instead of the ``rootpath`` location defined by the parameter file.
    """
    ifile = InputFile.read_ui_json(params_json)
    dh_group = ifile.data["drillhole_group"]
    if output_dir is not None:
        rootpath = output_dir
    else:
        rootpath = Path(ifile.data["rootpath"])
    use_directories = ifile.data["use_directories"]
    with fetch_active_workspace(ifile.data["geoh5"]):
        export_las_files(dh_group, rootpath, use_directories)


def export_las_files(
    group: DrillholeGroup, basepath: str | Path, use_directories: bool = True
):
    """
    Export contents of drillhole group to LAS files organized by directories.

    :param group: Drillhole group container.
    :param basepath: Base path where directories/files will be created.
    :param use_directories: Use directories to organize LAS files by property group.
    """

    if isinstance(basepath, str):
        basepath = Path(basepath)

    drillholes = [k for k in group.children if isinstance(k, Drillhole)]

    print(f"Exporting drillhole surveys and property group data to '{basepath}'")
    for drillhole in tqdm(drillholes):
        drillhole_to_las(drillhole, basepath, use_directories=use_directories)


if __name__ == "__main__":
    run(sys.argv[1])
