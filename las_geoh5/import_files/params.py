#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 package.
#
#  All rights reserved.
#

from pydantic import BaseModel, ConfigDict

LAS_GEOH5_STANDARD = {
    "well_name": "WELL",
    "depth_name": "DEPTH",
    "collar_x_name": "X",
    "collar_y_name": "Y",
    "collar_z_name": "ELEV",
}


class NameOptions(BaseModel):
    """
    Stores options for naming of dillhole parameters in las files.

    :param depth_name: Name of the depth field.
    :param collar_x_name: Name of the collar x field.
    :param collar_y_name: Name of the collar y field.
    :param collar_z_name: Name of the collar z field.
    """

    well_name: str = LAS_GEOH5_STANDARD["well_name"]
    depth_name: str = LAS_GEOH5_STANDARD["depth_name"]
    collar_x_name: str = LAS_GEOH5_STANDARD["collar_x_name"]
    collar_y_name: str = LAS_GEOH5_STANDARD["collar_y_name"]
    collar_z_name: str = LAS_GEOH5_STANDARD["collar_z_name"]


class ImportOptions(BaseModel):
    """
    Stores options for the drillhole import.

    :param names: Options for naming of dillhole parameters in las files.
    :param collocation_tolerance: Tolerance for collocation of collar and depth data.
    :param warnings: Whether to show warnings.
    :param skip_empty_header: Whether to skip empty headers.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    names: NameOptions = NameOptions()
    collocation_tolerance: float = 0.01
    warnings: bool = True
    skip_empty_header: bool = False
