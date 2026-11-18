from enum import StrEnum
from typing import Annotated

from fastapi import Query, Response
from pydantic import Field


class TreeName(StrEnum):
    lifemap = "lifemap"


class TilesType(StrEnum):
    composite = "composite"


class LangType(StrEnum):
    fr = "fr"
    en = "en"
    de = "de"
    es = "es"
    el = "el"


TaxidType = Annotated[int, Query(ge=0, lt=1e9)]

XYType = Annotated[int, Field(ge=0)]
ZoomType = Annotated[int, Field(ge=0, le=50)]


class ProtobufResponse(Response):
    media_type = "application/x-protobuf"
