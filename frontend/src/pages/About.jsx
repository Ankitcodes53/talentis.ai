import { motion } from 'framer-motion'

const About = () => {
  return (
    <div className="pt-24 px-4 min-h-screen pb-20">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-primary-800">
            About Talentis.ai
          </h1>
          <p className="text-xl text-primary-600">
            Revolutionizing recruitment through artificial intelligence
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card mb-8"
        >
          <h2 className="text-3xl font-bold mb-4 text-primary-800">Our Mission</h2>
          <p className="text-lg text-primary-600 leading-relaxed mb-4">
            At Talentis.ai, we believe that finding the perfect job or candidate shouldn't be 
            a matter of luck. Our advanced AI algorithms analyze thousands of data points to 
            create meaningful connections between talented individuals and forward-thinking companies.
          </p>
          <p className="text-lg text-primary-600 leading-relaxed">
            We're on a mission to make hiring faster, fairer, and more effective for everyone 
            involved in the process.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card mb-8"
        >
          <h2 className="text-3xl font-bold mb-6 text-primary-800">How It Works</h2>
          <div className="space-y-6">
            {[
              {
                step: '1',
                title: 'Create Your Profile',
                description: 'Share your skills, experience, and career goals with us.',
              },
              {
                step: '2',
                title: 'AI Analysis',
                description: 'Our AI analyzes your profile and matches you with opportunities.',
              },
              {
                step: '3',
                title: 'Get Matched',
                description: 'Receive personalized job recommendations or candidate profiles.',
              },
              {
                step: '4',
                title: 'Connect & Hire',
                description: 'Connect with matches and start the hiring process.',
              },
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="flex items-start space-x-4"
              >
                <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-r from-accent-purple to-accent-blue rounded-full flex items-center justify-center text-white font-bold text-xl">
                  {item.step}
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2 text-primary-800">
                    {item.title}
                  </h3>
                  <p className="text-primary-600">{item.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="card bg-gradient-to-r from-accent-purple to-accent-blue text-white text-center"
        >
          <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
          <p className="text-xl mb-6 opacity-90">
            Join thousands of companies and candidates already using Talentis.ai
          </p>
          <button className="px-8 py-4 bg-white text-accent-purple font-semibold rounded-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300">
            Sign Up Now
          </button>
        </motion.div>
      </div>
    </div>
  )
}

export default About
