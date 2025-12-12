import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'

const Home = () => {
  const features = [
    {
      title: 'AI-Powered Matching',
      description: 'Advanced algorithms match candidates with perfect job opportunities',
      icon: '🤖',
    },
    {
      title: 'Global Reach',
      description: 'Connect with talent and opportunities from around the world',
      icon: '🌍',
    },
    {
      title: 'Real-time Updates',
      description: 'Stay informed with instant notifications and updates',
      icon: '⚡',
    },
    {
      title: 'Smart Analytics',
      description: 'Data-driven insights to make better hiring decisions',
      icon: '📊',
    },
  ]

  return (
    <div className="pt-16">
      {/* Hero Section */}
      <section className="min-h-screen flex items-center justify-center px-4">
        <div className="max-w-6xl mx-auto text-center">
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-accent-purple via-accent-blue to-accent-teal bg-clip-text text-transparent"
          >
            The Future of Hiring is Here
          </motion.h1>
          
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-xl md:text-2xl text-primary-600 mb-12 max-w-3xl mx-auto"
          >
            Talentis.ai revolutionizes recruitment with AI-powered matching,
            connecting exceptional talent with amazing opportunities worldwide.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <Link to="/login" className="btn-primary text-lg">
              Find Jobs
            </Link>
            <Link to="/login" className="btn-secondary text-lg">
              Hire Talent
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <motion.h2
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-4xl font-bold text-center mb-16 text-primary-800"
          >
            Why Choose Talentis.ai?
          </motion.h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                whileHover={{ y: -10 }}
                className="card text-center"
              >
                <div className="text-5xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold mb-3 text-primary-800">
                  {feature.title}
                </h3>
                <p className="text-primary-600">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="max-w-4xl mx-auto card bg-gradient-to-r from-accent-purple to-accent-blue p-12 text-center text-white"
        >
          <h2 className="text-4xl font-bold mb-6">Ready to Transform Your Hiring?</h2>
          <p className="text-xl mb-8 opacity-90">
            Join thousands of companies and candidates already using Talentis.ai
          </p>
          <Link to="/login" className="inline-block px-8 py-4 bg-white text-accent-purple font-semibold rounded-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300">
            Get Started Today
          </Link>
        </motion.div>
      </section>
    </div>
  )
}

export default Home
