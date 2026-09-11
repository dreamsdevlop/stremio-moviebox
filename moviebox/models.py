from datetime import date
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class PagerModel(BaseModel):
    has_more: bool = Field(alias="hasMore", default=False)
    next_page: int = Field(alias="nextPage", default=1)
    page: int = 1

class SubjectModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    subject_id: str = Field(alias="subjectId")
    title: str
    release_date: date | str = Field(alias="releaseDate", default="1970-01-01")
    corner: str = ""

    @property
    def year(self) -> str:
        if isinstance(self.release_date, date):
            return str(self.release_date.year)
        if isinstance(self.release_date, str) and "-" in self.release_date:
            return self.release_date.split("-")[0]
        return ""

class SearchResultsModel(BaseModel):
    pager: PagerModel
    items: list[SubjectModel] = Field(default_factory=list)

class VideoFileModel(BaseModel):
    resolution: int = 0
    size: int = 0
    url: HttpUrl = Field(alias="resourceLink")
    source_url: str = Field(alias="sourceUrl", default="")
    se: int = 1
    ep: int = 1
    
class DownloadableFilesModel(BaseModel):
    pager: PagerModel
    file_list: list[VideoFileModel] = Field(alias="list", default_factory=list)
