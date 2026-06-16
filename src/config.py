from pydantic import BaseModel
from dotenv import load_dotenv
import os
load_dotenv()

class Settings(BaseModel):
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_chat_deployment: str = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    azure_search_endpoint: str = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    azure_search_api_key: str = os.getenv("AZURE_SEARCH_API_KEY", "")
    azure_search_index: str = os.getenv("AZURE_SEARCH_INDEX", "magento-guidance-index")
    default_top_k: int = int(os.getenv("DEFAULT_TOP_K", "3"))
    approval_store_path: str = os.getenv("APPROVAL_STORE_PATH", "./sample_data/approvals.json")
    magento_base_url: str = os.getenv("MAGENTO_BASE_URL", "")
    magento_admin_username: str = os.getenv("MAGENTO_ADMIN_USERNAME", "")
    magento_admin_password: str = os.getenv("MAGENTO_ADMIN_PASSWORD", "")
    magento_store_code: str = os.getenv("MAGENTO_STORE_CODE", "default")

settings = Settings()
