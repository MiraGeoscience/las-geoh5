#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of las_geoh5 project.
#
#  All rights reserved.

import re
import lasio
from geoh5py.shared.concatenation import ConcatenatedDrillhole

def geoh5_to_las(drillholes):

    wells = [k for k in drillholes.children if isinstance(k, ConcatenatedDrillhole)]
    for well in wells[:1]:

        las = lasio.LASFile()
        las.well["WELL"] = well.name

        for group in well.property_groups:

            if group.depth_:
                las.append_curve("DEPT", group.depth_.values, unit='m')
            else:
                # TODO convert from-to to depth and dump data to las
                continue

            properties = [well.get_data(k)[0] for k in group.properties]
            for data in [k for k in properties if k.name not in ["FROM", "TO", "DEPTH"]]:
                las.append_curve(str(data.uid), data.values, descr="")
                item = lasio.HeaderItem(mnemonic=str(data.uid), value=data.name)
                las.params.append(item)

    return las

if __name__ == "__main__":  # pragma: no cover
    print("Hello, world!")
