#  Copyright (c) 2022 Mira Geoscience Ltd.
#
#  This file is part of my_app project.
#
#  All rights reserved.
#

from pathlib import Path
from lasio import LASFile, HeaderItem
from geoh5py.data import ReferencedData
from geoh5py.groups import PropertyGroup
from geoh5py.shared.concatenation import ConcatenatedDrillhole

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
        file.append_curve("DEPT", group.from_.values, unit='m', descr="FROM")
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
                        descr="REFERENCE"
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
def write_curves(drillhole, basepath, directory=True):

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

        with open(survey_path, 'a', encoding="utf8") as io:
            file.write(io)

def write_survey(drillhole, basepath, directory=True):

    file = LASFile()
    file = add_well_data(file, drillhole)
    file = add_survey_data(file, drillhole)

    if directory:
        basepath = Path(basepath / "Surveys")
        if not basepath.exists():
            basepath.mkdir()

    with open(Path(basepath / f"{drillhole.name}.las"), 'a', encoding="utf8") as io:
        file.write(io)

def drillhole_to_las(drillhole, basepath, directory=True):


    write_survey(drillhole, basepath, directory)
    write_curves(drillhole, basepath, directory)