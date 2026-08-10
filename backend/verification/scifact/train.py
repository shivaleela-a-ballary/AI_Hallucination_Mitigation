"""Training utilities for the SciFact evidence classifier.

The classifier learns:
    (claim, evidence) -> SUPPORTED / REFUTED

UNCERTAIN is handled by the runtime verification layer when adequate
evidence cannot be established.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import (
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

from .dataset_loader import SciFactDatasetLoader
from .labels import EVIDENCE_LABEL_TO_ID, VerificationLabel
from .model import SciFactModelConfig
from .preprocess import SciFactExample, SciFactPreprocessor


def build_training_examples(
    dataset_root: str | Path,
) -> list[SciFactExample]:
    """Build evidence-backed training examples from SciFact."""

    loader = SciFactDatasetLoader(dataset_root)
    corpus = loader.load_corpus()
    claims = loader.load_claims("train")

    preprocessor = SciFactPreprocessor()

    return preprocessor.build_examples(
        claims=claims,
        corpus=corpus,
    )


def build_dev_examples(
    dataset_root: str | Path,
) -> list[SciFactExample]:
    """Build evidence-backed development examples from SciFact."""

    loader = SciFactDatasetLoader(dataset_root)
    corpus = loader.load_corpus()
    claims = loader.load_claims("dev")

    preprocessor = SciFactPreprocessor()

    return preprocessor.build_examples(
        claims=claims,
        corpus=corpus,
    )


def convert_examples_to_training_rows(
    examples: Iterable[SciFactExample],
) -> list[dict[str, object]]:
    """Convert examples into model-ready rows."""

    rows: list[dict[str, object]] = []

    for example in examples:
        if example.label not in EVIDENCE_LABEL_TO_ID:
            continue

        rows.append(
            {
                "claim": example.claim,
                "evidence": example.evidence,
                "label": EVIDENCE_LABEL_TO_ID[example.label],
            }
        )

    return rows


def validate_training_data(
    examples: Iterable[SciFactExample],
) -> None:
    """Validate evidence-classification training data."""

    examples = list(examples)

    if not examples:
        raise ValueError("No SciFact training examples were found.")

    labels = {example.label for example in examples}

    allowed = {
        VerificationLabel.SUPPORTED,
        VerificationLabel.REFUTED,
    }

    unexpected = labels - allowed

    if unexpected:
        raise ValueError(
            "Training data contains unsupported labels: "
            + ", ".join(label.value for label in unexpected)
        )

    if VerificationLabel.SUPPORTED not in labels:
        raise ValueError("No SUPPORTED examples found.")

    if VerificationLabel.REFUTED not in labels:
        raise ValueError("No REFUTED examples found.")


def _build_hf_dataset(rows: list[dict[str, object]]):
    """Create a Hugging Face Dataset from training rows."""

    from datasets import Dataset

    return Dataset.from_list(rows)


def _tokenize_dataset(dataset, tokenizer, max_length: int):
    """Tokenize claim/evidence pairs."""

    def tokenize(batch):
        return tokenizer(
            batch["claim"],
            batch["evidence"],
            truncation=True,
            max_length=max_length,
        )

    return dataset.map(
        tokenize,
        batched=True,
        remove_columns=["claim", "evidence"],
    )


def _compute_metrics(eval_prediction):
    """Compute standard binary classification metrics."""

    predictions = eval_prediction.predictions
    labels = eval_prediction.label_ids

    if isinstance(predictions, tuple):
        predictions = predictions[0]

    predicted_labels = np.argmax(predictions, axis=-1)

    precision, recall, f1, _ = precision_recall_fscore_support(
        labels,
        predicted_labels,
        average="macro",
        zero_division=0,
    )

    accuracy = accuracy_score(labels, predicted_labels)

    return {
        "accuracy": float(accuracy),
        "macro_precision": float(precision),
        "macro_recall": float(recall),
        "macro_f1": float(f1),
    }


def train_scifact_classifier(
    dataset_root: str | Path = "data/scifact",
    base_model_path: str | Path = "models/scifact-base",
    output_dir: str | Path = "models/scifact",
    *,
    epochs: float = 1.0,
    batch_size: int = 2,
    learning_rate: float = 2e-5,
    max_length: int = 256,
    max_steps: int = -1,
):
    """Train the local SciFact evidence classifier.

    This function is explicit and never executes during module import.
    """

    dataset_root = Path(dataset_root)
    base_model_path = Path(base_model_path)
    output_dir = Path(output_dir)

    if not base_model_path.is_dir():
        raise FileNotFoundError(
            f"Base model does not exist: {base_model_path}"
        )

    train_examples = build_training_examples(dataset_root)
    dev_examples = build_dev_examples(dataset_root)

    validate_training_data(train_examples)
    validate_training_data(dev_examples)

    train_rows = convert_examples_to_training_rows(train_examples)
    dev_rows = convert_examples_to_training_rows(dev_examples)

    if not train_rows:
        raise ValueError("No training rows were generated.")

    if not dev_rows:
        raise ValueError("No development rows were generated.")

    config = SciFactModelConfig(
        model_path=base_model_path,
        max_length=max_length,
        num_labels=2,
        local_files_only=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        str(config.model_path),
        local_files_only=True,
    )

    from transformers import AutoModelForSequenceClassification

    model = AutoModelForSequenceClassification.from_pretrained(
        str(config.model_path),
        num_labels=2,
        local_files_only=True,
    )

    model.config.id2label = {
        0: "SUPPORTED",
        1: "REFUTED",
    }

    model.config.label2id = {
        "SUPPORTED": 0,
        "REFUTED": 1,
    }

    train_dataset = _build_hf_dataset(train_rows)
    dev_dataset = _build_hf_dataset(dev_rows)

    train_dataset = _tokenize_dataset(
        train_dataset,
        tokenizer,
        max_length,
    )

    dev_dataset = _tokenize_dataset(
        dev_dataset,
        tokenizer,
        max_length,
    )

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=learning_rate,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=25,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        report_to="none",
        use_cpu=True,
        max_steps=max_steps,
    )

    data_collator = DataCollatorWithPadding(
        tokenizer=tokenizer,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=dev_dataset,
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=_compute_metrics,
    )

    trainer.train()

    metrics = trainer.evaluate()

    output_dir.mkdir(parents=True, exist_ok=True)

    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    return metrics