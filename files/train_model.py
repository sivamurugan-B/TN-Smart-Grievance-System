"""
Tamil Nadu Grievance Classifier - BERT Multi-task Model
Trains on tamilnadu_grievance_dataset_10000_v2.csv
Outputs: type, category, severity
"""

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertModel, AdamW, get_linear_schedule_with_warmup
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import pickle
import os
import json
from pathlib import Path

# ──────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────
MODEL_DIR = Path("./saved_model")
DATA_PATH = "../data/tamilnadu_grievance_dataset_10000_v2.csv"

BERT_MODEL   = "bert-base-uncased"
MAX_LEN      = 128
BATCH_SIZE   = 16
EPOCHS       = 3
LR           = 2e-5
DEVICE       = torch.device("cuda" if torch.cuda.is_available() else "cpu")

LABEL_COLS   = ["type", "category", "severity"]

# ──────────────────────────────────────────
# DATASET
# ──────────────────────────────────────────
class GrievanceDataset(Dataset):
    def __init__(self, texts, labels_dict, tokenizer, max_len):
        self.texts       = texts
        self.labels_dict = labels_dict  # {"type": [...], "category": [...], "severity": [...]}
        self.tokenizer   = tokenizer
        self.max_len     = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoding = self.tokenizer(
            self.texts[idx],
            add_special_tokens=True,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        item = {
            "input_ids":      encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
        }
        for col, vals in self.labels_dict.items():
            item[col] = torch.tensor(vals[idx], dtype=torch.long)
        return item


# ──────────────────────────────────────────
# MODEL
# ──────────────────────────────────────────
class BERTMultiTaskClassifier(nn.Module):
    def __init__(self, bert_model_name, num_type, num_category, num_severity, dropout=0.3):
        super().__init__()
        self.bert      = BertModel.from_pretrained(bert_model_name)
        hidden         = self.bert.config.hidden_size

        self.dropout   = nn.Dropout(dropout)
        self.fc_type     = nn.Linear(hidden, num_type)
        self.fc_category = nn.Linear(hidden, num_category)
        self.fc_severity = nn.Linear(hidden, num_severity)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled  = self.dropout(outputs.pooler_output)
        return (
            self.fc_type(pooled),
            self.fc_category(pooled),
            self.fc_severity(pooled),
        )


# ──────────────────────────────────────────
# TRAINING
# ──────────────────────────────────────────
def train_epoch(model, loader, optimizer, scheduler, device):
    model.train()
    ce = nn.CrossEntropyLoss()
    total_loss = 0

    for batch in loader:
        input_ids      = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        t_labels = batch["type"].to(device)
        c_labels = batch["category"].to(device)
        s_labels = batch["severity"].to(device)

        optimizer.zero_grad()
        t_logits, c_logits, s_logits = model(input_ids, attention_mask)

        loss = ce(t_logits, t_labels) + ce(c_logits, c_labels) + ce(s_logits, s_labels)
        loss.backward()

        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
        total_loss += loss.item()

    return total_loss / len(loader)


def eval_epoch(model, loader, device):
    model.eval()
    ce = nn.CrossEntropyLoss()
    total_loss = 0
    preds = {"type": [], "category": [], "severity": []}
    trues = {"type": [], "category": [], "severity": []}

    with torch.no_grad():
        for batch in loader:
            input_ids      = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            t_logits, c_logits, s_logits = model(input_ids, attention_mask)

            for key, logits, label_key in [
                ("type",     t_logits, "type"),
                ("category", c_logits, "category"),
                ("severity", s_logits, "severity"),
            ]:
                labels = batch[label_key].to(device)
                total_loss += ce(logits, labels).item()
                preds[key].extend(torch.argmax(logits, dim=1).cpu().numpy())
                trues[key].extend(labels.cpu().numpy())

    return total_loss / len(loader), preds, trues


# ──────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────
def main():
    print(f"Using device: {DEVICE}")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    df = pd.read_csv(DATA_PATH)
    df.dropna(inplace=True)
    print(f"Dataset size: {len(df)}")

    # Encode labels
    encoders = {}
    encoded  = {}
    for col in LABEL_COLS:
        le = LabelEncoder()
        encoded[col] = le.fit_transform(df[col])
        encoders[col] = le
        print(f"{col} classes: {list(le.classes_)}")

    # Save encoders
    with open(MODEL_DIR / "label_encoders.pkl", "wb") as f:
        pickle.dump(encoders, f)

    # Save class info for inference
    class_info = {col: list(le.classes_) for col, le in encoders.items()}
    with open(MODEL_DIR / "class_info.json", "w") as f:
        json.dump(class_info, f)

    # Train/val split
    texts = df["text"].tolist()
    X_train, X_val, *label_splits = train_test_split(
        texts,
        *[encoded[col] for col in LABEL_COLS],
        test_size=0.15,
        random_state=42,
    )

    train_labels = {col: label_splits[i*2]   for i, col in enumerate(LABEL_COLS)}
    val_labels   = {col: label_splits[i*2+1] for i, col in enumerate(LABEL_COLS)}

    # Tokenizer
    tokenizer = BertTokenizer.from_pretrained(BERT_MODEL)
    tokenizer.save_pretrained(MODEL_DIR / "tokenizer")

    # Datasets & loaders
    train_ds = GrievanceDataset(X_train, train_labels, tokenizer, MAX_LEN)
    val_ds   = GrievanceDataset(X_val,   val_labels,   tokenizer, MAX_LEN)
    train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=2)
    val_dl   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    # Model
    model = BERTMultiTaskClassifier(
        BERT_MODEL,
        num_type=len(encoders["type"].classes_),
        num_category=len(encoders["category"].classes_),
        num_severity=len(encoders["severity"].classes_),
    ).to(DEVICE)

    optimizer = AdamW(model.parameters(), lr=LR, eps=1e-8)
    total_steps = len(train_dl) * EPOCHS
    scheduler   = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=total_steps // 10, num_training_steps=total_steps
    )

    # Training loop
    best_val_loss = float("inf")
    for epoch in range(1, EPOCHS + 1):
        train_loss = train_epoch(model, train_dl, optimizer, scheduler, DEVICE)
        val_loss, preds, trues = eval_epoch(model, val_dl, DEVICE)

        print(f"\nEpoch {epoch}/{EPOCHS}  train_loss={train_loss:.4f}  val_loss={val_loss:.4f}")
        for col in LABEL_COLS:
            print(f"\n── {col.upper()} ──")
            print(classification_report(trues[col], preds[col],
                                        target_names=encoders[col].classes_))

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), MODEL_DIR / "best_model.pt")
            print("✓ Best model saved")

    print("\nTraining complete.")
    print(f"Model saved to: {MODEL_DIR}")


if __name__ == "__main__":
    main()
