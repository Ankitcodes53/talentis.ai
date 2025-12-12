import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../api/axios';
import AnimatedBackground from '../components/AnimatedBackground';

const CandidateDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [jobPostings, setJobPostings] = useState([]);
  const [matches, setMatches] = useState([]);
  const [interviews, setInterviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState(null);

  useEffect(() => {
    fetchJobPostings();
    fetchMatches();
    fetchInterviews();
  }, []);

  const fetchJobPostings = async () => {
    try {
      const response = await api.get('/api/jobs');
      setJobPostings(response.data.jobs || []);
    } catch (error) {
      console.error('Error fetching jobs:', error);
      toast.error('Failed to load job postings');
    } finally {
      setLoading(false);
    }
  };

  const fetchMatches = async () => {
    try {
      const response = await api.get('/api/matches/candidate');
      setMatches(response.data.matches || []);
    } catch (error) {
      console.error('Error fetching matches:', error);
    }
  };

  const fetchInterviews = async () => {
    try {
      const response = await api.get('/api/interviews/candidate');
      setInterviews(response.data.interviews || []);
    } catch (error) {
      console.error('Error fetching interviews:', error);
    }
  };

  const handleApplyJob = async (jobId) => {
    try {
      toast.loading('Processing application...');
      await api.post(`/api/jobs/${jobId}/apply`);
      toast.dismiss();
      toast.success('Application submitted successfully! Check your matches.');
      setSelectedJob(null); // Close modal
      // Refresh matches after applying
      fetchMatches();
    } catch (error) {
      toast.dismiss();
      toast.error(error.response?.data?.detail || 'Application failed');
    }
  };

  const completedInterviews = interviews.filter(i => i.status === 'completed');
  const upcomingInterviews = interviews.filter(i => i.status === 'in_progress' || i.status === 'scheduled');
  const pendingInvites = matches.filter(m => m.interview_status === 'invite_sent');

  const formatDateTime = (dateStr) => {
    if (!dateStr) return 'Not scheduled';
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZoneName: 'short'
    });
  };

  return (
    <div className="min-h-screen">
      <AnimatedBackground />

      {/* Header */}
      <div className="bg-white/80 backdrop-blur-lg border-b border-purple-100">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 
            onClick={() => navigate('/')}
            className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-teal-500 bg-clip-text text-transparent cursor-pointer hover:opacity-80 transition-opacity"
          >
            Talentis.ai
          </h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">👋 {user?.email}</span>
            <button
              onClick={logout}
              className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-all"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 border border-purple-100 shadow-lg"
          >
            <p className="text-sm text-gray-600 mb-1">💼 Available Jobs</p>
            <p className="text-4xl font-bold text-purple-600">{jobPostings.length}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 border border-teal-100 shadow-lg"
          >
            <p className="text-sm text-gray-600 mb-1">🎯 Your Matches</p>
            <p className="text-4xl font-bold text-teal-600">{matches.length}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 border border-blue-100 shadow-lg"
          >
            <p className="text-sm text-gray-600 mb-1">✅ Completed Interviews</p>
            <p className="text-4xl font-bold text-blue-600">{completedInterviews.length}</p>
          </motion.div>
        </div>

        {/* Pending Interview Invitations */}
        {pendingInvites.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 bg-gradient-to-br from-purple-50 to-blue-50 rounded-2xl p-6 border-2 border-purple-300 shadow-xl"
          >
            <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="text-3xl">📧</span> Interview Invitations Received
            </h2>
            <p className="text-gray-600 mb-6">You have {pendingInvites.length} pending interview invitation(s). Click the link to start your AI interview.</p>
            
            <div className="space-y-4">
              {pendingInvites.map((match) => (
                <motion.div
                  key={match.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="bg-white rounded-xl p-5 border-2 border-purple-200 hover:border-purple-400 transition-all shadow-md"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-xl font-bold text-gray-800">{match.job_title}</h3>
                      <p className="text-sm text-gray-600">{match.company_name}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Invited: {new Date(match.invite_sent_at).toLocaleDateString()}
                      </p>
                    </div>
                    <span className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-full text-sm font-bold">
                      {Math.round(match.match_score)}% Match
                    </span>
                  </div>
                  
                  <p className="text-gray-700 mb-4 text-sm">{match.match_explanation}</p>
                  
                  <div className="flex gap-3">
                    <a
                      href={match.interview_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-bold hover:from-purple-700 hover:to-blue-700 transition-all shadow-lg hover:shadow-xl text-center"
                    >
                      🎥 Start AI Interview
                    </a>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(match.interview_link);
                        toast.success('Interview link copied!');
                      }}
                      className="px-4 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-xl font-medium transition-all"
                      title="Copy link"
                    >
                      📋 Copy Link
                    </button>
                  </div>
                  
                  <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-xs text-blue-800">
                      💡 <strong>Note:</strong> This interview takes 12-18 minutes. You can complete it anytime within 48 hours.
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Job Postings */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 border border-purple-100 shadow-lg"
          >
            <h2 className="text-2xl font-bold text-gray-800 mb-6">📋 Job Postings by Recruiters</h2>
            
            {loading ? (
              <p className="text-gray-600 text-center py-8">Loading job postings...</p>
            ) : jobPostings.length === 0 ? (
              <p className="text-gray-600 text-center py-8">No job postings available yet</p>
            ) : (
              <div className="space-y-4 max-h-[600px] overflow-y-auto">
                {jobPostings.map((job, index) => (
                  <motion.div
                    key={job.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-gradient-to-r from-purple-50 to-teal-50 rounded-xl p-4 border border-purple-200"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <h3 className="font-bold text-gray-800">{job.title}</h3>
                        <p className="text-sm text-gray-600">{job.company_name || 'Company'}</p>
                      </div>
                      <span className="px-3 py-1 bg-green-600 text-white rounded-full text-xs font-medium">
                        {job.status || 'Active'}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-700 mb-3 line-clamp-2">{job.description}</p>

                    <div className="flex flex-wrap gap-2 mb-3">
                      {(job.skills_required || []).slice(0, 3).map((skill, idx) => (
                        <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs">
                          {skill}
                        </span>
                      ))}
                      {job.skills_required && job.skills_required.length > 3 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs">
                          +{job.skills_required.length - 3} more
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-700 mb-3">
                      {job.location && <span>📍 {job.location}</span>}
                      {job.salary_range && <span>💰 {job.salary_range}</span>}
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => setSelectedJob(job)}
                        className="flex-1 py-2 bg-white text-purple-600 border-2 border-purple-600 rounded-lg font-semibold hover:bg-purple-50 transition-all"
                      >
                        View Details
                      </button>
                      <button
                        onClick={() => handleApplyJob(job.id)}
                        className="flex-1 py-2 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
                      >
                        Apply Now
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>

          {/* Interview Invites */}
          {pendingInvites.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gradient-to-br from-green-50 to-teal-50 rounded-2xl p-6 border-2 border-green-300 shadow-xl mb-8"
            >
              <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                🎯 Interview Invitations ({pendingInvites.length})
                <span className="px-2 py-1 bg-green-500 text-white text-xs rounded-full animate-pulse">
                  New!
                </span>
              </h2>
              <p className="text-sm text-gray-600 mb-6">
                You've been invited to technical interviews! Click "Start Interview" to begin.
              </p>

              <div className="space-y-4">
                {pendingInvites.map((match, index) => (
                  <motion.div
                    key={match.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-white rounded-xl p-5 border-2 border-green-200 shadow-lg"
                  >
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <h3 className="font-bold text-xl text-gray-800">{match.job_title}</h3>
                        <p className="text-sm text-gray-600">{match.company_name}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          Invited: {new Date(match.invite_sent_at).toLocaleDateString()}
                        </p>
                      </div>
                      <span className="px-3 py-1 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-full text-sm font-bold">
                        {Math.round(match.match_score)}% Match
                      </span>
                    </div>

                    <div className="bg-gradient-to-r from-green-50 to-teal-50 rounded-lg p-4 mb-4">
                      <p className="text-sm font-medium text-gray-700 mb-2">📹 AI-Powered Video Interview</p>
                      <ul className="text-xs text-gray-600 space-y-1">
                        <li>✓ Camera & screen recording</li>
                        <li>✓ Real-time face detection & proctoring</li>
                        <li>✓ AI transcription & analysis</li>
                        <li>✓ Behavior & communication assessment</li>
                      </ul>
                    </div>

                    <button
                      onClick={() => navigate(`/interview/${match.id}`)}
                      className="w-full py-3 bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-lg font-bold text-lg hover:shadow-xl hover:scale-105 transition-all flex items-center justify-center gap-2"
                    >
                      <span>🎥</span> Start Interview
                    </button>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Past Results */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 border border-purple-100 shadow-lg"
          >
            <h2 className="text-2xl font-bold text-gray-800 mb-6">📊 Your Matches & Scores</h2>

            {matches.length === 0 ? (
              <p className="text-gray-600 text-center py-8">No matches yet. Complete your profile to get matched!</p>
            ) : (
              <div className="space-y-4 max-h-[600px] overflow-y-auto">
                {matches.map((match, index) => (
                  <motion.div
                    key={match.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-gradient-to-br from-purple-50 to-teal-50 rounded-xl p-4 border border-purple-200"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-bold text-gray-800">{match.job_title || 'Position'}</h3>
                        <p className="text-sm text-gray-600">{match.company_name || 'Company'}</p>
                        <p className="text-xs text-gray-500">
                          Matched: {new Date(match.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <span className="px-3 py-1 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-full text-sm font-bold">
                        {Math.round(match.match_score)}%
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 mb-3">
                      <div className="bg-white rounded-lg p-2">
                        <p className="text-xs text-gray-600">Skills Match</p>
                        <p className="text-lg font-bold text-purple-600">
                          {Math.round(match.skills_match_score || 0)}%
                        </p>
                      </div>
                      <div className="bg-white rounded-lg p-2">
                        <p className="text-xs text-gray-600">Experience</p>
                        <p className="text-lg font-bold text-teal-600">
                          {Math.round(match.experience_match_score || 0)}%
                        </p>
                      </div>
                    </div>

                    <div className={`border rounded-lg p-2 ${
                      match.interview_status === 'invite_sent' ? 'bg-green-50 border-green-200' :
                      match.interview_status === 'completed' ? 'bg-blue-50 border-blue-200' :
                      match.status === 'accepted' ? 'bg-green-50 border-green-200' :
                      match.status === 'rejected' ? 'bg-red-50 border-red-200' :
                      'bg-yellow-50 border-yellow-200'
                    }`}>
                      <p className="text-sm font-medium capitalize">
                        Interview: {match.interview_status === 'invite_sent' ? '✉️ Invitation Pending' : 
                                   match.interview_status === 'completed' ? '✅ Completed' :
                                   match.interview_status === 'started' ? '🎥 In Progress' :
                                   match.interview_status || 'Not Started'}
                      </p>
                    </div>

                    {match.interview_status === 'invite_sent' && (
                      <button
                        onClick={() => navigate(`/interview/${match.id}`)}
                        className="w-full mt-3 py-2 bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
                      >
                        🎥 Start Interview
                      </button>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        </div>

        {/* Completed Interviews */}
        {completedInterviews.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8 bg-white/80 backdrop-blur-lg rounded-2xl p-6 border border-purple-100 shadow-lg"
          >
            <h2 className="text-2xl font-bold text-gray-800 mb-6">📝 Interview Results</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {completedInterviews.map((interview, index) => (
                <motion.div
                  key={interview.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-gradient-to-br from-purple-50 to-teal-50 rounded-xl p-4 border border-purple-200"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-bold text-gray-800">Interview #{interview.id}</h3>
                      <p className="text-xs text-gray-500">
                        {new Date(interview.completed_at).toLocaleDateString()}
                      </p>
                    </div>
                    <span className="px-3 py-1 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-full text-sm font-bold">
                      {Math.round(interview.overall_score || 0)}%
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 mb-3">
                    <div className="bg-white rounded-lg p-2 text-center">
                      <p className="text-xs text-gray-600">Technical</p>
                      <p className="text-lg font-bold text-purple-600">
                        {Math.round(interview.technical_score || 0)}%
                      </p>
                    </div>
                    <div className="bg-white rounded-lg p-2 text-center">
                      <p className="text-xs text-gray-600">Comm.</p>
                      <p className="text-lg font-bold text-teal-600">
                        {Math.round(interview.communication_score || 0)}%
                      </p>
                    </div>
                    <div className="bg-white rounded-lg p-2 text-center">
                      <p className="text-xs text-gray-600">Cultural</p>
                      <p className="text-lg font-bold text-blue-600">
                        {Math.round(interview.cultural_fit_score || 0)}%
                      </p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* Job Details Modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
          >
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-3xl font-bold text-gray-800 mb-2">{selectedJob.title}</h2>
                <p className="text-lg text-gray-600">{selectedJob.company_name}</p>
              </div>
              <button
                onClick={() => setSelectedJob(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              {/* Salary & Location */}
              <div className="flex flex-wrap gap-4">
                {selectedJob.location && (
                  <div className="flex items-center gap-2 px-4 py-2 bg-purple-50 rounded-lg">
                    <span className="text-2xl">📍</span>
                    <span className="font-medium text-gray-700">{selectedJob.location}</span>
                  </div>
                )}
                {(selectedJob.salary_min && selectedJob.salary_max) && (
                  <div className="flex items-center gap-2 px-4 py-2 bg-teal-50 rounded-lg">
                    <span className="text-2xl">💰</span>
                    <span className="font-medium text-gray-700">
                      ${selectedJob.salary_min.toLocaleString()} - ${selectedJob.salary_max.toLocaleString()}
                    </span>
                  </div>
                )}
              </div>

              {/* Description */}
              <div>
                <h3 className="text-xl font-bold text-gray-800 mb-3">📝 Job Description</h3>
                <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                  {selectedJob.description}
                </p>
              </div>

              {/* Skills Required */}
              {selectedJob.skills_required && selectedJob.skills_required.length > 0 && (
                <div>
                  <h3 className="text-xl font-bold text-gray-800 mb-3">🎯 Required Skills</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedJob.skills_required.map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-4 py-2 bg-gradient-to-r from-purple-100 to-teal-100 text-purple-700 rounded-full font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Apply Button */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => setSelectedJob(null)}
                  className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-all"
                >
                  Close
                </button>
                <button
                  onClick={() => handleApplyJob(selectedJob.id)}
                  className="flex-1 py-3 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all"
                >
                  Apply to This Job
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default CandidateDashboard;
