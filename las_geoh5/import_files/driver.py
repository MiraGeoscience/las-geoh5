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


def run(filepath: str):  # pylint: disable=too-many-locals
    start = time()
    ifile = InputFile.read_ui_json(filepath)
    print(
        f"Importing las file data to workspace {ifile.data['geoh5'].h5file.stem} . . ."
    )

    translator = LASTranslator(
        depth=ifile.data["depths_name"],
        collar_x=ifile.data["collar_x_name"],
        collar_y=ifile.data["collar_y_name"],
        collar_z=ifile.data["collar_z_name"],
    )

    print("Reading las files . . .")
    begin_reading = time()
    with Pool() as pool:
        futures = []
        for file in tqdm(ifile.data["files"].split(";")):
            futures.append(
                pool.apply_async(lasio.read, (file,), {"mnemonic_case": "preserve"})
            )

        lasfiles = [future.get() for future in futures]
    end_reading = time()
    print(elapsed_time_logger(begin_reading, end_reading, "Finished reading las files"))

    with fetch_active_workspace(ifile.data["geoh5"], mode="a") as geoh5:
        dh_group = geoh5.get_entity(ifile.data["drillhole_group"].uid)[0]
        print(
            f"Saving drillhole data into drillhole group {dh_group.name} "
            f"under property group {ifile.data['name']}. . ."
        )
        begin_saving = time()
        las_to_drillhole(
            geoh5,
            lasfiles,
            dh_group,
            ifile.data["name"],
            translator=translator,
            skip_empty_header=ifile.data["skip_empty_header"],
        )
        end_saving = time()
        print(
            elapsed_time_logger(
                begin_saving, end_saving, "Finished saving drillhole data"
            )
        )

    end = time()
    print(elapsed_time_logger(start, end, "All done."))


if __name__ == "__main__":
    run(sys.argv[1])
