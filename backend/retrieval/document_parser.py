"""
Document Parsing and Passage Chunking for Ingestion.
Supports PDF, TXT, Markdown, CSV, and JSON formats.
Includes strict binary/garbage rejection and text validation to prevent corrupted claims.
"""

from __future__ import annotations

import io
import json
import logging
import re
from typing import BinaryIO

logger = logging.getLogger(__name__)


def is_valid_claim_text(text: str) -> bool:
    """
    Validate that text constitutes human-readable prose suitable for factual claim analysis.
    Rejects binary markers (%PDF-, etc.), control characters, and non-prose gibberish.
    """
    if not text or not isinstance(text, str):
        return False

    clean = text.strip()
    if len(clean) < 15:
        return False

    # Check for obvious binary or PDF stream signatures
    if clean.startswith("%PDF") or "\x00" in clean or "obj <<" in clean or "endobj" in clean:
        return False

    # Check printable character ratio (reject binary streams decoded as text)
    printable_count = sum(1 for c in clean if c.isprintable())
    if printable_count / max(len(clean), 1) < 0.85:
        return False

    # Must contain at least 3 legitimate words with alphabetic characters
    words = [w for w in clean.split() if any(c.isalpha() for c in w)]
    if len(words) < 3:
        return False

    return True


def extract_text_from_file(filename: str, content_bytes: bytes) -> str:
    """
    Extract clean, human-readable text content from various file types.
    Never returns raw binary byte streams for PDFs or other documents.
    """
    lower_name = filename.lower()

    # 1. PDF
    if lower_name.endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            pages = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    pages.append(f"--- Page {i + 1} ---\n{page_text.strip()}")
            extracted = "\n\n".join(pages)
            if extracted.strip():
                return extracted
            logger.warning("pypdf extracted zero text pages from %s (may be scanned image PDF).", filename)
            return ""
        except Exception as err:
            logger.warning("Failed to extract PDF text with pypdf from %s: %s", filename, err)
            # NEVER fall back to raw binary bytes for PDFs
            return ""

    # 2. JSON
    if lower_name.endswith(".json"):
        try:
            data = json.loads(content_bytes.decode("utf-8", errors="ignore"))
            if isinstance(data, list):
                return "\n\n".join(
                    json.dumps(item, indent=2) if isinstance(item, dict) else str(item)
                    for item in data
                )
            elif isinstance(data, dict):
                lines = []
                for k, v in data.items():
                    lines.append(f"## {k}\n{v if isinstance(v, str) else json.dumps(v, indent=2)}")
                return "\n\n".join(lines)
            return json.dumps(data, indent=2)
        except Exception:
            return ""

    # 3. CSV
    if lower_name.endswith(".csv"):
        try:
            text = content_bytes.decode("utf-8", errors="ignore")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            return "\n".join(lines)
        except Exception:
            return ""

    # 4. Images (PNG, JPG, JPEG, WEBP, BMP, TIFF, GIF)
    image_extensions = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif")
    if any(lower_name.endswith(ext) for ext in image_extensions):
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(content_bytes))
            ocr_text = ""
            try:
                import pytesseract
                ocr_text = pytesseract.image_to_string(img).strip()
            except Exception as ocr_err:
                logger.debug("Tesseract OCR not configured or failed: %s", ocr_err)

            if ocr_text:
                return f"[Extracted Text from Image '{filename}']:\n{ocr_text}"
            else:
                return (
                    f"Uploaded Image Asset: {filename}\n"
                    f"Format: {img.format}, Dimensions: {img.width}x{img.height} px, Mode: {img.mode}.\n"
                    f"Evidence ingested from visual diagram / screenshot: '{filename}'."
                )
        except Exception as img_err:
            logger.warning("Error processing image file %s: %s", filename, img_err)
            return f"Uploaded image asset: {filename}. Content indexed for evidence reference."

    # 5. Plain Text & Markdown
    try:
        decoded = content_bytes.decode("utf-8")
        if is_valid_claim_text(decoded):
            return decoded
        return ""
    except UnicodeDecodeError:
        try:
            decoded = content_bytes.decode("latin-1", errors="ignore")
            if is_valid_claim_text(decoded):
                return decoded
            return ""
        except Exception:
            return ""


def chunk_text(
    text: str,
    title: str = "Uploaded Document",
    target_words: int = 180,
    overlap_words: int = 30,
) -> list[dict[str, str]]:
    """
    Split long document text into overlapping, coherent evidence passages.
    Returns a list of dicts with 'title' and 'content'.
    """
    clean = re.sub(r"\r\n", "\n", text)
    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()

    if not clean or not is_valid_claim_text(clean):
        return []

    # First split by paragraphs
    paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]
    words_list: list[str] = []

    for p in paragraphs:
        words = p.split()
        if words:
            words_list.extend(words)

    if not words_list:
        return []

    # If document is small enough, return as single chunk
    if len(words_list) <= target_words + overlap_words:
        chunk_content = " ".join(words_list)
        if is_valid_claim_text(chunk_content):
            return [{
                "title": f"{title} (Section 1)",
                "content": chunk_content,
            }]
        return []

    chunks: list[dict[str, str]] = []
    step = max(1, target_words - overlap_words)
    chunk_idx = 1

    for i in range(0, len(words_list), step):
        window = words_list[i : i + target_words]
        if not window:
            break

        chunk_text_str = " ".join(window)
        if is_valid_claim_text(chunk_text_str):
            chunks.append({
                "title": f"{title} (Section {chunk_idx})",
                "content": chunk_text_str,
            })
            chunk_idx += 1

        if i + target_words >= len(words_list):
            break

    return chunks
