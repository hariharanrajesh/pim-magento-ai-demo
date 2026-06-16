from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class MagentoProductPayload(BaseModel):
    sku: str
    name: str
    brand: str
    category: str
    short_description: Optional[str] = ""
    description: Optional[str] = ""
    attributes: Dict[str, str] = Field(default_factory=dict)
    market: Optional[str] = "US"

class GeneratedContent(BaseModel):
    title: str
    bullets: List[str]
    long_description: str
    seo_keywords: List[str]
    approval_required: bool = True
    guidance_used: List[str] = Field(default_factory=list)
