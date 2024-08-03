#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

import argparse
import logging
import sys
from pathlib import Path

from las_geoh5.import_files import driver


_logger = logging.getLogger(__package__ + "." + Path(__file__).stem)


def main():
    logging.basicConfig(level=logging.WARNING)

    parser = argparse.ArgumentParser(
        prog="las_to_geoh5",
        description="Converts LAS files to a new GEOH5 file.",
    )
    parser.add_argument(
        "param_file",
        type=Path,
        help="Path the parameter JSON file, which references the input LAS files.",
    )
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        required=False,
        default=None,
        help=(
            """Path to the output GEOH5 file. If not specified, reads it from
            the JSON parameter file:
            - if ``monitoring_directory`` is defined, the output file will be saved
            in the monitoring directory, with a timestamped name;
            - otherwise, will use the ``geoh5`` location (and replace the existing file)."""
        ),
    )

    args = parser.parse_args()
    output_filepath = args.out
    if output_filepath:
        if not output_filepath.suffix:
            output_filepath = output_filepath.with_suffix(".geoh5")
        if output_filepath.exists():
            _logger.error(
                "Cowardly refuses to overwrite existing file '%s'.", output_filepath
            )
            sys.exit(1)
    driver.run(args.param_file, output_filepath)


if __name__ == "__main__":
    main()  # pragma: no cover
