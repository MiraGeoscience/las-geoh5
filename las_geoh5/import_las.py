#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

from __future__ import annotations

import logging
import re
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


_logger = logging.getLogger(__name__)


class LASTranslator:
    """Translator for the weakly standardized LAS file standard."""

    def __init__(self, names: NameOptions):
        self.names = names

    def translate(self, field: str):
        """
        Return translated field name or rais KeyError if field not recognized.

        :param field: Standardized field name.

        :return: Name of corresponding field in LAS file.
        """
        if field not in dict(self.names):
            raise KeyError(f"'{field}' is not a recognized field.")

        return getattr(self.names, field)

    def retrieve(self, field: str, lasfile: lasio.LASFile):
        """
        Access LAS data using translation.

        :param field: Name of field to retrieve.
        :param lasfile: lasio file object.

        :return: data stored in LAS file under translated field name.
        """
        if getattr(self.names, field) in lasfile.well:
            out = lasfile.well[getattr(self.names, field)].value
        elif getattr(self.names, field) in lasfile.curves:
            out = lasfile.curves[getattr(self.names, field)].data
        elif getattr(self.names, field) in lasfile.params:
            out = lasfile.params[getattr(self.names, field)].value
        else:
            msg = f"'{field}' field: '{getattr(self.names, field)}' not found in LAS file."
            raise KeyError(msg)

        return out


