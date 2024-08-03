#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

import argparse
import logging
from pathlib import Path

from las_geoh5.export_files import driver


# pylint: disable=duplicate-code


def main():
    logging.basicConfig(level=logging.WARNING)

    parser = argparse.ArgumentParser(
        prog="geoh5_to_las",
        description="Converts a GEOH5 File to new LAS file(s).",
    )
    parser.add_argument(
        "param_file",
        type=Path,
        help=(
            "Path the parameter JSON file, which references the input GEOH5 file, "
            "and output directory."
        ),
    )
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        required=False,
        default=None,
        help=(
            "Path to the directory where to write the output LAS files. "
            "If not specified, reads it from the ``rootpath`` key in the JSON parameter file."
        ),
    )
    args = parser.parse_args()
    output_dir = args.out
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    driver.run(args.param_file, output_dir)


if __name__ == "__main__":
    main()  # pragma: no cover
