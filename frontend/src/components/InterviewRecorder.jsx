import React, { useEffect, useRef, useState } from "react";
import api from "../api/axios";

export default function InterviewRecorder({ token, simulationId, simulation }) {
  const [attemptId, setAttemptId] = useState(null);
  const videoRef = useRef();
  const mediaRecorderRef = useRef();
  const screenRecorderRef = useRef();
  const faceDetectIntervalRef = useRef(null);
  const [recording, setRecording] = useState(false);
  const proctoring = useRef({ tab_blur_count: 0, multiple_faces: false, face_count: 0 });
  const editorEvents = useRef({ paste_count: 0 });
  
  // New interactive states
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [questions, setQuestions] = useState([]);
  const [speaking, setSpeaking] = useState(false);
  const [faceCount, setFaceCount] = useState(0);
  const [violations, setViolations] = useState([]);
  const [showWarning, setShowWarning] = useState(false);
  const speechSynthesisRef = useRef(null);

  useEffect(()=>{
    const onBlur = () => { 
      proctoring.current.tab_blur_count += 1;
      addViolation("⚠️ Tab switched or window lost focus");
    };
    window.addEventListener("blur", onBlur);
    return ()=> window.removeEventListener("blur", onBlur);
  },[]);

  useEffect(() => {
    // Parse questions from simulation prompt
    if (simulation?.prompt) {
      const lines = simulation.prompt.split('\n').filter(l => l.trim());
      const extractedQuestions = lines.length > 3 ? lines.slice(0, 5) : [
        simulation.prompt,
        "How would you approach this problem?",
        "What tools or technologies would you use?",
        "What challenges do you foresee?",
        "How would you ensure quality?"
      ];
      setQuestions(extractedQuestions);
    }
  }, [simulation]);

  const addViolation = (message) => {
    const timestamp = new Date().toLocaleTimeString();
    setViolations(prev => [...prev, { message, timestamp }]);
    setShowWarning(true);
    setTimeout(() => setShowWarning(false), 5000);
  };

  const speakQuestion = (text) => {
    if (!window.speechSynthesis) return;
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    utterance.lang = 'en-US';
    
    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    
    window.speechSynthesis.speak(utterance);
    speechSynthesisRef.current = utterance;
  };

  const startFaceDetection = async (videoEl, attemptId) => {
    // Use MediaPipe or FaceDetector - let's use a more reliable canvas-based detection
    faceDetectIntervalRef.current = setInterval(async () => {
      try {
        const canvas = document.createElement("canvas");
        canvas.width = videoEl.videoWidth || 640;
        canvas.height = videoEl.videoHeight || 480;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
        
        // Use face-api.js or basic detection
        // For now, use FaceDetector if available, otherwise use ML5 or face-api
        if ('FaceDetector' in window) {
          const detector = new window.FaceDetector({ fastMode: false, maxDetectedFaces: 10 });
          const results = await detector.detect(canvas);
          const count = results?.length || 0;
          
          setFaceCount(count);
          proctoring.current.face_count = count;
          
          if (count === 0) {
            addViolation("❌ No face detected - please stay in frame");
            await sendFaceFlag(attemptId, { no_face: true, face_count: count, timestamp_ms: Date.now() });
          } else if (count > 1) {
            proctoring.current.multiple_faces = true;
            addViolation(`🚨 MULTIPLE FACES DETECTED (${count}) - Only candidate allowed!`);
            await sendFaceFlag(attemptId, { multiple_faces: true, face_count: count, timestamp_ms: Date.now() });
          } else {
            // Exactly 1 face - good
            proctoring.current.multiple_faces = false;
          }
        } else {
          // Fallback: basic pixel analysis to detect presence
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const data = imageData.data;
          let skinPixels = 0;
          
          for (let i = 0; i < data.length; i += 4) {
            const r = data[i], g = data[i+1], b = data[i+2];
            // Simple skin tone detection
            if (r > 95 && g > 40 && b > 20 && r > g && r > b && Math.abs(r-g) > 15) {
              skinPixels++;
            }
          }
          
          const skinRatio = skinPixels / (canvas.width * canvas.height);
          if (skinRatio < 0.02) {
            setFaceCount(0);
            addViolation("❌ No face detected - please stay in frame");
          } else {
            setFaceCount(1); // Assume 1 face if skin detected
          }
        }
      } catch (err) {
        console.warn("Face detection error:", err);
      }
    }, 2000); // Check every 2 seconds (more frequent)
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

      // Start video recording
      const videoRec = new MediaRecorder(camStream, { mimeType: "video/webm;codecs=vp9" });
      videoRec.ondataavailable = (e) => { if (e.data && e.data.size > 0) uploadChunk(id, "video", e.data); };
      videoRec.start(2000);
      mediaRecorderRef.current = videoRec;

      // Request screen stream
      let screenStream;
      try {
        screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
        const screenRec = new MediaRecorder(screenStream, { mimeType: "video/webm;codecs=vp9" });
        screenRec.ondataavailable = (e) => { if (e.data && e.data.size > 0) uploadChunk(id, "screen", e.data); };
        screenRec.start(2000);
        screenRecorderRef.current = screenRec;
      } catch (screenErr) {
        console.warn("Screen sharing not available or denied:", screenErr);
        // Continue without screen recording - not critical
      }

      // start face detection
      startFaceDetection(videoRef.current, id);

      // paste detection
      window.addEventListener("paste", onPaste);
      setRecording(true);
      
      // Welcome message and start asking questions
      setTimeout(() => {
        speakQuestion(`Hello! Welcome to your ${simulation?.title || 'technical interview'}. Let's begin.`);
      }, 1000);
      
      // Ask first question after welcome
      setTimeout(() => {
        if (questions.length > 0) {
          speakQuestion(questions[0]);
        }
      }, 5000);
      
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

  const nextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      const next = currentQuestion + 1;
      setCurrentQuestion(next);
      speakQuestion(questions[next]);
    } else {
      speakQuestion("Great! That's all the questions. Please click Stop and Submit when you're ready.");
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
    addViolation("📋 Paste detected - external content usage flagged");
  };

  return (
    <div className="space-y-4">
      {/* Real-time Warning Banner */}
      {showWarning && violations.length > 0 && (
        <div className="bg-red-100 border-2 border-red-500 rounded-lg p-4 animate-pulse">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🚨</span>
            <div className="flex-1">
              <p className="font-bold text-red-800">PROCTORING ALERT</p>
              <p className="text-sm text-red-700">{violations[violations.length - 1].message}</p>
            </div>
          </div>
        </div>
      )}

      {/* Interview Status Bar */}
      <div className="bg-gradient-to-r from-purple-100 to-teal-100 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`flex items-center gap-2 ${faceCount === 1 ? 'text-green-600' : 'text-red-600'}`}>
              <span className="text-2xl">👤</span>
              <div>
                <p className="text-xs font-semibold">Face Detection</p>
                <p className="text-sm font-bold">{faceCount === 0 ? 'No face' : faceCount === 1 ? '✓ 1 person' : `⚠️ ${faceCount} people`}</p>
              </div>
            </div>
            <div className={`flex items-center gap-2 ${recording ? 'text-red-600' : 'text-gray-400'}`}>
              <span className="text-2xl">🔴</span>
              <div>
                <p className="text-xs font-semibold">Recording</p>
                <p className="text-sm font-bold">{recording ? 'LIVE' : 'Not started'}</p>
              </div>
            </div>
            {recording && (
              <div className="flex items-center gap-2 text-purple-600">
                <span className="text-2xl">💬</span>
                <div>
                  <p className="text-xs font-semibold">Question</p>
                  <p className="text-sm font-bold">{currentQuestion + 1} of {questions.length}</p>
                </div>
              </div>
            )}
          </div>
          {speaking && (
            <div className="flex items-center gap-2 text-teal-600 animate-pulse">
              <span className="text-2xl">🔊</span>
              <p className="text-sm font-bold">AI Speaking...</p>
            </div>
          )}
        </div>
      </div>

      {/* Video Preview */}
      <div className="relative bg-gray-900 rounded-lg overflow-hidden">
        <video 
          ref={videoRef} 
          width="100%" 
          height="auto" 
          autoPlay 
          muted 
          className="rounded-lg"
          style={{ maxHeight: '400px', objectFit: 'cover' }}
        />
        {recording && (
          <div className="absolute top-4 right-4 bg-red-600 text-white px-3 py-1 rounded-full text-sm font-bold flex items-center gap-2 animate-pulse">
            <span className="w-2 h-2 bg-white rounded-full"></span>
            REC
          </div>
        )}
        {faceCount === 0 && recording && (
          <div className="absolute inset-0 bg-red-600/20 flex items-center justify-center">
            <div className="bg-red-600 text-white px-6 py-3 rounded-lg font-bold text-lg">
              ⚠️ NO FACE DETECTED
            </div>
          </div>
        )}
        {faceCount > 1 && recording && (
          <div className="absolute inset-0 bg-red-600/20 flex items-center justify-center">
            <div className="bg-red-600 text-white px-6 py-3 rounded-lg font-bold text-lg">
              🚨 MULTIPLE PEOPLE DETECTED
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex gap-3">
        {!recording && (
          <button 
            onClick={startInterview} 
            className="flex-1 py-3 bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-lg font-bold text-lg hover:shadow-xl hover:scale-105 transition-all flex items-center justify-center gap-2"
          >
            <span>🎥</span> Start Interview
          </button>
        )}
        {recording && (
          <>
            <button 
              onClick={nextQuestion}
              disabled={currentQuestion >= questions.length - 1}
              className={`flex-1 py-3 rounded-lg font-bold text-lg transition-all flex items-center justify-center gap-2 ${
                currentQuestion >= questions.length - 1 
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                  : 'bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:shadow-xl hover:scale-105'
              }`}
            >
              <span>⏭️</span> Next Question
            </button>
            <button 
              onClick={stopInterview} 
              className="flex-1 py-3 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-lg font-bold text-lg hover:shadow-xl hover:scale-105 transition-all flex items-center justify-center gap-2"
            >
              <span>⏹️</span> Stop & Submit
            </button>
          </>
        )}
      </div>

      {/* Violations Log */}
      {violations.length > 0 && (
        <div className="bg-white border border-red-200 rounded-lg p-4">
          <h4 className="font-bold text-red-800 mb-2 flex items-center gap-2">
            <span>⚠️</span> Proctoring Violations ({violations.length})
          </h4>
          <div className="max-h-32 overflow-y-auto space-y-1">
            {violations.slice(-5).reverse().map((v, i) => (
              <div key={i} className="text-xs text-red-700 border-l-2 border-red-400 pl-2">
                <span className="font-mono text-gray-500">[{v.timestamp}]</span> {v.message}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
