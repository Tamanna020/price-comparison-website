import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, Mail, Lock, User, AlertCircle, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const AuthModal: React.FC = () => {
  const { isAuthModalOpen, closeAuthModal, authModalMode, login, register } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>(authModalMode);
  
  // Form state
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Sync mode when opened from external context
  React.useEffect(() => {
    setMode(authModalMode);
    setError(null);
  }, [authModalMode, isAuthModalOpen]);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (mode === 'register' && !name.trim()) {
      setError('Please enter your full name');
      return;
    }
    if (!email.trim() || !email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }
    if (!password || password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setIsSubmitting(true);
    if (mode === 'login') {
      const res = await login(email, password);
      if (!res.success) {
        setError(res.error || 'Invalid email or password');
      }
    } else {
      const res = await register(name, email, password);
      if (!res.success) {
        setError(res.error || 'Registration failed');
      }
    }
    setIsSubmitting(false);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={closeAuthModal}
          className="fixed inset-0 bg-espresso-950/60 backdrop-blur-sm transition-opacity"
        />

        {/* Modal Window */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          className="relative w-full max-w-md bg-ivory border border-rose-200/80 rounded-3xl shadow-2xl overflow-hidden z-10"
        >
          {/* Header Banner */}
          <div className="bg-gradient-to-r from-rose-500/10 via-champagne-500/15 to-rose-400/10 p-6 sm:p-8 pb-6 border-b border-rose-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="p-2 rounded-xl bg-white shadow-xs text-rose-500">
                  <Sparkles className="w-5 h-5" />
                </span>
                <div>
                  <h3 className="font-editorial text-2xl font-bold text-espresso-900">
                    {mode === 'login' ? 'Welcome Back' : 'Create Account'}
                  </h3>
                  <p className="text-xs text-espresso-500 font-sans mt-0.5">
                    {mode === 'login'
                      ? 'Access your saved routines & price intelligence'
                      : 'Personalized Indian beauty discovery & skin tracking'}
                  </p>
                </div>
              </div>
              <button
                onClick={closeAuthModal}
                className="p-1.5 rounded-full hover:bg-rose-100/60 text-espresso-500 hover:text-espresso-800 transition-colors"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Tab Switcher */}
            <div className="flex bg-white/70 p-1 rounded-xl mt-6 border border-rose-200/60 shadow-xs">
              <button
                type="button"
                onClick={() => {
                  setMode('login');
                  setError(null);
                }}
                className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  mode === 'login'
                    ? 'bg-rose-500 text-ivory shadow-xs font-semibold'
                    : 'text-espresso-600 hover:text-rose-600'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode('register');
                  setError(null);
                }}
                className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  mode === 'register'
                    ? 'bg-rose-500 text-ivory shadow-xs font-semibold'
                    : 'text-espresso-600 hover:text-rose-600'
                }`}
              >
                Create Account
              </button>
            </div>
          </div>

          {/* Form Body */}
          <form onSubmit={handleSubmit} className="p-6 sm:p-8 space-y-4">
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2"
              >
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
                <span>{error}</span>
              </motion.div>
            )}

            {mode === 'register' && (
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-espresso-700">
                  Full Name
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-espresso-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Ananya Sharma"
                    className="w-full pl-10 pr-4 py-2.5 bg-white border border-rose-200 rounded-xl text-sm text-espresso-900 placeholder:text-espresso-300 focus:outline-hidden focus:border-rose-400 focus:ring-2 focus:ring-rose-200/50 transition-all"
                  />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="block text-xs font-medium text-espresso-700">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-espresso-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ananya@example.com"
                  className="w-full pl-10 pr-4 py-2.5 bg-white border border-rose-200 rounded-xl text-sm text-espresso-900 placeholder:text-espresso-300 focus:outline-hidden focus:border-rose-400 focus:ring-2 focus:ring-rose-200/50 transition-all"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-medium text-espresso-700">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-espresso-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-4 py-2.5 bg-white border border-rose-200 rounded-xl text-sm text-espresso-900 placeholder:text-espresso-300 focus:outline-hidden focus:border-rose-400 focus:ring-2 focus:ring-rose-200/50 transition-all"
                />
              </div>
              <p className="text-[11px] text-espresso-400">
                Must be at least 8 characters with salted PBKDF2 encryption.
              </p>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 py-3 px-4 rounded-xl bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-ivory text-sm font-semibold flex items-center justify-center space-x-2 shadow-md hover:shadow-lg transition-all disabled:opacity-50"
            >
              <span>{isSubmitting ? 'Verifying...' : mode === 'login' ? 'Sign In' : 'Create My Account'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <div className="pt-2 text-center">
              <p className="text-[11px] text-espresso-500">
                By signing in, your personalized routine, skin profile, and watchlist are securely stored.
              </p>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

