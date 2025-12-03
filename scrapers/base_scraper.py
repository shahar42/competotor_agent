from abc import ABC, abstractmethod
from typing import List, Dict

class BaseScraper(ABC):
    @abstractmethod
    def search(self, keywords: str) -> List[Dict]:
        """
        Returns list of products:
        [{"name": str, "url": str, "price": float, "description": str}, ...]
        """
        pass
