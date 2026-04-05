# 🏛️ Tamil Nadu Grievance Management System
## AI-Powered Civic Complaint Platform · BERT + FastAPI + React + MongoDB

---

## 📁 Folder Structure

```
grievance-system/
├── model/
│   ├── train_model.py          ← BERT multi-task training script
│   ├── classifier.py           ← Inference engine (BERT + rule-based fallback)
│   ├── requirements.txt
│   └── saved_model/            ← Created after training
│       ├── best_model.pt
│       ├── class_info.json
│       ├── label_encoders.pkl
│       └── tokenizer/
│
├── backend/
│   ├── main.py                 ← FastAPI app + all endpoints
│   ├── database.py             ← MongoDB (Motor async) + in-memory fallback
│   └── requirements.txt
│
├── frontend/
│   ├── package.json
│   └── public/
│       └── index.html          ← Complete React app (single file, zero build needed)
│
└── data/
    └── tamilnadu_grievance_dataset_10000_v2.csv
```

---

## 🚀 Quick Start

### 1. Clone & Set Up Data
```bash
mkdir grievance-system && cd grievance-system
# Place the CSV in:  data/tamilnadu_grievance_dataset_10000_v2.csv
```

### 2. Train the BERT Model (optional – rule-based fallback works without)
```bash
cd model
pip install -r requirements.txt
python train_model.py
# Training takes ~30 min on GPU, ~2-3 hrs on CPU
# Model saved to saved_model/
```

### 3. Start the Backend
```bash
cd backend
pip install -r requirements.txt

# With MongoDB running locally:
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Without MongoDB (uses in-memory store automatically):
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Custom MongoDB URI:
MONGO_URI=mongodb://user:pass@host:27017 uvicorn main:app --reload
```

### 4. Open the Frontend
```bash
# Option A: Just open in browser (zero build needed)
open frontend/public/index.html

# Option B: npm start (with hot reload)
cd frontend
npm install
npm start
# → Opens at http://localhost:3000
```

---

## 🧠 AI Architecture

### BERT Multi-Task Classifier

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
Hybrid Severity (model prediction + keyword rules)
```

### Severity Hybrid Logic
```python
HIGH_KEYWORDS   = ["overflow","burst","danger","flood","collapse","fire","emergency",...]
MEDIUM_KEYWORDS = ["2 days","3 days","week","pending","repeatedly","pothole","blocked",...]

# Rule overrides model if keywords found
final_severity = rule_severity_boost(text, bert_prediction)
```

### Fallback Chain
```
BERT model found? → Use BERT
     │
     No
     ▼
Rule-based NLP (keyword matching for all 3 tasks)
```

---

## 📡 API Reference

### POST /predict
Classify complaint text without storing it.
```json
// Request
{ "text": "Sewage overflowing near Adyar market for 2 days" }

// Response
{
  "type": "Complaint",
  "category": "Drainage",
  "severity": "High",
  "method": "bert"
}
```

### POST /complaint
Submit, classify, and store a complaint.
```json
// Request
{ "text": "Please fix the broken street light on Mount Road" }

// Response
{
  "id": "665abc123def456...",
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

Response: { "total": 186, "complaints": [...] }
```

### GET /stats
```json
{
  "total": 1247,
  "by_severity": { "High": 312, "Medium": 298, "Low": 637 },
  "by_category": { "Water": 186, "Road": 210, "Electricity": 198, ... },
  "by_type": { "Complaint": 485, "Request": 421, "Suggestion": 341 },
  "recent_7days_count": 83
}
```

### DELETE /complaint/{id}
```
DELETE /complaint/665abc123def456
Response: { "message": "Complaint deleted", "id": "665abc123def456" }
```

---

## 🗄️ MongoDB Schema

```javascript
{
  _id: ObjectId,
  text: String,       // Original complaint text
  type: String,       // "Complaint" | "Request" | "Suggestion"
  category: String,   // "Water" | "Road" | "Electricity" | "Garbage" | "Drainage" | "Health" | "Transport"
  severity: String,   // "Low" | "Medium" | "High"
  method: String,     // "bert" | "rule-based"
  created_at: Date    // UTC timestamp
}
```

---

## 📊 Dataset Statistics
- **Total records**: 10,000
- **Types**: Complaint (33.7%), Request (33.6%), Suggestion (32.7%)
- **Categories**: Balanced across 7 categories (~1,400 each)
- **Severity**: Low (75.8%), High (19.6%), Medium (4.7%)

---

## 🔧 Environment Variables

| Variable   | Default                        | Description             |
|------------|--------------------------------|-------------------------|
| MONGO_URI  | mongodb://localhost:27017      | MongoDB connection URI  |
| DB_NAME    | grievance_db                   | Database name           |
| REACT_APP_API_URL | http://localhost:8000  | Backend URL for React   |

---

## 🏗️ Production Deployment

### Docker Compose (recommended)
```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:7
    volumes: [mongo_data:/data/db]
    ports: ["27017:27017"]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - MONGO_URI=mongodb://mongodb:27017
    depends_on: [mongodb]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - REACT_APP_API_URL=http://backend:8000

volumes:
  mongo_data:
```

### Nginx Reverse Proxy
```nginx
location /api/ {
    proxy_pass http://backend:8000/;
}
location / {
    root /usr/share/nginx/html;
    try_files $uri /index.html;
}
```

---

## 🔍 Testing

```bash
# Health check
curl http://localhost:8000/health

# Predict
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"Sewage overflowing near Adyar market for 2 days"}'

# Submit complaint
curl -X POST http://localhost:8000/complaint \
  -H "Content-Type: application/json" \
  -d '{"text":"Please fix the pothole on OMR"}'

# Get all complaints
curl http://localhost:8000/complaints?limit=10

# Get stats
curl http://localhost:8000/stats
```

---

## 📚 Interactive API Docs
FastAPI auto-generates Swagger UI:
- **Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
