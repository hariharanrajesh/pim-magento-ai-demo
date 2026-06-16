def build_generation_prompt(product: dict, guidance_chunks: list[dict]) -> str:
    guidance_text = "\n\n".join([f"[{g.get('title', 'guidance')}] {g.get('content', '')}" for g in guidance_chunks])
    attrs = "\n".join([f"- {k}: {v}" for k, v in product.get("attributes", {}).items()])
    return f"""
You are generating eCommerce product content for Adobe Commerce / Magento.
Create content suitable for catalog publishing.

Product:
- sku: {product.get('sku')}
- name: {product.get('name')}
- brand: {product.get('brand')}
- category: {product.get('category')}
- market: {product.get('market')}
Attributes:
{attrs}

Guidance:
{guidance_text}

Return strict JSON with keys only:
{{
  "title": "string",
  "bullets": ["string", "string", "string", "string", "string"],
  "long_description": "string",
  "seo_keywords": ["string", "string", "string", "string", "string"]
}}
""".strip()
