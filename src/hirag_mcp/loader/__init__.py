import time
from typing import List, Optional, Union, Literal

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

from hirag_mcp.schema import File

from .csv_loader import CSVLoader
from .excel_loader import ExcelLoader
from .html_loader import HTMLLoader
from .pdf_loader import PDFLoader
from .ppt_loader import PowerPointLoader
from .word_loader import WordLoader


DEFAULT_LOADER_CONFIGS = {
    "application/pdf": {
        "loader": PDFLoader,
        "args": {
            # TODO(tatiana): tune the args?
        },
        "init_args": {
            "max_output_docs": 5,
        },
    },
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
        "loader": WordLoader,
        "args": {
            # TODO(tatiana): tune the args?
        },
    },
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": {
        "loader": PowerPointLoader,
        "args": {"mode": "single", "strategy": "fast"},
    },
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
        "loader": ExcelLoader,
        "args": {
            # TODO(tatiana): tune the args?
        },
    },
    "text/html": {
        "loader": HTMLLoader,
        "args": {},
    },
    "text/csv": {
        "loader": CSVLoader,
        "args": {},
    },
}


# TODO(hhy): add a arg to decide whether to use markify or not
def load_document(
    document_path: str,
    content_type: str,
    document_meta: Optional[dict] = None,
    loader_configs: Optional[dict] = None,
    loader_type: Literal["mineru", "langchain"] = "mineru",
) -> List[File]:
    """Load a document from the given path and content type

    Args:
        document_path (str): The path to the document.
        content_type (str): The content type of the document.
        document_meta (Optional[dict]): The metadata of the document.
        loader_configs (Optional[dict]): If unspecified, use DEFAULT_LOADER_CONFIGS.

    Raises:
        ValueError: If the content type is not supported.

    Returns:
        List[File]: The loaded documents.
    """
    if loader_configs is None:
        loader_configs = DEFAULT_LOADER_CONFIGS

    if content_type not in loader_configs:
        raise ValueError(f"Unsupported document type: {content_type}")
    loader_conf = loader_configs[content_type]
    if "init_args" in loader_conf:
        loader = loader_conf["loader"](**loader_conf["init_args"])
    else:
        loader = loader_conf["loader"]()

    if loader_type == "langchain":
        if "args" in loader_conf:
            raw_docs = loader.load(document_path, document_meta, **loader_conf["args"])
        else:
            raw_docs = loader.load(document_path, document_meta)
    elif loader_type == "mineru":
        raw_docs = loader.load_markify(document_path, document_meta, "advanced")
    else:
        raise ValueError(
            f"Unsupported loader type: {loader_type}, should be one of ['mineru', 'langchain']"
        )
    return raw_docs


__all__ = [
    "PowerPointLoader",
    "PDFLoader",
    "WordLoader",
    "ExcelLoader",
    "load_document",
    "HTMLLoader",
    "CSVLoader",
]
