from fastapi import FastAPI, HTTPException
from src.models import MagentoProductPayload
from src.orchestrator import ContentOrchestrator
from src.workflows.approval_store import ApprovalStore
from src.clients.magento_client import MagentoClient

app = FastAPI(title="Magento PIM GenAI Demo API", version="1.0.0")
orchestrator = ContentOrchestrator()
store = ApprovalStore()
magento = MagentoClient()

@app.get("/")
def root():
    return {"status": "OK", "message": "FastAPI running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/generate")
def generate(payload: MagentoProductPayload):
    return orchestrator.generate(payload)

@app.get("/approvals")
def approvals():
    return store.list_all()

@app.post("/publish/{sku}")
def publish_to_magento(sku: str):
    record = store.latest_for_sku(sku)
    if not record:
        raise HTTPException(status_code=404, detail="No approval record found for SKU")
    generated = record["generated"]
    result = magento.update_product_content(sku, generated["title"], generated["long_description"])
    return {"sku": sku, "publish_result": result}
