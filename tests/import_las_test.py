#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

from __future__ import annotations

import importlib
import logging
from pathlib import Path

import lasio
import numpy as np
import pytest
from geoh5py import Workspace
from geoh5py.groups import DrillholeGroup
from geoh5py.objects import Drillhole
from geoh5py.ui_json import InputFile
from lasio import LASFile

from las_geoh5.import_files.driver import elapsed_time_logger
from las_geoh5.import_files.params import NameOptions
from las_geoh5.import_las import (LASTranslator, add_data, add_survey,
                                  create_or_append_drillhole)


def generate_lasfile(
    well: str,
    collar: dict[str, float],
    depths: np.ndarray,
    properties: dict[str, np.ndarray | None],
):
    file = lasio.LASFile()
    file.well["WELL"] = well
    for name, value in collar.items():
        file.well.append(lasio.HeaderItem(mnemonic=name, value=value))
    file.append_curve("DEPTH", depths)
    for prop, values in properties.items():
        file.append_curve(
            prop, np.random.rand(len(depths)) if values is None else values
        )

    return file


def write_lasfiles(basepath, lasfiles):
    filepaths = []
    for lasfile in lasfiles:
        filepath = basepath / f"{lasfile.well['WELL'].value}.las"
        if filepath.exists():
            filepath = basepath / f"{lasfile.well['WELL'].value}_1.las"
        filepaths.append(str(filepath))
        with open(filepath, "a", encoding="utf8") as file:
            lasfile.write(file)

    return filepaths


def write_input_file(  # pylint: disable=too-many-arguments
    workspace,
    drillhole_group,
    property_group_name,
    files,
    x_collar_name,
    y_collar_name,
    z_collar_name,
    module_name,
    skip_empty_header=False,
):
    basepath = workspace.h5file.parent
    module = importlib.import_module(f"las_geoh5.{module_name}.uijson")
    ui_json = getattr(module, "ui_json")
    ifile = InputFile(ui_json=ui_json, validate=False)
    with workspace.open():
        ifile.update_ui_values(
            {
                "geoh5": workspace,
                "drillhole_group": drillhole_group,
                "name": property_group_name,
                "files": ";".join(files),
                "collar_x_name": x_collar_name,
                "collar_y_name": y_collar_name,
                "collar_z_name": z_collar_name,
                "skip_empty_header": skip_empty_header,
            }
        )
        ifile.write_ui_json("import_las_files.ui.json", str(basepath))

    if ifile.path_name is None:
        raise ValueError("Input file path is None.")

    return Path(ifile.path_name)


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


def test_import_las_new_drillholes(tmp_path):
    with Workspace.create(tmp_path / "test.geoh5") as workspace:
        dh_group = DrillholeGroup.create(workspace, name="dh_group")

    lasfiles = write_lasfiles(tmp_path, TEST_FILES)
    filepath = write_input_file(
        workspace,
        dh_group,
        "my_property_group",
        lasfiles,
        "UTMX",
        "UTMY",
        "ELEV",
        "import_files",
    )

    module = importlib.import_module("las_geoh5.import_files.driver")
    getattr(module, "run")(filepath)

    with workspace.open():
        dh1 = workspace.get_entity("dh1")[0]
        assert dh1.collar["x"] == 0.0
        assert dh1.collar["y"] == 0.0
        assert dh1.collar["z"] == 10.0
        assert dh1.end_of_hole is None
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
        assert dh2.end_of_hole is None
        assert dh2.parent.uid == dh_group.uid
        assert dh2.property_groups[0].name == "my_property_group"
        assert len(dh2.property_groups) == 1
        assert dh2.property_groups[0].depth_.values.max() == 20.0
        assert len(dh2.property_groups[0].properties) == 3


def test_import_las_existing_drillholes(tmp_path):
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

    lasfiles = write_lasfiles(tmp_path, TEST_FILES)

    filepath = write_input_file(
        workspace,
        dh_group,
        "my_property_group",
        lasfiles,
        "UTMX",
        "UTMY",
        "ELEV",
        "import_files",
    )

    module = importlib.import_module("las_geoh5.import_files.driver")
    getattr(module, "run")(filepath)

    with workspace.open():
        dh1 = workspace.get_entity("dh1")[0]
        assert dh1.collar["x"] == 0.0
        assert dh1.collar["y"] == 0.0
        assert dh1.collar["z"] == 10.0
        assert dh1.end_of_hole is None
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
        assert dh2.end_of_hole == 20.0
        assert dh2.parent.uid == dh_group.uid
        assert dh2.property_groups[0].name == "my_property_group"
        assert len(dh2.property_groups) == 1
        assert dh2.property_groups[0].depth_.values.max() == 20.0
        assert len(dh2.property_groups[0].properties) == 3


