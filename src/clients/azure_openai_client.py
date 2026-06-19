import json
from openai import AzureOpenAI # type: ignore
from src.config import settings

class AzureOpenAIClient:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )

    def generate_structured_content(self, prompt: str) -> dict:
        response = self.client.chat.completions.create(
            model=settings.azure_openai_chat_deployment,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You generate structured JSON for product content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
        )
        return json.loads(response.choices[0].message.content)
