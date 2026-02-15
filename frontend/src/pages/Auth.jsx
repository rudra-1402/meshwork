import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import { LogIn, UserPlus, Mail, Lock, User, ArrowLeft } from 'lucide-react'

export default function Auth() {
  const [mode, setMode] = useState('login') // 'login' or 'register'
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-surface to-accent/5 dark:from-gray-900 dark:via-gray-800 dark:to-primary-900/20 flex items-center justify-center p-6">
      {/* Back Button */}
      <Link
        to="/"
        className="absolute top-6 left-6 inline-flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span className="text-sm font-medium">Back to Home</span>
      </Link>

      {/* Auth Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md"
      >
        <div className="card">
          {/* Header */}
          <div className="text-center mb-8">
            <motion.div
              key={mode}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="w-12 h-12 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400 mx-auto mb-4"
            >
              {mode === 'login' ? <LogIn className="w-6 h-6" /> : <UserPlus className="w-6 h-6" />}
            </motion.div>
            <h2 className="text-heading-2 mb-2">
              {mode === 'login' ? 'Welcome Back' : 'Create Account'}
            </h2>
            <p className="text-body-sm text-text-secondary">
              {mode === 'login'
                ? 'Sign in to continue to MeshWork'
                : 'Join MeshWork and start collaborating'}
            </p>
          </div>

          {/* Form */}
          <AnimatePresence mode="wait">
            <motion.form
              key={mode}
              initial={{ opacity: 0, x: mode === 'login' ? -20 : 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: mode === 'login' ? 20 : -20 }}
              transition={{ duration: 0.3 }}
              className="space-y-4"
              onSubmit={(e) => {
                e.preventDefault()
                // TODO: Connect to API
                navigate('/dashboard')
              }}
            >
              {/* Name Field (Register Only) */}
              {mode === 'register' && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <label className="label">Full Name</label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                    <input
                      type="text"
                      placeholder="John Doe"
                      className="input pl-11"
                      required
                    />
                  </div>
                </motion.div>
              )}

              {/* Email Field */}
              <div>
                <label className="label">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                  <input
                    type="email"
                    placeholder="you@example.com"
                    className="input pl-11"
                    required
                  />
                </div>
              </div>

              {/* Password Field */}
              <div>
                <label className="label">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                  <input
                    type="password"
                    placeholder="••••••••"
                    className="input pl-11"
                    required
                  />
                </div>
              </div>

              {/* Submit Button */}
              <button type="submit" className="btn-primary w-full">
                {mode === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            </motion.form>
          </AnimatePresence>

          {/* Toggle Mode */}
          <div className="mt-6 text-center">
            <p className="text-body-sm text-text-secondary">
              {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
              <button
                onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
                className="text-primary-600 dark:text-primary-400 font-medium hover:underline"
              >
                {mode === 'login' ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
