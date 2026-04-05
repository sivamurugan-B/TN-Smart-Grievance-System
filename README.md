m# Tamil Nadu AI Grievance Management System

AI-powered civic complaint platform – BERT + FastAPI + React + MongoDB

---

## Folder Structure

```
Ai Grievance System/
├── backend/
│   ├── main.py          ← FastAPI app (all endpoints)
│   ├── database.py      ← MongoDB (Motor async) + in-memory fallback
│   └── requirements.txt
│
├── model/
│   ├── classifier.py    ← Inference engine (BERT + rule-based fallback)
│   ├── train.py         ← BERT multi-task training script
│   ├── requirements.txt
│   └── saved_model/     ← Created after training
│       ├── best_model.pt
│       ├── class_info.json
│       ├── label_encoders.pkl
│       └── tokenizer/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── ComplaintForm.jsx
│   │   │   ├── ResultCard.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── ComplaintTable.jsx
│   │   ├── services/api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
└── data/
    └── tamilnadu_grievance_dataset_10000_v2.csv
```

---

## Quick Start

### Step 1 — Train the BERT Model (optional, ~30 min GPU / 2-3 hr CPU)

```bash
cd model
pip install -r requirements.txt
python train.py
# Saves to model/saved_model/
```

> If you skip this step the system uses the rule-based fallback automatically.

---

### Step 2 — Start the Backend

```bash
cd backend
pip install -r requirements.txt

# With MongoDB running locally:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
python -m uvicorn main:app --reload --port 8000


# Custom MongoDB URI:
MONGO_URI=mongodb://user:pass@host:27017 uvicorn main:app --reload
```

API docs available at: http://localhost:8000/docs

---

### Step 3 — Start the Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## API Reference

| Method | Endpoint            | Description                          |
|--------|---------------------|--------------------------------------|
| GET    | /health             | Health check                         |
| POST   | /predict            | Classify text (no storage)           |
| POST   | /complaint          | Submit + classify + store            |
| GET    | /complaints         | List with filters & pagination       |
| GET    | /stats              | Dashboard aggregations               |
| DELETE | /complaint/{id}     | Delete a complaint                   |

### POST /predict

```json
// Request
{ "text": "Sewage overflowing near Adyar market for 2 days" }

// Response
{ "type": "Complaint", "category": "Drainage", "severity": "High", "method": "bert" }
```

### POST /complaint

```json
// Request
{ "text": "Please fix the broken street light on Mount Road" }

// Response
{
  "id": "665abc123...",
  "text": "Please fix the broken street light on Mount Road",
  "type": "Request",
  "category": "Electricity",
  "severity": "Medium",
  "created_at": "2024-06-15T10:30:00Z",
  "method": "bert"
}
```

### GET /complaints

```
GET /complaints?page=1&limit=50&category=Water&severity=High&type=Complaint
```

---

## MongoDB Schema

```json
{
  "_id":        "ObjectId",
  "text":       "string",
  "type":       "Complaint | Request | Suggestion",
  "category":   "Water | Road | Electricity | Garbage | Drainage | Health | Transport",
  "severity":   "Low | Medium | High",
  "method":     "bert | rule-based",
  "created_at": "ISO timestamp"
}
```

---

## AI Architecture

```
Input Text
    │
    ▼
BertTokenizer (bert-base-uncased, max_len=128)
    │
    ▼
BertModel → pooler_output [batch, 768]
    │
    ├──► fc_type     → [Complaint, Request, Suggestion]
    ├──► fc_category → [Water, Road, Electricity, Garbage, Drainage, Health, Transport]
    └──► fc_severity → [Low, Medium, High]
    │
    ▼
Hybrid Severity (model + keyword rules)
```

### Severity Hybrid Logic

```python
HIGH_KEYWORDS   = ["overflow", "burst", "danger", "flood", "collapse", "emergency", ...]
MEDIUM_KEYWORDS = ["2 days", "3 days", "week", "pothole", "blocked", "stagnant", ...]
# Rule overrides BERT if keywords matched
```

---

## Environment Variables

| Variable      | Default                   | Description         |
|---------------|---------------------------|---------------------|
| MONGO_URI     | mongodb://localhost:27017 | MongoDB URI         |
| DB_NAME       | grievance_db              | Database name       |
| VITE_API_URL  | http://localhost:8000     | Backend URL         |
