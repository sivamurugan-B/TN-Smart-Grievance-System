"""
Tamil Nadu Grievance Classifier – BERT Multi-task Training
Dataset: tamilnadu_grievance_dataset_10000_v2.csv
Outputs: saved_model/best_model.pt, class_info.json, tokenizer/
"""

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from transformers import (
    BertModel,
    BertTokenizer,
    get_linear_schedule_with_warmup,
)

# ── Config ────────────────────────────────────
MODEL_DIR  = Path(__file__).parent / "saved_model"
DATA_PATH  = Path(__file__).parent.parent / "data" / "tamilnadu_grievance_dataset_10000_v2.csv"

BERT_MODEL  = "bert-base-uncased"
MAX_LEN     = 128
BATCH_SIZE  = 16
EPOCHS      = 3
LR          = 2e-5
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")
LABEL_COLS  = ["type", "category", "severity"]


# ── Dataset ───────────────────────────────────
class GrievanceDataset(Dataset):
    def __init__(self, texts, labels_dict, tokenizer, max_len):
        self.texts       = texts
        self.labels_dict = labels_dict
        self.tokenizer   = tokenizer
        self.max_len     = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.texts[idx],
            add_special_tokens = True,
            max_length         = self.max_len,
            padding            = "max_length",
            truncation         = True,
            return_tensors     = "pt",
        )
        item = {
            "input_ids":      enc["input_ids"].squeeze(),
            "attention_mask": enc["attention_mask"].squeeze(),
        }
        for col, vals in self.labels_dict.items():
            item[col] = torch.tensor(vals[idx], dtype=torch.long)
        return item


# ── Model ─────────────────────────────────────
class BERTMultiTaskClassifier(nn.Module):
    def __init__(self, bert_model_name, num_type, num_category, num_severity, dropout=0.3):
        super().__init__()
        self.bert        = BertModel.from_pretrained(bert_model_name)
        hidden           = self.bert.config.hidden_size
        self.dropout     = nn.Dropout(dropout)
        self.fc_type     = nn.Linear(hidden, num_type)
        self.fc_category = nn.Linear(hidden, num_category)
        self.fc_severity = nn.Linear(hidden, num_severity)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled  = self.dropout(outputs.pooler_output)
        return self.fc_type(pooled), self.fc_category(pooled), self.fc_severity(pooled)


# ── Train / Eval ──────────────────────────────
def train_epoch(model, loader, optimizer, scheduler, device):
    model.train()
    ce         = nn.CrossEntropyLoss()
    total_loss = 0.0

    for batch in loader:
        ids   = batch["input_ids"].to(device)
        mask  = batch["attention_mask"].to(device)
        t_lbl = batch["type"].to(device)
        c_lbl = batch["category"].to(device)
        s_lbl = batch["severity"].to(device)

        optimizer.zero_grad()
        t_log, c_log, s_log = model(ids, mask)

        loss = ce(t_log, t_lbl) + ce(c_log, c_lbl) + ce(s_log, s_lbl)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
        total_loss += loss.item()

    return total_loss / len(loader)


def eval_epoch(model, loader, device):
    model.eval()
    ce         = nn.CrossEntropyLoss()
    total_loss = 0.0
    preds      = {c: [] for c in LABEL_COLS}
    trues      = {c: [] for c in LABEL_COLS}

    with torch.no_grad():
        for batch in loader:
            ids  = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            t_log, c_log, s_log = model(ids, mask)

            for col, logits in zip(LABEL_COLS, [t_log, c_log, s_log]):
                lbls = batch[col].to(device)
                total_loss += ce(logits, lbls).item()
                preds[col].extend(torch.argmax(logits, dim=1).cpu().numpy())
                trues[col].extend(lbls.cpu().numpy())

    return total_loss / len(loader), preds, trues


# ── Main ──────────────────────────────────────
def main():
    print(f"Device: {DEVICE}")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH)
    df.dropna(subset=["text"] + LABEL_COLS, inplace=True)
    print(f"Dataset size: {len(df)}")

    # Encode labels
    encoders = {}
    encoded  = {}
    for col in LABEL_COLS:
        le           = LabelEncoder()
        encoded[col] = le.fit_transform(df[col])
        encoders[col] = le
        print(f"  {col}: {list(le.classes_)}")

    with open(MODEL_DIR / "label_encoders.pkl", "wb") as f:
        pickle.dump(encoders, f)

    class_info = {col: list(le.classes_) for col, le in encoders.items()}
    with open(MODEL_DIR / "class_info.json", "w") as f:
        json.dump(class_info, f, indent=2)

    # Train / val split
    texts = df["text"].tolist()
    splits = train_test_split(
        texts,
        *[encoded[c] for c in LABEL_COLS],
        test_size=0.15,
        random_state=42,
    )
    X_train, X_val = splits[0], splits[1]
    train_labels = {c: splits[2 + i * 2]     for i, c in enumerate(LABEL_COLS)}
    val_labels   = {c: splits[2 + i * 2 + 1] for i, c in enumerate(LABEL_COLS)}

    tokenizer = BertTokenizer.from_pretrained(BERT_MODEL)
    tokenizer.save_pretrained(MODEL_DIR / "tokenizer")

    train_ds = GrievanceDataset(X_train, train_labels, tokenizer, MAX_LEN)
    val_ds   = GrievanceDataset(X_val,   val_labels,   tokenizer, MAX_LEN)
    train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=2, pin_memory=True)
    val_dl   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    model = BERTMultiTaskClassifier(
        BERT_MODEL,
        num_type     = len(encoders["type"].classes_),
        num_category = len(encoders["category"].classes_),
        num_severity = len(encoders["severity"].classes_),
    ).to(DEVICE)

    optimizer   = AdamW(model.parameters(), lr=LR, eps=1e-8)
    total_steps = len(train_dl) * EPOCHS
    scheduler   = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=total_steps // 10, num_training_steps=total_steps
    )

    best_val_loss = float("inf")
    for epoch in range(1, EPOCHS + 1):
        train_loss            = train_epoch(model, train_dl, optimizer, scheduler, DEVICE)
        val_loss, preds, true = eval_epoch(model, val_dl, DEVICE)

        print(f"\nEpoch {epoch}/{EPOCHS}  train={train_loss:.4f}  val={val_loss:.4f}")
        for col in LABEL_COLS:
            print(f"\n── {col.upper()} ──")
            print(classification_report(true[col], preds[col],
                                        target_names=encoders[col].classes_))

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), MODEL_DIR / "best_model.pt")
            print("✓ Best model saved")

    print(f"\nTraining complete. Model saved to {MODEL_DIR}")


if __name__ == "__main__":
    main()
