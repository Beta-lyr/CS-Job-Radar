from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RawJobDTO(BaseModel):
    source_url: str
    raw_title: Optional[str] = None
    raw_company: Optional[str] = None
    raw_city: Optional[str] = None
    raw_salary: Optional[str] = None
    raw_education: Optional[str] = None
    raw_experience: Optional[str] = None
    raw_description: Optional[str] = None
    publish_date: Optional[datetime] = None


class BaseParser(ABC):
    @abstractmethod
    def parse_list(self, html: str, base_url: str) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def parse_detail(self, html: str, url: str) -> RawJobDTO:
        raise NotImplementedError
