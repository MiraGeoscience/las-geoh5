# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024-2026 Mira Geoscience Ltd.                                '
#                                                                              '
#  This file is part of las-geoh5 package.                                     '
#                                                                              '
#  las-geoh5 is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                 '
#                                                                              '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from geoh5py import Workspace
from geoh5py.groups import DrillholeGroup
from geoh5py.objects import Drillhole

from las_geoh5.scripts import geoh5_to_las

from .helpers import write_export_params_file


# pylint: disable=duplicate-code


@pytest.fixture(scope="module", name="input_workspace")
def input_workspace_fixture(tmp_path_factory) -> Workspace:
    tmp_path = tmp_path_factory.mktemp("input")
    with Workspace.create(tmp_path / "my workspace") as workspace:
        return workspace


@pytest.fixture(scope="module", name="dh_group")
def dh_group_fixture(input_workspace: Workspace) -> DrillholeGroup:
    with input_workspace.open() as workspace:
        drillhole_group: DrillholeGroup = DrillholeGroup.create(
            workspace, name="dh_group"
        )

        drillhole_a: Drillhole = Drillhole.create(
            workspace,
            collar=np.r_[0.0, 10.0, 10],
            parent=drillhole_group,
            name="dh1",
        )
        drillhole_a.add_data(
            {
                "my_data": {
                    "depth": np.arange(0, 50.0),
                    "values": np.random.randn(50),
                },
            }
        )
    return drillhole_group


def test_geoh5_to_las_without_output_dir(
    tmp_path: Path,
    input_workspace: Workspace,
    dh_group: DrillholeGroup,
):
    """Test the geoh5_to_las script."""

    export_dir = tmp_path / "export here"
    export_dir.mkdir()
    params_filepath = write_export_params_file(
        tmp_path / "export params.json",
        input_workspace,
        dh_group,
        export_dir,
        use_directories=False,
    )
    with patch("sys.argv", ["geoh5_to_las", str(params_filepath)]):
        geoh5_to_las.main()
    assert len([export_dir.glob("*.las")]) > 0


def test_geoh5_to_las_with_output_dir_name(
    tmp_path: Path,
    monkeypatch,
    input_workspace: Workspace,
    dh_group: DrillholeGroup,
):
    """Test the geoh5_to_las script."""

    unused_dir = tmp_path / "unused"
    params_filepath = write_export_params_file(
        tmp_path / "export_params.json",
        input_workspace,
        dh_group,
        unused_dir,
        use_directories=False,
    )

    working_dir = tmp_path / "working"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)
    output_dir_name = "export there"
    with patch(
        "sys.argv", ["geoh5_to_las", str(params_filepath), "-o", output_dir_name]
    ):
        geoh5_to_las.main()

    expected_output_dir = working_dir / output_dir_name
    assert len([expected_output_dir.glob("*.las")]) > 0
    assert not unused_dir.exists()


def test_geoh5_to_las_with_absolute_output_dir(
    tmp_path: Path,
    input_workspace: Workspace,
    dh_group: DrillholeGroup,
):
    """Test the geoh5_to_las script."""

    unused_dir = tmp_path / "unused"
    params_filepath = write_export_params_file(
        tmp_path / "export_params.json",
        input_workspace,
        dh_group,
        unused_dir,
        use_directories=False,
    )
    output_dir_name = "export there"
    forced_export_dir = tmp_path / output_dir_name
    with patch(
        "sys.argv",
        ["geoh5_to_las", str(params_filepath), "-o", str(forced_export_dir.absolute())],
    ):
        geoh5_to_las.main()

    assert len([forced_export_dir.glob("*.las")]) > 0
    assert not unused_dir.exists()