def get_depths(lasfile: lasio.LASFile) -> dict[str, np.ndarray]:
    """
    Get depth data from LAS file.

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
    Returns collar data from LAS file or None if data missing.

    :param lasfile: Las file object.
    :param translator: Translator for LAS file.
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
                    f"'{getattr(translator.names, field)}' not found in LAS file."
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
    Import survey data from CSV or LAS format and add to drillhole.

    :param survey: Path to a survey file stored as .csv or .las format.
    :param drillhole: Drillhole object to append data to.
    :param logger: logger object if warning are enabled.

    :return: Updated drillhole object.
    """

    if isinstance(survey, str):
        survey = Path(survey)

    if survey.suffix == ".las":
        file = lasio_read(survey)
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
    Add data from LAS file curves to drillhole.

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
    *,
    translator: LASTranslator | None = None,
    collocation_tolerance: float = 0.01,
    logger: logging.Logger | None = None,
) -> ConcatenatedDrillhole:
    """
    Create a drillhole or append data to drillhole if it exists in workspace.

    :param lasfile: Las file object.
    :param drillhole_group: Drillhole group container.
    :param group_name: Property group name.
    :param translator: Translator for LAS file.
    :param collocation_tolerance: Tolerance for determining collocation of data.
    :param logger: Logger object if warnings are enabled.

    :return: Created or augmented drillhole.
    """

    if translator is None:
        translator = LASTranslator(NameOptions())

    name = translator.retrieve("well_name", lasfile)
    if not isinstance(name, str):
        name = str(name)
    if not name and logger is not None:
        logger.warning(
            "No well name provided for LAS file. "
            "Saving drillhole with name 'Unknown'."
        )

    collar = get_collar(lasfile, translator, logger)
    drillhole = drillhole_group.get_entity(name)[0]  # type: ignore

    if not isinstance(drillhole, Drillhole):
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
    *,
    surveys: Path | list[Path] | None = None,
    logger: logging.Logger | None = None,
    options: ImportOptions | None = None,
):
    """
    Import a LAS file containing collocated datasets for a single drillhole.

    :param data: Las file(s) containing drillhole data.
    :param drillhole_group: Drillhole group container.
    :param property_group: Property group name.
    :param surveys: Path to a survey file stored as .csv or .las format.
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
    if not isinstance(surveys, list):
        surveys = [surveys] if surveys else []

    for datum in tqdm(data, desc="Adding drillholes and data to workspace"):
        collar = get_collar(datum, translator, logger)
        if all(k == 0 for k in collar) and options.skip_empty_header:
            continue

        create_or_append_drillhole(
            datum,
            drillhole_group,
            property_group,
            translator=translator,
            logger=logger,
            collocation_tolerance=options.collocation_tolerance,
        )

    for drillhole in tqdm(drillhole_group.children, desc="Attaching survey data."):
        if not isinstance(drillhole, ConcatenatedDrillhole):
            continue

        survey = [
            survey for survey in surveys if drillhole.name == survey.name.rstrip(".las")
        ]

        if any(survey):
            _ = add_survey(survey[0], drillhole, logger)

        elif len(drillhole.surveys) == 1:
            depths = []
            if drillhole.depth_ is not None:
                depths = [depth.values.max() for depth in drillhole.depth_]
            elif drillhole.to_ is not None:
                depths = [depth.values.max() for depth in drillhole.to_]

            if len(depths) == 0:
                continue

            new_row = drillhole.surveys[0, :]
            new_row[0] = np.max(depths)
            drillhole.surveys = np.vstack([drillhole.surveys, new_row])


def _patch_lasio_reader():
    """Patch lasio.reader.configure_metadata_patterns to handle edge cases."""

    # patch only once
    if getattr(lasio.reader, "patched_configure_metadata_patterns", False):
        return

    _logger.debug("Patching lasio.reader.configure_metadata_patterns")

    # TODO: Propose change on lasio to fix possible version issue

    def configure_metadata_patterns(line, section_name):  # pylint: disable=too-many-locals
        """Configure regular-expression patterns to parse section meta-data lines.

        # OVERLOAD lasio.reader.configure_metadata_patterns

        Arguments:
            line (str): line from LAS header section
            section_name (str): Name of the section the 'line' is from.

        Returns:
            An array of regular-expression strings (patterns).
        """

        # Default return value
        patterns = []

        # Default regular expressions for name, value and desc fields
        name_re = r"\.?(?P<name>[^.]*)\."
        value_re = r"(?P<value>.*):"
        desc_re = r"(?P<descr>.*)"

        # Default regular expression for unit field. Note that we
        # attempt to match "1000 psi" as a special case which allows
        # a single whitespace character, in contradiction to the LAS specification
        # See GitHub issue #363 for details.
        if "VERS" in line:
            unit_re = r"(?P<unit>\D*)"
        else:
            unit_re = r"(?P<unit>([0-9]+\s)?[^\s]*)"

        # Alternate regular expressions for special cases
        name_missing_period_re = r"(?P<name>[^:]*):"
        value_missing_period_re = r"(?P<value>.*)"
        value_without_colon_delimiter_re = r"(?P<value>[^:]*)"
        value_with_time_colon_re = (
            r"(?P<value>.*?)(?:(?<!( [0-2][0-3]| hh| HH)):(?!([0-5][0-9]|mm|MM)))"
        )
        name_with_dots_re = r"\.?(?P<name>[^.].*[.])\."
        no_desc_re = ""
        no_unit_re = ""

        # Configure special cases
        # 1. missing period (assume that only name and value are present)
        # 2. missing colon delimiter and description field
        # 3. double_dots '..' caused by mnemonic abbreviation (with period)
        #    next to the dot delimiter.
        if ":" in line:
            if "." not in line[: line.find(":")]:
                # If there is no period, then we assume that the colon exists and
                # everything on the left is the name, and everything on the right
                # is the value - therefore no unit or description field.
                name_re = name_missing_period_re
                value_re = value_missing_period_re
                desc_re = no_desc_re
                unit_re = no_unit_re
                value_with_time_colon_re = value_missing_period_re

        if ":" not in line:
            # If there isn't a colon delimiter then there isn't
            # a description field either.
            value_re = value_without_colon_delimiter_re
            desc_re = no_desc_re

            if ".." in line and section_name == "Curves":
                name_re = name_with_dots_re
        else:
            if re.search(r"[^ ]\.\.", line) and section_name == "Curves":
                double_dot = line.find("..")
                desc_colon = line.rfind(":")

                # Check that a double_dot is not in the
                # description string.
                if double_dot < desc_colon:
                    name_re = name_with_dots_re

        if section_name == "Parameter":
            # Search for a value entry with a time-value first.
            pattern = name_re + unit_re + value_with_time_colon_re + desc_re
            patterns.append(pattern)

        # Add the regular pattern for all section_names
        # for the Parameter section this will run after time-value pattern
        pattern = name_re + unit_re + value_re + desc_re
        patterns.append(pattern)

        return patterns

    lasio.reader.configure_metadata_patterns = configure_metadata_patterns
    lasio.reader.patched_configure_metadata_patterns = True


def lasio_read(file):
    """Read a LAS file using lasio.

    Wrapper around lasio.read that patches the reader to handle some
    edge cases in LAS files.
    """

    _patch_lasio_reader()
    return lasio.read(file, mnemonic_case="preserve", encoding="utf-8")
