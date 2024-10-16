#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

from __future__ import annotations

from pathlib import Path

from geoh5py.data import ReferencedData
from geoh5py.objects import Drillhole
from geoh5py.shared.concatenation import ConcatenatedPropertyGroup
from lasio import HeaderItem, LASFile


def add_well_data(
    file: LASFile,
    drillhole: Drillhole,
) -> LASFile:
    """
    Populate LAS file well data from drillhole.

    :param file: lasio file object.
    :param drillhole: geoh5py drillhole object.

    :returns: Updated lasio file object.
    """

    # Add well name
    file.well["WELL"] = drillhole.name

    # Add epsg code
    if drillhole.coordinate_reference_system is not None:
        file.well.append(
            HeaderItem(
                mnemonic="GDAT",
                value=drillhole.coordinate_reference_system["Code"],
                descr=drillhole.coordinate_reference_system["Name"],
            )
        )

    # Add collar data
    file.well.append(HeaderItem(mnemonic="X", value=float(drillhole.collar["x"])))
    file.well.append(HeaderItem(mnemonic="Y", value=float(drillhole.collar["y"])))
    file.well.append(HeaderItem(mnemonic="ELEV", value=float(drillhole.collar["z"])))

    return file


def add_curve_data(file: LASFile, drillhole: Drillhole, group):
    """
    Populate LAS file with curve data from each property in group.

    :param file: lasio file object.
    :param drillhole: geoh5py.drillhole object containing property
        groups for collocated data.
    :param group: Property group containing collocated float data
        objects of 'drillhole'.
    """

    if not isinstance(group, ConcatenatedPropertyGroup):
        raise TypeError("Property group must be of type ConcatenatedPropertyGroup.")

    if group.depth_:
        file.append_curve("DEPTH", group.depth_.values, unit="m")
    else:
        file.append_curve("DEPTH", group.from_.values, unit="m", descr="FROM")
        file.append_curve("TO", group.to_.values, unit="m", descr="TO")

    properties = [] if group.properties is None else group.properties
    data = [drillhole.get_data(k)[0] for k in properties]
    filtered_data = [k for k in data if len(k.values) != 0]
    for datum in filtered_data:
        if any(k in datum.name for k in ["FROM", "TO", "DEPT"]):
            continue

        file.append_curve(datum.name, datum.values)

        if isinstance(datum, ReferencedData) and datum.value_map is not None:
            for k, v in datum.value_map().items():  # pylint: disable=invalid-name
                file.params.append(
                    HeaderItem(
                        mnemonic=f"{datum.name} ({k})", value=v, descr="REFERENCE"
                    )
                )

    return file


def add_survey_data(file: LASFile, drillhole: Drillhole) -> LASFile:
    """
    Add drillhole survey data to LASFile object.

    :param file: LAS file object.
    :param drillhole: drillhole containing survey data.

    :return: Updated LAS file object.
    """

    # Add survey data
    file.append_curve("DEPTH", drillhole.surveys[:, 0], unit="m")
    file.append_curve(
        "DIP",
        drillhole.surveys[:, 1],
        unit="degrees",
        descr="from horizontal",
    )
    file.append_curve(
        "AZIM",
        drillhole.surveys[:, 2],
        unit="degrees",
        descr="from north (clockwise)",
    )

    return file


def write_curves(
    drillhole: Drillhole,
    basepath: str | Path,
    use_directories: bool = True,
):
    """
    Write a formatted .las file for each property group in 'drillhole'.

    :param drillhole: geoh5py drillhole object containing property
        groups for collocated data.
    :param basepath: Path to working directory.
    :param use_directories: True if data is stored in sub-directories
    """

    if isinstance(basepath, str):
        basepath = Path(basepath)

    if not drillhole.property_groups:
        raise AttributeError("Drillhole doesn't have any associated property groups.")

    for group in drillhole.property_groups:
        if group.property_group_type not in ["Interval table", "Depth table"]:
            continue  # bypasses strike and dip groups

        if group.name == "Static-Survey":
            continue  # bypasses survey data handled elsewhere

        file = LASFile()
        file = add_well_data(file, drillhole)
        file = add_curve_data(file, drillhole, group)

        if not [
            k for k in file.curves if k.mnemonic not in ["FROM", "TO", "DEPTH", "DEPT"]
        ]:
            continue

        if use_directories:
            subpath = basepath / group.name
            if not subpath.exists():
                subpath.mkdir()
        else:
            subpath = basepath

        filename = f"{drillhole.name}_{group.name}.las"
        with open(subpath / filename, "a", encoding="utf8") as io:  # pylint: disable=invalid-name
            file.write(io)


def write_survey(
    drillhole: Drillhole,
    basepath: str | Path,
    use_directories: bool = True,
):
    """
    Write a formatted .las file with survey data from 'drillhole'.

    :param drillhole: geoh5py drillhole object containing property
        groups for collocated data.
    :param basepath: Path to working directory.
    :param use_directories: True if data is stored in sub-directories
    """

    if isinstance(basepath, str):
        basepath = Path(basepath)

    file = LASFile()
    file = add_well_data(file, drillhole)
    file = add_survey_data(file, drillhole)

    if use_directories:
        basepath = basepath / "Surveys"
        if not basepath.exists():
            basepath.mkdir()

    filename = f"{drillhole.name}_survey.las"
    with open(basepath / filename, "a", encoding="utf8") as io:  # pylint: disable=invalid-name
        file.write(io)


def drillhole_to_las(
    drillhole: Drillhole,
    basepath: str | Path,
    use_directories: bool = True,
):
    """
    Write a formatted .las file with data from 'drillhole'.

    :param drillhole: geoh5py drillhole object containing property
        groups for collocated data.
    :param basepath: Path to working directory.
    :param use_directories: True if data is stored in sub-directories
    """

    write_survey(drillhole, basepath, use_directories)
    write_curves(drillhole, basepath, use_directories)
