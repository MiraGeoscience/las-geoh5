#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of las_geoh5 project.
#
#  All rights reserved.

from __future__ import annotations

import re

import las_geoh5


def test_version_is_consistent(pyproject: dict):
    assert las_geoh5.__version__ == pyproject["tool"]["poetry"]["version"]


def test_version_is_semver():
    semver_re = (
        r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
        r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
        r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
        r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    )
    assert re.search(semver_re, las_geoh5.__version__) is not None
