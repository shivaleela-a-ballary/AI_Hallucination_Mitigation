"""
Train a local two-class SciFact verifier.

Labels:
    0 = SUPPORTED
    1 = REFUTED

The application-level UNCERTAIN state is handled separately by
verification/confidence logic. It is NOT a third Transformer class.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_DIR = PROJECT_ROOT / "data" / "scifact"
MODEL_DIR = PROJECT_ROOT / "models" / "scifact"

TRAIN_FILE = DATA_DIR / "claims_train.jsonl"
DEV_FILE = DATA_DIR / "claims_dev.jsonl"

BASE_MODEL = "allenai/scibert_scivocab_uncased"

MAX_LENGTH = 256
BATCH_SIZE = 8
EPOCHS = 2
LEARNING_RATE = 2e-5
SEED = 42

LABEL_TO_ID = {
    "SUPPORTED": 0,
    "REFUTED": 1,
}

ID_TO_LABEL = {
    0: "SUPPORTED",
    1: "REFUTED",
}


# ---------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------

def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ---------------------------------------------------------
# Load examples using the project's existing preprocessing
# ---------------------------------------------------------

def load_examples(split: str):
    from .train import build_training_examples

    return build_training_examples(DATA_DIR)


# ---------------------------------------------------------
# Dataset
# ---------------------------------------------------------

class SciFactTorchDataset(Dataset):
    def __init__(self, examples, tokenizer):
        self.examples = list(examples)
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, index):
        example = self.examples[index]

        claim = example.claim
        evidence = example.evidence

        label_name = example.label.value

        if label_name not in LABEL_TO_ID:
            raise ValueError(
                f"Unexpected SciFact label: {label_name}"
            )

        encoded = self.tokenizer(
            claim,
            evidence,
            truncation=True,
            padding="max_length",
            max_length=MAX_LENGTH,
            return_tensors="pt",
        )

        item = {
            key: value.squeeze(0)
            for key, value in encoded.items()
        }

        item["labels"] = torch.tensor(
            LABEL_TO_ID[label_name],
            dtype=torch.long,
        )

        return item


# ---------------------------------------------------------
# Validation split
# ---------------------------------------------------------

def load_validation_examples():
    """
    The existing project preprocessing currently exposes
    build_training_examples() for the training split.

    For a safe first training run, we create a deterministic
    validation split from the real training examples rather
    than using test data.

    IMPORTANT:
    test data is never used for training.
    """

    from .train import build_training_examples

    examples = build_training_examples(DATA_DIR)

    examples = list(examples)

    random.Random(SEED).shuffle(examples)

    split_index = int(len(examples) * 0.8)

    train_examples = examples[:split_index]
    dev_examples = examples[split_index:]

    return train_examples, dev_examples


# ---------------------------------------------------------
# Evaluation
# ---------------------------------------------------------

def evaluate(model, dataloader, device):
    model.eval()

    total = 0
    correct = 0
    total_loss = 0.0

    with torch.no_grad():
        for batch in dataloader:
            batch = {
                key: value.to(device)
                for key, value in batch.items()
            }

            outputs = model(**batch)

            total_loss += outputs.loss.item()

            predictions = torch.argmax(
                outputs.logits,
                dim=-1,
            )

            labels = batch["labels"]

            correct += (
                predictions == labels
            ).sum().item()

            total += labels.size(0)

    accuracy = correct / total if total else 0.0
    loss = total_loss / len(dataloader) if dataloader else 0.0

    return loss, accuracy


# ---------------------------------------------------------
# Main training
# ---------------------------------------------------------

def main():
    set_seed(SEED)

    print("=" * 70)
    print("SciFact 2-Class Model Training")
    print("=" * 70)

    print(f"Project root : {PROJECT_ROOT}")
    print(f"Dataset      : {DATA_DIR}")
    print(f"Output model : {MODEL_DIR}")
    print(f"Base model   : {BASE_MODEL}")

    if not TRAIN_FILE.exists():
        raise FileNotFoundError(
            f"Missing training data: {TRAIN_FILE}"
        )

    if not DEV_FILE.exists():
        print(
            "WARNING: claims_dev.jsonl was not found. "
            "Using deterministic validation split."
        )

    print("\nLoading real SciFact examples...")

    train_examples, dev_examples = load_validation_examples()

    print(f"Training examples   : {len(train_examples)}")
    print(f"Validation examples : {len(dev_examples)}")

    train_labels = [
        example.label.value
        for example in train_examples
    ]

    dev_labels = [
        example.label.value
        for example in dev_examples
    ]

    print(
        "Training labels:",
        {
            label: train_labels.count(label)
            for label in sorted(set(train_labels))
        },
    )

    print(
        "Validation labels:",
        {
            label: dev_labels.count(label)
            for label in sorted(set(dev_labels))
        },
    )

    # -----------------------------------------------------
    # Load SciBERT locally
    # -----------------------------------------------------

    print("\nLoading local SciBERT...")

    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL,
        local_files_only=True,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL,
        num_labels=2,
        id2label=ID_TO_LABEL,
        label2id=LABEL_TO_ID,
        local_files_only=True,
    )

    print("SciBERT loaded successfully.")

    # -----------------------------------------------------
    # Dataset / DataLoader
    # -----------------------------------------------------

    train_dataset = SciFactTorchDataset(
        train_examples,
        tokenizer,
    )

    dev_dataset = SciFactTorchDataset(
        dev_examples,
        tokenizer,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
    )

    dev_loader = DataLoader(
        dev_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )

    # -----------------------------------------------------
    # Device
    # -----------------------------------------------------

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(f"\nDevice: {device}")

    model.to(device)

    # -----------------------------------------------------
    # Optimizer
    # -----------------------------------------------------

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    # -----------------------------------------------------
    # Training
    # -----------------------------------------------------

    for epoch in range(EPOCHS):

        print("\n" + "=" * 70)
        print(
            f"Epoch {epoch + 1}/{EPOCHS}"
        )
        print("=" * 70)

        model.train()

        total_loss = 0.0

        for step, batch in enumerate(train_loader, start=1):

            batch = {
                key: value.to(device)
                for key, value in batch.items()
            }

            optimizer.zero_grad()

            outputs = model(**batch)

            loss = outputs.loss

            loss.backward()

            torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                max_norm=1.0,
            )

            optimizer.step()

            total_loss += loss.item()

            if step % 10 == 0 or step == 1:
                print(
                    f"Step {step}/{len(train_loader)} "
                    f"Loss: {loss.item():.4f}"
                )

        avg_train_loss = (
            total_loss / len(train_loader)
        )

        dev_loss, dev_accuracy = evaluate(
            model,
            dev_loader,
            device,
        )

        print(
            f"\nTrain loss: {avg_train_loss:.4f}"
        )

        print(
            f"Validation loss: {dev_loss:.4f}"
        )

        print(
            f"Validation accuracy: "
            f"{dev_accuracy * 100:.2f}%"
        )

    # -----------------------------------------------------
    # Save model
    # -----------------------------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("\nSaving trained model...")

    model.save_pretrained(
        MODEL_DIR,
        safe_serialization=True,
    )

    tokenizer.save_pretrained(
        MODEL_DIR
    )

    # Explicitly save metadata too.
    config_path = MODEL_DIR / "training_metadata.json"

    metadata = {
        "base_model": BASE_MODEL,
        "num_labels": 2,
        "label2id": LABEL_TO_ID,
        "id2label": ID_TO_LABEL,
        "training_examples": len(train_examples),
        "validation_examples": len(dev_examples),
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "max_length": MAX_LENGTH,
        "seed": SEED,
    }

    config_path.write_text(
        json.dumps(
            metadata,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nModel saved to:")
    print(MODEL_DIR)

    # -----------------------------------------------------
    # Final smoke test
    # -----------------------------------------------------

    print("\nRunning model reload smoke test...")

    reloaded_tokenizer = AutoTokenizer.from_pretrained(
        MODEL_DIR,
        local_files_only=True,
    )

    reloaded_model = (
        AutoModelForSequenceClassification.from_pretrained(
            MODEL_DIR,
            local_files_only=True,
        )
    )

    reloaded_model.eval()

    sample = dev_examples[0]

    encoded = reloaded_tokenizer(
        sample.claim,
        sample.evidence,
        truncation=True,
        max_length=MAX_LENGTH,
        return_tensors="pt",
    )

    with torch.no_grad():
        output = reloaded_model(**encoded)

    probabilities = torch.softmax(
        output.logits,
        dim=-1,
    )[0]

    predicted_id = int(
        torch.argmax(probabilities).item()
    )

    predicted_label = ID_TO_LABEL[predicted_id]

    print("\nSmoke test result:")
    print(f"Claim            : {sample.claim}")
    print(f"Expected label   : {sample.label.value}")
    print(f"Predicted label  : {predicted_label}")
    print(
        f"Confidence       : "
        f"{float(probabilities[predicted_id]):.4f}"
    )

    print("\nProbability distribution:")

    for index, probability in enumerate(probabilities):
        print(
            f"  {ID_TO_LABEL[index]}: "
            f"{float(probability):.4f}"
        )

    print("\n" + "=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()