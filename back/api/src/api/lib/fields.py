from collections.abc import Callable
from enum import Enum
from typing import Annotated

from fastapi import Query

from api.lib.types import LangType


class TaxoFieldType(str, Enum):
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
) -> Callable[..., list[str]]:

    def dependency(
        field: Annotated[list[TaxoFieldType], Query(description="Fields to retrieve")] = default,
        lang: Annotated[
            LangType, Query(description="Language to use for translated field values")
        ] = LangType.en,
    ) -> list[str]:

        str_fields = [
            f.value if f not in TRANSLATED_FIELDS else f"{f.value}:{f.value}_{lang.value}" for f in field
        ]
        if "taxid" not in str_fields:
            str_fields = ["taxid"] + str_fields
        return str_fields

    return dependency
