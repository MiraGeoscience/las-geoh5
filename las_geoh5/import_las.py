#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import lasio
import numpy as np
from geoh5py import Workspace
from geoh5py.groups import DrillholeGroup
from geoh5py.objects import Drillhole
from geoh5py.shared import Entity
from tqdm import tqdm


class LASTranslator:
    """Translator for the weakly standardized LAS file standard."""

    las_geoh5_standard = {
        "well": "WELL",
        "depth": "DEPTH",
        "collar_x": "X",
        "collar_y": "Y",
        "collar_z": "ELEV",
    }

    def __init__(
        self,
        well: str = las_geoh5_standard["well"],
        depth: str = las_geoh5_standard["depth"],
        collar_x: str = las_geoh5_standard["collar_x"],
        collar_y: str = las_geoh5_standard["collar_y"],
        collar_z: str = las_geoh5_standard["collar_z"],
    ):
        self.well = well
        self.depth = depth
        self.collar_x = collar_x
        self.collar_y = collar_y
        self.collar_z = collar_z

    def translate(self, field: str):
        """
        Return translated field name or rais KeyError if field not recognized.

        :param field: Standardized field name.
        :return: Name of corresponding field in las file.
        """
        if field not in self.las_geoh5_standard:
            raise KeyError(f"'{field}' is not a recognized field.")

        return getattr(self, field)

    def retrieve(self, field, lasfile):
        """
        Access las data using translation.

        :param field: Name of field to retrieve.
        :param lasfile: lasio file object.
        :return: data stored in las file under translated field name.
        """
        if getattr(self, field) in lasfile.well:
            out = lasfile.well[getattr(self, field)].value
        elif getattr(self, field) in lasfile.curves:
            out = lasfile.curves[getattr(self, field)].data
        elif getattr(self, field) in lasfile.params:
            out = lasfile.params[getattr(self, field)].value
        else:
            msg = f"'{field}' field: '{getattr(self, field)}' not found in las file."
            raise KeyError(msg)

        return out


def get_depths(lasfile: lasio.LASFile) -> dict[str, np.ndarray]:
    """
    Get depth data from las file.

    :param lasfile: Las file object.

    :return: Depth data as 'from-to' interval or 'depth' locations.
    """

    depths = None
    for name, curve in lasfile.curves.items():
        if name.lower() in ["depth", "dept"]:
            depths = curve.data
            break

    if depths is None:
        raise ValueError(
            "In order to import data to geoh5py format, .las files "
            "must contain a depth curve named 'DEPTH' or 'DEPT'."
        )

    out = {}
    if "TO" in lasfile.curves:
        tos = lasfile["TO"]
        out["from-to"] = np.c_[depths, tos]
    else:
        out["depth"] = depths

    return out


def get_collar(lasfile: lasio.LASFile, translator: LASTranslator | None = None) -> list:
    """
    Returns collar data from las file or None if data missing.

    :param lasfile: Las file object.

    :return: Collar data.
    """

    if translator is None:
        translator = LASTranslator()

    collar = []
    for field in ["collar_x", "collar_y", "collar_z"]:
        collar_coord = 0.0
        try:
            collar_coord = translator.retrieve(field, lasfile)
        except KeyError:
            exclusions = ["STRT", "STOP", "STEP", "NULL"]
            options = [
                k.mnemonic
                for k in lasfile.well
                if k.value and k.mnemonic not in exclusions
            ]
            warnings.warn(
                f"{field.replace('_', ' ').capitalize()} field "
                f"'{getattr(translator, field)}' not found in las file."
                f" Setting coordinate to 0.0. Non-null header fields include: "
                f"{options}."
            )

            collar_coord = 0.0

        try:
            collar.append(float(collar_coord))
        except ValueError:
            collar.append(0.0)

    return collar


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


def add_survey(survey: str | Path, drillhole: Drillhole) -> Drillhole:
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
            surveys = np.c_[get_depths(file)["depth"], file["DIP"], file["AZIM"]]
            if len(drillhole.surveys) == 1:
                drillhole.surveys = surveys
        except KeyError:
            warnings.warn(
                "Attempted survey import failed because data read from "
                ".las file did not contain the expected 3 curves 'DEPTH'"
                ", 'DIP', 'AZIM'."
            )
    else:
        surveys = np.genfromtxt(survey, delimiter=",", skip_header=0)
        if surveys.shape[1] == 3:
            drillhole.surveys = surveys
        else:
            warnings.warn(
                "Attempted survey import failed because data read from "
                "comma separated file did not contain the expected 3 "
                "columns of depth/dip/azimuth."
            )

    return drillhole


