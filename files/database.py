"""
Database layer – MongoDB via Motor (async)
Falls back to in-memory store if MongoDB is unavailable.
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.getenv("DB_NAME",   "grievance_db")
COL_NAME  = "complaints"

# ──────────────────────────────────────────
# Try Motor (async MongoDB driver)
# ──────────────────────────────────────────
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from bson import ObjectId

    class MongoDatabase:
        def __init__(self):
            self.client     = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=3000)
            self.db         = self.client[DB_NAME]
            self.collection = self.db[COL_NAME]

        async def insert_complaint(self, doc: dict) -> str:
            result = await self.collection.insert_one(doc)
            return str(result.inserted_id)

        async def get_complaints(self, filters=None, skip=0, limit=50) -> dict:
            query  = filters or {}
            total  = await self.collection.count_documents(query)
            cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
            docs   = []
            async for doc in cursor:
                docs.append(self._serialize(doc))
            return {"total": total, "complaints": docs}

        async def get_stats(self) -> dict:
            total = await self.collection.count_documents({})

            pipeline_sev = [{"$group": {"_id": "$severity", "count": {"$sum": 1}}}]
            pipeline_cat = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}]
            pipeline_typ = [{"$group": {"_id": "$type",     "count": {"$sum": 1}}}]

            sev_raw = await self.collection.aggregate(pipeline_sev).to_list(None)
            cat_raw = await self.collection.aggregate(pipeline_cat).to_list(None)
            typ_raw = await self.collection.aggregate(pipeline_typ).to_list(None)

            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            recent   = await self.collection.count_documents({"created_at": {"$gte": week_ago}})

            return {
                "total":              total,
                "by_severity":        {r["_id"]: r["count"] for r in sev_raw if r["_id"]},
                "by_category":        {r["_id"]: r["count"] for r in cat_raw if r["_id"]},
                "by_type":            {r["_id"]: r["count"] for r in typ_raw if r["_id"]},
                "recent_7days_count": recent,
            }

        async def delete_complaint(self, complaint_id: str) -> bool:
            result = await self.collection.delete_one({"_id": ObjectId(complaint_id)})
            return result.deleted_count > 0

        def _serialize(self, doc: dict) -> dict:
            doc["id"] = str(doc.pop("_id"))
            return doc

    _db = MongoDatabase()
    print("✓ Connected to MongoDB (Motor async)")

except Exception as e:
    print(f"⚠ Motor/MongoDB unavailable ({e}) – using in-memory store.")

    # ──────────────────────────────────────────
    # In-memory fallback
    # ──────────────────────────────────────────
    class InMemoryDatabase:
        def __init__(self):
            self._store: list = []

        async def insert_complaint(self, doc: dict) -> str:
            cid        = str(uuid.uuid4())
            doc["id"]  = cid
            self._store.insert(0, dict(doc))
            return cid

        async def get_complaints(self, filters=None, skip=0, limit=50) -> dict:
            data = self._store
            if filters:
                for k, v in filters.items():
                    data = [d for d in data if d.get(k) == v]
            total = len(data)
            page  = data[skip: skip + limit]
            return {"total": total, "complaints": [self._fix(d) for d in page]}

        async def get_stats(self) -> dict:
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            total    = len(self._store)

            by_sev = {}
            by_cat = {}
            by_typ = {}
            recent = 0

            for d in self._store:
                by_sev[d.get("severity", "?")] = by_sev.get(d.get("severity", "?"), 0) + 1
                by_cat[d.get("category", "?")] = by_cat.get(d.get("category", "?"), 0) + 1
                by_typ[d.get("type", "?")]     = by_typ.get(d.get("type", "?"),     0) + 1
                ts = d.get("created_at")
                if isinstance(ts, datetime) and ts.tzinfo and ts >= week_ago:
                    recent += 1

            return {
                "total":              total,
                "by_severity":        by_sev,
                "by_category":        by_cat,
                "by_type":            by_typ,
                "recent_7days_count": recent,
            }

        async def delete_complaint(self, complaint_id: str) -> bool:
            before = len(self._store)
            self._store = [d for d in self._store if d.get("id") != complaint_id]
            return len(self._store) < before

        def _fix(self, d: dict) -> dict:
            return dict(d)

    _db = InMemoryDatabase()


db = _db
