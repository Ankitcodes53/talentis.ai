import { useState } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'

const Candidates = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    skills: '',
    experience_years: '',
  })
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      const candidateData = {
        ...formData,
        skills: formData.skills.split(',').map(s => s.trim()),
        experience_years: parseInt(formData.experience_years),
      }
      
      await axios.post('/api/candidates', candidateData)
      setSubmitted(true)
      setTimeout(() => setSubmitted(false), 3000)
      setFormData({
        name: '',
        email: '',
        phone: '',
        skills: '',
        experience_years: '',
      })
    } catch (error) {
      console.error('Error submitting candidate:', error)
    }
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  return (
    <div className="pt-24 px-4 min-h-screen pb-20">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-primary-800">
            Join Our Talent Network
          </h1>
          <p className="text-xl text-primary-600">
            Let AI connect you with your dream job
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          {submitted && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 bg-green-100 text-green-700 rounded-lg"
            >
              Successfully registered! We'll be in touch soon.
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-primary-700 font-semibold mb-2">
                Full Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="input-field"
                placeholder="John Doe"
              />
            </div>

            <div>
              <label className="block text-primary-700 font-semibold mb-2">
                Email *
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="input-field"
                placeholder="john@example.com"
              />
            </div>

            <div>
              <label className="block text-primary-700 font-semibold mb-2">
                Phone *
              </label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                required
                className="input-field"
                placeholder="+1 (555) 123-4567"
              />
            </div>

            <div>
              <label className="block text-primary-700 font-semibold mb-2">
                Skills (comma-separated) *
              </label>
              <input
                type="text"
                name="skills"
                value={formData.skills}
                onChange={handleChange}
                required
                className="input-field"
                placeholder="Python, React, Machine Learning"
              />
            </div>

            <div>
              <label className="block text-primary-700 font-semibold mb-2">
                Years of Experience *
              </label>
              <input
                type="number"
                name="experience_years"
                value={formData.experience_years}
                onChange={handleChange}
                required
                min="0"
                className="input-field"
                placeholder="5"
              />
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              className="w-full btn-primary text-lg py-4"
            >
              Submit Application
            </motion.button>
          </form>
        </motion.div>

        {/* Benefits Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-16 grid md:grid-cols-3 gap-6"
        >
          {[
            { icon: '🎯', title: 'Perfect Matches', text: 'AI finds jobs that fit your skills' },
            { icon: '🚀', title: 'Fast Process', text: 'Get matched with opportunities quickly' },
            { icon: '💼', title: 'Top Companies', text: 'Access exclusive job openings' },
          ].map((benefit, index) => (
            <div key={index} className="card text-center">
              <div className="text-4xl mb-3">{benefit.icon}</div>
              <h3 className="text-xl font-semibold mb-2 text-primary-800">
                {benefit.title}
              </h3>
              <p className="text-primary-600">{benefit.text}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  )
}

export default Candidates
