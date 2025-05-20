from typing import Literal, Optional

from langchain_core.documents import Document
from pydantic import BaseModel


class FileMetadata(BaseModel):
    type: Literal[
        "pdf",
        "docx",
        "pptx",
        "xlsx",
        "jpg",
        "png",
        "zip",
        "txt",
        "csv",
        "text",
        "tsv",
        "html",
    ]
    filename: str
    page_number: Optional[int] = None
    # The uri of the file
    # When the file is a local file, the uri is the path to the file
    # When the file is a remote file, the uri is the url of the file
    uri: str
    # Whether the file is private
    private: bool = False


class File(Document, BaseModel):
    # "file-mdhash(filename)"
    id: str
    # The content of the file
    page_content: str
    # The metadata of the file
    metadata: FileMetadata
