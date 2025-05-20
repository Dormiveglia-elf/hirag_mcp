from abc import ABC, abstractmethod
from typing import List


class BaseSummarizer(ABC):
    @abstractmethod
    def summarize_entity(self, entity_name: str, descriptions: List[str]) -> str:
        pass
