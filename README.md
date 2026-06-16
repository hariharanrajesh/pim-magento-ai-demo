# Magento-first PIM GenAI Demo (Azure Functions + Azure OpenAI + Azure AI Search + AKS + Python)

This bundle is a **proposed Magento-focused demo** for the case study **Intelligent Product Content Generation for eCommerce PIM Optimization**.

## What this demo does
1. A product create/update payload is sent to **Azure Functions**.
2. Azure Functions forwards the payload to a **FastAPI orchestrator**.
3. The orchestrator retrieves brand/SEO guidance from **Azure AI Search**.
4. The orchestrator calls **Azure OpenAI** to generate:
   - product title refinements
   - feature bullets
   - long description
   - SEO keywords
5. The content is stored in a lightweight approval queue.
6. A **Magento (Adobe Commerce) client stub** can push approved content back to Commerce by REST API.

## Project structure
```text
pim_magento_demo/
├── README.md
├── requirements.txt
├── .env.example
├── sample_data/
├── src/
├── function_app/
├── scripts/
├── deployment/
└── tests/
```

## Local prerequisites
- Python 3.11+
- Azure CLI
- Azure Functions Core Tools v4
- Docker Desktop (optional)
- kubectl (for AKS deployment)

## 1) Local setup
### Create virtual environment
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1
```

### Install packages
```bash
pip install -r requirements.txt
```

### Create environment file
```bash
cp .env.example .env
```
Populate the Azure OpenAI, Azure AI Search, and Magento values.

## 2) Start the API locally
```bash
uvicorn src.app:app --reload --port 8000
```

## 3) Seed Azure AI Search with sample guidance
```bash
python scripts/bootstrap_search_index.py
python scripts/seed_guidance.py
```

## 4) Test generation directly
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d @sample_data/magento_product.json
```

## 5) Inspect approvals
```bash
curl http://localhost:8000/approvals
```

## 6) Run the Azure Function locally
```bash
cd function_app
func start
```
Trigger the function:
```bash
curl -X POST http://localhost:7071/api/magento_product_event \
  -H "Content-Type: application/json" \
  -d @../sample_data/magento_product.json
```

## 7) Compile / validate
```bash
python -m compileall src function_app scripts tests
pytest -q
```

## 8) Docker build
```bash
docker build -t pim-magento-demo:latest -f deployment/Dockerfile .
```

## 9) Proposed AKS deployment
```bash
az group create --name rg-pim-magento-demo --location centralindia
az aks create --resource-group rg-pim-magento-demo --name aks-pim-magento-demo --node-count 1 --enable-managed-identity --generate-ssh-keys
az aks get-credentials --resource-group rg-pim-magento-demo --name aks-pim-magento-demo
kubectl apply -f deployment/aks/namespace.yaml
kubectl apply -f deployment/aks/secret.example.yaml
kubectl apply -f deployment/aks/deployment.yaml
kubectl apply -f deployment/aks/service.yaml
kubectl get svc -n pim-magento-demo
```

## 10) Proposed Function App deployment
```bash
az storage account create --name stpimmagentodemo123 --location centralindia --resource-group rg-pim-magento-demo --sku Standard_LRS
az functionapp create --resource-group rg-pim-magento-demo --consumption-plan-location centralindia --runtime python --runtime-version 3.11 --functions-version 4 --name func-pim-magento-demo --storage-account stpimmagentodemo123
cd function_app
func azure functionapp publish func-pim-magento-demo --python
az functionapp config appsettings set --name func-pim-magento-demo --resource-group rg-pim-magento-demo --settings ORCHESTRATOR_API_URL=http://<API-URL>/generate
```

## 11) Magento-specific demo flow
1. Use `sample_data/magento_product.json` as the incoming product payload.
2. Trigger `/api/magento_product_event` or `/generate`.
3. Review the generated content.
4. Optionally call `/publish/{sku}` after you populate Magento credentials in `.env`.
5. Show the updated payload that would be sent to Adobe Commerce.

## 12) Notes
- The Magento write-back uses a **demo-safe client** with REST authentication and update methods separated into one client file.
- Keep approval in the loop for the demo.
- If you want a storefront-side demo, you can extend this with GraphQL query examples later.
