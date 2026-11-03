import os
from functools import lru_cache

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


@lru_cache
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    solr_dev_url: HttpUrl
    solr_prod_url: HttpUrl
    bbox_dev_url: HttpUrl
    bbox_prod_url: HttpUrl

    taxo_path: str = "/taxo/select"
    addi_path: str = "/addi/select"

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
