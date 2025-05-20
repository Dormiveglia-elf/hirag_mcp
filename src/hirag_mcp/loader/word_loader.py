from langchain_community import document_loaders
from hirag_mcp.loader.base_loader import BaseLoader
from hirag_mcp.loader.markify_loader import markify_client


class WordLoader(BaseLoader):
    def __init__(self):
        self.loader_type = document_loaders.UnstructuredWordDocumentLoader
        self.loader_markify = markify_client
