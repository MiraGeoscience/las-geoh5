#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of my_app project.
#
#  All rights reserved.
#

import numpy as np
from pathlib import Path
from geoh5py.workspace import Workspace

from geoh5py.groups.drillhole_group import DrillholeGroup
from geoh5py.objects.drillhole import Drillhole

from las_geoh5 import drillhole_group_to_las, write_uijson

def test_geoh5_to_las(tmp_path):

    n_data = 10
    with Workspace.create(Path(tmp_path / "test.geoh5")) as workspace:

        # Create a workspace
        dh_group = DrillholeGroup.create(workspace, name="dh_group")
        well_a = Drillhole.create(
            workspace,
            collar=np.r_[0.0, 10.0, 10],
            surveys=np.c_[
                np.linspace(0, 100, n_data),
                np.ones(n_data) * 45.0,
                np.linspace(-89, -75, n_data),
            ],
            parent=dh_group,
            name="dh1",
        )

        # Add from-to data
        from_to_a = np.sort(np.random.uniform(low=0.05, high=100, size=(50,))).reshape(
            (-1, 2)
        )
        well_a_interval_data = well_a.add_data(
            {
                "interval_values": {
                    "values": np.random.randn(from_to_a.shape[0]),
                    "from-to": from_to_a.tolist(),
                },
            }
        )

        # Add depth data
        well_a_depth_data = well_a.add_data(
            {
                "depth_values": {
                    "depth": np.arange(0, 50.0),
                    "values": np.random.randn(50),
                },
                "collocated_depth_values": {
                    "depth": np.arange(0.01, 50.01),
                    "values": np.random.randn(50)
                },
            }
        )

        well_b = Drillhole.create(
            workspace,
            collar=np.r_[10.0, 10.0, 10],
            surveys=np.c_[
                np.linspace(0, 100, n_data),
                np.ones(n_data) * 45.0,
                np.linspace(-89, -75, n_data),
            ],
            parent=dh_group,
            name="dh2",
        )

        # Add from-to data
        from_to_a = np.sort(np.random.uniform(low=0.05, high=100, size=(50,))).reshape(
            (-1, 2)
        )
        well_b_interval_data = well_b.add_data(
            {
                "interval_values": {
                    "values": np.random.randn(from_to_a.shape[0]),
                    "from-to": from_to_a.tolist(),
                }
            }
        )


        drillhole_group_to_las(dh_group, tmp_path)


        pass

def test_write_uijson(tmp_path):
    write_uijson(tmp_path)