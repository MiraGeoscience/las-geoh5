#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of my_app project.
#
#  All rights reserved.
#

from __future__ import annotations

import importlib

import lasio
import numpy as np
from geoh5py import Workspace
from geoh5py.groups import DrillholeGroup
from geoh5py.ui_json import InputFile


def generate_lasfile(
    well: str,
    collar: dict[str, float],
    depths: np.ndarray,
    properties: dict[str, np.ndarray | None],
):
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


def write_lasfiles(basepath, lasfiles):
    for lasfile in lasfiles:
        with open(
            basepath / f"{lasfile.well['WELL'].value}.las", "a", encoding="utf8"
        ) as file:
            lasfile.write(file)

    return [f.well["WELL"].value for f in lasfiles]


def write_input_file(  # pylint: disable=too-many-arguments
    workspace,
    drillhole_group,
    property_group_name,
    files,
    depths_name,
    x_collar_name,
    y_collar_name,
    z_collar_name,
    module_name,
):
    filepath = workspace.h5file.parent
    module = importlib.import_module(f"las_geoh5.{module_name}.uijson")
    ui_json = getattr(module, "ui_json")
    ifile = InputFile(ui_json=ui_json, validate=False)
    ifile.update_ui_values(
        {
            "geoh5": workspace,
            "drillhole_group": drillhole_group,
            "name": property_group_name,
            "files": [str(filepath / name) + ".las" for name in files],
            "depths_name": depths_name,
            "collar_x_name": x_collar_name,
            "collar_y_name": y_collar_name,
            "collar_z_name": z_collar_name,
        }
    )
    ifile.write_ui_json("import_las_files.ui.json", filepath)

    return ifile.path_name


def test_import_las_empty_drillhole_group(tmp_path):
    lasfiles = [
        generate_lasfile(
            "dh1",
            {"X": 0.0, "Y": 10.0, "ELEV": 10.0},
            np.arange(0, 10, 0.5),
            {"my_first_property": None},
        ),
        generate_lasfile(
            "dh2",
            {"X": 10.0, "Y": 10.0, "ELEV": 0.0},
            np.arange(0, 10, 0.5),
            {"my_first_property": None},
        ),
    ]
    lasfiles = write_lasfiles(tmp_path, lasfiles)

    with Workspace.create(tmp_path / "test.geoh5") as workspace:
        dh_group = DrillholeGroup.create(workspace, name="dh_group")

    filepath = write_input_file(
        workspace,
        dh_group,
        "my_property_group",
        lasfiles,
        "DEPTH",
        "X",
        "Y",
        "ELEV",
        "import_files",
    )

    module = importlib.import_module("las_geoh5.import_files.driver")
    getattr(module, "run")(filepath)

    assert True
