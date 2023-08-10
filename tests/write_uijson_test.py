#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 project.
#
#  All rights reserved.
#

from las_geoh5.write_uijson import main


def test_write_ui_json(tmp_path):
    main([str(tmp_path), "export"])
    assert (tmp_path / "export_to_las.ui.json").exists()
    main([str(tmp_path), "import"])
    assert (tmp_path / "import_to_las.ui.json").exists()
