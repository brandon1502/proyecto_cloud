from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import SessionLocal
import threading
from app.services.linux_adapter import simulate_slice_creation

router = APIRouter(prefix="/slices", tags=["slices"])

# --- Dependencia para obtener sesión DB ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Crear slice ---
@router.post("/")
def create_slice(db: Session = Depends(get_db)):
    # Insertar el slice en estado "creating"
    db.execute(
        text("INSERT INTO slices (owner_id, name, status) VALUES (1, 'Slice_EX1', 'creating')")
    )
    db.commit()
    slice_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    # Lanzar el proceso simulado en segundo plano (nueva conexión)
    def background_task(slice_id):
        db2 = SessionLocal()
        try:
            simulate_slice_creation(db2, slice_id)
        finally:
            db2.close()

    threading.Thread(target=background_task, args=(slice_id,)).start()

    return {"id": slice_id, "status": "creating"}

# --- Listar slices ---
@router.get("/")
def list_slices(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT slice_id, name, status, created_at FROM slices ORDER BY slice_id DESC")
    ).fetchall()
    return [dict(r._mapping) for r in rows]

# --- Ver detalle de slice + eventos ---
@router.get("/{slice_id}")
def slice_detail(slice_id: int, db: Session = Depends(get_db)):
    slice_row = db.execute(
        text("SELECT * FROM slices WHERE slice_id = :sid"), {"sid": slice_id}
    ).fetchone()
    if not slice_row:
        return {"error": "Slice no encontrado"}

    events = db.execute(
        text("SELECT * FROM slice_events WHERE slice_id = :sid ORDER BY event_id ASC"),
        {"sid": slice_id},
    ).fetchall()

    return {
        "slice": dict(slice_row._mapping),
        "events": [dict(e._mapping) for e in events],
    }
