from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, List


@dataclass
class BaseEntity(ABC):
    extract_func: Callable
    entity_extract_prompt: str

    @abstractmethod
    def entity(self, text: str) -> List[str]:
        pass
