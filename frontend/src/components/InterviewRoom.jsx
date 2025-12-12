import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import api from '../api/axios';

const InterviewRoom = ({ interviewId, questions, onComplete, onCancel }) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProctoringActive, setIsProctoringActive] = useState(false);
  const [proctoringFlags, setProctoringFlags] = useState([]);
  const [faceDetected, setFaceDetected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  // Refs for media
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const screenRecorderRef = useRef(null);
  const videoStreamRef = useRef(null);
  const screenStreamRef = useRef(null);
  const detectionIntervalRef = useRef(null);
  
  // Face-api.js state
  const [faceApiLoaded, setFaceApiLoaded] = useState(false);
  const [modelsLoaded, setModelsLoaded] = useState(false);

  useEffect(() => {
    loadFaceApi();
    return () => {
      cleanup();
    };
  }, []);

  const loadFaceApi = async () => {
    try {
      // Load face-api.js from CDN
      if (!window.faceapi) {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js';
        script.async = true;
        script.onload = () => {
          setFaceApiLoaded(true);
          loadModels();
        };
        script.onerror = () => {
          toast.error('Failed to load face detection library');
          setIsLoading(false);
        };
        document.body.appendChild(script);
      } else {
        setFaceApiLoaded(true);
        loadModels();
      }
    } catch (error) {
      console.error('Error loading face-api:', error);
      toast.error('Proctoring initialization failed');
      setIsLoading(false);
    }
  };

  const loadModels = async () => {
    try {
      const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model';
      
      await Promise.all([
        window.faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
        window.faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
        window.faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
      ]);
      
      setModelsLoaded(true);
      setIsLoading(false);
      toast.success('Proctoring system ready');
    } catch (error) {
      console.error('Error loading face-api models:', error);
      toast.error('Face detection models failed to load');
      setIsLoading(false);
    }
  };

  const startInterview = async () => {
    try {
      // Request camera access
      const videoStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: true
      });
      
      videoStreamRef.current = videoStream;
      if (videoRef.current) {
        videoRef.current.srcObject = videoStream;
      }

      // Request screen recording
      try {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: { mediaSource: 'screen' },
          audio: false
        });
        
        screenStreamRef.current = screenStream;
        
        // Set up screen recorder
        const mediaRecorder = new MediaRecorder(screenStream, {
          mimeType: 'video/webm;codecs=vp9'
        });
        
        const chunks = [];
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            chunks.push(event.data);
          }
        };
        
        mediaRecorder.onstop = () => {
          const blob = new Blob(chunks, { type: 'video/webm' });
          // In production, upload to server
          console.log('Screen recording saved:', blob.size, 'bytes');
        };
        
        screenRecorderRef.current = mediaRecorder;
        mediaRecorder.start(1000); // Capture every second
        
        toast.success('Screen recording started');
      } catch (screenError) {
        console.warn('Screen recording denied:', screenError);
        toast.error('Screen recording is required for this interview');
        cleanup();
        return;
      }

      setIsRecording(true);
      setIsProctoringActive(true);
      
      // Start face detection
      if (modelsLoaded) {
        startFaceDetection();
      }
      
      toast.success('Interview started - stay focused!');
    } catch (error) {
      console.error('Error starting interview:', error);
      toast.error('Camera access is required for this interview');
    }
  };

  const startFaceDetection = () => {
    detectionIntervalRef.current = setInterval(async () => {
      if (videoRef.current && window.faceapi && modelsLoaded) {
        try {
          const detections = await window.faceapi
            .detectAllFaces(videoRef.current, new window.faceapi.TinyFaceDetectorOptions())
            .withFaceLandmarks();

          // Draw on canvas
          if (canvasRef.current && detections.length > 0) {
            const displaySize = {
              width: videoRef.current.videoWidth,
              height: videoRef.current.videoHeight
            };
            window.faceapi.matchDimensions(canvasRef.current, displaySize);
            const resizedDetections = window.faceapi.resizeResults(detections, displaySize);
            
            const ctx = canvasRef.current.getContext('2d');
            ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
            window.faceapi.draw.drawDetections(canvasRef.current, resizedDetections);
            window.faceapi.draw.drawFaceLandmarks(canvasRef.current, resizedDetections);
          }

          // Proctoring checks
          if (detections.length === 0) {
            setFaceDetected(false);
            addProctoringFlag('NO_FACE', 'No face detected in frame');
          } else if (detections.length > 1) {
            setFaceDetected(true);
            addProctoringFlag('MULTIPLE_FACES', `${detections.length} faces detected`);
          } else {
            setFaceDetected(true);
            
            // Check head orientation using landmarks
            const landmarks = detections[0].landmarks;
            const headPose = calculateHeadPose(landmarks);
            
            if (Math.abs(headPose.yaw) > 30) {
              addProctoringFlag('HEAD_TURNED', `Head turned ${headPose.yaw.toFixed(1)}° (threshold: 30°)`);
            }
            
            if (Math.abs(headPose.pitch) > 25) {
              addProctoringFlag('HEAD_TILTED', `Head tilted ${headPose.pitch.toFixed(1)}° vertically`);
            }
          }
        } catch (error) {
          console.error('Face detection error:', error);
        }
      }
    }, 1000); // Check every second
  };

  const calculateHeadPose = (landmarks) => {
    // Get key facial landmarks
    const nose = landmarks.getNose();
    const leftEye = landmarks.getLeftEye();
    const rightEye = landmarks.getRightEye();
    const mouth = landmarks.getMouth();
    
    // Calculate yaw (left-right rotation)
    const noseTip = nose[3];
    const leftEyeCenter = getCenter(leftEye);
    const rightEyeCenter = getCenter(rightEye);
    
    const eyeCenterX = (leftEyeCenter.x + rightEyeCenter.x) / 2;
    const noseOffset = noseTip.x - eyeCenterX;
    const eyeDistance = Math.abs(rightEyeCenter.x - leftEyeCenter.x);
    
    // Normalize and convert to degrees (-90 to +90)
    const yaw = (noseOffset / eyeDistance) * 90;
    
    // Calculate pitch (up-down tilt)
    const eyeCenterY = (leftEyeCenter.y + rightEyeCenter.y) / 2;
    const mouthCenter = getCenter(mouth);
    const verticalDistance = mouthCenter.y - eyeCenterY;
    const faceHeight = landmarks.getJawOutline()[8].y - eyeCenterY;
    
    const pitch = ((verticalDistance - faceHeight * 0.5) / faceHeight) * 60;
    
    return { yaw, pitch };
  };

  const getCenter = (points) => {
    const sum = points.reduce((acc, point) => ({
      x: acc.x + point.x,
      y: acc.y + point.y
    }), { x: 0, y: 0 });
    
    return {
      x: sum.x / points.length,
      y: sum.y / points.length
    };
  };

  const addProctoringFlag = (type, description) => {
    const newFlag = {
      type,
      description,
      timestamp: new Date().toISOString(),
      questionIndex: currentQuestionIndex
    };
    
    setProctoringFlags(prev => {
      // Avoid duplicate flags within 5 seconds
      const recentFlag = prev.find(
        f => f.type === type && 
        new Date(f.timestamp).getTime() > Date.now() - 5000
      );
      
      if (!recentFlag) {
        // Send to server
        sendProctoringFlag(newFlag);
        
        // Show warning toast
        if (type !== 'NO_FACE' || prev.filter(f => f.type === 'NO_FACE').length % 3 === 0) {
          toast.error(`⚠️ ${description}`, { duration: 3000 });
        }
        
        return [...prev, newFlag];
      }
      return prev;
    });
  };

  const sendProctoringFlag = async (flag) => {
    try {
      await api.post('/api/interview/proctor', {
        interview_id: interviewId,
        flag_type: flag.type,
        description: flag.description,
        timestamp: flag.timestamp,
        question_index: flag.questionIndex
      });
    } catch (error) {
      console.error('Error sending proctoring flag:', error);
    }
  };

  const handleAnswerChange = (e) => {
    setCurrentAnswer(e.target.value);
  };

  const handleNextQuestion = () => {
    if (!currentAnswer.trim()) {
      toast.error('Please provide an answer before continuing');
      return;
    }
    
    setAnswers(prev => ({
      ...prev,
      [questions[currentQuestionIndex].question_id]: currentAnswer
    }));
    
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      setCurrentAnswer('');
      toast.success('Answer saved');
    } else {
      handleSubmitInterview();
    }
  };

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
      setCurrentAnswer(answers[questions[currentQuestionIndex - 1].question_id] || '');
    }
  };

  const handleSubmitInterview = async () => {
    try {
      const finalAnswers = {
        ...answers,
        [questions[currentQuestionIndex].question_id]: currentAnswer
      };
      
      cleanup();
      
      toast.loading('Submitting interview...');
      await onComplete(finalAnswers);
      toast.dismiss();
      toast.success('Interview submitted successfully!');
    } catch (error) {
      toast.error('Failed to submit interview');
      console.error(error);
    }
  };

  const cleanup = () => {
    // Stop face detection
    if (detectionIntervalRef.current) {
      clearInterval(detectionIntervalRef.current);
    }
    
    // Stop video stream
    if (videoStreamRef.current) {
      videoStreamRef.current.getTracks().forEach(track => track.stop());
    }
    
    // Stop screen recording
    if (screenRecorderRef.current && screenRecorderRef.current.state !== 'inactive') {
      screenRecorderRef.current.stop();
    }
    
    // Stop screen stream
    if (screenStreamRef.current) {
      screenStreamRef.current.getTracks().forEach(track => track.stop());
    }
    
    setIsRecording(false);
    setIsProctoringActive(false);
  };

  const currentQuestion = questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-purple-900 via-purple-800 to-teal-700 z-50 overflow-y-auto">
      <div className="min-h-screen p-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 mb-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-white mb-1">AI-Proctored Interview</h1>
                <p className="text-white/80 text-sm">
                  Question {currentQuestionIndex + 1} of {questions.length}
                </p>
              </div>
              <div className="flex items-center gap-4">
                {isProctoringActive && (
                  <div className="flex items-center gap-2 text-white">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                    <span className="text-sm font-medium">Recording</span>
                  </div>
                )}
                <button
                  onClick={() => {
                    cleanup();
                    onCancel();
                  }}
                  className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors"
                >
                  Exit
                </button>
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="mt-4 bg-white/20 rounded-full h-2 overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                className="h-full bg-gradient-to-r from-teal-400 to-purple-400"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Video Feed & Proctoring */}
            <div className="lg:col-span-1 space-y-4">
              {/* Video Feed */}
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 border border-white/20">
                <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Camera Feed
                </h3>
                <div className="relative bg-gray-900 rounded-xl overflow-hidden aspect-video">
                  <video
                    ref={videoRef}
                    autoPlay
                    muted
                    className="w-full h-full object-cover"
                  />
                  <canvas
                    ref={canvasRef}
                    className="absolute top-0 left-0 w-full h-full"
                  />
                  
                  {!isRecording && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                      <p className="text-white text-sm">Camera not started</p>
                    </div>
                  )}
                  
                  {/* Face Detection Status */}
                  {isRecording && (
                    <div className="absolute top-3 right-3">
                      <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                        faceDetected 
                          ? 'bg-green-500 text-white' 
                          : 'bg-red-500 text-white animate-pulse'
                      }`}>
                        {faceDetected ? '✓ Face Detected' : '⚠ No Face'}
                      </div>
                    </div>
                  )}
                </div>

                {!isRecording && !isLoading && (
                  <button
                    onClick={startInterview}
                    className="w-full mt-4 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-semibold hover:from-green-600 hover:to-emerald-700 transition-all shadow-lg"
                  >
                    🎥 Start Interview
                  </button>
                )}
              </div>

              {/* Proctoring Status */}
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 border border-white/20">
                <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  Proctoring Alerts
                  {proctoringFlags.length > 0 && (
                    <span className="ml-auto px-2 py-1 bg-red-500 text-white text-xs rounded-full">
                      {proctoringFlags.length}
                    </span>
                  )}
                </h3>
                
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {proctoringFlags.length === 0 ? (
                    <p className="text-white/60 text-sm">No violations detected</p>
                  ) : (
                    proctoringFlags.slice(-5).reverse().map((flag, idx) => (
                      <div
                        key={idx}
                        className="bg-red-500/20 border border-red-500/30 rounded-lg p-2"
                      >
                        <div className="flex items-start gap-2">
                          <span className="text-red-400 text-lg">⚠</span>
                          <div className="flex-1">
                            <p className="text-white text-sm font-medium">{flag.type.replace(/_/g, ' ')}</p>
                            <p className="text-white/80 text-xs">{flag.description}</p>
                            <p className="text-white/60 text-xs mt-1">
                              Q{flag.questionIndex + 1} • {new Date(flag.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Right Column - Interview Questions */}
            <div className="lg:col-span-2">
              <div className="bg-white/95 backdrop-blur-lg rounded-2xl p-8 border border-white/20 shadow-2xl">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={currentQuestionIndex}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.3 }}
                  >
                    {/* Question */}
                    <div className="mb-6">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
                          {currentQuestion?.category || 'Question'}
                        </span>
                        <span className="text-gray-500 text-sm">
                          {currentQuestionIndex + 1}/{questions.length}
                        </span>
                      </div>
                      <h2 className="text-2xl font-bold text-gray-800 mb-2">
                        {currentQuestion?.question_text}
                      </h2>
                    </div>

                    {/* Answer Input */}
                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Your Answer:
                      </label>
                      <textarea
                        value={currentAnswer}
                        onChange={handleAnswerChange}
                        disabled={!isRecording}
                        placeholder={isRecording ? "Type your answer here..." : "Start the interview to begin answering"}
                        className="w-full h-64 px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all resize-none disabled:bg-gray-100 disabled:cursor-not-allowed"
                      />
                      <div className="flex justify-between items-center mt-2">
                        <p className="text-sm text-gray-500">
                          {currentAnswer.length} characters
                        </p>
                        {!isRecording && (
                          <p className="text-sm text-red-500 font-medium">
                            ⚠ Camera must be started to answer
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Navigation Buttons */}
                    <div className="flex gap-4">
                      <button
                        onClick={handlePreviousQuestion}
                        disabled={currentQuestionIndex === 0 || !isRecording}
                        className="px-6 py-3 bg-gray-200 text-gray-700 rounded-xl font-semibold hover:bg-gray-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        ← Previous
                      </button>
                      
                      <button
                        onClick={handleNextQuestion}
                        disabled={!isRecording || !currentAnswer.trim()}
                        className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-teal-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
                      >
                        {currentQuestionIndex === questions.length - 1 ? 'Submit Interview' : 'Next Question →'}
                      </button>
                    </div>
                  </motion.div>
                </AnimatePresence>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InterviewRoom;
