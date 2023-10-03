#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  All rights reserved.
#

from las_geoh5.uijson.write_uijson import main


def test_write_ui_json(tmp_path):
    main([str(tmp_path), "export_directories"])
    assert (tmp_path / "export_las_directories.ui.json").exists()
    main([str(tmp_path), "import_directories"])
    assert (tmp_path / "import_las_directories.ui.json").exists()
    main([str(tmp_path), "import_files"])
    assert (tmp_path / "import_las_files.ui.json").exists()