def test_las_translator_retrieve(tmp_path):
    lasfiles = [
        generate_lasfile(
            "dh1",
            {"UTMX": 0.0, "UTMY": 10.0},
            np.arange(0, 10, 0.5),
            {"my_first_property": None},
        )
    ]
    lasfiles = write_lasfiles(tmp_path, lasfiles)
    lasfile = lasio.read(tmp_path / f"{lasfiles[0]}")

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
        KeyError, match="'collar_z_name' field: 'ELEV' not found in las file."
    ):
        translator.retrieve("collar_z_name", lasfile)


def test_las_translator_translate():
    translator = LASTranslator(NameOptions(collar_x_name="UTMX"))
    assert translator.translate("collar_x_name") == "UTMX"
    with pytest.raises(KeyError, match="'not_a_field' is not a recognized field."):
        translator.translate("not_a_field")


def test_elapsed_time_logger():
    msg = elapsed_time_logger(0, 90, "Finished some task")
    assert msg == "Finished some task. Time elapsed: 1m 30s."
    msg = elapsed_time_logger(0, 59, "Finished another task.")
    assert msg == "Finished another task. Time elapsed: 59.00s."
    msg = elapsed_time_logger(0, 0.0001, "Done another task.")
    assert msg == "Done another task. Time elapsed: 0.00s."
    msg = elapsed_time_logger(0, 0.2345, "Boy I'm getting a lot done.")
    assert msg == "Boy I'm getting a lot done. Time elapsed: 0.23s."


def test_skip_empty_header_option(tmp_path):
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
    lasfiles = write_lasfiles(tmp_path, files)
    filepath = write_input_file(
        workspace,
        dh_group,
        "my_property_group",
        lasfiles,
        "UTMX",
        "UTMY",
        "ELEV",
        "import_files",
        skip_empty_header=True,
    )

    module = importlib.import_module("las_geoh5.import_files.driver")
    getattr(module, "run")(filepath)

    with workspace.open():
        dh1 = workspace.get_entity("dh1")[0]
        assert dh1.collar["x"] == 0.0
        assert dh1.collar["y"] == 0.0
        assert dh1.collar["z"] == 10.0
        dh1 = workspace.get_entity("dh2")[0]
        assert not dh1


def test_add_data_increments_property_group(tmp_path):
    workspace = Workspace(tmp_path / "test.geoh5")
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


def test_add_data_increments_data_name(tmp_path):
    workspace = Workspace(tmp_path / "test.geoh5")
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


def test_add_survey_csv(tmp_path):
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


def test_add_survey_lasfile(tmp_path):
    with Workspace.create(tmp_path / "test.geoh5") as workspace:
        dh_group = DrillholeGroup.create(workspace, name="dh_group")
        dh = Drillhole.create(workspace, name="dh", parent=dh_group)

        survey = np.c_[
            np.arange(0, 100, 10), np.ones(10) * 45.0, np.linspace(-89, -75, 10)
        ]

        survey_file = (
            generate_lasfile(
                "dh1",
                {"UTMX": 0.0, "UTMY": 0.0, "ELEV": 10.0},
                np.arange(0, 100, 10),
                {"DIP": survey[:, 1], "AZIM": survey[:, 2]},
            ),
        )

        _ = write_lasfiles(tmp_path, survey_file)
        survey_path = tmp_path / "dh1.las"

        add_survey(survey_path, dh)
        assert np.allclose(dh.surveys, survey)


def test_warning_no_well_name(tmp_path, caplog):
    logger = logging.getLogger("las_geoh5.import_las")
    ws = Workspace(tmp_path / "test.geoh5")
    dh_group = DrillholeGroup.create(ws, name="dh_group")

    lasfiles = [
        generate_lasfile(
            "",
            {"X": 0.0, "Y": 10.0, "ELEV": 10.0},
            np.arange(0, 10, 0.5),
            {"my_first_property": None},
        )
    ]
    lasfiles = write_lasfiles(tmp_path, lasfiles)
    lasfile = lasio.read(tmp_path / f"{lasfiles[0]}")

    assert not lasfile.header["Well"]["Well"].value
    match = "No well name provided for las file. Saving drillhole with name 'Unknown'"
    with caplog.at_level(logging.WARNING):
        create_or_append_drillhole(
            lasfile,
            dh_group,
            "my_property_group",
            translator=LASTranslator(NameOptions()),
            logger=logger,
        )

        assert match in caplog.text
