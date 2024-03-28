#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import lasio
import numpy as np
from geoh5py import Workspace
from geoh5py.groups import DrillholeGroup
from geoh5py.objects import Drillhole, ObjectBase
from geoh5py.shared import Entity
from geoh5py.shared.concatenation import ConcatenatedDrillhole
from tqdm import tqdm

from las_geoh5.import_files.params import ImportOptions, NameOptions


class LASTranslator:
    """Translator for the weakly standardized LAS file standard."""

    def __init__(self, names: NameOptions):
        self.names = names

    def translate(self, field: str):
        """
        Return translated field name or rais KeyError if field not recognized.

        :param field: Standardized field name.

        :return: Name of corresponding field in las file.
        """
        if field not in dict(self.names):
            raise KeyError(f"'{field}' is not a recognized field.")

        return getattr(self.names, field)

    def retrieve(self, field: str, lasfile: lasio.LASFile):
        """
        Access las data using translation.

        :param field: Name of field to retrieve.
        :param lasfile: lasio file object.

        :return: data stored in las file under translated field name.
        """
        if getattr(self.names, field) in lasfile.well:
            out = lasfile.well[getattr(self.names, field)].value
        elif getattr(self.names, field) in lasfile.curves:
            out = lasfile.curves[getattr(self.names, field)].data
        elif getattr(self.names, field) in lasfile.params:
            out = lasfile.params[getattr(self.names, field)].value
        else:
            msg = f"'{field}' field: '{getattr(self.names, field)}' not found in las file."
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


def get_collar(
    lasfile: lasio.LASFile,
    translator: LASTranslator | None = None,
    logger: logging.Logger | None = None,
) -> list:
    """
    Returns collar data from las file or None if data missing.

    :param lasfile: Las file object.
    :param translator: Translator for las file.
    :param logger: Logger object if warnings are enabled.

    :return: Collar data.
    """

    if translator is None:
        translator = LASTranslator(names=NameOptions())

    collar = []
    for field in ["collar_x_name", "collar_y_name", "collar_z_name"]:
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
            if logger is not None:
                logger.warning(
                    f"{field.replace('_', ' ').capitalize()} field "
                    f"'{getattr(translator.names, field)}' not found in las file."
                    f" Setting coordinate to 0.0. Non-null header fields include: "
                    f"{options}."
                )

            collar_coord = 0.0

        try:
            collar.append(float(collar_coord))
        except ValueError:
            collar.append(0.0)

    return collar


def find_copy_name(obj: Workspace | ObjectBase, basename: str, start: int = 0):
    """
    Augment name with increasing integer value until no entities found.

    :param obj: A geoh5py object or workspace.
    :param basename: Existing name of entity in workspace.
    :param start: Integer name augmenter to test for existence.  Default is
        0 and does not add a suffix

    :returns: Suffix name of the earliest non-existent copy in workspace.
    """

    name = basename if start == 0 else f"{basename} ({start})"
    child = obj.get_entity(name)
    if child and child[0] is not None:
        name = find_copy_name(obj, basename, start=start + 1)
    return name


