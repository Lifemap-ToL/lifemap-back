import os
from functools import lru_cache
from pathlib import Path

from pydantic import HttpUrl, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict

from api.lib.types import LangType, TreeName

# Use absolute path to .env for pytest
BASE_DIR = Path(__file__).resolve().parent.parent.parent


@lru_cache
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")
    solr_dev_url: HttpUrl
    solr_prod_url: HttpUrl
    bbox_dev_url: HttpUrl
    bbox_prod_url: HttpUrl

    rows: PositiveInt = 10_000

    taxo_path: str = "/taxo/select"
    addi_path: str = "/addi/select"
    suggester_path: dict[LangType, str] = {
        LangType.en: "/taxo/suggesthandler",
        LangType.fr: "/taxo/suggesthandlerfr",
        LangType.de: "/taxo/suggesthandlerde",
        LangType.es: "/taxo/suggesthandleres",
        LangType.el: "/taxo/suggesthandlerel",
    }
    suggester_name: dict[LangType, str] = {
        LangType.en: "mySuggester",
        LangType.fr: "mySuggesterFr",
        LangType.de: "mySuggesterDe",
        LangType.es: "mySuggesterEs",
        LangType.el: "mySuggesterEl",
    }
    metadata_path: dict[TreeName, Path] = {TreeName.ncbi: Path("/static/metadata.json")}

    @property
    def solr_url(self) -> str:
        base_url: HttpUrl = (
            self.solr_dev_url if os.getenv("FASTAPI_ENV") == "development" else self.solr_prod_url
        )
        # HttpUrl typing ensures there is a trailing slash
        return f"{base_url!s}solr"

    @property
    def solr_taxo_url(self) -> str:
        return f"{self.solr_url}/taxo"

    @property
    def solr_addi_url(self) -> str:
        return f"{self.solr_url}/addi"

    @property
    def bbox_url(self) -> str:
        if os.getenv("FASTAPI_ENV") == "development":
            return str(self.bbox_dev_url)
        else:
            return str(self.bbox_prod_url)
