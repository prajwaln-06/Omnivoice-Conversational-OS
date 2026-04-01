# backend/ai/rag.py
# Pranav's AI layer — delegates to Sinchana's RAG pipeline

import asyncio
import logging
logger = logging.getLogger(__name__)

try:
    from rag_pipeline.rag import get_context as _sinchana_get_context
    RAG_AVAILABLE = True
    logger.info("[RAG] Sinchana's RAG pipeline loaded successfully")
except ImportError as e:
    RAG_AVAILABLE = False
    logger.warning(f"[RAG] Could not load rag_pipeline: {e}")


async def get_context(query: str, domain: str) -> str:
    """
    Wrapper around Sinchana's get_context.
    Returns relevant context string for LLM injection.
    NEVER raises exceptions — returns "" on any failure.
    Called by Prajwal's analyze route.
    """
    if not RAG_AVAILABLE:
        return ""
    try:
        if len(query) > 1200:
            chunk_size = 1000
            chunks = [query[i : i + chunk_size] for i in range(0, len(query), chunk_size)]
            tasks = [asyncio.create_task(_sinchana_get_context(chunk, domain)) for chunk in chunks]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            sanitized = [res for res in results if isinstance(res, str) and res and res != "..."]
            combined = "\n".join(sanitized)
            return combined if combined else ""

        result = await _sinchana_get_context(query, domain)
        return result if result and result != "..." else ""
    except Exception as e:
        logger.error(f"[RAG] get_context failed: {e}")
        return ""


if __name__ == "__main__":
    import asyncio

    print("Testing healthcare context...")
    r1 = asyncio.run(get_context("patient has fever and headache", "healthcare"))
    print(r1 if r1 else "Empty — ChromaDB may need ingestion")

    print("\nTesting banking context...")
    r2 = asyncio.run(get_context("home loan 40 lakhs", "banking"))
    print(r2 if r2 else "Empty — ChromaDB may need ingestion")