from enum import Enum
from typing import Annotated

from fastapi import Query, Response
from pydantic import ConfigDict, Field, PositiveInt, RootModel


class TreeName(str, Enum):
    lifemap = "lifemap"


class TilesType(str, Enum):
    composite = "composite"


TaxidType = Annotated[PositiveInt, Query(lt=1e9)]

XYZType = Annotated[int, Field(ge=0)]


class ScinamesMap(RootModel[dict[str, str]]):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"2": "Bacteria", "9538": "Erythrocebus patas"}]}
    )


class ProtobufResponse(Response):
    media_type = "application/x-protobuf"