def add_data(
    drillhole: Drillhole,
    lasfile: lasio.LASFile,
    group_name: str,
) -> Drillhole:
    """
    Add data from las file curves to drillhole.

    :param drillhole: Drillhole object to append data to.
    :param lasfile: Las file object.
    :param property_group: Property group.

    :return: Updated drillhole object.
    """

    depths = get_depths(lasfile)
    if "depth" in depths:
        method_name = "validate_depth_data"
        locations = depths["depth"]
    else:
        method_name = "validate_interval_data"
        locations = depths["from-to"]

    try:
        property_group = getattr(drillhole, method_name)(
            "noname",
            locations,
            np.zeros_like(locations),
            property_group=group_name,
            collocation_distance=1e-4,
        )
    except ValueError as err:
        msg = (
            f"validate_depth_data call failed with message:\n{err.args[0]}. "
            f"Skipping import for drillhole {drillhole.name}."
        )
        warnings.warn(msg)

        # TODO: Increment property group name if it already exists and the depth
        # Sampling is different.  Could try removing the try/except block once
        # done and see if error start to appear.

        return drillhole

    kwargs: dict[str, Any] = {}
    for curve in tqdm(
        [k for k in lasfile.curves if k.mnemonic not in ["DEPT", "DEPTH", "TO"]]
    ):
        name = curve.mnemonic
        if drillhole.get_data(name):
            msg = f"Drillhole '{drillhole.name}' already contains '{name}' data"
            warnings.warn(msg)
            continue

        kwargs[name] = {"values": curve.data, "association": "DEPTH"}

        is_referenced = any(name in k.mnemonic for k in lasfile.params)
        is_referenced &= any(k.descr == "REFERENCE" for k in lasfile.params)
        if is_referenced:
            kwargs[name]["values"] = kwargs[name]["values"].astype(int)
            value_map = {
                k.mnemonic: k.value for k in lasfile.params if name in k.mnemonic
            }
            value_map = {int(k.split()[1][1:-1]): v for k, v in value_map.items()}
            kwargs[name]["value_map"] = value_map
            kwargs[name]["type"] = "referenced"

        existing_data = drillhole.workspace.get_entity(name)[0]
        if existing_data and isinstance(existing_data, Entity):
            kwargs[name]["entity_type"] = existing_data.entity_type

    drillhole.add_data(kwargs, property_group=property_group)

    return drillhole


def create_or_append_drillhole(
    workspace: Workspace,
    lasfile: lasio.LASFile,
    drillhole_group: DrillholeGroup,
    group_name: str,
    translator: LASTranslator | None = None,
) -> Drillhole:
    """
    Create a drillhole or append data to drillhole if it exists in workspace.

    :param workspace: Project workspace opened with read/write access.
    :param lasfile: Las file object.
    :param drillhole_group: Drillhole group container.
    :param group_name: Property group name.
    :param translator: Translator for las file.

    :return: Created or augmented drillhole.
    """

    if translator is None:
        translator = LASTranslator()

    name = translator.retrieve("well", lasfile)
    collar = get_collar(lasfile, translator)
    drillhole = drillhole_group.get_entity(name)[0]  # type: ignore

    if not isinstance(drillhole, Drillhole) or (
        isinstance(drillhole, Drillhole)
        and not np.allclose(collar, drillhole.collar.tolist())
    ):
        name = name if drillhole is None else find_copy_name(workspace, name)
        kwargs = {
            "name": name,
            "parent": drillhole_group,
        }
        if collar:
            kwargs["collar"] = collar

        drillhole = Drillhole.create(workspace, **kwargs)

    if not isinstance(drillhole, Drillhole):
        raise TypeError(
            f"Drillhole {name} exists in workspace but is not a Drillhole object."
        )

    drillhole = add_data(drillhole, lasfile, group_name)

    return drillhole


def las_to_drillhole(  # pylint: disable=too-many-arguments
    workspace: Workspace,
    data: lasio.LASFile | list[lasio.LASFile],
    drillhole_group: DrillholeGroup,
    property_group: str,
    survey: Path | list[Path] | None = None,
    translator: LASTranslator | None = None,
    skip_empty_header: bool = False,
):
    """
    Import a las file containing collocated datasets for a single drillhole.

    :param workspace: Project workspace.
    :param data: Las file(s) containing drillhole data.
    :param drillhole_group: Drillhole group container.
    :param property_group: Property group name.
    :param survey: Path to a survey file stored as .csv or .las format.
    :param translator: Translator for las file.
    :param skip_empty_header: Skip empty header data.

    :return: A :obj:`geoh5py.objects.Drillhole` object
    """

    if not isinstance(data, list):
        data = [data]
    if not isinstance(survey, list):
        survey = [survey] if survey else []
    if translator is None:
        translator = LASTranslator()

    for datum in data:
        collar = get_collar(datum, translator)
        if all(k == 0 for k in collar) and skip_empty_header:
            continue

        drillhole = create_or_append_drillhole(
            workspace, datum, drillhole_group, property_group, translator=translator
        )
        ind = [drillhole.name == s.name.rstrip(".las") for s in survey]
        if any(ind):
            survey_path = survey[np.where(ind)[0][0]]
            _ = add_survey(survey_path, drillhole)
