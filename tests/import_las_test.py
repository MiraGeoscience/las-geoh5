#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

from __future__ import annotations

import datetime
import importlib
import logging
from pathlib import Path
from unittest.mock import patch

import lasio
import numpy as np
import pytest
from geoh5py import Workspace
from geoh5py.groups import DrillholeGroup
from geoh5py.objects import Drillhole
from lasio import LASFile

from las_geoh5.import_files.driver import log_execution_time
from las_geoh5.import_files.params import NameOptions
from las_geoh5.import_las import (
    LASTranslator,
    add_data,
    add_survey,
    create_or_append_drillhole,
)

from .helpers import generate_lasfile, write_import_params_file, write_lasfile


TEST_FILES = [
    generate_lasfile(
        "dh1",
        {"UTMX": 0.0, "UTMY": 0.0, "ELEV": 10.0},
        np.arange(0, 11, 1),
        {"my_property": np.zeros(11)},
    ),
    generate_lasfile(
        "dh1",
        {"UTMX": 0.0, "UTMY": 0.0, "ELEV": 10.0},
        np.arange(0, 11, 1),
        {"my_property": np.ones(11)},
    ),
    generate_lasfile(
        "dh2",
        {"UTMX": 10.0, "UTMY": 10.0, "ELEV": 0.0},
        np.arange(0, 21, 1),
        {
            "my_property": None,
            "my_other_property": None,
        },
    ),
]


def test_import_las_new_drillholes(tmp_path: Path):
    with Workspace.create(tmp_path / "test.geoh5") as workspace:
        dh_group = DrillholeGroup.create(workspace, name="dh_group")

    lasfiles = [write_lasfile(tmp_path, lasfile) for lasfile in TEST_FILES]
    filepath = write_import_params_file(
        tmp_path / "import_las_files.ui.json",
        dh_group,
        "my_property_group",
        lasfiles,
        (
            "UTMX",
            "UTMY",
            "ELEV",
        ),
    )

    module = importlib.import_module("las_geoh5.import_files.driver")
    module.run(filepath)

    with workspace.open():
        dh1 = workspace.get_entity("dh1")[0]
        assert dh1.collar["x"] == 0.0
        assert dh1.collar["y"] == 0.0
        assert dh1.collar["z"] == 10.0
        assert dh1.surveys.shape == (1, 3)
        assert np.allclose(dh1.surveys, np.r_[0, 0, -90])
        assert dh1.end_of_hole == 0.0
        assert dh1.parent.uid == dh_group.uid
        assert all(dh1.get_data("my_property")[0].values == 0.0)
        assert dh1.property_groups[0].name == "my_property_group"
        assert len(dh1.property_groups) == 1
        assert dh1.property_groups[0].depth_.values.max() == 10.0
        assert len(dh1.property_groups[0].properties) == 3

        dh2 = workspace.get_entity("dh2")[0]
        assert dh2.collar["x"] == 10.0
        assert dh2.collar["y"] == 10.0
        assert dh2.collar["z"] == 0.0
        assert dh2.end_of_hole == 0.0
        assert dh2.parent.uid == dh_group.uid
        assert dh2.property_groups[0].name == "my_property_group"
        assert len(dh2.property_groups) == 1
        assert dh2.property_groups[0].depth_.values.max() == 20.0
        assert len(dh2.property_groups[0].properties) == 3


