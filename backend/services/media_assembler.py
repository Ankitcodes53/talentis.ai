import os, glob, shutil, subprocess
from pathlib import Path
from models import SimulationAttempt

UPLOAD_TMP = os.getenv("UPLOAD_DIR", "/tmp/talentis_media")
MEDIA_STORE = os.getenv("MEDIA_STORE", "/tmp/talentis_media/final")

def _concat_with_ffmpeg(chunks, outpath):
    listfile = outpath + ".list.txt"
    with open(listfile, "w") as lf:
        for c in chunks:
            lf.write(f"file '{os.path.abspath(c)}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-c", "copy", outpath]
    subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    try:
        os.remove(listfile)
    except:
        pass

def _binary_concat(chunks, outpath):
    with open(outpath, "wb") as wfd:
        for c in chunks:
            with open(c, "rb") as rfd:
                shutil.copyfileobj(rfd, wfd)

def assemble_chunks_and_store(db_session, attempt_id: int):
    os.makedirs(MEDIA_STORE, exist_ok=True)
    # find chunk files
    video_chunks = sorted(glob.glob(os.path.join(UPLOAD_TMP, f"{attempt_id}_video_*.chunk")))
    screen_chunks = sorted(glob.glob(os.path.join(UPLOAD_TMP, f"{attempt_id}_screen_*.chunk")))

    def assemble(chunks, filename):
        if not chunks:
            return None
        outpath = os.path.join(MEDIA_STORE, filename)
        try:
            _concat_with_ffmpeg(chunks, outpath)
        except Exception:
            # fallback to naive binary concat
            _binary_concat(chunks, outpath)
        return outpath

    video_path = assemble(video_chunks, f"attempt_{attempt_id}_video.webm")
    screen_path = assemble(screen_chunks, f"attempt_{attempt_id}_screen.webm")

    # update DB
    session = db_session
    attempt = session.query(SimulationAttempt).filter(SimulationAttempt.id == attempt_id).first()
    if attempt:
        if video_path:
            # store accessible URL path (relative to /media mount)
            video_name = os.path.basename(video_path)
            attempt.video_url = f"/media/{video_name}"
        if screen_path:
            screen_name = os.path.basename(screen_path)
            attempt.screen_url = f"/media/{screen_name}"
        session.add(attempt)
        session.commit()
    return video_path, screen_path
