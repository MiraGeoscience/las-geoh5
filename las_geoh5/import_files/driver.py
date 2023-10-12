#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of my_app project.
#
#  All rights reserved.
#

from __future__ import annotations

import sys
from time import time

import lasio
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile

from las_geoh5.import_las import LASTranslator, las_to_drillhole


def elapsed_time_logger(start, end, message):
    if message[-1] != ".":
        message += "."

    elapsed = end - start
    minutes = elapsed // 60
    seconds = elapsed % 60

    if minutes >= 1:
        out = f"{message} Time elapsed: {minutes}m {seconds}s."
    else:
        out = f"{message} Time elapsed: {seconds:.2f}s."

    return out


def run(file: str):
    start = time()
    ifile = InputFile.read_ui_json(file)

    # TODO: Once fix implemented in geoh5py can revert back to simply pulling
    # drillhole group from input file rather that using get_entity.
    # dh_group = ifile.data["drillhole_group"]

    geoh5 = ifile.data["geoh5"]
    print(f"Importing las file data to workspace {geoh5.h5file.stem} . . .")
    drillhole_group = ifile.data["drillhole_group"]
    name = ifile.data["name"]
    files = ifile.data["files"].split(";")
    begin_loading = time()
    print("Loading las files . . .")
    files = [lasio.read(file, mnemonic_case="preserve") for file in files]
    end_loading = time()
    print(elapsed_time_logger(begin_loading, end_loading, "Finished loading las files"))
    translator = LASTranslator(
        depth=ifile.data["depths_name"],
        collar_x=ifile.data["collar_x_name"],
        collar_y=ifile.data["collar_y_name"],
        collar_z=ifile.data["collar_z_name"],
    )
    skip_empty_header = ifile.data["skip_empty_header"]
    with fetch_active_workspace(ifile.data["geoh5"], mode="a") as workspace:
        dh_group = ifile.workspace.get_entity(drillhole_group.uid)[0]
        begin_saving = time()
        print(
            f"Saving drillhole data into drillhole group {drillhole_group.name} "
            f"under property group {name}. . ."
        )
        las_to_drillhole(
            workspace,
            files,
            dh_group,
            name,
            translator=translator,
            skip_empty_header=skip_empty_header,
        )
        end_saving = time()

        print(
            elapsed_time_logger(
                begin_saving, end_saving, "Finished saving drillhole data"
            )
        )

    end = time()
    print(elapsed_time_logger(start, end, "All done."))


def import_las_files(workspace, dh_group, property_group_name, files):
    for file in files:
        lasfile = lasio.read(file)
        las_to_drillhole(workspace, lasfile, dh_group, property_group_name)


if __name__ == "__main__":
    run(sys.argv[1])
