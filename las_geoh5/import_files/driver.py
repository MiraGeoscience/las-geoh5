#  Copyright (c) 2024 Mira Geoscience Ltd.
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

from las_geoh5.import_files.params import ImportOptions, NameOptions
from las_geoh5.import_las import las_to_drillhole


def get_logger(
    name: str, level: int = logging.INFO, path: str | Path | None = None
) -> logging.Logger:
    """
    Create a looger with stream and optional file handlers.

    :param name: Logger name.
    :param level: logging level.
    :param path: Creates a file handler at the specified path if not None.
    :return: Logger object.
    """
    if isinstance(path, str):
        path = Path(path)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s : %(name)s : %(levelname)s : %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)
    logger.addHandler(stream_handler)

    if path is not None:
        filename = f"{'_'.join([k.lower() for k in name.split(' ')])}.log"
        file_handler = logging.FileHandler(path / filename)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    return logger


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


def run(filepath: Path):  # pylint: disable=too-many-locals
    start = time()
    ifile = InputFile.read_ui_json(filepath)

    logger = get_logger("Import Files", path=filepath.parent)
    logger.info(
        "Importing las file data to workspace %s.geoh5.",
        ifile.data["geoh5"].h5file.stem,
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

    name_options = NameOptions(**ifile.data)
    import_options = ImportOptions(names=name_options, **ifile.data)
    las_to_drillhole(
        lasfiles,
        dh_group,
        ifile.data["name"],
        options=import_options,
    )
    end_saving = time()
    logger.info(
        elapsed_time_logger(begin_saving, end_saving, "Finished saving drillhole data")
    )
    end = time()
    logger.info(elapsed_time_logger(start, end, "All done."))
    logpath = Path(logger.handlers[1].baseFilename)  # type: ignore
    dh_group.add_file(logpath)
    logger.handlers[1].close()
    logpath.unlink()

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
    run(Path(sys.argv[1]))
