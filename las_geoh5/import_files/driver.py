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
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path
from shutil import move

from geoh5py import Workspace
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile
from tqdm import tqdm

from las_geoh5.import_files.params import ImportOptions, NameOptions
from las_geoh5.import_las import las_to_drillhole, lasio_read


_logger = logging.getLogger(__name__)
_logger.name = "Import Files"


@contextmanager
def log_to_file(
    logger: logging.Logger, log_dir: Path, log_level: int = logging.INFO
) -> Iterator[Path]:
    """
    Configure the given logger with file handler at the given path.

    :param logger: The logger object.
    :param log_dir: The directory where to create the log file.
    :param log_level: The log level to set for the file handler.
    """

    log_file = log_dir / (_logger.name.lower().replace(" ", "_") + ".log")

    original_level = logger.level
    logger.setLevel(
        log_level if original_level == 0 else min(original_level, log_level)
    )
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)
    try:
        yield log_file
    finally:
        file_handler.close()
        logger.removeHandler(file_handler)
        logger.setLevel(original_level)


@contextmanager
def log_execution_time(message: str, log_level: int = logging.INFO) -> Iterator[None]:
    start = datetime.now()

    # no exception handling: only display message if no exception happened
    yield

    elapsed = (datetime.now() - start).total_seconds()
    minutes = int(elapsed / 60)
    seconds = elapsed - 60 * minutes

    message = message.strip()
    if message and message[-1] != ".":
        message += "."

    prefix_msg = f"{message} Time elapsed:"
    if minutes >= 1:
        out = f"{prefix_msg} {minutes}m {seconds:.0f}s."
    else:
        out = f"{prefix_msg} {seconds:.2f}s."

    _logger.log(log_level, out)


def run(params_json: Path, output_geoh5: Path | None = None):
    """
    Import LAS files into a geoh5 file.

    :param params_json: The JSON file with import parameters, with references to the input
        LAS files, and an input GEOH5 file (``geoh5`` in parameters) that contains the
        destination drill hole group.
        For output, will either write the created GEOH5 with a timestamped name to
        ``monitoring_directory``, if defined, or overwrite the input GEOH5 file.
    :param output_geoh5: if specified, use this path to write out the resulting GEOH5 file,
        instead of the GEOH5 output location defined by the parameter file.
    """

    with log_to_file(_logger, params_json.parent) as log_file:
        with log_execution_time("All done"):
            ifile = InputFile.read_ui_json(params_json)

            _logger.info(
                "Importing LAS file data to workspace '%s.geoh5'.",
                ifile.data["geoh5"].h5file.stem,
            )

            workspace = Workspace()
            with log_execution_time("Finished reading LAS files"):
                with Pool() as pool:
                    futures = []
                    for file in tqdm(
                        ifile.data["files"].split(";"), desc="Reading LAS files"
                    ):
                        futures.append(pool.apply_async(lasio_read, (file,)))

                    lasfiles = [future.get() for future in futures]

            with fetch_active_workspace(ifile.data["geoh5"]) as geoh5:
                dh_group = geoh5.get_entity(ifile.data["drillhole_group"].uid)[0]
                dh_group = dh_group.copy(parent=workspace)

            _logger.info(
                "Saving drillhole data into drillhole group '%s' under property group '%s'",
                dh_group.name,
                ifile.data["name"],
            )

            with log_execution_time("Finished saving drillhole data"):
                name_options = NameOptions(**ifile.data)
                las_to_drillhole(
                    lasfiles,
                    dh_group,
                    ifile.data["name"],
                    options=ImportOptions(names=name_options, **ifile.data),
                )

    if log_file.exists() and log_file.stat().st_size > 0:
        dh_group.add_file(log_file)
    log_file.unlink(missing_ok=True)

    if output_geoh5 is not None:
        output_geoh5.unlink(missing_ok=True)
        workspace.save_as(output_geoh5)
    elif ifile.data["monitoring_directory"]:
        working_path = Path(ifile.data["monitoring_directory"]) / ".working"
        working_path.mkdir(exist_ok=True)
        temp_geoh5 = f"temp{datetime.now().timestamp():.3f}.geoh5"
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
    FILE = sys.argv[1]
    run(Path(FILE))
