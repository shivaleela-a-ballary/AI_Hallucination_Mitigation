"""
Evaluation dataset loader and benchmark examples for claim verification.
Provides authentic scientific and biomedical claims with verified ground truth labels.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class EvaluationExample:
    """A benchmark claim with ground truth annotation."""
    claim: str
    actual_label: str  # "SUPPORTED", "REFUTED", "UNCERTAIN"
    evidence_text: str | None = None
    relevant_doc_titles: list[str] = field(default_factory=list)
    domain: str = "biomedical"
    notes: str = ""


# Core verified benchmark examples drawn from scientific evidence standards (e.g. SciFact / biomedical literature)
BENCHMARK_EXAMPLES: list[EvaluationExample] = [
    # ------------------ SUPPORTED SCIENTIFIC CLAIMS ------------------
    EvaluationExample(
        claim="MicroRNAs can inhibit translation or induce degradation of target mRNAs.",
        actual_label="SUPPORTED",
        evidence_text="MicroRNAs (miRNAs) are small non-coding RNAs that regulate gene expression post-transcriptionally by binding to target mRNAs, leading to translational repression or mRNA cleavage.",
        relevant_doc_titles=["MicroRNAs regulate gene expression", "Role of miRNAs in post-transcriptional regulation"],
        domain="molecular_biology",
        notes="Established mechanism of miRNA action",
    ),
    EvaluationExample(
        claim="CRISPR-Cas9 enables targeted genome editing in eukaryotic cells.",
        actual_label="SUPPORTED",
        evidence_text="The RNA-guided Cas9 endonuclease from the microbial CRISPR adaptive immune system can be used to facilitate targeted genome editing in eukaryotic cells with high precision.",
        relevant_doc_titles=["Multiplex genome engineering using CRISPR/Cas systems"],
        domain="genetics",
        notes="Landmark CRISPR findings",
    ),
    EvaluationExample(
        claim="Telomerase activity is upregulated in the vast majority of human cancers.",
        actual_label="SUPPORTED",
        evidence_text="Telomerase reactivation or upregulation occurs in approximately 85-90% of human malignancies, contributing to cellular immortality and tumor progression.",
        relevant_doc_titles=["Telomerase and cancer biology"],
        domain="oncology",
        notes="Hallmark of cancer biology",
    ),
    EvaluationExample(
        claim="Statins inhibit HMG-CoA reductase to reduce LDL cholesterol levels.",
        actual_label="SUPPORTED",
        evidence_text="Statins competitively inhibit 3-hydroxy-3-methylglutaryl coenzyme A (HMG-CoA) reductase, the rate-limiting enzyme in cholesterol synthesis, substantially lowering circulating LDL cholesterol.",
        relevant_doc_titles=["Mechanisms of statin therapy in cardiovascular disease"],
        domain="pharmacology",
        notes="Pharmacology consensus",
    ),
    EvaluationExample(
        claim="Angiotensin-converting enzyme 2 (ACE2) acts as the primary functional receptor for SARS-CoV-2 entry into host cells.",
        actual_label="SUPPORTED",
        evidence_text="SARS-CoV-2 uses the SARS-CoV receptor ACE2 for host cell entry and the serine protease TMPRSS2 for S protein priming.",
        relevant_doc_titles=["SARS-CoV-2 cell entry depends on ACE2 and TMPRSS2"],
        domain="virology",
        notes="Established viral mechanism",
    ),
    EvaluationExample(
        claim="Loss-of-function mutations in BRCA1 impair homologous recombination DNA repair.",
        actual_label="SUPPORTED",
        evidence_text="BRCA1 is essential for the repair of double-strand DNA breaks via homologous recombination; loss of BRCA1 causes genome instability and predisposition to breast and ovarian cancer.",
        relevant_doc_titles=["BRCA1 and homologous recombination repair"],
        domain="genetics",
        notes="DNA repair mechanism",
    ),

    # ------------------ REFUTED SCIENTIFIC CLAIMS ------------------
    EvaluationExample(
        claim="Penicillin has no antibacterial efficacy against bacterial infections.",
        actual_label="REFUTED",
        evidence_text="Penicillin is a potent beta-lactam antibiotic that inhibits bacterial cell wall synthesis by binding penicillin-binding proteins, causing lysis of susceptible Gram-positive bacteria.",
        relevant_doc_titles=["Discovery and mechanism of penicillin"],
        domain="microbiology",
        notes="Directly contradicts established microbiology",
    ),
    EvaluationExample(
        claim="Insulin increases blood glucose levels by accelerating hepatic gluconeogenesis.",
        actual_label="REFUTED",
        evidence_text="Insulin lowers blood glucose by promoting glucose uptake in muscle and adipose tissue and suppressing hepatic glucose production and gluconeogenesis.",
        relevant_doc_titles=["Physiological actions of insulin on metabolism"],
        domain="endocrinology",
        notes="Directly inverted physiological function",
    ),
    EvaluationExample(
        claim="Type 1 diabetes is primarily caused by dietary excessive sugar consumption rather than autoimmune beta cell destruction.",
        actual_label="REFUTED",
        evidence_text="Type 1 diabetes is an autoimmune disease characterized by T-cell mediated destruction of insulin-producing beta cells in the pancreatic islets of Langerhans.",
        relevant_doc_titles=["Pathogenesis of Type 1 Diabetes"],
        domain="immunology",
        notes="Contradicted etiology",
    ),
    EvaluationExample(
        claim="Mitochondria do not produce ATP and play no role in cellular respiration.",
        actual_label="REFUTED",
        evidence_text="Mitochondria are the powerhouses of the cell, generating the bulk of cellular ATP through oxidative phosphorylation and the electron transport chain.",
        relevant_doc_titles=["Mitochondrial bioenergetics and ATP synthesis"],
        domain="biochemistry",
        notes="Contradicted bioenergetics fact",
    ),
    EvaluationExample(
        claim="Vaccines against measles cause childhood autism.",
        actual_label="REFUTED",
        evidence_text="Extensive global epidemiological studies involving millions of children have repeatedly demonstrated no link between the MMR vaccine and autism spectrum disorders.",
        relevant_doc_titles=["MMR vaccination and autism: a comprehensive meta-analysis"],
        domain="epidemiology",
        notes="Disproven medical claim",
    ),
    EvaluationExample(
        claim="Red blood cells use mitochondrial oxidative phosphorylation for all their energy production.",
        actual_label="REFUTED",
        evidence_text="Mature human erythrocytes lack mitochondria and nuclei and rely entirely on anaerobic glycolysis for ATP generation.",
        relevant_doc_titles=["Erythrocyte metabolism"],
        domain="hematology",
        notes="Contradicted cell biology fact",
    ),

    # ------------------ UNCERTAIN / INSUFFICIENT CLAIMS ------------------
    EvaluationExample(
        claim="Telepathic neurological resonance connects identical twins across long distances.",
        actual_label="UNCERTAIN",
        evidence_text=None,
        relevant_doc_titles=[],
        domain="fringe",
        notes="No valid scientific evidence exists",
    ),
    EvaluationExample(
        claim="Consuming purple crystal dust completely eliminates all viral infections within 30 seconds.",
        actual_label="UNCERTAIN",
        evidence_text=None,
        relevant_doc_titles=[],
        domain="fringe",
        notes="Unsubstantiated pseudoscience claim",
    ),
    EvaluationExample(
        claim="Exoplanet Kepler-186f has an advanced subterranean carbon-based civilization.",
        actual_label="UNCERTAIN",
        evidence_text=None,
        relevant_doc_titles=[],
        domain="astrophysics",
        notes="No scientific evidence available to verify",
    ),
    EvaluationExample(
        claim="Drinking water inverted in magnetic pyramids triples human lifespan.",
        actual_label="UNCERTAIN",
        evidence_text=None,
        relevant_doc_titles=[],
        domain="fringe",
        notes="Unsubstantiated claim",
    ),
]


def load_evaluation_dataset(dataset_path: str | Path | None = None) -> list[EvaluationExample]:
    """
    Load evaluation benchmark dataset from a JSONL file or return default benchmark set.
    """
    if dataset_path:
        path = Path(dataset_path)
        if path.is_file():
            examples: list[EvaluationExample] = []
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    examples.append(
                        EvaluationExample(
                            claim=item["claim"],
                            actual_label=item.get("label", item.get("actual_label", "UNCERTAIN")).upper(),
                            evidence_text=item.get("evidence", item.get("evidence_text")),
                            relevant_doc_titles=item.get("relevant_doc_titles", []),
                            domain=item.get("domain", "biomedical"),
                            notes=item.get("notes", ""),
                        )
                    )
            return examples

    return list(BENCHMARK_EXAMPLES)
