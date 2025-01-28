from pydantic import Field

from app.schemas.base import CreationMixin, File
from app.schemas.singlecell_base import SingleCellData


class SubCellularModelScriptCreate(SingleCellData):
    file: File = Field(
        ..., title="File", description=".mod file associated with the sub-cellular model script."
    )
    temperature: float = Field(
        ...,
        title="temperature",
        description="The temperature at which the mechanism has been built to work on",
    )
    is_temperature_dependent: bool = Field(
        ...,
        title="is temperature dependent",
        description="Whether the mechanism changes depending on temperature or not",
    )
    is_ljp_corrected: bool = Field(
        False,
        title="is ljp corrected",
        description="Whether the mechanism is corrected for liquid junction potential or not",
    )
    stochastic: bool = Field(
        False, title="stochastic", description="Can the mechanisms behave stochastically"
    )


class SubCellularModelScriptRead(SubCellularModelScriptCreate, CreationMixin):
    pass
