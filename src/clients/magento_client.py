import requests
from src.config import settings

class MagentoClient:
    def __init__(self):
        self.base_url = settings.magento_base_url.rstrip("/")
        self.username = settings.magento_admin_username
        self.password = settings.magento_admin_password
        self.store_code = settings.magento_store_code

    def get_admin_token(self) -> str:
        if not self.base_url:
            return ""
        url = f"{self.base_url}/rest/V1/integration/admin/token"
        response = requests.post(url, json={"username": self.username, "password": self.password}, timeout=30)
        response.raise_for_status()
        return response.json()

    def update_product_content(self, sku: str, title: str, long_description: str) -> dict:
        token = self.get_admin_token()
        if not token:
            return {"status": "demo_stub_only", "sku": sku}
        url = f"{self.base_url}/rest/V1/products/{sku}"
        payload = {
            "product": {
                "sku": sku,
                "name": title,
                "custom_attributes": [
                    {"attribute_code": "description", "value": long_description}
                ]
            }
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
