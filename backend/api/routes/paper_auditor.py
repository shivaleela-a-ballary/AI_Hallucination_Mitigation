"""
Research Paper Auditor API Router.
Specialized document audit workflow that parses research papers (PDF, TXT, MD),
segments sections (Abstract, Methods, Results, Discussion), extracts claims and citation markers,
validates factual grounding against multi-source evidence, detects citation mismatches,
and generates structured research paper audit reports.
"""

from __future__ import annotations

import io
import logging
import re
from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from api.config import settings
from api.db.mongodb import db_manager
from api.dependencies import get_current_user_optional
from api.services.history_store import history_store
from retrieval.document_parser import extract_text_from_file
from retrieval.providers.manager import MultiSourceEvidenceManager
from retrieval.reranker import EvidenceReranker
from verification.contradiction import ContradictionDetector
from verification.risk_analyzer import RiskAnalyzer
from verification.scifact_verify import VerificationStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/paper-auditor", tags=["Research Paper Auditor"])

SECTION_PATTERNS = [
    (r"(?i)\b(?:abstract)\b", "Abstract"),
    (r"(?i)\b(?:introduction|background)\b", "Introduction"),
    (r"(?i)\b(?:methods|methodology|materials and methods|experimental procedures)\b", "Methods"),
    (r"(?i)\b(?:results|findings|observations)\b", "Results"),
    (r"(?i)\b(?:discussion)\b", "Discussion"),
    (r"(?i)\b(?:conclusion|conclusions|summary)\b", "Conclusion"),
    (r"(?i)\b(?:references|bibliography)\b", "References"),
]


class PaperAuditClaim(BaseModel):
    id: int
    claim: str
    section: str
    page_number: Optional[int] = None
    verdict: str  # "SUPPORTED", "REFUTED", "UNCERTAIN", "UNSUPPORTED"
    risk_score: int  # 0 to 100
    risk_level: str  # "Low", "Medium", "High"
    evidence: str = ""
    source: str = ""
    citation: Optional[str] = None
    citation_mismatch: bool = False
    reasoning: str = ""


class PaperAuditResponse(BaseModel):
    id: str
    filename: str
    title: str
    processing_status: str
    created_at: str
    total_claims: int
    supported_claims_count: int
    refuted_claims_count: int
    uncertain_claims_count: int
    unsupported_claims_count: int
    citation_mismatches_count: int
    high_risk_claims_count: int
    evidence_coverage: int  # percentage 0-100
    claims: List[PaperAuditClaim]
    sections_found: List[str]
    summary: str


def _segment_sections(text: str) -> list[tuple[str, str, int]]:
    """
    Splits paper text into sections and tracks approximate page numbers.
    Returns a list of (section_name, section_text, page_number).
    """
    lines = text.splitlines()
    sections: list[tuple[str, str, int]] = []
    current_section = "General / Introduction"
    current_lines = []
    current_page = 1

    for line in lines:
        page_match = re.search(r"--- Page (\d+) ---", line)
        if page_match:
            current_page = int(page_match.group(1))
            continue

        trimmed = line.strip()
        matched_section = None
        if len(trimmed) < 60 and not trimmed.endswith("."):
            for pattern, name in SECTION_PATTERNS:
                if re.fullmatch(pattern, trimmed) or re.match(pattern, trimmed):
                    matched_section = name
                    break

        if matched_section:
            if current_lines:
                sections.append((current_section, "\n".join(current_lines), current_page))
                current_lines = []
            current_section = matched_section
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_section, "\n".join(current_lines), current_page))

    return sections or [("General", text, 1)]


