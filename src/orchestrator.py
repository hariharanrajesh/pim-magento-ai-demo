from src.models import MagentoProductPayload, GeneratedContent
from src.clients.azure_openai_client import AzureOpenAIClient
from src.clients.azure_search_client import AzureSearchClient
from src.prompting import build_generation_prompt
from src.workflows.approval_store import ApprovalStore

class ContentOrchestrator:
    def __init__(self):
        self.ai = AzureOpenAIClient()
        self.search = AzureSearchClient()
        self.approvals = ApprovalStore()

    def generate(self, product: MagentoProductPayload) -> GeneratedContent:
        query = f"{product.brand} {product.category} {product.name} SEO approved content Magento"
        guidance = self.search.retrieve_guidance(query)
        prompt = build_generation_prompt(product.model_dump(), guidance)
        generated = self.ai.generate_structured_content(prompt)
        content = GeneratedContent(
            title=generated["title"],
            bullets=generated["bullets"],
            long_description=generated["long_description"],
            seo_keywords=generated["seo_keywords"],
            guidance_used=[g["title"] for g in guidance if g.get("title")],
        )
        self.approvals.save_pending({
            "sku": product.sku,
            "status": "PENDING_APPROVAL",
            "generated": content.model_dump(),
        })
        return content
