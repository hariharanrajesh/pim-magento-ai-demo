from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex, SimpleField, SearchableField, SearchFieldDataType
from src.config import settings

client = SearchIndexClient(endpoint=settings.azure_search_endpoint, credential=AzureKeyCredential(settings.azure_search_api_key))
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="title", type=SearchFieldDataType.String),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SearchableField(name="tags", type=SearchFieldDataType.String),
]
index = SearchIndex(name=settings.azure_search_index, fields=fields)
client.create_or_update_index(index)
print(f"Index ready: {settings.azure_search_index}")
