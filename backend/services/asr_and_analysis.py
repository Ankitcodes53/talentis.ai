import os, json, math, traceback
from models import SimulationAttempt
from services.whisper_transcribe import transcribe_and_attach_to_attempt, transcribe_file_local, WHISPER_AVAILABLE

def simple_behavior_analyzer(transcript: str, editor_events: dict = None, proctoring: dict = None):
    text = (transcript or "").lower()
    steps = []
    if any(k in text for k in ["step", "first", "next", "then", "finally"]):
        steps.append("Stepwise reasoning detected")
    clarifying = []
    for kw in ["do you mean", "should i", "is the", "do we", "clarify"]:
        if kw in text:
            clarifying.append(kw)
    words = transcript.split() if transcript else []
    fluency = min(1.0, len(words)/150.0)
    # basic metrics
    return {
        "steps": steps,
        "clarifying_questions": clarifying,
        "word_count": len(words),
        "fluency": fluency,
        "editor_events_summary": editor_events or {}
    }

def analyze_media_async(db_session, attempt_id: int):
    try:
        session = db_session
        attempt = session.query(SimulationAttempt).filter(SimulationAttempt.id == attempt_id).first()
        if not attempt:
            return
        # pick best media (screen preferred if present)
        media_path = attempt.screen_url or attempt.video_url
        if not media_path:
            return
        # Transcribe using whisper_transcribe helper
        try:
            transcribe_and_attach_to_attempt(attempt_id, media_path)
        except Exception as e:
            # fallback: call transcribe_file_local directly and set transcript
            try:
                text, raw = transcribe_file_local(media_path)
                attempt.transcript = text
                session.add(attempt); session.commit()
            except Exception:
                pass

        # reload attempt
        attempt = session.query(SimulationAttempt).filter(SimulationAttempt.id == attempt_id).first()
        transcript = attempt.transcript or ""
        editor_events = (attempt.responses or {}).get("editor_events") if attempt.responses else {}
        proctoring = (attempt.responses or {}).get("proctoring") if attempt.responses else {}

        behavior = simple_behavior_analyzer(transcript, editor_events, proctoring)

        # Proctoring heuristics (simple)
        risk = 0.0
        flags = {}
        if proctoring and proctoring.get("multiple_faces"):
            flags["multiple_faces"] = proctoring.get("multiple_faces")
            risk += 0.5
        blur = proctoring.get("tab_blur_count", 0) if proctoring else 0
        flags["tab_blur_count"] = blur
        risk += min(0.3, 0.05 * blur)
        paste_count = editor_events.get("paste_count", 0) if editor_events else 0
        flags["paste_count"] = paste_count
        risk += min(0.3, 0.1 * paste_count)

        # Save analysis
        attempt.behavior_analysis = behavior
        attempt.proctoring_flags = flags
        attempt.cheating_risk = round(min(1.0, risk), 2)
        session.add(attempt)
        session.commit()

    except Exception:
        traceback.print_exc()
