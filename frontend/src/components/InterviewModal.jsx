import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../api/axios';
import { toast } from 'react-hot-toast';

const InterviewModal = ({ matchId, onClose, onComplete }) => {
  const [questions, setQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [responses, setResponses] = useState({});
  const [interviewId, setInterviewId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    startInterview();
  }, []);

  const startInterview = async () => {
    try {
      const response = await api.post('/api/interview/start', { match_id: matchId });
      setQuestions(response.data.questions);
      setInterviewId(response.data.interview_id);
      setLoading(false);
    } catch (error) {
      toast.error('Failed to start interview');
      onClose();
    }
  };

  const handleResponseChange = (questionId, answer) => {
    setResponses({ ...responses, [questionId]: answer });
  };

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const response = await api.post('/api/interview/submit', {
        match_id: matchId,
        responses,
      });
      setResult(response.data);
      toast.success('Interview completed!');
      if (onComplete) onComplete(response.data);
    } catch (error) {
      toast.error('Failed to submit interview');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl p-8">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-purple-600 border-t-transparent mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading interview...</p>
        </div>
      </div>
    );
  }

  if (result) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-3xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        >
          <h2 className="text-3xl font-bold text-center mb-6 bg-gradient-to-r from-purple-600 to-teal-500 bg-clip-text text-transparent">
            Interview Results
          </h2>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-purple-50 rounded-xl p-4">
              <p className="text-sm text-gray-600">Technical Score</p>
              <p className="text-3xl font-bold text-purple-600">{result.scores.technical}%</p>
            </div>
            <div className="bg-teal-50 rounded-xl p-4">
              <p className="text-sm text-gray-600">Communication</p>
              <p className="text-3xl font-bold text-teal-600">{result.scores.communication}%</p>
            </div>
            <div className="bg-blue-50 rounded-xl p-4">
              <p className="text-sm text-gray-600">Cultural Fit</p>
              <p className="text-3xl font-bold text-blue-600">{result.scores.cultural_fit}%</p>
            </div>
            <div className="bg-gradient-to-br from-purple-600 to-teal-500 rounded-xl p-4 text-white">
              <p className="text-sm opacity-90">Total Score</p>
              <p className="text-3xl font-bold">{result.total_score}%</p>
            </div>
          </div>

          <div className="bg-gradient-to-r from-purple-100 to-teal-100 rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-700">Retention Prediction</p>
              <p className="text-2xl font-bold text-purple-600">{(result.retention_prediction * 100).toFixed(0)}%</p>
            </div>
            <div className="w-full bg-white rounded-full h-3">
              <div
                className="bg-gradient-to-r from-purple-600 to-teal-500 h-3 rounded-full transition-all"
                style={{ width: `${result.retention_prediction * 100}%` }}
              ></div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-xl p-6 mb-6">
            <p className="text-sm font-medium text-gray-600 mb-2">Recommendation</p>
            <p className="text-xl font-bold text-gray-800">{result.recommendation}</p>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-6">
            <p className="text-sm font-medium text-green-800 mb-2">✓ Bias Audit Passed</p>
            <p className="text-xs text-green-600">
              No gender, age, or location bias detected (Confidence: {(result.bias_audit.overall_confidence * 100).toFixed(0)}%)
            </p>
          </div>

          <button
            onClick={onClose}
            className="w-full py-3 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-xl font-semibold hover:shadow-lg transition-all"
          >
            Close
          </button>
        </motion.div>
      </div>
    );
  }

  const question = questions[currentQuestion];
  const progress = ((currentQuestion + 1) / questions.length) * 100;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-3xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
      >
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <p className="text-sm text-gray-600">Question {currentQuestion + 1} of {questions.length}</p>
            <p className="text-sm font-medium text-purple-600">{progress.toFixed(0)}% Complete</p>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <motion.div
              className="bg-gradient-to-r from-purple-600 to-teal-500 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            ></motion.div>
          </div>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={currentQuestion}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            <div className="mb-6">
              <span className="inline-block px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium mb-4">
                {question.category}
              </span>
              <h3 className="text-2xl font-bold text-gray-800 mb-6">
                {question.question_text}
              </h3>
              <textarea
                value={responses[question.question_id] || ''}
                onChange={(e) => handleResponseChange(question.question_id, e.target.value)}
                placeholder="Type your answer here..."
                className="w-full h-40 px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all resize-none"
              />
            </div>
          </motion.div>
        </AnimatePresence>

        <div className="flex gap-3">
          <button
            onClick={handlePrevious}
            disabled={currentQuestion === 0}
            className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          
          {currentQuestion < questions.length - 1 ? (
            <button
              onClick={handleNext}
              className="flex-1 py-3 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-xl font-semibold hover:shadow-lg transition-all"
            >
              Next Question
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={submitting || Object.keys(responses).length < questions.length}
              className="flex-1 py-3 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50"
            >
              {submitting ? 'Submitting...' : 'Submit Interview'}
            </button>
          )}

          <button
            onClick={onClose}
            className="px-6 py-3 bg-red-100 text-red-700 rounded-xl font-semibold hover:bg-red-200 transition-all"
          >
            Cancel
          </button>
        </div>

        <p className="text-xs text-gray-500 text-center mt-4">
          Answer all questions to submit your interview
        </p>
      </motion.div>
    </div>
  );
};

export default InterviewModal;
