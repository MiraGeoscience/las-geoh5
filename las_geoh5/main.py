#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of las_geoh5 project.
#
#  All rights reserved.

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
import numpy as np
from lasio import LASFile, HeaderItem
from geoh5py.shared.concatenation import ConcatenatedDrillhole
from geoh5py.data import ReferencedData
from geoh5py.groups import PropertyGroup
from geoh5py.ui_json import InputFile
from geoh5py.ui_json.constants import default_ui_json
from geoh5py.ui_json.templates import group_parameter


def add_well_data(file: LASFile, drillhole: ConcatenatedDrillhole):
    """
    Populate las file well data from drillhole.

    :param file: lasio file object.
    :param drillhole: geoh5py drillhole object.

    :returns: Updated lasio file object.
    """

    # Add well name
    file.well["WELL"] = drillhole.name

    # Add epsg code
    file.well.append(
        HeaderItem(
            mnemonic="GDAT",
            value=drillhole.coordinate_reference_system["Code"],
            descr=drillhole.coordinate_reference_system["Name"]
        )
    )

    # Add collar data
    file.well.append(
        HeaderItem(
            mnemonic="X",
            value=float(drillhole.collar["x"])
        )
    )
    file.well.append(
        HeaderItem(
            mnemonic="Y",
            value=float(drillhole.collar["y"])
        )
    )
    file.well.append(
        HeaderItem(
            mnemonic="ELEV",
            value=float(drillhole.collar["z"])
        )
    )

    return file

def add_curve_data(
    file: LASFile,
    drillhole: ConcatenatedDrillhole,
    group: PropertyGroup
):
    """
    Populate las file with curve data from each property in group.

    :param file: lasio file object.
    :param drillhole: geoh5py drillhole object containing property
        groups for collocated data.
    :param group: Property group containing collocated float data
        objects of 'drillhole'.
    """

    if group.depth_:
        file.append_curve("DEPT", group.depth_.values, unit='m')
    else:
        file.append_curve("DEPTH", group.from_.values, unit='m', descr="FROM")
        file.append_curve("TO", group.to_.values, unit='m', descr="TO")

    properties = [drillhole.get_data(k)[0] for k in group.properties]
    for data in [k for k in properties if k.name not in ["FROM", "TO", "DEPTH"]]:
        file.append_curve(data.name, data.values)
        if isinstance(data, ReferencedData):
            for k, v in data.value_map.map.items():
                file.params.append(
                    HeaderItem(
                        mnemonic=f"{data.name} ({k})",
                        value=v,
                        descr="Reference"
                    )
                )
            # file.append_curve(
            #     f"{data.name} (REF)",
            #     np.array([data.value_map[k] for k in data.values]),
            #     descr="REFERENCE"
            # )

    return file

def add_survey_data(file, drillhole):

    # Add survey data
    file.append_curve("DEPT", drillhole.surveys[:, 0], unit='m')
    file.append_curve("DIP", drillhole.surveys[:, 1], unit="degrees", descr="from horizontal")
    file.append_curve("AZIM", drillhole.surveys[:, 2], unit="degrees", descr="from north (clockwise)")

    return file
def write_curves(drillhole, basepath):

    for group in drillhole.property_groups:
        file = LASFile()
        file = add_well_data(file, drillhole)
        file = add_curve_data(file, drillhole, group)

        subpath = Path(basepath / group.name)
        if not subpath.exists():
            subpath.mkdir()

        with open(Path(subpath / f"{drillhole.name}.las"), 'a', encoding="utf8") as io:
            file.write(io)

def write_survey(drillhole, basepath):

    file = LASFile()
    file = add_well_data(file, drillhole)
    file = add_survey_data(file, drillhole)

    subpath = Path(basepath / "Surveys")
    if not subpath.exists():
        subpath.mkdir()

    with open(Path(subpath / f"{drillhole.name}.las"), 'a', encoding="utf8") as io:
        file.write(io)

def drillhole_to_las(drillhole, basepath):

    write_survey(drillhole, basepath)
    write_curves(drillhole, basepath)

def drillhole_group_to_las(group, basepath):

    drillholes = [
        k for k in group.children if isinstance(k, ConcatenatedDrillhole)
    ]

    for drillhole in drillholes:
        drillhole_to_las(drillhole, basepath)


def write_uijson(basepath):
    ui_json = deepcopy(default_ui_json)
    ui_json.update(
        {
            "title": "Export drillhole group",
            "run_command": "las_geoh5.main",
            "conda_environment": "las-geoh5",
            "drillhole_group": group_parameter(
                    label="drillhole group",
                    group_type="{825424fb-c2c6-4fea-9f2b-6cd00023d393}",
                ),
        }
    )
    ifile = InputFile(ui_json=ui_json)
    ifile.validate=False
    ifile.write_ui_json("drillholes_to_las.ui.json", basepath)

    return ifile




if __name__ == "__main__":  # pragma: no cover
    file = sys.argv[1]
    ifile = InputFile.read_ui_json(file)
    if ifile.data["title"].split()[0].lower() == "export":
        drillhole_group_to_las()

