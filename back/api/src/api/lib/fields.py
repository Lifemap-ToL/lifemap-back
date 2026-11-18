from collections.abc import Callable
from enum import StrEnum
from typing import Annotated, Literal

from fastapi import Body, Query

from api.lib.types import LangType


class TaxoFieldType(StrEnum):
    taxid = "taxid"
    sci_name = "sci_name"
    authority = "auhority"
    synonyms = "synonyms"
    nbdesc = "nbdesc"
    zoom = "zoom"
    coordinates = "coordinates"
    lat = "lat"
    lon = "lon"
    rank = "rank"
    common_name = "common_name"


TRANSLATED_FIELDS = (TaxoFieldType.rank, TaxoFieldType.common_name)


def fields_param(
    default: Annotated[list[TaxoFieldType], Query(description="Fields to retrieve")],
    source: Literal["query", "body"] = "query",
) -> Callable[..., list[str]]:

    # source is "query" for GET requests, "body" for POST
    Param = Query if source == "query" else Body

    def dependency(
        field: Annotated[list[TaxoFieldType], Param(description="Fields to retrieve")] = default,
        lang: Annotated[
            LangType, Param(description="Language to use for translated field values")
        ] = LangType.en,
    ) -> list[str]:

        str_fields = [f.value if f not in TRANSLATED_FIELDS else f"{f}:{f}_{lang}" for f in field]
        if "taxid" not in str_fields:
            str_fields = ["taxid"] + str_fields
        return str_fields

    return dependency
