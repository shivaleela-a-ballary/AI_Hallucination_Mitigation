"""
Uploads and Document Ingestion API Router.
Handles file uploads (PDF, TXT, MD, CSV, JSON) and direct text passage ingestion.
Persists metadata & chunks in MongoDB, and exposes them to multi-source evidence retrieval.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from api.db.mongodb import db_manager
from api.dependencies import get_current_user_optional
from retrieval.document_parser import chunk_text, extract_text_from_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/uploads", tags=["Document Ingestion"])


class TextUploadRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    content: str = Field(..., min_length=10)
    source_name: Optional[str] = Field(default="Custom Document")


def _get_user_info(user: Optional[Any]) -> tuple[Optional[str], str]:
    if not user:
        return None, "guest"
    if isinstance(user, dict):
        return user.get("id"), user.get("username", "guest")
    return getattr(user, "id", None), getattr(user, "username", "guest")


@router.post("/file", status_code=status.HTTP_201_CREATED)
async def upload_document_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    user: Optional[Any] = Depends(get_current_user_optional),
):
    """
    Ingest and parse an uploaded document file (.pdf, .txt, .md, .csv, .json).
    Splits content into evidence chunks and indexes it into the multi-source pipeline.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing.")

    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Max size: 25MB
    if len(content_bytes) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 25MB limit.")

    extracted_text = extract_text_from_file(file.filename, content_bytes)
    if not extracted_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Unable to extract readable text content from the uploaded file.",
        )

    doc_title = title.strip() if title and title.strip() else file.filename
    chunks = chunk_text(extracted_text, title=doc_title)
    user_id, user_name = _get_user_info(user)

    doc_id = str(uuid4())
    doc_record = {
        "id": doc_id,
        "filename": file.filename,
        "title": doc_title,
        "file_size": len(content_bytes),
        "file_type": file.filename.split(".")[-1].lower() if "." in file.filename else "text",
        "char_count": len(extracted_text),
        "chunk_count": len(chunks),
        "chunks": chunks,
        "raw_text_preview": extracted_text[:500] + ("..." if len(extracted_text) > 500 else ""),
        "user_id": user_id,
        "user_name": user_name,
    }

    saved = db_manager.save_uploaded_document(doc_record)
    logger.info("Successfully ingested document '%s' with %d chunks (ID: %s)", file.filename, len(chunks), doc_id)

    return {
        "message": f"Successfully ingested and indexed '{file.filename}' into evidence store.",
        "document": saved,
    }


@router.post("/text", status_code=status.HTTP_201_CREATED)
def upload_raw_text(
    payload: TextUploadRequest,
    user: Optional[Any] = Depends(get_current_user_optional),
):
    """
    Ingest a raw text article or study excerpt directly.
    """
    chunks = chunk_text(payload.content, title=payload.title)
    if not chunks:
        raise HTTPException(status_code=400, detail="Content is too short or empty.")

    user_id, user_name = _get_user_info(user)
    doc_id = str(uuid4())
    doc_record = {
        "id": doc_id,
        "filename": f"{payload.title[:30]}.txt",
        "title": payload.title,
        "file_size": len(payload.content.encode("utf-8")),
        "file_type": "text",
        "char_count": len(payload.content),
        "chunk_count": len(chunks),
        "chunks": chunks,
        "raw_text_preview": payload.content[:500] + ("..." if len(payload.content) > 500 else ""),
        "user_id": user_id,
        "user_name": user_name,
    }

    saved = db_manager.save_uploaded_document(doc_record)
    return {
        "message": f"Successfully ingested '{payload.title}' with {len(chunks)} evidence chunk(s).",
        "document": saved,
    }


@router.get("")
def list_uploaded_documents(user: Optional[Any] = Depends(get_current_user_optional)):
    """
    List all ingested documents available in the evidence store.
    """
    documents = db_manager.get_uploaded_documents()
    return {
        "total": len(documents),
        "documents": documents,
    }


@router.get("/{document_id}")
def get_uploaded_document(
    document_id: str,
    user: Optional[Any] = Depends(get_current_user_optional),
):
    """
    Get detailed information and all parsed chunks of a specific ingested document.
    """
    doc = db_manager.get_uploaded_document_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.delete("/{document_id}")
def delete_uploaded_document(
    document_id: str,
    user: Optional[Any] = Depends(get_current_user_optional),
):
    """
    Delete an ingested document and remove its passages from the active evidence store.
    """
    deleted = db_manager.delete_uploaded_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found or already deleted.")
    return {
        "message": "Document successfully deleted from evidence store.",
        "id": document_id,
    }
