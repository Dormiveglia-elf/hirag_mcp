from abc import ABC, abstractmethod


class BaseChunk(ABC):
    @abstractmethod
    def chunk(self, text: str) -> list[str]:
        pass
