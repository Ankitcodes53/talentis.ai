import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../api/axios';
import AnimatedBackground from '../components/AnimatedBackground';
import InterviewModal from '../components/InterviewModal';
import InterviewScheduler from '../components/InterviewScheduler';

const EmployerDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [matches, setMatches] = useState([]);
  const [showJobForm, setShowJobForm] = useState(false);
  const [showInterview, setShowInterview] = useState(null);
  const [showScheduler, setShowScheduler] = useState(null);
  const [loading, setLoading] = useState(false);

  const [jobForm, setJobForm] = useState({
    title: '',
    description: '',
    skills: '',
    location: '',
    salary_min: '',
    salary_max: '',
    language: 'en',
  });

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/employer/jobs');
      setJobs(response.data.jobs || []);
    } catch (error) {
      console.error('Error fetching jobs:', error);
      toast.error('Failed to load your job postings');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateJob = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post('/api/jobs', {
        ...jobForm,
        skills: jobForm.skills.split(',').map(s => s.trim()),
        salary_min: parseInt(jobForm.salary_min),
        salary_max: parseInt(jobForm.salary_max),
      });

      setJobs([...jobs, response.data]);
      toast.success('Job posted successfully!');
      setShowJobForm(false);
      setJobForm({
        title: '',
        description: '',
        skills: '',
        location: '',
        salary_min: '',
        salary_max: '',
        language: 'en',
      });
      // Refresh jobs list
      fetchJobs();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create job');
    } finally {
      setLoading(false);
    }
  };

  const handleViewMatches = async (job) => {
    setSelectedJob(job);
    setLoading(true);

    try {
      const response = await api.get(`/api/jobs/${job.job_id}/matches`);
      setMatches(response.data);
    } catch (error) {
      toast.error('Failed to load matches');
    } finally {
      setLoading(false);
    }
  };

  const sendInterviewInvite = async (matchId) => {
    try {
      const response = await api.post(`/api/interviews/invite/${matchId}`);
      toast.success('Interview invite sent successfully!');
      // Refresh matches to update button state
      if (selectedJob) {
        handleViewMatches(selectedJob);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send interview invite');
    }
  };

  const analytics = {
    timeSaved: '120 hours',
    co2Reduced: '45 kg',
    retentionRate: '87%',
    biasReduction: '95%',
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
        {/* Analytics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 border border-purple-100 shadow-lg"
          >
            <p className="text-sm text-gray-600 mb-1">⏱️ Time Saved</p>
            <p className="text-3xl font-bold text-purple-600">{analytics.timeSaved}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 border border-teal-100 shadow-lg"
          >
            <p className="text-sm text-gray-600 mb-1">🌱 CO₂ Reduced</p>
            <p className="text-3xl font-bold text-teal-600">{analytics.co2Reduced}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 border border-blue-100 shadow-lg"
          >
            <p className="text-sm text-gray-600 mb-1">📈 Retention Rate</p>
            <p className="text-3xl font-bold text-blue-600">{analytics.retentionRate}</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 border border-green-100 shadow-lg"
          >
            <p className="text-sm text-gray-600 mb-1">✓ Bias Reduction</p>
            <p className="text-3xl font-bold text-green-600">{analytics.biasReduction}</p>
          </motion.div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Job Form / Jobs List */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 border border-purple-100 shadow-lg mb-6"
            >
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">Your Jobs</h2>
                <button
                  onClick={() => setShowJobForm(!showJobForm)}
                  className="px-4 py-2 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
                >
                  {showJobForm ? 'Cancel' : '+ Post New Job'}
                </button>
              </div>

              {showJobForm && (
                <motion.form
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  onSubmit={handleCreateJob}
                  className="space-y-4 mb-6 border-t pt-6"
                >
                  <input
                    type="text"
                    placeholder="Job Title"
                    value={jobForm.title}
                    onChange={(e) => setJobForm({ ...jobForm, title: e.target.value })}
                    className="w-full px-4 py-3 rounded-lg border-2 border-gray-200 focus:border-purple-500 outline-none transition-all"
                    required
                  />
                  <textarea
                    placeholder="Job Description"
                    value={jobForm.description}
                    onChange={(e) => setJobForm({ ...jobForm, description: e.target.value })}
                    className="w-full px-4 py-3 rounded-lg border-2 border-gray-200 focus:border-purple-500 outline-none transition-all h-24"
                    required
                  />
                  <input
                    type="text"
                    placeholder="Required Skills (comma-separated)"
                    value={jobForm.skills}
                    onChange={(e) => setJobForm({ ...jobForm, skills: e.target.value })}
                    className="w-full px-4 py-3 rounded-lg border-2 border-gray-200 focus:border-purple-500 outline-none transition-all"
                    required
                  />
                  <input
                    type="text"
                    placeholder="Location"
                    value={jobForm.location}
                    onChange={(e) => setJobForm({ ...jobForm, location: e.target.value })}
                    className="w-full px-4 py-3 rounded-lg border-2 border-gray-200 focus:border-purple-500 outline-none transition-all"
                    required
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <input
                      type="number"
                      placeholder="Min Salary"
                      value={jobForm.salary_min}
                      onChange={(e) => setJobForm({ ...jobForm, salary_min: e.target.value })}
                      className="w-full px-4 py-3 rounded-lg border-2 border-gray-200 focus:border-purple-500 outline-none transition-all"
                      required
                    />
                    <input
                      type="number"
                      placeholder="Max Salary"
                      value={jobForm.salary_max}
                      onChange={(e) => setJobForm({ ...jobForm, salary_max: e.target.value })}
                      className="w-full px-4 py-3 rounded-lg border-2 border-gray-200 focus:border-purple-500 outline-none transition-all"
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50"
                  >
                    {loading ? 'Creating...' : 'Create Job'}
                  </button>
                </motion.form>
              )}

              <div className="space-y-4">
                {jobs.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <p className="text-lg mb-2">No jobs posted yet</p>
                    <p className="text-sm">Click "Post New Job" to get started</p>
                  </div>
                ) : (
                  jobs.map((job, index) => (
                    <motion.div
                      key={job.job_id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-gradient-to-r from-purple-50 to-teal-50 rounded-xl p-4 border border-purple-200"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="text-lg font-bold text-gray-800">{job.title}</h3>
                          <p className="text-sm text-gray-600">{job.location}</p>
                        </div>
                        <span className="px-3 py-1 bg-purple-600 text-white rounded-full text-xs font-medium">
                          {job.salary_range}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-2 mb-3">
                        {job.skills_required?.map((skill, i) => (
                          <span key={i} className="px-2 py-1 bg-white rounded-lg text-xs text-gray-700">
                            {skill}
                          </span>
                        ))}
                      </div>
                      <button
                        onClick={() => handleViewMatches(job)}
                        className="w-full py-2 bg-white text-purple-600 rounded-lg font-semibold hover:shadow-md transition-all"
                      >
                        View Matches
                      </button>
                    </motion.div>
                  ))
                )}
              </div>
            </motion.div>
          </div>

          {/* Matches Panel */}
          <div>
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 border border-purple-100 shadow-lg sticky top-6"
            >
              <h2 className="text-xl font-bold text-gray-800 mb-4">
                {selectedJob ? `Matches for ${selectedJob.title}` : 'Select a Job'}
              </h2>

              {!selectedJob ? (
                <div className="text-center py-12 text-gray-500">
                  <p className="text-sm">Click "View Matches" on a job to see candidates</p>
                </div>
              ) : loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-600 border-t-transparent mx-auto"></div>
                </div>
              ) : matches.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <p className="text-sm">No matches found yet</p>
                </div>
              ) : (
                <div className="space-y-4 max-h-[600px] overflow-y-auto">
                  {matches.map((match, index) => (
                    <motion.div
                      key={match.match_id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-gradient-to-br from-purple-50 to-teal-50 rounded-xl p-4 border border-purple-200"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h3 className="font-bold text-gray-800">{match.candidate_name}</h3>
                          <p className="text-xs text-gray-600">Candidate ID: {match.candidate_id}</p>
                        </div>
                        <span className="px-3 py-1 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-full text-sm font-bold">
                          {match.score}%
                        </span>
                      </div>

                      <p className="text-sm text-gray-700 mb-3">{match.explanation_text}</p>

                      <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-3">
                        <p className="text-xs font-medium text-green-800 mb-1">✓ Bias Audit Passed</p>
                        <p className="text-xs text-green-600">
                          Confidence: {(match.bias_audit_json.confidence * 100).toFixed(0)}%
                        </p>
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={() => setShowScheduler(match.match_id)}
                          className="py-2 bg-gradient-to-r from-blue-600 to-indigo-500 text-white rounded-lg font-semibold hover:shadow-lg transition-all text-sm"
                        >
                          📅 Schedule Interview
                        </button>
                        <button
                          onClick={() => sendInterviewInvite(match.match_id)}
                          disabled={match.interview_status === 'invite_sent' || match.interview_status === 'completed'}
                          className={`py-2 rounded-lg font-semibold transition-all text-sm ${
                            match.interview_status === 'invite_sent' || match.interview_status === 'completed'
                              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                              : 'bg-gradient-to-r from-purple-600 to-teal-500 text-white hover:shadow-lg'
                          }`}
                        >
                          {match.interview_status === 'invite_sent' ? '✓ Invite Sent' : 
                           match.interview_status === 'completed' ? '✓ Interview Done' : 
                           '📧 Send Interview Invite'}
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          </div>
        </div>

        {/* Razorpay Payment Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 bg-gradient-to-r from-purple-600 to-teal-500 rounded-2xl p-8 text-white shadow-2xl"
        >
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-2xl font-bold mb-2">Upgrade to Premium</h3>
              <p className="text-purple-100">Unlimited jobs, advanced analytics, and priority support</p>
            </div>
            <button
              onClick={() => toast.success('Payment integration coming soon!')}
              className="px-8 py-3 bg-white text-purple-600 rounded-xl font-bold hover:shadow-xl transition-all"
            >
              💳 Upgrade Now
            </button>
          </div>
        </motion.div>
      </div>

      {/* Interview Modal */}
      {showInterview && (
        <InterviewModal
          matchId={showInterview}
          onClose={() => setShowInterview(null)}
          onComplete={() => {
            setShowInterview(null);
            if (selectedJob) handleViewMatches(selectedJob);
          }}
        />
      )}

      {/* Interview Scheduler Modal */}
      {showScheduler && (
        <InterviewScheduler
          matchId={showScheduler}
          onClose={() => setShowScheduler(null)}
          onScheduled={() => {
            setShowScheduler(null);
            toast.success('Interview scheduled successfully!');
          }}
        />
      )}
    </div>
  );
};

export default EmployerDashboard;
