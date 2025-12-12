from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks, Body
from fastapi import status
from sqlalchemy.orm import Session
from database import get_db
from models import Simulation, SimulationAttempt, User
from auth import get_current_user
import os, uuid, aiofiles, json

router = APIRouter(prefix="/api/video-interviews", tags=["video-interviews"])
UPLOAD_TMP = os.getenv("UPLOAD_DIR", "/tmp/talentis_media")

@router.post("/start")
def start_interview(simulation_id: int = Form(...), db=Depends(get_db), user=Depends(get_current_user)):
    sim = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if user.role.value != "candidate":
        raise HTTPException(status_code=403, detail="Only candidates can start interview")
    attempt = SimulationAttempt(simulation_id=simulation_id, candidate_id=user.id, responses={})
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return {"attempt_id": attempt.id}

@router.post("/upload-chunk/{attempt_id}")
async def upload_chunk(attempt_id: int, kind: str = Form(...), chunk: UploadFile = File(...),
                       db=Depends(get_db), user=Depends(get_current_user)):
    """
    kind: "video", "screen", or "editor_events" (editor_events: small JSON)
    """
    attempt = db.query(SimulationAttempt).filter(SimulationAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.candidate_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    os.makedirs(UPLOAD_TMP, exist_ok=True)
    fname = f"{attempt_id}_{kind}_{uuid.uuid4().hex}.chunk"
    path = os.path.join(UPLOAD_TMP, fname)
    async with aiofiles.open(path, "wb") as out:
        content = await chunk.read()
        await out.write(content)
    # If editor events (JSON), optionally parse and persist in attempt.responses for later
    if kind == "editor_events":
        try:
            j = json.loads(content.decode("utf-8"))
            # append to responses.editor_events list
            resp = attempt.responses or {}
            resp_editor = resp.get("editor_events", {})
            # merge counts if exists
            for k,v in j.items():
                resp_editor[k] = resp_editor.get(k, 0) + v
            resp["editor_events"] = resp_editor
            attempt.responses = resp
            db.add(attempt); db.commit()
        except Exception:
            pass
    return {"status": "ok", "path": path}

@router.post("/finish/{attempt_id}", status_code=status.HTTP_202_ACCEPTED)
def finish_attempt(attempt_id: int, background_tasks: BackgroundTasks, db=Depends(get_db), user=Depends(get_current_user)):
    attempt = db.query(SimulationAttempt).filter(SimulationAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.candidate_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    # Kick off assembler + analysis in background
    background_tasks.add_task(_assemble_and_analyze, attempt_id)
    return {"status": "processing", "attempt_id": attempt_id}

def _assemble_and_analyze(attempt_id: int):
    # Use a DB session inside background worker
    from database import SessionLocal
    from services.media_assembler import assemble_chunks_and_store
    from services.asr_and_analysis import analyze_media_async
    db = None
    try:
        db = SessionLocal()
        assemble_chunks_and_store(db, attempt_id)
        analyze_media_async(db, attempt_id)
    except Exception as e:
        print(f"Error in background task: {e}")
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass

@router.post("/face-flag/{attempt_id}")
def face_flag(attempt_id: int, payload: dict = Body(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Accepts lightweight proctoring pings from the browser.
    payload example: {"multiple_faces": true, "face_count": 2, "timestamp_ms": 123456789}
    Stores under SimulationAttempt.responses['proctoring'].
    """
    attempt = db.query(SimulationAttempt).filter(SimulationAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.candidate_id != user.id:
        # allow candidates to report their own session only; recruiters could also call a different route if needed
        raise HTTPException(status_code=403, detail="Not allowed")

    try:
        resp = attempt.responses or {}
        proctor = resp.get("proctoring", {})
        # merge incoming payload: prefer to keep highest observed face_count and sum blur counts etc.
        if "face_count" in payload:
            proctor["face_count"] = max(proctor.get("face_count", 0), int(payload.get("face_count", 0)))
        if "multiple_faces" in payload:
            proctor["multiple_faces"] = bool(payload.get("multiple_faces"))
        # optional fields
        if "tab_blur_count" in payload:
            proctor["tab_blur_count"] = proctor.get("tab_blur_count", 0) + int(payload.get("tab_blur_count", 0))
        # store last_seen timestamp
        proctor["last_seen_ts"] = payload.get("timestamp_ms")
        resp["proctoring"] = proctor
        attempt.responses = resp
        db.add(attempt); db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status":"ok", "proctoring": proctor}

@router.get("/review/{attempt_id}")
def get_review(attempt_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    attempt = db.query(SimulationAttempt).filter(SimulationAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    # Authorization: candidate who owns it or employer of job or admin — for prototype we allow auth users
    return {
        "id": attempt.id,
        "simulation_id": attempt.simulation_id,
        "video_url": attempt.video_url,
        "screen_url": attempt.screen_url,
        "transcript": attempt.transcript,
        "behavior_analysis": attempt.behavior_analysis,
        "proctoring_flags": attempt.proctoring_flags,
        "cheating_risk": attempt.cheating_risk
    }
