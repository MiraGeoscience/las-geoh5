#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las_geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

from __future__ import annotations
import re
from pathlib import Path
from lasio.las import reader as lasio_reader

__version__ = "0.2.1"


def assets_path() -> Path:
    """Return the path to the assets folder."""

    parent = Path(__file__).parent
    folder_name = f"{parent.name}-assets"
    assets_folder = parent.parent / folder_name
    if not assets_folder.is_dir():
        raise RuntimeError(f"Assets folder not found: {assets_folder}")

    return assets_folder


def _patch_lasio_reader():
    # TODO: Propose change on lasio to fix possible version issue

    if getattr(lasio_reader, "patched_configure_metadata_patterns", False):
        print("(was patched)")
        return

    print("patching!")
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
            if not "." in line[: line.find(":")]:
                # If there is no period, then we assume that the colon exists and
                # everything on the left is the name, and everything on the right
                # is the value - therefore no unit or description field.
                name_re = name_missing_period_re
                value_re = value_missing_period_re
                desc_re = no_desc_re
                unit_re = no_unit_re
                value_with_time_colon_re = value_missing_period_re

        if not ":" in line:
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

    lasio_reader.configure_metadata_patterns = configure_metadata_patterns
    lasio_reader.patched_configure_metadata_patterns = True


_patch_lasio_reader()

__all__ = [
    "__version__",
    "assets_path",
]
