import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import InterviewRecorder from '../components/InterviewRecorder';
import AnimatedBackground from '../components/AnimatedBackground';

const InterviewPage = () => {
  const { matchId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [match, setMatch] = useState(null);
  const [simulation, setSimulation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    if (matchId) {
      fetchMatchDetails();
    }
  }, [matchId]);

  const fetchMatchDetails = async () => {
    try {
      const matchesResponse = await api.get('/api/matches/candidate');
      const foundMatch = matchesResponse.data.matches.find(m => m.id === parseInt(matchId));
      
      if (!foundMatch) {
        toast.error('Interview invitation not found');
        navigate('/candidate-dashboard');
        return;
      }
      
      setMatch(foundMatch);
      
      // Try to load simulation
      try {
        console.log('Fetching simulations for job_id:', foundMatch.job_id);
        const simResponse = await api.get(`/api/simulations/job/${foundMatch.job_id}`);
        console.log('Simulations response:', simResponse.data);
        
        if (simResponse.data.simulations && simResponse.data.simulations.length > 0) {
          const loadedSim = simResponse.data.simulations[0];
          console.log('Setting simulation:', loadedSim);
          setSimulation(loadedSim);
          toast.success('Interview ready!');
        } else {
          console.warn('No simulations found for this job');
        }
      } catch (error) {
        console.error('Error loading simulation:', error);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error:', error);
      toast.error('Failed to load interview');
      setLoading(false);
    }
  };

  const handleStartInterview = () => {
    setStarted(true);
    toast.success('Interview started!');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <AnimatedBackground />
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading interview...</p>
        </div>
      </div>
    );
  }

  if (!match) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <AnimatedBackground />
        <div className="text-center">
          <p className="text-red-600 text-xl">Interview not found</p>
          <button onClick={() => navigate('/candidate-dashboard')} className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <AnimatedBackground />
      <div className="bg-white/80 backdrop-blur-lg border-b border-purple-100">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-teal-500 bg-clip-text text-transparent">
            Talentis.ai - AI Interview
          </h1>
          <span className="text-sm text-gray-600">👋 {user?.email}</span>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {!started ? (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-3xl mx-auto">
            <div className="bg-white/90 backdrop-blur-lg rounded-2xl p-8 border border-purple-100 shadow-2xl">
              <div className="text-center mb-8">
                <h2 className="text-3xl font-bold text-gray-800 mb-2">🎯 Technical Interview</h2>
                <p className="text-lg text-gray-600">{match.job_title}</p>
                <p className="text-sm text-gray-500">{match.company_name}</p>
              </div>

              <div className="bg-gradient-to-r from-purple-50 to-teal-50 rounded-xl p-6 mb-6">
                <h3 className="font-bold text-gray-800 mb-4">📋 Interview Format:</h3>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start gap-2"><span className="text-purple-600">✓</span><span><strong>Camera Recording:</strong> Your face will be recorded</span></li>
                  <li className="flex items-start gap-2"><span className="text-purple-600">✓</span><span><strong>Screen Recording:</strong> Your screen will be captured</span></li>
                  <li className="flex items-start gap-2"><span className="text-purple-600">✓</span><span><strong>Face Detection:</strong> AI monitors for proctoring</span></li>
                  <li className="flex items-start gap-2"><span className="text-purple-600">✓</span><span><strong>AI Transcription:</strong> Responses analyzed</span></li>
                  <li className="flex items-start gap-2"><span className="text-purple-600">✓</span><span><strong>Behavior Analysis:</strong> Communication evaluated</span></li>
                </ul>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 mb-6">
                <h3 className="font-bold text-gray-800 mb-3">⚠️ Guidelines:</h3>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li>• Well-lit, quiet environment</li>
                  <li>• Stable internet connection</li>
                  <li>• Only you should be visible</li>
                  <li>• Do not switch tabs</li>
                  <li>• Speak clearly</li>
                </ul>
              </div>

              <div className="flex gap-4">
                <button onClick={() => navigate('/candidate-dashboard')} className="flex-1 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-all">
                  Cancel
                </button>
                <button onClick={handleStartInterview} className="flex-1 py-3 bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-lg font-bold text-lg hover:shadow-xl hover:scale-105 transition-all">
                  🎥 I'm Ready - Start Interview
                </button>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-6xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <div className="bg-white/90 backdrop-blur-lg rounded-2xl p-6 border border-purple-100 shadow-xl">
                  <h3 className="text-xl font-bold text-gray-800 mb-4">🎥 Live Interview</h3>
                  <InterviewRecorder 
                    token={localStorage.getItem('token')} 
                    simulationId={simulation?.id} 
                    simulation={simulation}
                  />
                </div>
              </div>

              <div className="lg:col-span-1">
                <div className="bg-white/90 backdrop-blur-lg rounded-2xl p-6 border border-purple-100 shadow-xl sticky top-6">
                  <h3 className="text-lg font-bold text-gray-800 mb-4">📝 Interview Scenario</h3>
                  {simulation?.prompt ? (
                    <div className="space-y-4 max-h-[600px] overflow-y-auto">
                      <div className="bg-gradient-to-r from-purple-50 to-teal-50 rounded-lg p-4 border border-purple-200">
                        <p className="text-xs text-purple-600 font-semibold mb-2">{simulation.type?.toUpperCase()} ASSESSMENT</p>
                        <h4 className="text-sm font-bold text-gray-800 mb-3">{simulation.title}</h4>
                        <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                          {simulation.prompt}
                        </div>
                      </div>
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <p className="text-xs text-blue-600 font-semibold mb-2">💡 INSTRUCTIONS</p>
                        <ul className="text-sm text-gray-700 space-y-1">
                          <li>• Read the scenario carefully</li>
                          <li>• Think out loud as you solve</li>
                          <li>• Explain your reasoning</li>
                          <li>• Take your time</li>
                        </ul>
                      </div>
                    </div>
                  ) : simulation?.questions && simulation.questions.length > 0 ? (
                    <div className="space-y-4 max-h-[600px] overflow-y-auto">
                      {simulation.questions.map((q, index) => (
                        <div key={index} className="bg-gradient-to-r from-purple-50 to-teal-50 rounded-lg p-4 border border-purple-200">
                          <p className="text-xs text-gray-500 mb-1">Question {index + 1}</p>
                          <p className="text-sm text-gray-800 font-medium">{q.question || q}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <p className="text-sm text-gray-600 mb-4">Answer these questions naturally:</p>
                      <div className="bg-gradient-to-r from-purple-50 to-teal-50 rounded-lg p-4"><p className="text-sm font-medium text-gray-800">1. Tell us about yourself</p></div>
                      <div className="bg-gradient-to-r from-purple-50 to-teal-50 rounded-lg p-4"><p className="text-sm font-medium text-gray-800">2. Why this position?</p></div>
                      <div className="bg-gradient-to-r from-purple-50 to-teal-50 rounded-lg p-4"><p className="text-sm font-medium text-gray-800">3. A challenging project</p></div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default InterviewPage;
