import { motion } from 'framer-motion'
import { Users, BookOpen, Trophy, MessageSquare } from 'lucide-react'

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-surface">
      {/* Navigation */}
      <nav className="border-b border-surface-border bg-surface-elevated">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-heading-3 font-bold text-gradient">MeshWork</h1>
            <div className="flex items-center gap-4">
              <button className="btn-secondary text-sm">Settings</button>
              <div className="w-10 h-10 rounded-full bg-primary-500 flex items-center justify-center text-white font-semibold">
                JD
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h2 className="text-heading-1 mb-2">Welcome back, John!</h2>
          <p className="text-body text-text-secondary">
            Here's what's happening in your workspace today.
          </p>
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid md:grid-cols-4 gap-6 mb-8"
        >
          <StatCard icon={<Users />} label="Communities" value="12" />
          <StatCard icon={<BookOpen />} label="Tasks Completed" value="47" />
          <StatCard icon={<Trophy />} label="Total XP" value="2,450" />
          <StatCard icon={<MessageSquare />} label="Messages" value="128" />
        </motion.div>

        {/* Content Sections */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="card"
            >
              <h3 className="text-heading-3 mb-4">Your Communities</h3>
              <p className="text-body-sm text-text-muted">
                Community list will appear here...
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="card"
            >
              <h3 className="text-heading-3 mb-4">Recent Activity</h3>
              <p className="text-body-sm text-text-muted">
                Activity feed will appear here...
              </p>
            </motion.div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="card"
            >
              <h3 className="text-heading-3 mb-4">Leaderboard</h3>
              <p className="text-body-sm text-text-muted">
                Top performers will appear here...
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="card"
            >
              <h3 className="text-heading-3 mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <button className="btn-secondary w-full text-left text-sm">
                  Create Community
                </button>
                <button className="btn-secondary w-full text-left text-sm">
                  Join Community
                </button>
                <button className="btn-secondary w-full text-left text-sm">
                  View Profile
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value }) {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="card"
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400">
          {icon}
        </div>
        <div>
          <p className="text-caption text-text-muted">{label}</p>
          <p className="text-heading-3">{value}</p>
        </div>
      </div>
    </motion.div>
  )
}
