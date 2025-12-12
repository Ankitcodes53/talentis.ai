import React, { useEffect, useRef, useState } from "react";
import api from "../api/axios";

export default function InterviewRecorder({ token, simulationId }) {
  const [attemptId, setAttemptId] = useState(null);
  const videoRef = useRef();
  const mediaRecorderRef = useRef();
  const screenRecorderRef = useRef();
  const faceDetectIntervalRef = useRef(null);
  const [recording, setRecording] = useState(false);
  const proctoring = useRef({ tab_blur_count: 0, multiple_faces: false, face_count: 0 });
  const editorEvents = useRef({ paste_count: 0 });

  useEffect(()=>{
    const onBlur = () => { proctoring.current.tab_blur_count += 1; };
    window.addEventListener("blur", onBlur);
    return ()=> window.removeEventListener("blur", onBlur);
  },[]);

  const startFaceDetection = async (videoEl, attemptId) => {
    // Use the FaceDetector Web API if available
    const supportsFaceDetector = ('FaceDetector' in window);
    if (!supportsFaceDetector) {
      console.warn("FaceDetector not supported in this browser. Skipping client face detection.");
      return;
    }
    const detector = new window.FaceDetector({ fastMode: true, maxDetectedFaces: 4 });

    faceDetectIntervalRef.current = setInterval(async () => {
      try {
        // capture a single frame from the video
        const canvas = document.createElement("canvas");
        canvas.width = videoEl.videoWidth || 320;
        canvas.height = videoEl.videoHeight || 240;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
        // perform detection
        const results = await detector.detect(canvas);
        const faceCount = results?.length || 0;
        if (faceCount > 1) {
          proctoring.current.multiple_faces = true;
          proctoring.current.face_count = faceCount;
          // send a ping once (or you can send repeated pings if you want)
          await sendFaceFlag(attemptId, { multiple_faces: true, face_count: faceCount, timestamp_ms: Date.now() });
        } else {
          // update last known face_count
          proctoring.current.face_count = faceCount;
        }
      } catch (err) {
        console.warn("Face detection error:", err);
      }
    }, 3000); // every 3 seconds
  };

  const stopFaceDetection = () => {
    if (faceDetectIntervalRef.current) {
      clearInterval(faceDetectIntervalRef.current);
      faceDetectIntervalRef.current = null;
    }
  };

  const sendFaceFlag = async (attemptId, payload) => {
    try {
      await api.post(`/api/video-interviews/face-flag/${attemptId}`, payload);
    } catch (e) {
      console.warn("Failed to send face flag:", e);
    }
  };

  const startInterview = async () => {
    try {
      if (simulationId === null || simulationId === undefined) {
        alert("Cannot start interview: No simulation available");
        return;
      }

      // Step 1: Request camera and microphone permissions with popup
      const permissionGranted = window.confirm(
        "This interview requires access to your camera and microphone for video recording.\n\n" +
        "Click OK to grant permissions and start the interview."
      );
      
      if (!permissionGranted) {
        alert("Camera and microphone access is required to start the interview.");
        return;
      }

      // Step 2: Request actual media permissions
      let camStream;
      try {
        camStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      } catch (err) {
        alert("Failed to access camera/microphone. Please check your browser permissions and try again.");
        console.error("Media permission error:", err);
        return;
      }

      // Step 3: Start interview attempt - use regular JSON body instead of FormData
      console.log('Starting interview with simulation_id:', simulationId);
      
      const r = await api.post("/api/video-interviews/start", {
        simulation_id: simulationId
      });
      const id = r.data.attempt_id;
      setAttemptId(id);

      // Step 4: Setup camera stream
      videoRef.current.srcObject = camStream;
      await videoRef.current.play();

      const videoRec = new MediaRecorder(camStream, { mimeType: "video/webm;codecs=vp9" });
      videoRec.ondataavailable = (e) => { if (e.data && e.data.size > 0) uploadChunk(id, "video", e.data); };
      videoRec.start(2000);
      mediaRecorderRef.current = videoRec;

      // Screen stream
      const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
      const screenRec = new MediaRecorder(screenStream, { mimeType: "video/webm;codecs=vp9" });
      screenRec.ondataavailable = (e) => { if (e.data && e.data.size > 0) uploadChunk(id, "screen", e.data); };
      screenRec.start(2000);
      screenRecorderRef.current = screenRec;

      // start face detection (if supported)
      startFaceDetection(videoRef.current, id);

      // paste detection
      window.addEventListener("paste", onPaste);
      setRecording(true);
    } catch (error) {
      console.error("Failed to start interview:", error);
      let errorMsg = "Unknown error";
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMsg = error.response.data.detail.map(e => e.msg || e).join(', ');
        } else if (typeof error.response.data.detail === 'object') {
          errorMsg = JSON.stringify(error.response.data.detail);
        } else {
          errorMsg = error.response.data.detail;
        }
      } else if (error.message) {
        errorMsg = error.message;
      }
      alert("Failed to start interview: " + errorMsg);
    }
  };

  const stopInterview = async () => {
    if(mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") mediaRecorderRef.current.stop();
    if(screenRecorderRef.current && screenRecorderRef.current.state !== "inactive") screenRecorderRef.current.stop();
    stopFaceDetection();
    window.removeEventListener("paste", onPaste);

    // upload final small JSON chunk for editor events + proctoring flags
    const fd = new FormData();
    fd.append("kind", "editor_events");
    const blob = new Blob([JSON.stringify({ paste_count: editorEvents.current.paste_count, proctoring: proctoring.current })], { type: "application/json" });
    fd.append("chunk", blob, "editor_events.json");
    await api.post(`/api/video-interviews/upload-chunk/${attemptId}`, fd, {
      headers: { "Content-Type": "multipart/form-data" }
    });

    await api.post(`/api/video-interviews/finish/${attemptId}`, {});
    alert("Interview submitted successfully!");
    setRecording(false);
  };

  const uploadChunk = async (attemptId, kind, blob) => {
    const fd = new FormData();
    fd.append("kind", kind);
    fd.append("chunk", blob, `${kind}.webm`);
    await api.post(`/api/video-interviews/upload-chunk/${attemptId}`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
    }).catch((err)=>console.warn("Chunk upload failed:", err));
  };

  const onPaste = (e) => {
    editorEvents.current.paste_count = (editorEvents.current.paste_count || 0) + 1;
  };

  return (
    <div className="p-4 bg-white rounded shadow">
      <h3 className="text-lg font-semibold mb-2">Interview Recorder</h3>
      <video ref={videoRef} width="320" height="240" autoPlay muted className="border" />
      <div className="mt-3">
        {!recording && <button onClick={startInterview} className="px-4 py-2 bg-green-600 text-white rounded">Start Interview</button>}
        {recording && <button onClick={stopInterview} className="px-4 py-2 bg-red-600 text-white rounded">Stop & Submit</button>}
      </div>
      <div className="mt-2 text-sm text-gray-600">Tab switches: {proctoring.current.tab_blur_count} • Faces: {proctoring.current.face_count} • Multiple faces: {proctoring.current.multiple_faces ? "Yes": "No"}</div>
    </div>
  );
}
