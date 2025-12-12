import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-hot-toast';
import AnimatedBackground from '../components/AnimatedBackground';

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('employer');
  const [companyName, setCompanyName] = useState('');
  const [fullName, setFullName] = useState('');
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      let userData;
      if (isLogin) {
        userData = await login(email, password);
        toast.success('Welcome back!');
      } else {
        userData = await register(email, password, role, companyName, fullName);
        toast.success('Account created successfully!');
      }
      
      navigate(userData.role === 'employer' ? '/employer' : '/candidate');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Authentication failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <AnimatedBackground />
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl shadow-2xl p-8 border border-purple-100">
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            className="text-center mb-8"
          >
            <h1 
              onClick={() => navigate('/')}
              className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-teal-500 bg-clip-text text-transparent mb-2 cursor-pointer hover:opacity-80 transition-opacity"
            >
              Talentis.ai
            </h1>
            <p className="text-gray-600">AI-Powered Global Hiring</p>
          </motion.div>

          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 rounded-xl font-medium transition-all ${
                isLogin
                  ? 'bg-gradient-to-r from-purple-600 to-teal-500 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 rounded-xl font-medium transition-all ${
                !isLogin
                  ? 'bg-gradient-to-r from-purple-600 to-teal-500 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    I am a...
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setRole('employer')}
                      className={`py-3 rounded-xl font-medium transition-all ${
                        role === 'employer'
                          ? 'bg-purple-600 text-white shadow-lg scale-105'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      🏢 Employer
                    </button>
                    <button
                      type="button"
                      onClick={() => setRole('candidate')}
                      className={`py-3 rounded-xl font-medium transition-all ${
                        role === 'candidate'
                          ? 'bg-teal-500 text-white shadow-lg scale-105'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      👤 Candidate
                    </button>
                  </div>
                </div>

                <input
                  type="text"
                  placeholder="Full Name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all"
                  required
                />

                {role === 'employer' && (
                  <input
                    type="text"
                    placeholder="Company Name"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all"
                  />
                )}
              </>
            )}

            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all"
              required
            />

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all"
              required
            />

            {isLogin && (
              <div className="text-right">
                <button
                  type="button"
                  onClick={() => navigate('/password-reset')}
                  className="text-sm text-purple-600 hover:text-purple-700 font-medium"
                >
                  Forgot Password?
                </button>
              </div>
            )}

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              className="w-full py-3 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all"
            >
              {isLogin ? 'Login' : 'Create Account'}
            </motion.button>
          </form>

          {isLogin && (
            <div className="mt-6 p-4 bg-purple-50 rounded-xl border border-purple-100">
              <p className="text-sm text-gray-600 mb-2">🎉 Quick Test Login:</p>
              <button
                onClick={() => {
                  setEmail('employer@talentis.ai');
                  setPassword('password123');
                  setTimeout(() => handleSubmit({ preventDefault: () => {} }), 100);
                }}
                className="text-sm text-purple-600 hover:text-purple-700 font-medium"
              >
                employer@talentis.ai / password123
              </button>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
