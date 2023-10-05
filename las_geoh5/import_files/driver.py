#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of my_app project.
#
#  All rights reserved.
#

from __future__ import annotations

import sys

import lasio
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile

from las_geoh5.import_las import LASTranslator, las_to_drillhole


def run(file: str):
    ifile = InputFile.read_ui_json(file)

    # TODO: Once fix implemented in geohh5py can revert back to simply pulling
    # drillhole group from input file rather that using get_entity.
    # dh_group = ifile.data["drillhole_group"]

    name = ifile.data["name"]
    files = ifile.data["files"]
    files = [lasio.read(file, mnemonic_case="preserve") for file in files]
    translator = LASTranslator(
        depth=ifile.data["depths_name"],
        collar_x=ifile.data["collar_x_name"],
        collar_y=ifile.data["collar_y_name"],
        collar_z=ifile.data["collar_z_name"],
    )
    with fetch_active_workspace(ifile.data["geoh5"], mode="a") as workspace:
        dh_group = ifile.workspace.get_entity(ifile.data["drillhole_group"].name)[0]
        las_to_drillhole(workspace, files, dh_group, name, translator=translator)


def import_las_files(workspace, dh_group, property_group_name, files):
    for file in files:
        lasfile = lasio.read(file)
        las_to_drillhole(workspace, lasfile, dh_group, property_group_name)


if __name__ == "__main__":
    run(sys.argv[1])
