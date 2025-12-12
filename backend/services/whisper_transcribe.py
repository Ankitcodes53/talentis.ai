# services/whisper_transcribe.py
"""
Audio transcription using Whisper
"""
import os
import logging
from pathlib import Path
from database import SessionLocal
from models import SimulationAttempt

logger = logging.getLogger(__name__)

# Try to import whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
    model_name = os.getenv("WHISPER_MODEL", "small")
    logger.info(f"Loading Whisper model: {model_name}")
    WHISPER_MODEL = whisper.load_model(model_name)
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.warning(f"Whisper not available: {e}")
    WHISPER_AVAILABLE = False
    WHISPER_MODEL = None


def transcribe_file_local(path: str):
    """
    Transcribe audio file using local Whisper model
    
    Args:
        path: Path to audio file
        
    Returns:
        tuple: (transcript_text, raw_whisper_result)
    """
    if not WHISPER_AVAILABLE:
        raise RuntimeError("Whisper model not available. Install openai-whisper.")
    
    # Ensure path exists
    if not Path(path).exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    
    logger.info(f"Transcribing file: {path}")
    
    # Whisper returns dict with 'text' among other fields
    result = WHISPER_MODEL.transcribe(path, language="en")
    text = result.get("text", "")
    
    logger.info(f"Transcription complete. Length: {len(text)} chars")
    
    return text, result


def transcribe_and_attach_to_attempt(attempt_id: int, media_path: str):
    """
    Convenience wrapper: transcribe media_path and attach transcript to DB attempt.
    
    Args:
        attempt_id: SimulationAttempt ID
        media_path: Path to audio/video file
    """
    session = SessionLocal()
    try:
        attempt = session.query(SimulationAttempt).filter(
            SimulationAttempt.id == attempt_id
        ).first()
        
        if not attempt:
            raise RuntimeError(f"Attempt not found: {attempt_id}")
        
        # Transcribe the file
        transcript, raw = transcribe_file_local(media_path)
        
        # Update attempt with transcript
        attempt.transcript = transcript
        
        # Store some metadata in behavior_analysis
        current_behavior = attempt.behavior_analysis or {}
        current_behavior["_whisper_raw_summary"] = {
            "word_count": len(transcript.split()),
            "char_count": len(transcript),
            "raw_keys": list(raw.keys())[:5]
        }
        attempt.behavior_analysis = current_behavior
        
        session.add(attempt)
        session.commit()
        
        logger.info(f"Transcript attached to attempt {attempt_id}")
        
    except Exception as e:
        session.rollback()
        logger.exception(f"Error transcribing and attaching: {e}")
        raise
    finally:
        session.close()
