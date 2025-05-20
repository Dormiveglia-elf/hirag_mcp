import os
from hirag_mcp import HiRAG
import asyncio

async def index():
    index = await HiRAG.create()
    document_path = f"tests/Guide-to-U.S.-Healthcare-System.pdf"
    content_type = "application/pdf"
    document_meta = {
        "type": "pdf",
        "filename": "Guide-to-U.S.-Healthcare-System.pdf",
        "uri": document_path,
        "private": False,
    }
    await index.insert_to_kb(
        document_path=document_path,
        content_type=content_type,
        document_meta=document_meta,
    )

if __name__ == "__main__":
    asyncio.run(index())