def test_import_las_existing_drillholes(tmp_path: Path):
    with Workspace.create(tmp_path / "test.geoh5") as workspace:
        dh_group = DrillholeGroup.create(workspace, name="dh_group")
        dh1 = Drillhole.create(
            workspace, name="dh1", parent=dh_group, collar=[0, 0, 10]
        )
        dh2 = Drillhole.create(
            workspace, name="dh2", parent=dh_group, collar=[10, 10, 0]
        )
        survey = np.c_[
            np.linspace(0, 20, 20),
            np.ones(20) * 45.0,
            np.linspace(-89, -75, 20),
        ]
        dh2.surveys = survey
        dh1.add_data(
            {
                "my_other_property": {
                    "depth": np.arange(0.0, 11.0, 1.0),
                    "values": np.random.rand(11),
                },
            },
            property_group="my_property_group",
        )

    lasfiles = [write_lasfile(tmp_path, lasfile) for lasfile in TEST_FILES]
    filepath = write_import_params_file(
        tmp_path / "import_las_files.ui.json",
        dh_group,
        "my_property_group",
        lasfiles,
        (
            "UTMX",
            "UTMY",
            "ELEV",
        ),
    )

    module = importlib.import_module("las_geoh5.import_files.driver")
    module.run(filepath)

    with workspace.open():
        dh1 = workspace.get_entity("dh1")[0]
        assert dh1.collar["x"] == 0.0
        assert dh1.collar["y"] == 0.0
        assert dh1.collar["z"] == 10.0

        assert dh1.parent.uid == dh_group.uid
        assert all(dh1.get_data("my_property")[0].values == 0.0)
        assert dh1.property_groups[0].name == "my_property_group"
        assert len(dh1.property_groups) == 1
        assert dh1.property_groups[0].depth_.values.max() == 10.0
        assert len(dh1.property_groups[0].properties) == 4

        dh2 = workspace.get_entity("dh2")[0]
        assert dh2.collar["x"] == 10.0
        assert dh2.collar["y"] == 10.0
        assert dh2.collar["z"] == 0.0
        assert dh2.end_of_hole == 0.0
        assert dh2.parent.uid == dh_group.uid
        assert dh2.property_groups[0].name == "my_property_group"
        assert len(dh2.property_groups) == 1
        assert dh2.property_groups[0].depth_.values.max() == 20.0
        assert len(dh2.property_groups[0].properties) == 3


def test_las_translator_retrieve(tmp_path: Path):
    lasfile = generate_lasfile(
        "dh1",
        {"UTMX": 0.0, "UTMY": 10.0},
        np.arange(0, 10, 0.5),
        {"my_first_property": None},
    )
    lasfile = lasio.read(write_lasfile(tmp_path, lasfile))

    translator = LASTranslator(
        NameOptions(
            well_name="well",
            collar_x_name="UTMX",
            collar_y_name="UTMY",
            collar_z_name="ELEV",
        )
    )
    assert translator.retrieve("collar_x_name", lasfile) == 0.0
    assert translator.retrieve("collar_y_name", lasfile) == 10.0
    assert translator.retrieve("well_name", lasfile) == "dh1"

    with pytest.raises(
        KeyError, match="'collar_z_name' field: 'ELEV' not found in LAS file."
    ):
        translator.retrieve("collar_z_name", lasfile)


def test_las_translator_translate():
    translator = LASTranslator(NameOptions(collar_x_name="UTMX"))
    assert translator.translate("collar_x_name") == "UTMX"
    with pytest.raises(KeyError, match="'not_a_field' is not a recognized field."):
        translator.translate("not_a_field")


@pytest.mark.parametrize(
    "elapsed_seconds, formatted",
    [(90, "1m 30s"), (59, "59.00s"), (0.0001, "0.00s"), (0.2345, "0.23s")],
)
def test_log_execution_time(caplog, elapsed_seconds: int, formatted: str):
    caplog.set_level(logging.INFO)

    start = datetime.datetime(2024, 1, 1, 12, 0, 0)
    with patch("las_geoh5.import_files.driver.datetime") as mock_datetime:
        mock_datetime.now.side_effect = [
            start,
            start + datetime.timedelta(seconds=elapsed_seconds),
        ]

        msg = f"Some task planned for {elapsed_seconds} seconds"
        with log_execution_time(msg):
            pass
    assert len(caplog.records) == 1
    assert caplog.records[0].msg == f"{msg}. Time elapsed: {formatted}."