def add_survey(
    survey: str | Path,
    drillhole: ConcatenatedDrillhole,
    logger: logging.Logger | None = None,
) -> ConcatenatedDrillhole:
    """
    Import survey data from csv or las format and add to drillhole.

    :param survey: Path to a survey file stored as .csv or .las format.
    :param drillhole: Drillhole object to append data to.
    :param logger: logger object if warning are enabled.

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
            if logger is not None:
                logger.warning(
                    "Attempted survey import failed because data read from "
                    ".las file did not contain the expected 3 curves 'DEPTH'"
                    ", 'DIP', 'AZIM'."
                )
    else:
        surveys = np.genfromtxt(survey, delimiter=",", skip_header=0)
        if surveys.shape[1] == 3:
            drillhole.surveys = surveys
        else:
            if logger is not None:
                logger.warning(
                    "Attempted survey import failed because data read from "
                    "comma separated file did not contain the expected 3 "
                    "columns of depth/dip/azimuth."
                )

    return drillhole


def add_data(
    drillhole: ConcatenatedDrillhole,
    lasfile: lasio.LASFile,
    group_name: str,
    collocation_tolerance: float = 0.01,
) -> ConcatenatedDrillhole:
    """
    Add data from las file curves to drillhole.

    :param drillhole: Drillhole object to append data to.
    :param lasfile: Las file object.
    :param group_name: Property group name.
    :param collocation_tolerance: Tolerance for determining collocation of data.

    :return: Updated drillhole object.
    """

    depths = get_depths(lasfile)
    property_group_kwargs = {}
    if "depth" in depths:
        locations = depths["depth"]
        property_group_kwargs["property_group_type"] = "Depth table"
        property_group_kwargs["association"] = "DEPTH"
    else:
        locations = depths["from-to"]
        property_group_kwargs["property_group_type"] = "Interval table"
        property_group_kwargs["association"] = "FROM-TO"

    kwargs: dict[str, Any] = {}
    for curve in [
        k for k in lasfile.curves if k.mnemonic not in ["DEPT", "DEPTH", "TO"]
    ]:
        name = curve.mnemonic
        if drillhole.get_data(name):
            name = find_copy_name(drillhole, name)

        kwargs[name] = {"values": curve.data, "association": "DEPTH"}
        kwargs[name].update(depths)

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

    if kwargs:
        if drillhole.property_groups is not None:
            root_name_matches = [
                g for g in drillhole.property_groups if group_name in g.name
            ]
            if root_name_matches:
                group = [
                    g
                    for g in root_name_matches
                    if g.is_collocated(locations, collocation_tolerance)
                ]
                if group:
                    group_name = group[0].name
                else:
                    group_name = find_copy_name(drillhole.workspace, group_name)

        drillhole.add_data(kwargs, property_group=group_name)

    return drillhole


def create_or_append_drillhole(
    lasfile: lasio.LASFile,
    drillhole_group: DrillholeGroup,
    group_name: str,
    translator: LASTranslator | None = None,
    collocation_tolerance: float = 0.01,
    logger: logging.Logger | None = None,
) -> ConcatenatedDrillhole:
    """
    Create a drillhole or append data to drillhole if it exists in workspace.

    :param lasfile: Las file object.
    :param drillhole_group: Drillhole group container.
    :param group_name: Property group name.
    :param translator: Translator for las file.
    :param collocation_tolerance: Tolerance for determining collocation of data.
    :param logger: Logger object if warnings are enabled.

    :return: Created or augmented drillhole.
    """

    if translator is None:
        translator = LASTranslator(NameOptions())

    name = translator.retrieve("well_name", lasfile)
    if not name and logger is not None:
        logger.warning(
            "No well name provided for las file. "
            "Saving drillhole with name 'Unknown'."
        )

    collar = get_collar(lasfile, translator, logger)
    drillhole = drillhole_group.get_entity(name)[0]  # type: ignore

    if not isinstance(drillhole, Drillhole) or (
        isinstance(drillhole, Drillhole)
        and not np.allclose(collar, drillhole.collar.tolist())
    ):
        name = find_copy_name(drillhole_group.workspace, name)
        kwargs = {
            "name": name,
            "parent": drillhole_group,
        }
        if collar:
            kwargs["collar"] = collar

        drillhole = Drillhole.create(drillhole_group.workspace, **kwargs)

    if not isinstance(drillhole, ConcatenatedDrillhole):
        raise TypeError(
            f"Drillhole {name} exists in workspace but is not a Drillhole object."
        )

    drillhole = add_data(
        drillhole, lasfile, group_name, collocation_tolerance=collocation_tolerance
    )

    return drillhole


def las_to_drillhole(
    data: lasio.LASFile | list[lasio.LASFile],
    drillhole_group: DrillholeGroup,
    property_group: str,
    survey: Path | list[Path] | None = None,
    logger: logging.Logger | None = None,
    options: ImportOptions | None = None,
):
    """
    Import a las file containing collocated datasets for a single drillhole.

    :param data: Las file(s) containing drillhole data.
    :param drillhole_group: Drillhole group container.
    :param property_group: Property group name.
    :param survey: Path to a survey file stored as .csv or .las format.
    :param logger: Logger object if warnings are enabled.
    :param options: Import options covering name translations, collocation
        tolerance, and warnings control.

    :return: A :obj:`geoh5py.objects.Drillhole` object
    """

    if options is None:
        options = ImportOptions()

    translator = LASTranslator(names=options.names)

    if not isinstance(data, list):
        data = [data]
    if not isinstance(survey, list):
        survey = [survey] if survey else []

    for datum in tqdm(data, desc="Adding drillholes and data to workspace"):
        collar = get_collar(datum, translator, logger)
        if all(k == 0 for k in collar) and options.skip_empty_header:
            continue

        drillhole = create_or_append_drillhole(
            datum,
            drillhole_group,
            property_group,
            translator=translator,
            logger=logger,
            collocation_tolerance=options.collocation_tolerance,
        )
        ind = [drillhole.name == s.name.rstrip(".las") for s in survey]
        if any(ind):
            survey_path = survey[np.where(ind)[0][0]]
            _ = add_survey(survey_path, drillhole, logger)