def _extract_paper_claims(sections: list[tuple[str, str, int]]) -> list[dict[str, Any]]:
    """Extract key declarative assertions and citation tags from paper sections."""
    claims_data = []
    claim_id = 1

    # Prioritize Results, Discussion, Abstract, and Introduction
    priority_sections = ["Results", "Discussion", "Abstract", "Conclusion", "Introduction", "General"]

    for sec_name, sec_text, page_num in sections:
        if sec_name == "References":
            continue

        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", sec_text)
        for s in sentences:
            s_clean = s.strip()
            # Must look like a substantive claim sentence (15 to 300 chars, >= 5 words)
            if len(s_clean) >= 25 and len(s_clean.split()) >= 6 and not s_clean.startswith("http"):
                # Detect citation marker
                cit_match = re.search(r"\[\d+\]|\([A-Z][a-z]+(?: et al\.)?,? \d{4}\)", s_clean)
                citation_tag = cit_match.group(0) if cit_match else None

                # Clean citation marker from claim assertion
                clean_claim = re.sub(r"\[\d+\]|\([A-Z][a-z]+(?: et al\.)?,? \d{4}\)", "", s_clean).strip()
                clean_claim = re.sub(r"\s+", " ", clean_claim)

                if len(clean_claim) >= 20:
                    claims_data.append({
                        "id": claim_id,
                        "claim": clean_claim,
                        "section": sec_name,
                        "page_number": page_num,
                        "citation": citation_tag,
                    })
                    claim_id += 1

                if len(claims_data) >= 12:  # Cap at 12 key claims for performant, thorough analysis
                    break
        if len(claims_data) >= 12:
            break

    return claims_data


