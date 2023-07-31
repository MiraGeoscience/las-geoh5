#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of my_app project.
#
#  All rights reserved.
#

from __future__ import annotations

from pathlib import Path
from lasio import LASFile, HeaderItem
from geoh5py.data import ReferencedData
from geoh5py.groups import PropertyGroup
from geoh5py.shared.concatenation import ConcatenatedDrillhole
from geoh5py.objects import Drillhole

def add_well_data(
    file: LASFile,
    drillhole: Drillhole | ConcatenatedDrillhole
):
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
            value=drillhole.coordinate_reference_system["Code"],  # type: ignore
            descr=drillhole.coordinate_reference_system["Name"]  # type: ignore
        )
    )

    # Add collar data
    file.well.append(
        HeaderItem(
            mnemonic="X",
            value=float(drillhole.collar["x"])  # type: ignore
        )
    )
    file.well.append(
        HeaderItem(
            mnemonic="Y",
            value=float(drillhole.collar["y"])  # type: ignore
        )
    )
    file.well.append(
        HeaderItem(
            mnemonic="ELEV",
            value=float(drillhole.collar["z"])  # type: ignore
        )
    )

    return file

def add_curve_data(
    file: LASFile,
    drillhole: Drillhole | ConcatenatedDrillhole,
    group: PropertyGroup
):
    """
    Populate las file with curve data from each property in group.

    :param file: lasio file object.
    :param drillhole: geoh5py.drillhole object containing property
        groups for collocated data.
    :param group: Property group containing collocated float data
        objects of 'drillhole'.
    """

    if group.depth_:  # type: ignore
        file.append_curve(
            "DEPT", group.depth_.values, unit='m'  # type: ignore
        )
    else:
        file.append_curve(
            "DEPT", group.from_.values, unit='m', descr="FROM"  # type: ignore
        )
        file.append_curve(
            "TO", group.to_.values, unit='m', descr="TO"  # type: ignore
        )

    properties = [drillhole.get_data(k)[0] for k in group.properties]
    for data in [k for k in properties if k.name not in ["FROM", "TO", "DEPTH"]]:
        file.append_curve(data.name, data.values)
        if isinstance(data, ReferencedData):
            for k, v in data.value_map.map.items():  # pylint: disable=invalid-name
                file.params.append(
                    HeaderItem(
                        mnemonic=f"{data.name} ({k})",
                        value=v,
                        descr="REFERENCE"
                    )
                )

    return file

def add_survey_data(
    file: LASFile,
    drillhole: Drillhole | ConcatenatedDrillhole
):
    """
    Add drillhole survey data to LASFile object.

    :param file: las file object.
    :param drillhole: drillhole containing survey data.

    :return: Updated las file object.
    """

    # Add survey data
    file.append_curve(
        "DEPT",
        drillhole.surveys[:, 0],  # type: ignore
        unit='m'
    )
    file.append_curve(
        "DIP",
        drillhole.surveys[:, 1],  # type: ignore
        unit="degrees",
        descr="from horizontal"
    )
    file.append_curve(
        "AZIM",
        drillhole.surveys[:, 2],  # type: ignore
        unit="degrees",
        descr="from north (clockwise)"
    )

    return file
def write_curves(
    drillhole: Drillhole | ConcatenatedDrillhole,
    basepath: str | Path,
    directory: bool = True
):
    """
    Write a formatted .las file with data from 'drillhole'.

    :param drillhole: geoh5py drillhole object containing property
        groups for collocated data.
    :param basepath: Path to working directory.
    :param directory: True if data is stored in sub-directories
    """

    if isinstance(basepath, str):
        basepath = Path(basepath)

    if not drillhole.property_groups:
        raise AttributeError(
            "Drillhole doesn't have any associated property groups."
        )

    for group in drillhole.property_groups:
        file = LASFile()
        file = add_well_data(file, drillhole)
        file = add_curve_data(file, drillhole, group)

        if directory:
            subpath = Path(basepath / group.name)
            if not subpath.exists():
                subpath.mkdir()
        else:
            subpath = basepath

        survey_path = Path(subpath / f"{drillhole.name}.las")
        if survey_path.exists():
            survey_path = Path(subpath / f"{drillhole.name}_survey.las")

        with open(
            survey_path, 'a', encoding="utf8"
        ) as io:  # pylint: disable=invalid-name
            file.write(io)

def write_survey(
    drillhole: Drillhole | ConcatenatedDrillhole,
    basepath: str | Path,
    directory: bool = True
):
    """
    Write a formatted .las file with survey data from 'drillhole'.

    :param drillhole: geoh5py drillhole object containing property
        groups for collocated data.
    :param basepath: Path to working directory.
    :param directory: True if data is stored in sub-directories
    """

    if isinstance(basepath, str):
        basepath = Path(basepath)

    file = LASFile()
    file = add_well_data(file, drillhole)
    file = add_survey_data(file, drillhole)

    if directory:
        basepath = Path(basepath / "Surveys")
        if not basepath.exists():
            basepath.mkdir()

    with open(
        Path(basepath / f"{drillhole.name}.las"), 'a', encoding="utf8"
    ) as io:  # pylint: disable=invalid-name
        file.write(io)

def drillhole_to_las(
    drillhole: Drillhole | ConcatenatedDrillhole,
    basepath: str | Path,
    directory: bool = True
):
    """
    Write a formatted .las file with data from 'drillhole'.

    :param drillhole: geoh5py drillhole object containing property
        groups for collocated data.
    :param basepath: Path to working directory.
    :param directory: True if data is stored in sub-directories
    """

    write_survey(drillhole, basepath, directory)
    write_curves(drillhole, basepath, directory)
