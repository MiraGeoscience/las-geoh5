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
from geoh5py.ui_json import InputFile

from las_geoh5.scripts import las_to_geoh5

from .helpers import generate_lasfile, write_import_params_file, write_lasfile


# pylint: disable=duplicate-code
@pytest.fixture(scope="module", name="lasfile")
def lasfile_fixture(tmp_path_factory) -> Path:
    input_dir = tmp_path_factory.mktemp("input")
    lasfile = generate_lasfile(
        "dh1",
        {"UTMX": 0.0, "UTMY": 0.0, "ELEV": 10.0},
        np.arange(0, 11, 1),
        {"my_property": np.zeros(11)},
    )

    return write_lasfile(input_dir, lasfile)


@pytest.fixture(name="input_workspace")
def input_workspace_fixture(tmp_path: Path) -> Workspace:
    with Workspace.create(tmp_path / "workspace for DH group.geoh5") as workspace:
        return workspace


@pytest.fixture(name="dh_group")
def dh_group_fixture(input_workspace: Workspace) -> DrillholeGroup:
    with input_workspace.open() as workspace:
        dh_group = DrillholeGroup.create(workspace, name="dh_group")
        assert dh_group is not None
    return dh_group


@pytest.fixture(name="params_filepath")
def params_filepath_fixture(
    tmp_path: Path,
    lasfile: Path,
    dh_group: DrillholeGroup,
) -> Path:
    json_dir = tmp_path / "uijson"
    json_dir.mkdir()

    return write_import_params_file(
        json_dir / "import params.json",
        dh_group,
        "my_property_group",
        [lasfile],
        (
            "UTMX",
            "UTMY",
            "ELEV",
        ),
        skip_empty_header=True,
    )


def test_las_to_geoh5_without_output_name(
    params_filepath: Path, input_workspace: Workspace
):
    """Test the las_to_geoh5 script."""

    workspace_file = input_workspace.h5file
    assert isinstance(workspace_file, Path)
    modified_date = workspace_file.stat().st_mtime

    with patch("sys.argv", ["las_to_geoh5", str(params_filepath)]):
        las_to_geoh5.main()

    assert workspace_file.is_file()
    last_modified_date = workspace_file.stat().st_mtime
    assert last_modified_date > modified_date


def test_las_to_geoh5_with_monitoring_folder(
    tmp_path: Path,
    params_filepath: Path,
    input_workspace: Workspace,
):
    """Test the las_to_geoh5 script."""

    workspace_file = input_workspace.h5file
    assert isinstance(workspace_file, Path)
    modified_date = workspace_file.stat().st_mtime

    monitoring_folder = tmp_path / "monitored here"
    monitoring_folder.mkdir()

    ifile = InputFile.read_ui_json(params_filepath)
    ifile.data["monitoring_directory"] = str(monitoring_folder)
    ifile.write_ui_json(params_filepath.name, params_filepath.parent)

    with patch("sys.argv", ["las_to_geoh5", str(params_filepath)]):
        las_to_geoh5.main()

    assert len(list(monitoring_folder.glob("*.geoh5"))) == 1

    # check input file has not changed
    assert workspace_file.is_file()
    last_modified_date = workspace_file.stat().st_mtime
    assert last_modified_date == modified_date


@pytest.mark.parametrize("output_name", ["my output.geoh5", "my output"])
def test_las_to_geoh5_with_output_name(
    tmp_path: Path,
    monkeypatch,
    params_filepath: Path,
    input_workspace: Workspace,
    output_name: str,
):
    """Test the las_to_geoh5 script."""

    workspace_file = input_workspace.h5file
    assert isinstance(workspace_file, Path)
    modified_date = workspace_file.stat().st_mtime

    working_dir = tmp_path / "working"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)
    with patch("sys.argv", ["las_to_geoh5", str(params_filepath), "-o", output_name]):
        las_to_geoh5.main()

    expected_output = working_dir / output_name
    if not expected_output.suffix:
        expected_output = expected_output.with_suffix(".geoh5")
    assert expected_output.is_file()

    # check input file has not changed
    assert workspace_file.is_file()
    last_modified_date = workspace_file.stat().st_mtime
    assert last_modified_date == modified_date


@pytest.mark.parametrize("output_name", ["my output.geoh5", "my output"])
def test_las_to_geoh5_with_absolute_output_path(
    tmp_path: Path, params_filepath: Path, input_workspace: Workspace, output_name: str
):
    """Test the las_to_geoh5 script."""

    workspace_file = input_workspace.h5file
    assert isinstance(workspace_file, Path)
    modified_date = workspace_file.stat().st_mtime

    output_dir = tmp_path / "output"
    output_dir.mkdir()
    with patch(
        "sys.argv",
        [
            "las_to_geoh5",
            str(params_filepath),
            "-o",
            str((output_dir / output_name).absolute()),
        ],
    ):
        las_to_geoh5.main()

    expected_output = output_dir / output_name
    if not expected_output.suffix:
        expected_output = expected_output.with_suffix(".geoh5")
    assert expected_output.is_file()

    # check input file has not changed
    assert workspace_file.is_file()
    last_modified_date = workspace_file.stat().st_mtime
    assert last_modified_date == modified_date
