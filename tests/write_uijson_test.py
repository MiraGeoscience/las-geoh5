#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  las-geoh5 is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
#

from las_geoh5.uijson.write_uijson import main

# pylint: disable=R0801


def test_write_ui_json(tmp_path):
    main([str(tmp_path), "export_files"])
    assert (tmp_path / "export_las_files.ui.json").exists()
    main([str(tmp_path), "import_directories"])
    assert (tmp_path / "import_las_directories.ui.json").exists()
    main([str(tmp_path), "import_files"])
    assert (tmp_path / "import_las_files.ui.json").exists()
