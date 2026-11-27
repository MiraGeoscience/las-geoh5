# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024-2026 Mira Geoscience Ltd.                                '
#                                                                              '
#  This file is part of las-geoh5 package.                                     '
#                                                                              '
#  las-geoh5 is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                 '
#                                                                              '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from pathlib import Path

import lasio
import numpy as np
from geoh5py import Workspace
from geoh5py.groups import DrillholeGroup
from geoh5py.ui_json import UIJson

from las_geoh5 import assets_path


def generate_lasfile(
    well: str,
    collar: dict[str, float],
    depths: np.ndarray,
    properties: dict[str, np.ndarray | None],
) -> lasio.LASFile:
    file = lasio.LASFile()
    file.well["WELL"] = well
    for name, value in collar.items():
        file.well.append(lasio.HeaderItem(mnemonic=name, value=value))
    file.append_curve("DEPTH", depths)
    for prop, values in properties.items():
        file.append_curve(
            prop, np.random.rand(len(depths)) if values is None else values
        )

    return file


def write_lasfile(basepath: Path, lasfile: lasio.LASFile) -> Path:
    filepath = basepath / f"{lasfile.well['WELL'].value}.LAS"
    if filepath.exists():
        filepath = basepath / f"{lasfile.well['WELL'].value}_1.LAS"
    with open(filepath, "a", encoding="utf8") as file:
        lasfile.write(file)

    return filepath


def write_import_params_file(
    json_output_path: Path,
    drillhole_group: DrillholeGroup | None,
    property_group_name: str,
    files: list[Path],
    collar_xyz_names: tuple[str, str, str],
    *,
    skip_empty_header=False,
) -> Path:
    if drillhole_group is None:
        workspace = Workspace.create(json_output_path.parent / "import.geoh5")
    else:
        workspace = drillhole_group.workspace

    import_json = assets_path() / "uijson" / "import_las_files.ui.json"

    ifile = UIJson.read(import_json)

    ifile.set_values(
        copy=False,
        **{
            "geoh5": workspace.h5file,
            "drillhole_group": drillhole_group,
            "name": property_group_name,
            "files": ";".join([str(f) for f in files]),
            "collar_x_name": collar_xyz_names[0],
            "collar_y_name": collar_xyz_names[1],
            "collar_z_name": collar_xyz_names[2],
            "skip_empty_header": skip_empty_header,
        },
    )
    ifile.write(json_output_path)

    return json_output_path


def write_export_params_file(
    json_output_path: Path,
    workspace: Workspace,
    drillhole_group: DrillholeGroup,
    export_dir: Path,
    use_directories: bool,
) -> Path:
    import_json = assets_path() / "uijson" / "export_las_files.ui.json"
    ifile = UIJson.read(import_json)

    ifile.set_values(
        copy=False,
        **{
            "geoh5": workspace.h5file,
            "drillhole_group": drillhole_group.uid,
            "rootpath": str(export_dir),
            "use_directories": use_directories,
        },
    )
    ifile.write(json_output_path)

    return json_output_path
