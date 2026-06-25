"""RAG lookup over SBI product catalog using ChromaDB."""

from __future__ import annotations

from typing import Any

import chromadb
from chromadb.utils import embedding_functions

from config import settings
from data.sbi_products import SBI_PRODUCTS

COLLECTION_NAME = "sbi_products"
_chroma_client: chromadb.ClientAPI | None = None
_collection = None


def _get_collection():
    global _chroma_client, _collection
    if _collection is not None:
        return _collection

    _chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    kwargs: dict = {"name": COLLECTION_NAME, "metadata": {"hnsw:space": "cosine"}}
    if settings.openai_api_key:
        kwargs["embedding_function"] = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name="text-embedding-3-small",
        )
    _collection = _chroma_client.get_or_create_collection(**kwargs)
    return _collection


def ingest_products(force: bool = False) -> int:
    collection = _get_collection()
    if collection.count() > 0 and not force:
        return collection.count()

    if force and collection.count() > 0:
        ids = collection.get()["ids"]
        if ids:
            collection.delete(ids=ids)

    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []
    ids: list[str] = []

    for idx, product in enumerate(SBI_PRODUCTS):
        doc = (
            f"{product['name']}. {product['description']} "
            f"Target life event: {product['target_life_event']}. "
            f"Benefits: {', '.join(product['key_benefits'])}"
        )
        documents.append(doc)
        metadatas.append(
            {
                "name": product["name"],
                "description": product["description"],
                "target_life_event": product["target_life_event"],
                "key_benefits": ", ".join(product["key_benefits"]),
                "cta_link": product["cta_link"],
            }
        )
        ids.append(f"product_{idx}")

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    return len(ids)


def _fallback_lookup(life_event: str, top_k: int = 2) -> list[dict[str, Any]]:
    matched = [p for p in SBI_PRODUCTS if p["target_life_event"] == life_event]
    if not matched:
        matched = SBI_PRODUCTS[:top_k]
    return [
        {
            "name": p["name"],
            "description": p["description"],
            "target_life_event": p["target_life_event"],
            "key_benefits": p["key_benefits"],
            "cta_link": p["cta_link"],
            "relevance_score": 1.0,
        }
        for p in matched[:top_k]
    ]


def rag_lookup(life_event: str, top_k: int = 2) -> list[dict[str, Any]]:
    if not settings.openai_api_key:
        return _fallback_lookup(life_event, top_k)

    collection = _get_collection()
    if collection.count() == 0:
        ingest_products()

    query = f"Best SBI banking product recommendation for life event: {life_event}"
    results = collection.query(query_texts=[query], n_results=top_k)

    products: list[dict[str, Any]] = []
    if not results["metadatas"] or not results["metadatas"][0]:
        return products

    for meta, distance in zip(results["metadatas"][0], results["distances"][0]):
        products.append(
            {
                "name": meta["name"],
                "description": meta["description"],
                "target_life_event": meta["target_life_event"],
                "key_benefits": meta["key_benefits"].split(", "),
                "cta_link": meta["cta_link"],
                "relevance_score": round(1 - distance, 4),
            }
        )

    return products
