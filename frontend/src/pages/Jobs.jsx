import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'

const Jobs = () => {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    try {
      const response = await axios.get('/api/jobs')
      setJobs(response.data.jobs || [])
    } catch (error) {
      console.error('Error fetching jobs:', error)
      // Demo data fallback
      setJobs([
        {
          id: 1,
          title: 'Senior Frontend Developer',
          company: 'TechCorp Inc.',
          location: 'Remote',
          job_type: 'full-time',
          salary_range: '$120k - $160k',
          required_skills: 'React,TypeScript,Tailwind',
        },
        {
          id: 2,
          title: 'AI/ML Engineer',
          company: 'AI Innovations',
          location: 'San Francisco, CA',
          job_type: 'full-time',
          salary_range: '$140k - $200k',
          required_skills: 'Python,TensorFlow,LangChain',
        },
        {
          id: 3,
          title: 'Product Designer',
          company: 'Design Studio',
          location: 'New York, NY',
          job_type: 'contract',
          salary_range: '$90k - $120k',
          required_skills: 'Figma,UI/UX,Prototyping',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="pt-24 px-4 min-h-screen pb-20">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-primary-800">
            Discover Your Next Opportunity
          </h1>
          <p className="text-xl text-primary-600">
            Browse through AI-curated job listings tailored to your skills
          </p>
        </motion.div>

        {/* Search & Filter */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card mb-8"
        >
          <div className="grid md:grid-cols-3 gap-4">
            <input
              type="text"
              placeholder="Job title or keyword"
              className="input-field"
            />
            <input
              type="text"
              placeholder="Location"
              className="input-field"
            />
            <button className="btn-primary">Search Jobs</button>
          </div>
        </motion.div>

        {/* Job Listings */}
        {loading ? (
          <div className="text-center py-20">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-accent-purple"></div>
          </div>
        ) : (
          <div className="space-y-6">
            {jobs.map((job, index) => (
              <motion.div
                key={job.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.02 }}
                className="card cursor-pointer"
              >
                <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                  <div className="flex-1">
                    <h3 className="text-2xl font-semibold text-primary-800 mb-2">
                      {job.title}
                    </h3>
                    <p className="text-lg text-primary-600 mb-3">
                      {job.company} • {job.location}
                    </p>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {job.required_skills?.split(',').map((skill, i) => (
                        <span
                          key={i}
                          className="px-3 py-1 bg-accent-purple/10 text-accent-purple rounded-full text-sm font-medium"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                    <p className="text-primary-500">
                      {job.job_type} • {job.salary_range}
                    </p>
                  </div>
                  <button className="mt-4 md:mt-0 btn-primary">
                    Apply Now
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Jobs
