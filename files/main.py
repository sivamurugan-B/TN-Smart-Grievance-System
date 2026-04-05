"""
Tamil Nadu Grievance Management System - FastAPI Backend
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model"))

from datetime import datetime, timezone
from typing import List, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import db
from classifier import get_classifier

# ──────────────────────────────────────────
# App
# ──────────────────────────────────────────
app = FastAPI(
    title="Tamil Nadu Grievance Management API",
    description="AI-powered civic complaint classification and tracking system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────
class PredictRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=2000,
                      example="The drainage is overflowing near Tambaram market causing flooding.")

class PredictResponse(BaseModel):
    type:     str
    category: str
    severity: str
    method:   str

class ComplaintRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=2000)

class ComplaintResponse(BaseModel):
    id:         str
    text:       str
    type:       str
    category:   str
    severity:   str
    created_at: datetime
    method:     Optional[str] = None

class ComplaintsListResponse(BaseModel):
    total:      int
    complaints: List[ComplaintResponse]

class StatsResponse(BaseModel):
    total:              int
    by_severity:        dict
    by_category:        dict
    by_type:            dict
    recent_7days_count: int


# ──────────────────────────────────────────
# Startup
# ──────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    print("🚀 Starting Tamil Nadu Grievance API...")
    # Warm up classifier
    clf = get_classifier()
    test = clf.predict("The road has a large pothole near Anna Nagar.")
    print(f"✓ Classifier ready (method={test['method']})")


# ──────────────────────────────────────────
# Routes
# ──────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Tamil Nadu Grievance API is running"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/predict", response_model=PredictResponse, tags=["AI"])
async def predict(req: PredictRequest):
    """Predict type, category, and severity for a complaint text."""
    try:
        clf    = get_classifier()
        result = clf.predict(req.text)
        return PredictResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/complaint", response_model=ComplaintResponse, tags=["Complaints"])
async def submit_complaint(req: ComplaintRequest):
    """Submit a complaint – AI classifies it and stores to MongoDB."""
    try:
        clf    = get_classifier()
        result = clf.predict(req.text)

        doc = {
            "text":       req.text,
            "type":       result["type"],
            "category":   result["category"],
            "severity":   result["severity"],
            "method":     result.get("method", "unknown"),
            "created_at": datetime.now(timezone.utc),
        }
        inserted_id = await db.insert_complaint(doc)

        return ComplaintResponse(
            id         = inserted_id,
            text       = doc["text"],
            type       = doc["type"],
            category   = doc["category"],
            severity   = doc["severity"],
            created_at = doc["created_at"],
            method     = doc["method"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit complaint: {str(e)}")


@app.get("/complaints", response_model=ComplaintsListResponse, tags=["Complaints"])
async def get_complaints(
    page:     int  = Query(1, ge=1),
    limit:    int  = Query(50, ge=1, le=200),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    type:     Optional[str] = Query(None),
):
    """Retrieve complaints with optional filters and pagination."""
    filters = {}
    if category: filters["category"] = category
    if severity: filters["severity"] = severity
    if type:     filters["type"]     = type

    skip   = (page - 1) * limit
    result = await db.get_complaints(filters=filters, skip=skip, limit=limit)
    return ComplaintsListResponse(total=result["total"], complaints=result["complaints"])


@app.get("/stats", response_model=StatsResponse, tags=["Dashboard"])
async def get_stats():
    """Aggregated stats for the dashboard."""
    stats = await db.get_stats()
    return stats


@app.delete("/complaint/{complaint_id}", tags=["Complaints"])
async def delete_complaint(complaint_id: str):
    """Delete a complaint by ID."""
    deleted = await db.delete_complaint(complaint_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"message": "Complaint deleted", "id": complaint_id}


# ──────────────────────────────────────────
# Entry
# ──────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
