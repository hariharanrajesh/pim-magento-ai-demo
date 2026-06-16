import json
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from src.config import settings

with open("sample_data/guidance.json", "r", encoding="utf-8") as f:
    docs = json.load(f)
client = SearchClient(endpoint=settings.azure_search_endpoint, index_name=settings.azure_search_index, credential=AzureKeyCredential(settings.azure_search_api_key))
client.upload_documents(docs)
print(f"Seeded {len(docs)} guidance docs")
