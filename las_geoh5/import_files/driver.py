#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

from __future__ import annotations

import logging
import sys
from multiprocessing import Pool
from pathlib import Path
from shutil import move
from time import time

import lasio
from geoh5py import Workspace
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile
from tqdm import tqdm

from las_geoh5.import_las import LASTranslator, las_to_drillhole

logger = logging.getLogger("Import Files")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s : %(name)s : %(levelname)s : %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


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

    logger.info(
        "Importing las file data to workspace %s.geoh5.",
        ifile.data["geoh5"].h5file.stem,
    )

    translator = LASTranslator(
        depth=ifile.data["depths_name"],
        collar_x=ifile.data["collar_x_name"],
        collar_y=ifile.data["collar_y_name"],
        collar_z=ifile.data["collar_z_name"],
    )

    workspace = Workspace()
    begin_reading = time()

    with Pool() as pool:
        futures = []
        for file in tqdm(ifile.data["files"].split(";"), desc="Reading las files"):
            futures.append(
                pool.apply_async(lasio.read, (file,), {"mnemonic_case": "preserve"})
            )

        lasfiles = [future.get() for future in futures]

    end_reading = time()
    logger.info(
        elapsed_time_logger(begin_reading, end_reading, "Finished reading las files")
    )

    with fetch_active_workspace(ifile.data["geoh5"]) as geoh5:
        dh_group = geoh5.get_entity(ifile.data["drillhole_group"].uid)[0]
        dh_group = dh_group.copy(parent=workspace)

    logger.info(
        "Saving drillhole data into drillhole group %s under property group %s",
        dh_group.name,
        ifile.data["name"],
    )
    begin_saving = time()
    las_to_drillhole(
        workspace,
        lasfiles,
        dh_group,
        ifile.data["name"],
        translator=translator,
        skip_empty_header=ifile.data["skip_empty_header"],
    )
    end_saving = time()
    logger.info(
        elapsed_time_logger(begin_saving, end_saving, "Finished saving drillhole data")
    )
    end = time()
    logger.info(elapsed_time_logger(start, end, "All done."))

    if ifile.data["monitoring_directory"]:
        working_path = Path(ifile.data["monitoring_directory"]) / ".working"
        working_path.mkdir(exist_ok=True)
        temp_geoh5 = f"temp{time():.3f}.geoh5"
        workspace.save_as(working_path / temp_geoh5)
        workspace.close()
        move(
            working_path / temp_geoh5,
            Path(ifile.data["monitoring_directory"]) / temp_geoh5,
        )

    else:
        geoh5_path = geoh5.h5file
        geoh5.h5file.unlink()
        workspace.save_as(geoh5_path)

    workspace.close()


if __name__ == "__main__":
    run(sys.argv[1])
