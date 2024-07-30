#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  All rights reserved.
#
#
#  This file is part of las-geoh5 project.
#
#  All rights reserved.
#

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

from geoh5py.ui_json import InputFile


def write_uijson(basepath: str | Path, mode: str = "import_files"):
    """
    Write a ui.json file for either import or export or LAS Files.

    :param basepath: Root directory for LAS Data.
    :param mode: Switch for 'import' or 'export' behaviour.

    :return: Input file for the written data.
    """

    if mode not in ["import_files", "import_directories", "export_files"]:
        msg = "Mode argument must be 'import_files', 'import_directories', or 'export_files'."
        raise ValueError(msg)

    module = importlib.import_module(f"las_geoh5.{mode}.uijson")
    ui_json = module.ui_json
    filename = "_".join([mode.split("_")[0], "las", mode.split("_")[1]])

    ifile = InputFile(ui_json=ui_json, validate=False)
    ifile.path = str(basepath)
    ifile.write_ui_json(filename, basepath)

    return ifile


def main(args):
    parser = argparse.ArgumentParser(description="Write ui.json files.")
    parser.add_argument(
        "path", type=Path, help="Path to folder where ui.json files will be written."
    )
    parser.add_argument(
        "mode",
        type=str,
        choices={"import_files", "import_directories", "export_files", "all"},
        help=(
            "Mode switching between 'import_files', 'import_directories',"
            " 'export_files', and 'all' behaviour."
        ),
    )
    args = parser.parse_args(args)
    if args.mode == "all":
        for mode in [
            "import_files",
            "import_directories",
            "export_files",
        ]:  # pylint: disable=invalid-name
            write_uijson(args.path, mode)
    else:
        write_uijson(args.path, args.mode)


if __name__ == "__main__":
    main(sys.argv[1:])
