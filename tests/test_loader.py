import os


from hirag_mcp.loader import load_document


def test_load_pdf():
    document_path = f"{os.path.dirname(__file__)}/Guide-to-U.S.-Healthcare-System.pdf"
    content_type = "application/pdf"
    document_meta = {
        "type": "pdf",
        "filename": "Guide-to-U.S.-Healthcare-System.pdf",
        "uri": document_path,
        "private": False,
    }
    loader_configs = None
    documents = load_document(
        document_path, content_type, document_meta, loader_configs
    )
    assert len(documents) > 0
    assert documents[0].page_content is not None
    assert documents[0].metadata is not None
    assert documents[0].id.startswith("doc-")
