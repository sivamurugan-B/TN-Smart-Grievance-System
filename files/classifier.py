"""
Grievance Classifier - Inference Engine
Loads trained BERT model and predicts type/category/severity.
Falls back to rule-based if model not found.
"""

import re
import json
import pickle
import torch
import torch.nn as nn
from pathlib import Path
from transformers import BertTokenizer, BertModel

MODEL_DIR = Path(__file__).parent / "saved_model"
DEVICE    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MAX_LEN   = 128

# ──────────────────────────────────────────
# Severity keyword rules
# ──────────────────────────────────────────
HIGH_KEYWORDS   = ["overflow","burst","danger","dangerous","flood","collapse","fire","emergency",
                   "accident","death","sewage","leak","collapse","broken pipe","electric shock"]
MEDIUM_KEYWORDS = ["2 days","3 days","week","weeks","month","pending","repeatedly","continuous",
                   "pothole","blocked","overflowing","stagnant","smell","odor"]

def rule_severity_boost(text: str, model_severity: str) -> str:
    t = text.lower()
    if any(k in t for k in HIGH_KEYWORDS):
        return "High"
    if any(k in t for k in MEDIUM_KEYWORDS):
        return "Medium" if model_severity == "Low" else model_severity
    return model_severity


# ──────────────────────────────────────────
# BERT model definition (must match train)
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
        return self.fc_type(pooled), self.fc_category(pooled), self.fc_severity(pooled)


# ──────────────────────────────────────────
# Rule-based fallback (no trained model)
# ──────────────────────────────────────────
_TYPE_PATTERNS = {
    "Complaint": ["problem","issue","not working","broken","damaged","complaint","no water",
                  "no electricity","blocked","overflow","pothole","garbage"],
    "Request":   ["please","kindly","arrange","fix","repair","install","provide","requesting",
                  "request","need","require"],
    "Suggestion":["suggest","suggestion","better","improve","should","could","recommend","if possible"],
}

_CAT_PATTERNS = {
    "Water":       ["water","pipe","tap","supply","drinking water","leakage","pipeline"],
    "Road":        ["road","pothole","pavement","footpath","highway","street","tar"],
    "Electricity": ["electricity","light","power","street light","electric","current","transformer"],
    "Garbage":     ["garbage","waste","trash","litter","dump","bin","sanitation","sewage"],
    "Drainage":    ["drainage","drain","sewage","overflow","flood","waterlogging","clog"],
    "Health":      ["health","disease","mosquito","dengue","malaria","hospital","medical","stagnant"],
    "Transport":   ["bus","transport","metro","auto","signal","traffic","road divider","flyover"],
}

def _rule_classify(text: str) -> dict:
    t = text.lower()

    # Type
    type_scores = {k: sum(1 for kw in kws if kw in t) for k, kws in _TYPE_PATTERNS.items()}
    pred_type   = max(type_scores, key=type_scores.get)
    if max(type_scores.values()) == 0:
        pred_type = "Complaint"

    # Category
    cat_scores = {k: sum(1 for kw in kws if kw in t) for k, kws in _CAT_PATTERNS.items()}
    pred_cat   = max(cat_scores, key=cat_scores.get)
    if max(cat_scores.values()) == 0:
        pred_cat = "Road"

    # Severity (rule-based)
    pred_sev = "Low"
    if any(k in t for k in HIGH_KEYWORDS):
        pred_sev = "High"
    elif any(k in t for k in MEDIUM_KEYWORDS):
        pred_sev = "Medium"

    return {"type": pred_type, "category": pred_cat, "severity": pred_sev,
            "method": "rule-based"}


# ──────────────────────────────────────────
# Classifier class
# ──────────────────────────────────────────
class GrievanceClassifier:
    def __init__(self):
        self.model     = None
        self.tokenizer = None
        self.classes   = None
        self._load_model()

    def _load_model(self):
        weights_path = MODEL_DIR / "best_model.pt"
        class_path   = MODEL_DIR / "class_info.json"
        tok_path     = MODEL_DIR / "tokenizer"

        if not (weights_path.exists() and class_path.exists() and tok_path.exists()):
            print("⚠ No trained model found – using rule-based classifier.")
            return

        try:
            with open(class_path) as f:
                self.classes = json.load(f)

            self.tokenizer = BertTokenizer.from_pretrained(str(tok_path))

            self.model = BERTMultiTaskClassifier(
                "bert-base-uncased",
                num_type=len(self.classes["type"]),
                num_category=len(self.classes["category"]),
                num_severity=len(self.classes["severity"]),
            )
            self.model.load_state_dict(
                torch.load(str(weights_path), map_location=DEVICE)
            )
            self.model.to(DEVICE)
            self.model.eval()
            print("✓ BERT model loaded successfully.")
        except Exception as e:
            print(f"⚠ Model load failed ({e}) – using rule-based fallback.")
            self.model = None

    def predict(self, text: str) -> dict:
        if self.model is None:
            result = _rule_classify(text)
            result["severity"] = rule_severity_boost(text, result["severity"])
            return result

        enc = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=MAX_LEN,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        input_ids      = enc["input_ids"].to(DEVICE)
        attention_mask = enc["attention_mask"].to(DEVICE)

        with torch.no_grad():
            t_logits, c_logits, s_logits = self.model(input_ids, attention_mask)

        pred_type     = self.classes["type"][torch.argmax(t_logits, dim=1).item()]
        pred_category = self.classes["category"][torch.argmax(c_logits, dim=1).item()]
        pred_severity = self.classes["severity"][torch.argmax(s_logits, dim=1).item()]

        # Hybrid severity boost
        pred_severity = rule_severity_boost(text, pred_severity)

        return {
            "type":     pred_type,
            "category": pred_category,
            "severity": pred_severity,
            "method":   "bert",
        }


# Singleton instance
_classifier = None

def get_classifier() -> GrievanceClassifier:
    global _classifier
    if _classifier is None:
        _classifier = GrievanceClassifier()
    return _classifier
