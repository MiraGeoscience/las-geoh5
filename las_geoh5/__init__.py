#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las_geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

# flake8: noqa

from __future__ import annotations

from pathlib import Path

__version__ = "0.2.0"


def assets_path() -> Path:
    """Return the path to the assets folder."""

    parent = Path(__file__).parent
    folder_name = f"{parent.name}-assets"
    assets_folder = parent.parent / folder_name
    if not assets_folder.is_dir():
        raise RuntimeError(f"Assets folder not found: {assets_folder}")

    return assets_folder
