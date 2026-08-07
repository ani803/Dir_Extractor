from abc import ABC, abstractmethod

from models import Company
from search.search_result import SearchResult


class BaseProvider(ABC):

    result_class = SearchResult

    @abstractmethod
    def search(self, company: Company) -> SearchResult:
        pass