def test_skip_empty_header_option(tmp_path: Path):
    with Workspace.create(tmp_path / "test.geoh5") as workspace:
        dh_group = DrillholeGroup.create(workspace, name="dh_group")

    files = [
        generate_lasfile(
            "dh1",
            {"UTMX": 0.0, "UTMY": 0.0, "ELEV": 10.0},
            np.arange(0, 11, 1),
            {"my_property": np.zeros(11)},
        ),
        generate_lasfile(
            "dh2",
            {},
            np.arange(0, 11, 1),
            {"my_property": np.random.rand(11)},
        ),
    ]
    lasfiles = [write_lasfile(tmp_path, lasfile) for lasfile in files]
    filepath = write_import_params_file(
        tmp_path / "import_las_files.ui.json",
        dh_group,
        "my_property_group",
        lasfiles,
        (
            "UTMX",
            "UTMY",
            "ELEV",
        ),
        skip_empty_header=True,
    )

    module = importlib.import_module("las_geoh5.import_files.driver")
    module.run(filepath)

    with workspace.open():
        dh1 = workspace.get_entity("dh1")[0]
        assert dh1.collar["x"] == 0.0
        assert dh1.collar["y"] == 0.0
        assert dh1.collar["z"] == 10.0
        dh1 = workspace.get_entity("dh2")[0]
        assert not dh1


def test_add_data_increments_property_group(tmp_path: Path):
    workspace = Workspace.create(tmp_path / "test.geoh5")
    dh_group = DrillholeGroup.create(workspace, name="dh_group")
    drillhole = Drillhole.create(
        workspace,
        collar=np.r_[0.0, 0.0, 0.0],
        parent=dh_group,
        name="dh1",
    )
    drillhole.add_data(
        {"my data": {"depth": np.linspace(0, 10, 11), "values": np.random.rand(11)}},
        property_group="my group",
    )

    file = LASFile()
    file.well["WELL"] = drillhole.name
    file.append_curve("DEPTH", np.linspace(0, 10, 9), unit="m")
    file.append_curve("my new data", np.random.rand(9))

    drillhole = add_data(drillhole, file, "my group")

    assert len(drillhole.property_groups) == 2
    assert [k.name in ["my group", "my group (1)"] for k in drillhole.property_groups]

    file = LASFile()
    file.well["WELL"] = drillhole.name
    file.append_curve("DEPTH", np.linspace(0, 10, 7), unit="m")
    file.append_curve("my other new data", np.random.rand(7))

    drillhole = add_data(drillhole, file, "my group")

    assert len(drillhole.property_groups) == 3
    assert [
        k.name in ["my group", "my group (1)", "my group (2)"]
        for k in drillhole.property_groups
    ]


def test_add_data_increments_data_name(tmp_path: Path):
    workspace = Workspace.create(tmp_path / "test.geoh5")
    dh_group = DrillholeGroup.create(workspace, name="dh_group")
    drillhole = Drillhole.create(
        workspace,
        collar=np.r_[0.0, 0.0, 0.0],
        parent=dh_group,
        name="dh1",
    )
    drillhole.add_data(
        {"my data": {"depth": np.linspace(0, 10, 11), "values": np.random.rand(11)}},
        property_group="my group",
    )

    file = LASFile()
    file.well["WELL"] = drillhole.name
    file.append_curve("DEPTH", np.linspace(0, 10, 9), unit="m")
    file.append_curve("my data", np.random.rand(9))

    drillhole = add_data(drillhole, file, "my group")

    assert len(drillhole.property_groups) == 2
    assert [k.name in ["my group", "my group (1)"] for k in drillhole.property_groups]
    assert all(
        k in [c.name for c in drillhole.children] for k in ["my data", "my data (1)"]
    )

    file = LASFile()
    file.well["WELL"] = drillhole.name
    file.append_curve("DEPTH", np.linspace(0, 10, 7), unit="m")
    file.append_curve("my other new data", np.random.rand(7))

    drillhole = add_data(drillhole, file, "my group")

    assert len(drillhole.property_groups) == 3
    assert [
        k.name in ["my group", "my group (1)", "my group (2)"]
        for k in drillhole.property_groups
    ]


