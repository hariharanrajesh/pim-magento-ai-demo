from azure.core.credentials import AzureKeyCredential # type: ignore
from azure.search.documents import SearchClient # type: ignore
from src.config import settings

class AzureSearchClient:
    def __init__(self):
        self.client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_search_index,
            credential=AzureKeyCredential(settings.azure_search_api_key),
        )

    def retrieve_guidance(self, query: str, top_k: int | None = None):
        results = self.client.search(search_text=query, top=top_k or settings.default_top_k)
        return [{
            "id": item.get("id"),
            "title": item.get("title"),
            "content": item.get("content"),
            "tags": item.get("tags")
        } for item in results]
