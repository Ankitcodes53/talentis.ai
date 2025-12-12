import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { 
  Code, 
  Play, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Terminal,
  Loader,
  ChevronRight,
  ChevronLeft,
  Trophy,
  AlertCircle
} from 'lucide-react'
import toast from 'react-hot-toast'

export default function CodingTest({ skills = [], difficulty = 'medium', onComplete }) {
  const [problems, setProblems] = useState([])
  const [currentProblemIndex, setCurrentProblemIndex] = useState(0)
  const [code, setCode] = useState('')
  const [output, setOutput] = useState('')
  const [testResults, setTestResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [timeLeft, setTimeLeft] = useState(3600) // 60 minutes default
  const [timerActive, setTimerActive] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [editorLoaded, setEditorLoaded] = useState(false)
  const editorRef = useRef(null)
  const monacoRef = useRef(null)

  const currentProblem = problems[currentProblemIndex]
  const isCompiledLanguage = ['java', 'cpp17'].includes(currentProblem?.language)

  // Load Monaco Editor from CDN
  useEffect(() => {
    if (window.monaco) {
      setEditorLoaded(true)
      return
    }

    const loaderScript = document.createElement('script')
    loaderScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs/loader.min.js'
    loaderScript.async = true
    loaderScript.onload = () => {
      window.require.config({ 
        paths: { 
          vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' 
        } 
      })
      window.require(['vs/editor/editor.main'], () => {
        setEditorLoaded(true)
      })
    }
    document.body.appendChild(loaderScript)

    return () => {
      if (loaderScript.parentNode) {
        loaderScript.parentNode.removeChild(loaderScript)
      }
    }
  }, [])

  // Initialize Monaco Editor
  useEffect(() => {
    if (!editorLoaded || !currentProblem || isCompiledLanguage) return

    const container = document.getElementById('monaco-editor')
    if (!container) return

    // Dispose previous editor
    if (editorRef.current) {
      editorRef.current.dispose()
    }

    // Language mapping for Monaco
    const languageMap = {
      'python3': 'python',
      'nodejs': 'javascript',
      'javascript': 'javascript',
      'typescript': 'typescript'
    }

    const monacoLanguage = languageMap[currentProblem.language] || 'javascript'

    // Create new editor
    const editor = window.monaco.editor.create(container, {
      value: code || currentProblem.starter_code || '',
      language: monacoLanguage,
      theme: 'vs-dark',
      fontSize: 14,
      minimap: { enabled: true },
      scrollBeyondLastLine: false,
      automaticLayout: true,
      lineNumbers: 'on',
      roundedSelection: false,
      readOnly: false,
      cursorStyle: 'line',
      wordWrap: 'on'
    })

    editorRef.current = editor
    monacoRef.current = window.monaco

    // Update code state on change
    editor.onDidChangeModelContent(() => {
      setCode(editor.getValue())
    })

    return () => {
      if (editor) {
        editor.dispose()
      }
    }
  }, [editorLoaded, currentProblem, isCompiledLanguage])

  // Timer countdown
  useEffect(() => {
    if (!timerActive || timeLeft <= 0) return

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          setTimerActive(false)
          handleTimeUp()
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [timerActive, timeLeft])

  // Fetch coding problems
  useEffect(() => {
    fetchProblems()
  }, [])

  const fetchProblems = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await axios.post('/api/coding/test', {
        skills: skills.length > 0 ? skills : ['Python', 'Algorithms'],
        difficulty,
        count: 3
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })

      setProblems(response.data.problems)
      if (response.data.problems.length > 0) {
        setCode(response.data.problems[0].starter_code || '')
        setTimerActive(true) // Start timer when problems loaded
      }
      toast.success('Coding problems loaded!')
    } catch (error) {
      console.error('Error fetching problems:', error)
      toast.error('Failed to load problems')
    } finally {
      setLoading(false)
    }
  }

  const executeCode = async () => {
    if (!code.trim()) {
      toast.error('Please write some code first!')
      return
    }

    setExecuting(true)
    setOutput('')

    try {
      const token = localStorage.getItem('token')
      const response = await axios.post('/api/coding/execute', {
        code,
        language: currentProblem.language,
        stdin: ''
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })

      setOutput(response.data.output || 'No output')
      
      // Check test cases
      if (currentProblem.test_cases && currentProblem.test_cases.length > 0) {
        const results = validateTestCases(response.data.output)
        setTestResults(prev => {
          const updated = [...prev]
          updated[currentProblemIndex] = results
          return updated
        })

        const passedCount = results.filter(r => r.passed).length
        if (passedCount === results.length) {
          toast.success(`All ${results.length} test cases passed! 🎉`)
        } else {
          toast.error(`${passedCount}/${results.length} test cases passed`)
        }
      }

      if (response.data.error) {
        toast.error('Execution error: ' + response.data.error)
      }
    } catch (error) {
      console.error('Execution error:', error)
      toast.error('Failed to execute code')
      setOutput('Error: ' + (error.response?.data?.detail || error.message))
    } finally {
      setExecuting(false)
    }
  }

  const validateTestCases = (output) => {
    return currentProblem.test_cases.map((testCase, idx) => {
      const expected = testCase.expected_output.trim()
      const actual = output.trim()
      
      // Simple string comparison (can be enhanced)
      const passed = actual.includes(expected) || actual === expected
      
      return {
        testCase: idx + 1,
        input: testCase.input,
        expected,
        actual: output,
        passed
      }
    })
  }

  const handleNext = () => {
    if (currentProblemIndex < problems.length - 1) {
      setCurrentProblemIndex(prev => prev + 1)
      setCode(problems[currentProblemIndex + 1].starter_code || '')
      setOutput('')
    }
  }

  const handlePrevious = () => {
    if (currentProblemIndex > 0) {
      setCurrentProblemIndex(prev => prev - 1)
      setCode(problems[currentProblemIndex - 1].starter_code || '')
      setOutput('')
    }
  }

  const handleTimeUp = () => {
    toast.error('Time is up! Submitting your solutions...')
    handleSubmitTest()
  }

  const handleSubmitTest = () => {
    setShowResults(true)
    setTimerActive(false)

    const totalProblems = problems.length
    const solvedProblems = testResults.filter(results => 
      results && results.every(r => r.passed)
    ).length

    const score = Math.round((solvedProblems / totalProblems) * 100)

    toast.success(`Test completed! Score: ${score}%`)
    
    if (onComplete) {
      onComplete({
        score,
        totalProblems,
        solvedProblems,
        timeSpent: 3600 - timeLeft,
        results: testResults
      })
    }
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getDifficultyColor = (diff) => {
    switch(diff) {
      case 'easy': return 'text-green-400'
      case 'medium': return 'text-yellow-400'
      case 'hard': return 'text-red-400'
      default: return 'text-purple-400'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 via-purple-800 to-teal-700">
        <div className="text-center">
          <Loader className="w-16 h-16 text-teal-400 animate-spin mx-auto mb-4" />
          <p className="text-white text-xl">Loading coding challenges...</p>
        </div>
      </div>
    )
  }

  if (showResults) {
    const totalProblems = problems.length
    const solvedProblems = testResults.filter(results => 
      results && results.every(r => r.passed)
    ).length
    const score = Math.round((solvedProblems / totalProblems) * 100)

    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-teal-700 p-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="max-w-4xl mx-auto bg-white/10 backdrop-blur-lg rounded-2xl border border-white/20 p-8"
        >
          <div className="text-center mb-8">
            <Trophy className="w-24 h-24 text-yellow-400 mx-auto mb-4" />
            <h2 className="text-4xl font-bold text-white mb-2">Test Completed!</h2>
            <p className="text-purple-200 text-xl">Your Score: {score}%</p>
          </div>

          <div className="grid grid-cols-3 gap-6 mb-8">
            <div className="bg-white/10 rounded-xl p-6 text-center">
              <p className="text-purple-200 mb-2">Total Problems</p>
              <p className="text-4xl font-bold text-white">{totalProblems}</p>
            </div>
            <div className="bg-white/10 rounded-xl p-6 text-center">
              <p className="text-purple-200 mb-2">Solved</p>
              <p className="text-4xl font-bold text-green-400">{solvedProblems}</p>
            </div>
            <div className="bg-white/10 rounded-xl p-6 text-center">
              <p className="text-purple-200 mb-2">Time Spent</p>
              <p className="text-4xl font-bold text-teal-400">{formatTime(3600 - timeLeft)}</p>
            </div>
          </div>

          <div className="space-y-4 mb-8">
            {problems.map((problem, idx) => {
              const results = testResults[idx]
              const solved = results && results.every(r => r.passed)
              
              return (
                <div key={idx} className="bg-white/10 rounded-xl p-4 flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    {solved ? (
                      <CheckCircle className="w-6 h-6 text-green-400" />
                    ) : (
                      <XCircle className="w-6 h-6 text-red-400" />
                    )}
                    <div>
                      <p className="text-white font-semibold">{problem.title}</p>
                      <p className={`text-sm ${getDifficultyColor(problem.difficulty)}`}>
                        {problem.difficulty.toUpperCase()}
                      </p>
                    </div>
                  </div>
                  {results && (
                    <p className="text-purple-200">
                      {results.filter(r => r.passed).length}/{results.length} tests passed
                    </p>
                  )}
                </div>
              )
            })}
          </div>

          <button
            onClick={() => window.location.reload()}
            className="w-full px-6 py-3 bg-gradient-to-r from-teal-500 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
          >
            Take Another Test
          </button>
        </motion.div>
      </div>
    )
  }

  if (!currentProblem) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 via-purple-800 to-teal-700">
        <p className="text-white text-xl">No problems available</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-teal-700 p-4">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-4">
        <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-white/20 p-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Code className="w-8 h-8 text-teal-400" />
            <div>
              <h1 className="text-2xl font-bold text-white">Coding Assessment</h1>
              <p className="text-purple-200">Problem {currentProblemIndex + 1} of {problems.length}</p>
            </div>
          </div>

          {/* Timer */}
          <div className={`flex items-center space-x-3 px-6 py-3 rounded-lg ${
            timeLeft < 300 ? 'bg-red-500/20 border border-red-500/50' : 'bg-white/10'
          }`}>
            <Clock className={`w-6 h-6 ${timeLeft < 300 ? 'text-red-400' : 'text-teal-400'}`} />
            <div className="text-center">
              <p className="text-xs text-purple-200">Time Left</p>
              <p className={`text-2xl font-bold ${timeLeft < 300 ? 'text-red-400' : 'text-white'}`}>
                {formatTime(timeLeft)}
              </p>
            </div>
          </div>

          <button
            onClick={handleSubmitTest}
            className="px-6 py-3 bg-gradient-to-r from-green-500 to-teal-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all flex items-center space-x-2"
          >
            <Trophy className="w-5 h-5" />
            <span>Submit Test</span>
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Problem Description */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-white/20 p-6 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 180px)' }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-white">{currentProblem.title}</h2>
            <span className={`px-3 py-1 rounded-lg text-sm font-semibold ${getDifficultyColor(currentProblem.difficulty)}`}>
              {currentProblem.difficulty.toUpperCase()}
            </span>
          </div>

          <div className="prose prose-invert mb-6">
            <p className="text-purple-200 whitespace-pre-wrap">{currentProblem.description}</p>
          </div>

          {/* Test Cases */}
          {currentProblem.test_cases && currentProblem.test_cases.length > 0 && (
            <div className="mt-6">
              <h3 className="text-xl font-bold text-white mb-4">Test Cases</h3>
              {currentProblem.test_cases.map((testCase, idx) => (
                <div key={idx} className="bg-white/5 rounded-lg p-4 mb-3">
                  <p className="text-purple-200 text-sm mb-1">Input:</p>
                  <code className="text-teal-400 bg-black/30 px-3 py-1 rounded block mb-2">
                    {testCase.input}
                  </code>
                  <p className="text-purple-200 text-sm mb-1">Expected Output:</p>
                  <code className="text-green-400 bg-black/30 px-3 py-1 rounded block">
                    {testCase.expected_output}
                  </code>
                </div>
              ))}
            </div>
          )}

          {/* Test Results */}
          {testResults[currentProblemIndex] && testResults[currentProblemIndex].length > 0 && (
            <div className="mt-6">
              <h3 className="text-xl font-bold text-white mb-4">Test Results</h3>
              {testResults[currentProblemIndex].map((result, idx) => (
                <div key={idx} className={`rounded-lg p-4 mb-3 ${
                  result.passed ? 'bg-green-500/20 border border-green-500/50' : 'bg-red-500/20 border border-red-500/50'
                }`}>
                  <div className="flex items-center space-x-2 mb-2">
                    {result.passed ? (
                      <CheckCircle className="w-5 h-5 text-green-400" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-400" />
                    )}
                    <p className="text-white font-semibold">Test Case {result.testCase}</p>
                  </div>
                  {!result.passed && (
                    <div className="text-sm">
                      <p className="text-purple-200">Expected: <span className="text-green-400">{result.expected}</span></p>
                      <p className="text-purple-200">Got: <span className="text-red-400">{result.actual.substring(0, 100)}</span></p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Navigation */}
          <div className="flex gap-3 mt-6">
            <button
              onClick={handlePrevious}
              disabled={currentProblemIndex === 0}
              className="flex-1 px-4 py-2 bg-white/10 text-white rounded-lg hover:bg-white/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              <ChevronLeft className="w-5 h-5" />
              <span>Previous</span>
            </button>
            <button
              onClick={handleNext}
              disabled={currentProblemIndex === problems.length - 1}
              className="flex-1 px-4 py-2 bg-white/10 text-white rounded-lg hover:bg-white/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              <span>Next</span>
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Code Editor / Output */}
        <div className="flex flex-col gap-4">
          {/* Editor */}
          <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-white/20 overflow-hidden flex-1">
            <div className="bg-black/30 px-4 py-3 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Terminal className="w-5 h-5 text-teal-400" />
                <span className="text-white font-semibold">Code Editor</span>
                <span className="text-purple-300 text-sm">({currentProblem.language})</span>
              </div>
              <button
                onClick={executeCode}
                disabled={executing}
                className="px-4 py-2 bg-gradient-to-r from-teal-500 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50 flex items-center space-x-2"
              >
                {executing ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    <span>Running...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    <span>Run Code</span>
                  </>
                )}
              </button>
            </div>

            {/* Monaco Editor or JDoodle Embed */}
            {isCompiledLanguage ? (
              <div className="p-4">
                <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-4 mb-4 flex items-start space-x-3">
                  <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-yellow-200 font-semibold mb-1">Compiled Language</p>
                    <p className="text-yellow-100 text-sm">
                      For Java/C++, you can use JDoodle embed or paste code below and click Run.
                    </p>
                  </div>
                </div>
                <textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="w-full h-96 bg-gray-900 text-green-400 font-mono p-4 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-teal-500"
                  placeholder="Paste your code here..."
                />
              </div>
            ) : (
              <div 
                id="monaco-editor" 
                style={{ height: '400px', width: '100%' }}
              />
            )}
          </div>

          {/* Output */}
          <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-white/20 overflow-hidden" style={{ height: '200px' }}>
            <div className="bg-black/30 px-4 py-3 border-b border-white/10">
              <div className="flex items-center space-x-3">
                <Terminal className="w-5 h-5 text-green-400" />
                <span className="text-white font-semibold">Output</span>
              </div>
            </div>
            <div className="p-4 h-full overflow-y-auto">
              {executing ? (
                <div className="flex items-center space-x-2 text-purple-300">
                  <Loader className="w-4 h-4 animate-spin" />
                  <span>Executing code...</span>
                </div>
              ) : output ? (
                <pre className="text-green-400 font-mono text-sm whitespace-pre-wrap">{output}</pre>
              ) : (
                <p className="text-purple-300 italic">Output will appear here...</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
