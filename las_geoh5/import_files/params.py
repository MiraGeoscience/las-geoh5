#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of las-geoh5 package.
#
#  All rights reserved.
#

from pydantic import BaseModel, ConfigDict, model_validator


LAS_GEOH5_STANDARD = {
    "collar_x_name": "X",
    "collar_y_name": "Y",
    "collar_z_name": "ELEV",
}


class NameOptions(BaseModel):
    """
    Stores options for naming of dillhole parameters in LAS files.

    :param collar_x_name: Name of the collar x field.
    :param collar_y_name: Name of the collar y field.
    :param collar_z_name: Name of the collar z field.
    """

    well_name: str = "WELL"
    collar_x_name: str = "X"
    collar_y_name: str = "Y"
    collar_z_name: str = "ELEV"

    @model_validator(mode="before")
    @classmethod
    def skip_none_value(cls, data: dict) -> dict:
        return {k: v for k, v in data.items() if v is not None}


class ImportOptions(BaseModel):
    """
    Stores options for the drillhole import.

    :param names: Options for naming of dillhole parameters in LAS files.
    :param collocation_tolerance: Tolerance for collocation of collar and depth data.
    :param warnings: Whether to show warnings.
    :param skip_empty_header: Whether to skip empty headers.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    names: NameOptions = NameOptions()
    collocation_tolerance: float = 0.01
    warnings: bool = True
    skip_empty_header: bool = False
