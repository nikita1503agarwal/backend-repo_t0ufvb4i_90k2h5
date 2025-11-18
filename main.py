import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any, Dict

from database import db, create_document, get_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Utilities --------------------

def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d


def serialize_list(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [serialize_doc(d) for d in docs]


# -------------------- Root & Health --------------------

@app.get("/")
def read_root():
    return {"message": "English for Kids API is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# -------------------- Schemas (for request bodies) --------------------

class ProgressIn(BaseModel):
    user_id: str
    lesson_id: str
    correct: int = 0
    incorrect: int = 0
    last_score: Optional[int] = None


# -------------------- Content Endpoints --------------------

@app.get("/api/lessons")
def list_lessons():
    try:
        lessons = get_documents("lesson")
        return serialize_list(lessons)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/lessons/{lesson_id}/words")
def list_words_for_lesson(lesson_id: str):
    try:
        words = get_documents("word", {"lesson_id": lesson_id})
        return serialize_list(words)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/progress")
def submit_progress(payload: ProgressIn):
    """Insert a new progress record for now (simple approach)."""
    try:
        # Could be improved to upsert; for simplicity, just create a record
        data = payload.model_dump()
        new_id = create_document("progress", data)
        return {"id": new_id, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/progress/{user_id}/{lesson_id}")
def get_progress(user_id: str, lesson_id: str):
    try:
        docs = get_documents("progress", {"user_id": user_id, "lesson_id": lesson_id}, limit=1)
        return serialize_doc(docs[0]) if docs else {"status": "none"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- Seeder (demo content) --------------------

@app.post("/api/seed")
def seed_content():
    """Seed a few demo lessons and words if collections are empty."""
    try:
        lessons_count = db["lesson"].count_documents({}) if db else 0
        created = {"lessons": 0, "words": 0}

        if lessons_count == 0:
            # Create demo lessons
            demo_lessons = [
                {"title": "צבעים", "english_title": "Colors", "description": "לומדים צבעים בסיסיים", "level": "beginner", "cover_emoji": "🎨"},
                {"title": "חיות", "english_title": "Animals", "description": "מכירים חיות נפוצות", "level": "beginner", "cover_emoji": "🐾"},
                {"title": "אוכל", "english_title": "Food", "description": "מילים על אוכל טעים", "level": "beginner", "cover_emoji": "🍎"},
            ]
            lesson_ids: List[str] = []
            for l in demo_lessons:
                lid = create_document("lesson", l)
                lesson_ids.append(lid)
                created["lessons"] += 1

            # Words per lesson
            color_words = [
                {"english": "red", "hebrew": "אדום"},
                {"english": "blue", "hebrew": "כחול"},
                {"english": "green", "hebrew": "ירוק"},
                {"english": "yellow", "hebrew": "צהוב"},
            ]
            animal_words = [
                {"english": "dog", "hebrew": "כלב"},
                {"english": "cat", "hebrew": "חתול"},
                {"english": "bird", "hebrew": "ציפור"},
                {"english": "fish", "hebrew": "דג"},
            ]
            food_words = [
                {"english": "apple", "hebrew": "תפוח"},
                {"english": "bread", "hebrew": "לחם"},
                {"english": "milk", "hebrew": "חלב"},
                {"english": "cheese", "hebrew": "גבינה"},
            ]

            for w in color_words:
                create_document("word", {**w, "lesson_id": lesson_ids[0]})
                created["words"] += 1
            for w in animal_words:
                create_document("word", {**w, "lesson_id": lesson_ids[1]})
                created["words"] += 1
            for w in food_words:
                create_document("word", {**w, "lesson_id": lesson_ids[2]})
                created["words"] += 1
        else:
            return {"status": "exists", "message": "Lessons already seeded"}

        return {"status": "ok", "created": created}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