def test_add_survey_csv(tmp_path: Path):
    with Workspace.create(tmp_path / "test.geoh5") as workspace:
        dh_group = DrillholeGroup.create(workspace, name="dh_group")
        dh = Drillhole.create(workspace, name="dh", parent=dh_group)

        survey = np.c_[
            np.linspace(0, 100, 10), np.ones(10) * 45.0, np.linspace(-89, -75, 10)
        ]

        np.savetxt(
            tmp_path / "survey.csv", survey, header="DEPTH, DIP, AZIMUTH", delimiter=","
        )

        add_survey(tmp_path / "survey.csv", dh)
        assert np.allclose(dh.surveys, survey)


def test_add_survey_lasfile(tmp_path: Path):
    with Workspace.create(tmp_path / "test.geoh5") as workspace:
        dh_group = DrillholeGroup.create(workspace, name="dh_group")
        dh = Drillhole.create(workspace, name="dh", parent=dh_group)

        survey = np.c_[
            np.arange(0, 100, 10), np.ones(10) * 45.0, np.linspace(-89, -75, 10)
        ]

        survey_file = generate_lasfile(
            "dh1",
            {"UTMX": 0.0, "UTMY": 0.0, "ELEV": 10.0},
            np.arange(0, 100, 10),
            {"DIP": survey[:, 1], "AZIM": survey[:, 2]},
        )

        _ = write_lasfile(tmp_path, survey_file)
        survey_path = tmp_path / "dh1.las"

        add_survey(survey_path, dh)
        assert np.allclose(dh.surveys, survey)


def test_warning_no_well_name(tmp_path: Path, caplog):
    logger = logging.getLogger("las_geoh5.import_las")
    ws = Workspace.create(tmp_path / "test.geoh5")
    dh_group = DrillholeGroup.create(ws, name="dh_group")

    lasfile = generate_lasfile(
        "",
        {"X": 0.0, "Y": 10.0, "ELEV": 10.0},
        np.arange(0, 10, 0.5),
        {"my_first_property": None},
    )
    lasfile = lasio.read(write_lasfile(tmp_path, lasfile))

    assert not lasfile.header["Well"]["Well"].value
    match = "No well name provided for LAS file. Saving drillhole with name 'Unknown'"
    with caplog.at_level(logging.WARNING):
        create_or_append_drillhole(
            lasfile,
            dh_group,
            "my_property_group",
            translator=LASTranslator(NameOptions()),
            logger=logger,
        )

        assert match in caplog.text


def test_handle_numeric_well_name(tmp_path: Path):
    with Workspace.create(tmp_path / "test.geoh5") as workspace:
        dh_group = DrillholeGroup.create(workspace, name="dh_group")

    lasfile = generate_lasfile(
        "123",
        {"UTMX": 0.0, "UTMY": 0.0, "ELEV": 10.0},
        np.arange(0, 11, 1),
        {"my_property": np.zeros(11)},
    )
    lasfile = write_lasfile(tmp_path, lasfile)

    filepath = write_import_params_file(
        tmp_path / "import_las_files.ui.json",
        dh_group,
        "my_property_group",
        [lasfile],
        (
            "UTMX",
            "UTMY",
            "ELEV",
        ),
    )

    module = importlib.import_module("las_geoh5.import_files.driver")
    module.run(filepath)

    with workspace.open():
        dh_group = workspace.get_entity("dh_group")[0]
        assert "123" in [k.name for k in dh_group.children]


def test_existing_drillhole_new_collar_location(tmp_path):
    ws = Workspace.create(tmp_path / "test.geoh5")
    dh_group = DrillholeGroup.create(ws, name="dh_group")
    dh = Drillhole.create(ws, name="dh", parent=dh_group, collar=[0, 0, 0])
    lasfile = generate_lasfile(
        well="dh",
        collar={"X": 0.0, "Y": 0.0, "ELEV": 10.0},
        depths=np.arange(0, 11, 1),
        properties={"my_property": np.zeros(11)},
    )
    lasfile = lasio.read(write_lasfile(tmp_path, lasfile))
    dh_compare = create_or_append_drillhole(lasfile, dh_group, "test")

    assert dh.uid == dh_compare.uid
