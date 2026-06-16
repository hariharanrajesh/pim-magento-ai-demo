import json
import logging
import os
import requests
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="magento_product_event", methods=["POST"])
def magento_product_event(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Received Magento product event")
    try:
        payload = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON", status_code=400)

    api_url = os.getenv("ORCHESTRATOR_API_URL", "http://localhost:8000/generate")
    response = requests.post(api_url, json=payload, timeout=60)
    return func.HttpResponse(
        body=json.dumps(response.json()),
        status_code=response.status_code,
        mimetype="application/json",
    )
