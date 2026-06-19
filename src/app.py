"""
Application: GenAI PIM Optimization Service
Author: Rajesh H (Sr. Architect - Technology)
Date: <2026-06-15>

Description:
This application provides AI-powered services for Product Information Management (PIM),
including content generation, enrichment, and retrieval using Retrieval-Augmented Generation (RAG).

Key Features:
- Product description generation using LLM
- Semantic search using embeddings
- Integration with vector database
- REST API endpoints for client consumption

Architecture Overview:
- FastAPI-based REST service
- LLM integration (OpenAI / Azure OpenAI)
- Vector store for semantic retrieval
- Modular service layer for business logic

Usage:
Run the application using:
    uvicorn app:app --reload

Dependencies:
- fastapi
- uvicorn
- openai / azure-ai
- langchain (optional)

"""
from fastapi import FastAPI, HTTPException # type: ignore
from src.models import MagentoProductPayload
from src.orchestrator import ContentOrchestrator
from src.workflows.approval_store import ApprovalStore
from src.clients.magento_client import MagentoClient
import logging

app = FastAPI(title="Magento PIM GenAI Demo API", version="1.0.0")
orchestrator = ContentOrchestrator()
store = ApprovalStore()
magento = MagentoClient()

logger = logging.getLogger(__name__)

@app.get("/")
def root():
    logger.debug("Root endpoint called")
    return {"status": "ok", "message": "FastAPI running"}

@app.get("/health")
def health():
    logger.debug("Health check endpoint called")
    return {"status": "ok"}

@app.post("/generate")
def generate(payload: MagentoProductPayload):
    logger.info(f"Generate request for SKU: {payload.sku}")
    try:
        result = orchestrator.generate(payload)
        logger.info(f"Successfully generated content for SKU: {payload.sku}")
        return result
    except ValueError as e:
        logger.warning(f"Validation error for SKU {payload.sku}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating content for SKU {payload.sku}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Content generation failed")

@app.get("/approvals")
def approvals():
    logger.debug("Fetching all approvals")
    return store.list_all()

@app.post("/publish/{sku}")
def publish_to_magento(sku: str):
    # Validate SKU
    if not sku or not sku.strip():
        logger.warning("Publish attempt with empty SKU")
        raise HTTPException(status_code=400, detail="SKU cannot be empty")

    sku = sku.strip()
    logger.info(f"Publishing product with SKU: {sku}")

    # Fetch record
    record = store.latest_for_sku(sku)
    if not record:
        logger.warning(f"No approval record found for SKU: {sku}")
        raise HTTPException(status_code=404, detail=f"No approval record found for SKU: {sku}")

    try:
        # Extract and validate record structure
        generated = record.get("generated")
        if not generated or not isinstance(generated, dict):
            logger.error(f"Invalid record structure for SKU: {sku}")
            raise HTTPException(status_code=500, detail="Invalid approval record format")

        # Extract and validate content
        title = generated.get("title", "").strip()
        long_description = generated.get("long_description", "").strip()

        if not title or not long_description:
            logger.warning(f"Missing content fields for SKU: {sku}")
            raise HTTPException(status_code=400, detail="Missing title or description in approval record")

        # Publish to Magento
        result = magento.update_product_content(sku, title, long_description)
        logger.info(f"Successfully published SKU {sku} to Magento")
        return {"sku": sku, "publish_result": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish SKU {sku}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to publish to Magento")
