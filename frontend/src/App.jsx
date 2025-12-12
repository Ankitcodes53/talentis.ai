import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'
import AnimatedBackground from './components/AnimatedBackground'
import Homepage from './pages/Homepage'
import Login from './pages/Login'
import PasswordReset from './pages/PasswordReset'
import EmployerDashboard from './pages/EmployerDashboard'
import CandidateDashboard from './pages/CandidateDashboard'
import JobsExplorer from './pages/JobsExplorer'
import CodingTest from './components/CodingTest'
import Explore from './pages/Explore'
import Home from './pages/Home'
import InterviewPage from './pages/InterviewPage'

// Protected Route Component
function ProtectedRoute({ children, allowedRole }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 via-purple-800 to-teal-700">
        <div className="text-white text-2xl">Loading...</div>
      </div>
    )
  }
  
  if (!user) {
    return <Navigate to="/login" replace />
  }
  
  if (allowedRole && user.role !== allowedRole) {
    return <Navigate to={user.role === 'employer' ? '/employer' : '/candidate'} replace />
  }
  
  return children
}

function AppContent() {
  const { user } = useAuth()
  
  return (
    <div className="min-h-screen relative overflow-hidden">
      <AnimatedBackground />
      <div className="relative z-10">
        <Routes>
          <Route path="/" element={user ? <Home /> : <Homepage />} />
          <Route path="/explore" element={<ProtectedRoute><Explore /></ProtectedRoute>} />
          <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
          <Route path="/password-reset" element={<PasswordReset />} />
          <Route path="/interview/:matchId" element={<InterviewPage />} />
          <Route path="/jobs" element={<JobsExplorer />} />
          <Route path="/coding-test" element={<ProtectedRoute><CodingTest /></ProtectedRoute>} />
          <Route path="/employer" element={<ProtectedRoute allowedRole="employer"><EmployerDashboard /></ProtectedRoute>} />
          <Route path="/candidate" element={<ProtectedRoute allowedRole="candidate"><CandidateDashboard /></ProtectedRoute>} />
        </Routes>
      </div>
      <Toaster position="top-right" />
    </div>
  )
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  )
}

export default App
