import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../api/axios';
import AnimatedBackground from '../components/AnimatedBackground';

const JobsExplorer = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [atsResult, setAtsResult] = useState(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchPublicJobs();
  }, []);

  const fetchPublicJobs = async () => {
    try {
      const response = await api.get('/api/jobs/public');
      setJobs(response.data);
    } catch (error) {
      toast.error('Failed to load jobs');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getCompanyLogo = (companyName) => {
    // Use Clearbit Logo API (free tier)
    const domain = companyName.toLowerCase().replace(/[^a-z0-9]/g, '') + '.com';
    return `https://logo.clearbit.com/${domain}`;
  };

  const handleInterestedClick = (job) => {
    if (!user) {
      toast.error('Please login as a candidate to apply');
      navigate('/login');
      return;
    }

    if (user.role !== 'candidate') {
      toast.error('Only candidates can apply to jobs');
      return;
    }

    setSelectedJob(job);
    setAtsResult(null);
  };

  const handleResumeUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|txt|docx)$/i)) {
      toast.error('Please upload a PDF, TXT, or DOCX file');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    setUploading(true);
    setAtsResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post(`/api/jobs/${selectedJob.job_id}/interested`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setAtsResult(response.data);

      if (response.data.auto_scheduled) {
        toast.success('🎉 Interview Scheduled! Check your dashboard.');
      } else {
        toast.success('Application submitted successfully!');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit application');
      console.error(error);
    } finally {
      setUploading(false);
    }
  };

  const formatSalary = (min, max) => {
    return `$${(min / 1000).toFixed(0)}k - $${(max / 1000).toFixed(0)}k`;
  };

  const getMatchColor = (percentage) => {
    if (percentage >= 80) return 'text-green-500';
    if (percentage >= 60) return 'text-yellow-500';
    return 'text-orange-500';
  };

  const getMatchBgColor = (percentage) => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      <AnimatedBackground />
      
      {/* Header */}
      <div className="relative z-10 pt-20 pb-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-600 to-teal-500 bg-clip-text text-transparent mb-4">
              Explore Global Opportunities
            </h1>
            <p className="text-xl text-gray-700">
              AI-powered job matching • Upload your resume • Get instant ATS score
            </p>
          </motion.div>

          {/* Jobs Grid */}
          {loading ? (
            <div className="flex justify-center items-center py-20">
              <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-purple-600"></div>
            </div>
          ) : jobs.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-20"
            >
              <p className="text-2xl text-gray-600">No jobs available at the moment</p>
              <p className="text-gray-500 mt-2">Check back soon for new opportunities!</p>
            </motion.div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {jobs.map((job, index) => (
                <motion.div
                  key={job.job_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.02, y: -5 }}
                  className="bg-white/90 backdrop-blur-lg rounded-2xl shadow-xl p-6 border border-purple-100 hover:border-purple-300 transition-all"
                >
                  {/* Company Logo */}
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-purple-100 to-teal-100 flex items-center justify-center overflow-hidden shadow-md">
                      <img
                        src={getCompanyLogo(job.company_name)}
                        alt={job.company_name}
                        className="w-12 h-12 object-contain"
                        onError={(e) => {
                          e.target.style.display = 'none';
                          e.target.parentElement.innerHTML = `<span class="text-2xl font-bold text-purple-600">${job.company_name.charAt(0)}</span>`;
                        }}
                      />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-gray-800">{job.title}</h3>
                      <p className="text-sm text-gray-600">{job.company_name}</p>
                    </div>
                  </div>

                  {/* Location & Salary */}
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center gap-2 text-sm text-gray-700">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <span>{job.location}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-700 font-semibold">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>{formatSalary(job.salary_min, job.salary_max)}</span>
                    </div>
                  </div>

                  {/* Skills */}
                  <div className="mb-4">
                    <p className="text-xs text-gray-600 mb-2 font-medium">Required Skills:</p>
                    <div className="flex flex-wrap gap-2">
                      {job.skills_required.slice(0, 4).map((skill, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-gradient-to-r from-purple-100 to-teal-100 text-purple-700 text-xs font-medium rounded-full"
                        >
                          {skill}
                        </span>
                      ))}
                      {job.skills_required.length > 4 && (
                        <span className="px-3 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-full">
                          +{job.skills_required.length - 4} more
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Interested Button */}
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleInterestedClick(job)}
                    className="w-full py-3 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all"
                  >
                    💼 I'm Interested
                  </motion.button>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Resume Upload Modal */}
      <AnimatePresence>
        {selectedJob && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => !uploading && setSelectedJob(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            >
              <div className="p-8">
                {/* Modal Header */}
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-teal-500 bg-clip-text text-transparent">
                      Apply to {selectedJob.title}
                    </h2>
                    <p className="text-gray-600 mt-1">{selectedJob.company_name}</p>
                  </div>
                  <button
                    onClick={() => !uploading && setSelectedJob(null)}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                    disabled={uploading}
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Upload Section */}
                {!atsResult ? (
                  <div className="space-y-6">
                    <div className="bg-gradient-to-br from-purple-50 to-teal-50 rounded-2xl p-6 border-2 border-dashed border-purple-300">
                      <div className="text-center">
                        <svg className="mx-auto h-12 w-12 text-purple-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        <h3 className="text-lg font-semibold text-gray-800 mb-2">Upload Your Resume</h3>
                        <p className="text-sm text-gray-600 mb-4">
                          Get instant ATS score powered by AI • PDF, TXT, or DOCX • Max 5MB
                        </p>
                        <label className="cursor-pointer">
                          <input
                            type="file"
                            accept=".pdf,.txt,.docx"
                            onChange={handleResumeUpload}
                            className="hidden"
                            disabled={uploading}
                          />
                          <motion.div
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className="inline-block px-8 py-3 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all"
                          >
                            {uploading ? (
                              <span className="flex items-center gap-2">
                                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Analyzing Resume...
                              </span>
                            ) : (
                              '📄 Choose File'
                            )}
                          </motion.div>
                        </label>
                      </div>
                    </div>

                    <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
                      <div className="flex gap-3">
                        <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div className="text-sm text-blue-800">
                          <p className="font-medium mb-1">AI-Powered ATS Scoring</p>
                          <p className="text-blue-700">
                            Our AI will analyze your resume against the job requirements and provide an instant match score.
                            If you score above 70%, we'll automatically schedule an interview!
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* ATS Results */
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="space-y-6"
                  >
                    {/* Score Display */}
                    <div className="text-center">
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 200, damping: 15 }}
                        className="inline-block"
                      >
                        <div className={`relative inline-flex items-center justify-center w-32 h-32 rounded-full ${getMatchBgColor(atsResult.match_percentage)}/20 border-4 ${getMatchBgColor(atsResult.match_percentage)} mb-4`}>
                          <span className={`text-4xl font-bold ${getMatchColor(atsResult.match_percentage)}`}>
                            {atsResult.match_percentage.toFixed(0)}%
                          </span>
                        </div>
                      </motion.div>
                      <h3 className="text-2xl font-bold text-gray-800 mb-2">
                        {atsResult.recommendation}
                      </h3>
                    </div>

                    {/* Explanation */}
                    <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                      <h4 className="font-semibold text-gray-800 mb-2">Analysis:</h4>
                      <p className="text-gray-700 text-sm leading-relaxed">
                        {atsResult.explanation}
                      </p>
                    </div>

                    {/* Interview Scheduled */}
                    {atsResult.auto_scheduled && (
                      <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6 border-2 border-green-300"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
                            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          </div>
                          <div className="flex-1">
                            <h4 className="text-xl font-bold text-green-800">🎉 Interview Scheduled!</h4>
                            <p className="text-green-700 text-sm mt-1">
                              Your match score is excellent! Check your candidate dashboard for interview details.
                            </p>
                          </div>
                        </div>
                      </motion.div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex gap-3">
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => navigate('/candidate')}
                        className="flex-1 py-3 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all"
                      >
                        Go to Dashboard
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => {
                          setSelectedJob(null);
                          setAtsResult(null);
                        }}
                        className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-all"
                      >
                        Close
                      </motion.button>
                    </div>
                  </motion.div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default JobsExplorer;
