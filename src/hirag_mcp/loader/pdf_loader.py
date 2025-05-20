import warnings
from typing import List

from langchain_community import document_loaders
from hirag_mcp.loader.base_loader import BaseLoader
from hirag_mcp.loader.markify_loader import markify_client

from hirag_mcp._utils import compute_mdhash_id
from hirag_mcp.schema import File

# Suppress PyPDF warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pypdf")


class PDFLoader(BaseLoader):
    """Loads PDF documents"""

    def __init__(self, max_output_docs: int = 5):
        self.loader_type = document_loaders.PyPDFLoader
        self.loader_markify = markify_client
        self.max_output_docs = max_output_docs

    def _load(self, document_path: str, **loader_args) -> List[File]:
        raw_docs = self.loader_type(document_path, **loader_args).load()
        return raw_docs

    def _set_doc_metadata(self, files: List[File], document_meta: dict) -> List[File]:
        for doc in files:
            document_meta[self.page_number_key] = doc.metadata[self.page_number_key]
            doc.metadata = document_meta
            doc.id = compute_mdhash_id(doc.page_content.strip(), prefix="doc-")