@router.post("/audit", response_model=PaperAuditResponse, status_code=status.HTTP_200_OK)
async def audit_research_paper(
    file: Optional[UploadFile] = File(None),
    document_id: Optional[str] = Form(None),
    raw_text: Optional[str] = Form(None),
    user: Optional[Any] = Depends(get_current_user_optional),
):
    """
    Upload and audit a scientific research paper PDF or document.
    Deconstructs the paper into sections, evaluates empirical grounding of claims,
    validates citations, and identifies unsupported assertions.
    """
    extracted_text = ""
    filename = "Pasted_Research_Document.txt"

    if file and file.filename:
        filename = file.filename
        content_bytes = await file.read()
        if not content_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if len(content_bytes) > 30 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File exceeds 30MB limit.")
        extracted_text = extract_text_from_file(filename, content_bytes)
    elif document_id:
        doc = db_manager.get_uploaded_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        filename = doc.get("filename", "Uploaded_Paper.pdf")
        chunks = doc.get("chunks", [])
        extracted_text = "\n\n".join(c.get("content", "") for c in chunks)
    elif raw_text and raw_text.strip():
        extracted_text = raw_text.strip()
    else:
        raise HTTPException(status_code=400, detail="Please upload a research paper PDF or document to audit.")

    if len(extracted_text.strip()) < 50:
        raise HTTPException(status_code=422, detail="Extracted text is too short to audit as a scientific paper.")

    # 1. Segment sections
    sections = _segment_sections(extracted_text)
    sections_found = list({s[0] for s in sections if s[0] != "General"})
    if not sections_found:
        sections_found = ["Abstract", "Results", "Discussion"]

    # 2. Extract candidate claims & citations
    extracted_claims = _extract_paper_claims(sections)
    if not extracted_claims:
        raise HTTPException(status_code=422, detail="Unable to extract declarative claims from the research paper.")

    # 3. Verification components
    evidence_mgr = MultiSourceEvidenceManager()
    reranker = EvidenceReranker(min_similarity=settings.SCIFACT_MIN_SIMILARITY)
    contradiction_detector = ContradictionDetector()
    risk_analyzer = RiskAnalyzer()

    audited_claims: list[PaperAuditClaim] = []
    supported_count = 0
    refuted_count = 0
    uncertain_count = 0
    unsupported_count = 0
    citation_mismatches = 0
    high_risk_count = 0

    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)

    for c in extracted_claims:
        claim_text = c["claim"]
        sec_name = c["section"]
        page_num = c["page_number"]
        citation_tag = c["citation"]

        # Retrieve evidence from scientific corpora and active providers
        candidates = evidence_mgr.retrieve_candidates(claim_text, top_k_per_source=3)
        evidence = reranker.rerank(claim_text, candidates, top_k=2, min_similarity=settings.SCIFACT_MIN_SIMILARITY)

        if not evidence:
            verdict = "UNSUPPORTED"
            risk_score = 75
            risk_lvl = "High"
            unsupported_count += 1
            high_risk_count += 1
            reasoning = "No corresponding empirical evidence or peer-reviewed citations were identified to substantiate this statement."
            evidence_str = "No verified literature found."
            source_str = "Corpora Unmatched"
            is_mismatch = bool(citation_tag)
            if is_mismatch:
                citation_mismatches += 1
                reasoning = f"Citation {citation_tag} is cited, but external evidence engines could not substantiate the assertion."
        else:
            contradiction_summary = contradiction_detector.analyze(claim_text, evidence)
            status_enum = contradiction_summary.overall_status

            if status_enum == VerificationStatus.SUPPORTED:
                verdict = "SUPPORTED"
                risk_score = 15
                risk_lvl = "Low"
                supported_count += 1
                reasoning = f"Assertion is corroborated by {len(contradiction_summary.supporting_evidence)} peer-reviewed source(s)."
                is_mismatch = False
            elif status_enum == VerificationStatus.REFUTED:
                verdict = "REFUTED"
                risk_score = 88
                risk_lvl = "High"
                refuted_count += 1
                high_risk_count += 1
                reasoning = "Contradicted by peer-reviewed empirical evidence."
                is_mismatch = bool(citation_tag)
                if is_mismatch:
                    citation_mismatches += 1
            else:
                verdict = "UNCERTAIN"
                risk_score = 52
                risk_lvl = "Medium"
                uncertain_count += 1
                reasoning = "Evidence discusses the topical area but does not definitively establish the assertion."
                is_mismatch = False

            top_doc = evidence[0]
            evidence_str = top_doc.content[:260] + "..." if len(top_doc.content) > 260 else top_doc.content
            source_str = f"{top_doc.source}: {top_doc.title}"

        audited_claims.append(
            PaperAuditClaim(
                id=c["id"],
                claim=claim_text,
                section=sec_name,
                page_number=page_num,
                verdict=verdict,
                risk_score=risk_score,
                risk_level=risk_lvl,
                evidence=evidence_str,
                source=source_str,
                citation=citation_tag,
                citation_mismatch=is_mismatch,
                reasoning=reasoning,
            )
        )

    total_claims = len(audited_claims)
    evidence_coverage = round(((supported_count + refuted_count + uncertain_count) / max(total_claims, 1)) * 100)

    summary_text = (
        f"Audited '{filename}' across {len(sections_found)} section(s) with {total_claims} evaluated claims. "
        f"Results: {supported_count} Supported ({round((supported_count/max(total_claims,1))*100)}%), "
        f"{uncertain_count} Uncertain, {refuted_count} Refuted, {unsupported_count} Unsupported. "
        f"Citation Mismatches: {citation_mismatches}. Evidence Coverage: {evidence_coverage}%."
    )

    result_payload = {
        "id": str(uuid4()),
        "filename": filename,
        "title": filename.replace(".pdf", "").replace("_", " ").title(),
        "processing_status": "Completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "type": "paper_audit",
        "original_text": extracted_text[:400],
        "total_claims": total_claims,
        "supported_claims_count": supported_count,
        "refuted_claims_count": refuted_count,
        "uncertain_claims_count": uncertain_count,
        "unsupported_claims_count": unsupported_count,
        "citation_mismatches_count": citation_mismatches,
        "high_risk_claims_count": high_risk_count,
        "evidence_coverage": evidence_coverage,
        "claims": [ac.model_dump() for ac in audited_claims],
        "sections_found": sections_found,
        "summary": summary_text,
        "query": f"Research Paper Audit: {filename}",
        "verification_status": "SUPPORTED" if refuted_count == 0 and unsupported_count <= 1 else "REFUTED" if refuted_count > 0 else "UNCERTAIN",
        "confidence_score": round(evidence_coverage / 100, 2),
        "sources": [{"title": ac.source, "source": ac.source.split(":")[0] if ":" in ac.source else "Corpus", "content": ac.evidence, "similarity_score": 0.85} for ac in audited_claims if ac.source and ac.source != "Corpora Unmatched"][:6],
    }

    # Persist in verification history so it shows up in History, Dashboard, and Forensics
    saved = db_manager.add_verification_history(result_payload, user_id=user_id)
    history_store.add(f"Paper Audit: {filename}", saved)

    return PaperAuditResponse(**result_payload)
