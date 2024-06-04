#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from pathlib import Path

import lasio
import numpy as np
from geoh5py import Workspace
from geoh5py.groups import DrillholeGroup
from geoh5py.ui_json import InputFile

from las_geoh5.export_files import uijson as export_uijson
from las_geoh5.import_files import uijson as import_uijson


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
    filepath = basepath / f"{lasfile.well['WELL'].value}.las"
    if filepath.exists():
        filepath = basepath / f"{lasfile.well['WELL'].value}_1.las"
    with open(filepath, "a", encoding="utf8") as file:
        lasfile.write(file)

    return filepath


def write_import_params_file(
    json_output_path: Path,
    drillhole_group: DrillholeGroup,
    property_group_name: str,
    files: list[Path],
    collar_xyz_names: tuple[str, str, str],
    skip_empty_header=False,
) -> Path:
    workspace = drillhole_group.workspace
    ifile = InputFile(ui_json=import_uijson.ui_json, validate=False)
    with workspace.open():
        ifile.update_ui_values(
            {
                "geoh5": workspace,
                "drillhole_group": drillhole_group,
                "name": property_group_name,
                "files": ";".join([str(f) for f in files]),
                "collar_x_name": collar_xyz_names[0],
                "collar_y_name": collar_xyz_names[1],
                "collar_z_name": collar_xyz_names[2],
                "skip_empty_header": skip_empty_header,
            }
        )
        ifile.write_ui_json(json_output_path.name, json_output_path.parent)

    if ifile.path_name is None:
        raise ValueError("Input file path is None.")

    return Path(ifile.path_name)


def write_export_params_file(
    json_output_path: Path,
    workspace: Workspace,
    drillhole_group: DrillholeGroup,
    export_dir: Path,
    use_directories: bool,
) -> Path:
    ifile = InputFile(ui_json=export_uijson.ui_json, validate=False)
    with workspace.open():
        ifile.update_ui_values(
            {
                "geoh5": workspace,
                "drillhole_group": drillhole_group,
                "rootpath": str(export_dir),
                "use_directories": use_directories,
            }
        )
    ifile.write_ui_json(json_output_path.name, json_output_path.parent)

    if ifile.path_name is None:
        raise ValueError("Input file path is None.")

    return Path(ifile.path_name)
