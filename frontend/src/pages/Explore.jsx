import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../api/axios';
import AnimatedBackground from '../components/AnimatedBackground';

const Explore = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('jobs');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch jobs
      const jobsResponse = await api.get('/api/jobs');
      setJobs(jobsResponse.data.jobs || []);

      // Fetch candidates if employer
      if (user?.role === 'employer') {
        try {
          const candidatesResponse = await api.get('/api/candidates');
          setCandidates(candidatesResponse.data.candidates || []);
        } catch (error) {
          console.log('Candidates fetch error:', error);
        }
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load content');
    } finally {
      setLoading(false);
    }
  };

  const filteredJobs = jobs.filter(job => 
    job.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    job.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    job.location?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (job.skills_required || []).some(skill => 
      skill.toLowerCase().includes(searchQuery.toLowerCase())
    )
  );

  const filteredCandidates = candidates.filter(candidate =>
    candidate.user_email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (candidate.skills || []).some(skill => 
      skill.toLowerCase().includes(searchQuery.toLowerCase())
    )
  );

  const handleApplyJob = async (jobId) => {
    try {
      toast.loading('Processing application...');
      // Create application logic here
      await api.post(`/api/jobs/${jobId}/apply`);
      toast.dismiss();
      toast.success('Application submitted successfully!');
    } catch (error) {
      toast.dismiss();
      toast.error(error.response?.data?.detail || 'Application failed');
    }
  };

  const handleContactCandidate = (candidateId) => {
    toast.success('Contact feature coming soon!');
  };

  return (
    <div className="min-h-screen">
      <AnimatedBackground />

      {/* Header */}
      <div className="bg-white/80 backdrop-blur-lg border-b border-purple-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <h1 
              onClick={() => navigate('/')}
              className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-teal-500 bg-clip-text text-transparent cursor-pointer"
            >
              Talentis.ai
            </h1>
            
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-all"
              >
                🏠 Home
              </button>
              <button
                onClick={() => navigate(user?.role === 'employer' ? '/employer' : '/candidate')}
                className="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-all"
              >
                📊 Dashboard
              </button>
              <span className="text-sm text-gray-600">👋 {user?.email}</span>
              <button
                onClick={logout}
                className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-all"
              >
                Logout
              </button>
            </div>
          </div>

          {/* Search Bar */}
          <div className="mt-4">
            <input
              type="text"
              placeholder="🔍 Search jobs, skills, locations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-3 border border-purple-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          {/* Tabs */}
          <div className="mt-4 flex gap-4">
            <button
              onClick={() => setActiveTab('jobs')}
              className={`px-6 py-2 rounded-lg font-semibold transition-all ${
                activeTab === 'jobs'
                  ? 'bg-gradient-to-r from-purple-600 to-teal-500 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              }`}
            >
              💼 Jobs ({filteredJobs.length})
            </button>
            {user?.role === 'employer' && (
              <button
                onClick={() => setActiveTab('candidates')}
                className={`px-6 py-2 rounded-lg font-semibold transition-all ${
                  activeTab === 'candidates'
                    ? 'bg-gradient-to-r from-purple-600 to-teal-500 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-100'
                }`}
              >
                👥 Candidates ({filteredCandidates.length})
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {loading ? (
          <div className="text-center py-20">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        ) : (
          <>
            {/* Jobs Tab */}
            {activeTab === 'jobs' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredJobs.length === 0 ? (
                  <div className="col-span-full text-center py-20">
                    <p className="text-gray-600 text-lg">No jobs found</p>
                    {user?.role === 'employer' && (
                      <button
                        onClick={() => navigate('/employer')}
                        className="mt-4 px-6 py-3 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-lg font-semibold"
                      >
                        Post a Job
                      </button>
                    )}
                  </div>
                ) : (
                  filteredJobs.map((job, index) => (
                    <motion.div
                      key={job.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 border border-purple-100 shadow-lg hover:shadow-xl transition-all"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                          <h3 className="text-xl font-bold text-gray-800 mb-1">
                            {job.title}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {job.company_name || 'Company Name'}
                          </p>
                        </div>
                        <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                          {job.job_type || 'Full-time'}
                        </span>
                      </div>

                      <p className="text-sm text-gray-700 mb-4 line-clamp-3">
                        {job.description}
                      </p>

                      <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
                        {job.location && <span>📍 {job.location}</span>}
                      </div>

                      {job.salary_range && (
                        <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
                          <span>💰 {job.salary_range}</span>
                        </div>
                      )}

                      <div className="flex flex-wrap gap-2 mb-4">
                        {(job.skills_required || []).slice(0, 3).map((skill, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium"
                          >
                            {skill}
                          </span>
                        ))}
                        {job.skills_required && job.skills_required.length > 3 && (
                          <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
                            +{job.skills_required.length - 3}
                          </span>
                        )}
                      </div>

                      <div className="flex gap-2">
                        {user?.role === 'candidate' && (
                          <button
                            onClick={() => handleApplyJob(job.id)}
                            className="flex-1 py-2 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
                          >
                            Apply Now
                          </button>
                        )}
                        <button
                          className="px-4 py-2 bg-white border border-purple-200 text-purple-600 rounded-lg hover:bg-purple-50 transition-all"
                        >
                          View
                        </button>
                      </div>

                      <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-500">
                        Posted: {new Date(job.created_at).toLocaleDateString()}
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            )}

            {/* Candidates Tab */}
            {activeTab === 'candidates' && user?.role === 'employer' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredCandidates.length === 0 ? (
                  <div className="col-span-full text-center py-20">
                    <p className="text-gray-600 text-lg">No candidates found</p>
                  </div>
                ) : (
                  filteredCandidates.map((candidate, index) => (
                    <motion.div
                      key={candidate.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 border border-purple-100 shadow-lg hover:shadow-xl transition-all"
                    >
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-12 h-12 bg-gradient-to-r from-purple-600 to-teal-500 rounded-full flex items-center justify-center text-white font-bold text-xl">
                          {candidate.user_email?.[0]?.toUpperCase() || 'C'}
                        </div>
                        <div>
                          <h3 className="font-bold text-gray-800">
                            {candidate.user_name || 'Candidate'}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {candidate.user_email}
                          </p>
                        </div>
                      </div>

                      {candidate.experience_years && (
                        <p className="text-sm text-gray-700 mb-3">
                          💼 {candidate.experience_years} years experience
                        </p>
                      )}

                      {candidate.location && (
                        <p className="text-sm text-gray-700 mb-3">
                          📍 {candidate.location}
                        </p>
                      )}

                      <div className="flex flex-wrap gap-2 mb-4">
                        {(candidate.skills || []).slice(0, 4).map((skill, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1 bg-teal-100 text-teal-700 rounded-full text-xs font-medium"
                          >
                            {skill}
                          </span>
                        ))}
                        {candidate.skills && candidate.skills.length > 4 && (
                          <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
                            +{candidate.skills.length - 4}
                          </span>
                        )}
                      </div>

                      <button
                        onClick={() => handleContactCandidate(candidate.id)}
                        className="w-full py-2 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
                      >
                        Contact
                      </button>
                    </motion.div>
                  ))
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Explore;
