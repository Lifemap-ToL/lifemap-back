from enum import Enum
from typing import Annotated

from fastapi import Query
from pydantic import PositiveInt


class TreeName(str, Enum):
    lifemap = "lifemap"


TaxidType = Annotated[PositiveInt, Query(lt=1e9)]
SciNameCollectionType = dict[str, str]
