from abc import ABC, abstractmethod


class BaseFetcher(ABC):
    @abstractmethod
    def fetch(self, url: str) -> str:
        raise NotImplementedError
