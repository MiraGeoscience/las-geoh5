#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of my_app project.
#
#  All rights reserved.
#
from __future__ import annotations

import warnings
from pathlib import Path

import lasio
import numpy as np
from geoh5py import Workspace
from geoh5py.groups import DrillholeGroup
from geoh5py.objects import Drillhole
from geoh5py.shared.concatenation import ConcatenatedDrillhole


def get_depths(lasfile: lasio.LASFile):
    """
    Get depth data from las file.

    :param lasfile: Las file object.

    :return: Depth data.
    """

    try:
        return lasfile["DEPTH"]
    except KeyError:
        pass

    try:
        return lasfile["DEPT"]
    except KeyError as err:
        raise KeyError(
            "In order to import data to geoh5py format, .las files "
            "must contain a depth curve named 'DEPTH' or 'DEPT'."
        ) from err


def find_copy_name(workspace: Workspace, basename: str, start: int = 1):
    """
    Augment name with increasing integer value until no entities found.

    :param workspace: A geoh5py.Workspace object.
    :param basename: Existing name of entity in workspace.
    :param start: Integer name augmenter to test for existence.

    :returns: Augmented name of the earliest non-existent copy in workspace.
    """

    name = f"{basename} ({start})"
    obj = workspace.get_entity(name)
    if obj and obj[0] is not None:
        find_copy_name(workspace, basename, start=start + 1)
    return name


def add_survey(survey: str | Path, drillhole: Drillhole | ConcatenatedDrillhole):
    """
    Import survey data from csv or las format and add to drillhole.

    :param survey: Path to a survey file stored as .csv or .las format.
    :param drillhole: Drillhole object to append data to.

    :return: Updated drillhole object.
    """

    if isinstance(survey, str):
        survey = Path(survey)

    if survey.suffix == ".las":
        file = lasio.read(survey, mnemonic_case="preserve")
        try:
            surveys = np.c_[get_depths(file), file["DIP"], file["AZIM"]]
            if len(drillhole.surveys) == 1:  # type: ignore
                drillhole.surveys = surveys  # type: ignore
        except KeyError:
            warnings.warn(
                "Attempted survey import failed because data read from "
                ".las file did not contain the expected 3 curves 'DEPTH'"
                ", 'DIP', 'AZIM'."
            )
    else:
        surveys = np.genfromtxt(survey, delimiter=",", skip_header=0)
        if surveys.shape[1] == 3:  # type: ignore
            drillhole.surveys = surveys  # type: ignore
        else:
            warnings.warn(
                "Attempted survey import failed because data read from "
                "comma separated file did not contain the expected 3 "
                "columns of depth/dip/azimuth."
            )

    return drillhole


def create_or_append_drillhole(  # pylint: disable=too-many-locals
    workspace: Workspace,
    lasfile: lasio.LASFile,
    drillhole_group: DrillholeGroup,
    property_group: str | None = None,
):
    """
    Create a drillhole or append data to drillhole if it exists in workspace.

    :param workspace: Project workspace.
    :param lasfile: Las file object.
    :param drillhole_group: Drillhole group container.
    :param property_group: Property group name.

    :return: Created or augmented drillhole.
    """

    name = lasfile.well["WELL"].value

    collar: list | None = []
    for attr in ["X", "Y", "ELEV"]:
        item = lasfile.well.get(attr, None)

        if item is None:
            collar = None
            break

        collar.append(item.value)  # type: ignore

    drillhole = drillhole_group.get_entity(name)
    drillhole = drillhole[0] if drillhole else None  # type: ignore
    if drillhole is None:
        kwargs = {"name": name}
        kwargs["parent"] = drillhole_group
        if collar:
            kwargs["collar"] = collar

        drillhole = Drillhole.create(workspace, **kwargs)

    elif not np.allclose(collar, drillhole.collar.tolist()):  # type: ignore
        kwargs = {"name": find_copy_name(workspace, drillhole.name)}  # type: ignore
        kwargs["parent"] = drillhole_group
        if collar:
            kwargs["collar"] = collar

        drillhole = Drillhole.create(workspace, **kwargs)

    pg_type = "Interval table" if "TO" in lasfile.curves else "Depth table"
    property_group = drillhole.find_or_create_property_group(  # type: ignore
        name=property_group, property_group_type=pg_type, association="DEPTH"
    )
    for curve in [
        k for k in lasfile.curves if k.mnemonic not in ["DEPT", "DEPTH", "TO"]
    ]:
        name = curve.mnemonic

        if drillhole.get_data(name):  # type: ignore
            continue

        kwargs = {"values": curve.data}
        depths = get_depths(lasfile)
        if "TO" in lasfile.curves:
            tos = lasfile["TO"]
            kwargs["from-to"] = np.c_[depths, tos]
        else:
            kwargs["depth"] = depths

        is_referenced = any(name in k.mnemonic for k in lasfile.params)
        is_referenced &= any(k.descr == "REFERENCE" for k in lasfile.params)
        if is_referenced:
            kwargs["values"] = kwargs["values"].astype(int)
            value_map = {
                k.mnemonic: k.value for k in lasfile.params if name in k.mnemonic
            }
            value_map = {int(k.split()[1][1:-1]): v for k, v in value_map.items()}
            kwargs["value_map"] = value_map
            kwargs["type"] = "referenced"

        drillhole.add_data(  # type: ignore
            {name: kwargs}, property_group=property_group
        )

    return drillhole


def las_to_drillhole(
    workspace: Workspace,
    data: lasio.LASFile | list[lasio.LASFile],
    drillhole_group: DrillholeGroup,
    property_group: str | None = None,
    survey: Path | list[Path] | None = None,
) -> ConcatenatedDrillhole:
    """
    Import a las file containing collocated datasets for a single drillhole.


    :param workspace: Project workspace.
    :param data: Las file(s) containing drillhole data.
    :param drillhole_group: Drillhole group container.
    :param property_group: Property group name.
    :param survey: Path to a survey file stored as .csv or .las format.

    :return: A geoh5py.ConcatenatedDrillhole object
    """

    if not isinstance(data, list):
        data = [data]
    if not isinstance(survey, list):
        survey = [survey] if survey else []

    for datum in data:
        drillhole = create_or_append_drillhole(
            workspace, datum, drillhole_group, property_group
        )
        ind = [drillhole.name == s.name.rstrip(".las") for s in survey]
        if any(ind):
            survey_path = survey[np.where(ind)[0][0]]
            drillhole = add_survey(survey_path, drillhole)

    return drillhole
