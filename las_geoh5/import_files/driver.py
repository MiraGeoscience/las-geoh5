#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of my_app project.
#
#  All rights reserved.
#

from __future__ import annotations

import sys
from multiprocessing import Pool
from time import time

import lasio
from geoh5py import Workspace
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile
from tqdm import tqdm

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
    print(
        f"Importing las file data to workspace {ifile.data['geoh5'].h5file.stem} . . ."
    )

    workspace = Workspace()

    # dh_group = ifile.data["drillhole_group"]
    name = ifile.data["name"]
    files = ifile.data["files"].split(";")
    translator = LASTranslator(
        depth=ifile.data["depths_name"],
        collar_x=ifile.data["collar_x_name"],
        collar_y=ifile.data["collar_y_name"],
        collar_z=ifile.data["collar_z_name"],
    )
    skip_empty_header = ifile.data["skip_empty_header"]

    print("Reading las files . . .")
    begin_reading = time()
    with Pool() as pool:
        futures = []
        for file in tqdm(files):
            futures.append(
                pool.apply_async(lasio.read, (file,), {"mnemonic_case": "preserve"})
            )

        lasfiles = [future.get() for future in futures]
    end_reading = time()
    print(elapsed_time_logger(begin_reading, end_reading, "Finished reading las files"))

    with fetch_active_workspace(ifile.data["geoh5"], mode="a") as geoh5:
        dh_group = geoh5.get_entity(ifile.data["drillhole_group"].uid)[0]
        dh_group = dh_group.copy(parent=workspace, copy_children=True)
        print(
            f"Saving drillhole data into drillhole group {dh_group.name} "
            f"under property group {name}. . ."
        )
        begin_saving = time()
        las_to_drillhole(
            workspace,
            lasfiles,
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

    geoh5_path = geoh5.h5file
    geoh5_path.unlink()
    workspace.save_as(geoh5_path)


if __name__ == "__main__":
    run(sys.argv[1])
