// frontend/src/components/AuthModal.jsx
import React, { useState } from 'react';
import { loginUser, registerUser, API_BASE_URL } from '../api';
import { Sparkles, Lock, Mail, User, ArrowRight, CheckCircle } from 'lucide-react';

const TRUSTED_DOMAINS = [
  'gmail.com', 'googlemail.com',
  'outlook.com', 'hotmail.com', 'live.com', 'msn.com',
  'yahoo.com', 'yahoo.co.in', 'yahoo.co.uk', 'yahoo.fr', 'ymail.com', 'rocketmail.com',
  'icloud.com', 'me.com', 'mac.com',
  'proton.me', 'protonmail.com', 'tuta.com', 'tutanota.com',
  'zoho.com', 'zohomail.com', 'aol.com', 'mail.com', 'gmx.com', 'fastmail.com', 'hey.com',
  'github.com', 'google.com', 'microsoft.com'
];

const isAllowedDomain = (email) => {
  if (!email || !email.includes('@')) return false;
  const parts = email.split('@');
  if (parts.length !== 2) return false;
  const domain = parts[1].toLowerCase().trim();
  
  if (TRUSTED_DOMAINS.includes(domain)) return true;
  if (domain.endsWith('.edu') || domain.endsWith('.edu.in') || domain.endsWith('.ac.in') || domain.endsWith('.ac.uk')) {
    return true;
  }
  return false;
};

export default function AuthModal({ onAuthSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
  });

  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
    setSuccessMessage('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccessMessage('');

    // Pre-flight check for domain in registration mode
    if (!isLogin) {
      if (!isAllowedDomain(formData.email)) {
        setError('Please use a recognized email provider (e.g. Gmail, Outlook, Yahoo, iCloud, Proton, Zoho) or an official .edu domain.');
        setLoading(false);
        return;
      }
    }

    try {
      if (isLogin) {
        // 1. Handle Login
        const data = await loginUser(formData.username, formData.password);
        localStorage.setItem('token', data.access_token);
        onAuthSuccess();
      } else {
        // 2. Handle Registration with domain deliverability verification
        await registerUser({
          username: formData.username,
          email: formData.email,
          password: formData.password,
        });
        
        // Switch to sign-in tab with prefilled username
        setIsLogin(true);
        setFormData((prev) => ({ ...prev, password: '' }));
        setSuccessMessage('Account created successfully! Please sign in with your credentials.');
      }
    } catch (err) {
      console.error('Registration/Login error:', err);
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail) && detail.length > 0) {
        setError(detail.map(d => d.msg || JSON.stringify(d)).join(', '));
      } else if (!err.response) {
        setError(`Cannot reach backend (${API_BASE_URL}). If using Render free tier, the server may take 30-50 seconds to wake up from idle. Please wait a moment and retry.`);
      } else {
        setError(err.message || 'Authentication failed. Please check your inputs.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        {/* Header Branding */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-indigo-600/20 text-indigo-400 mb-3 border border-indigo-500/30">
            <Sparkles className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            OpenSource Navigator
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            {isLogin ? 'Welcome back! Log in to explore projects.' : 'Create an account to save & explore projects.'}
          </p>
        </div>

        {/* Success Alert */}
        {successMessage && (
          <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-start gap-2">
            <CheckCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Username
            </label>
            <div className="relative">
              <User className="w-5 h-5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                name="username"
                required
                value={formData.username}
                onChange={handleChange}
                placeholder="johndoe"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
          </div>

          {!isLogin && (
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-5 h-5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  name="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="john@gmail.com"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Supports Gmail, Outlook, Yahoo, iCloud, Proton, Zoho, or .edu domains.
              </p>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="w-5 h-5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                name="password"
                required
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-white font-medium rounded-xl transition-all shadow-lg shadow-indigo-600/20 flex items-center justify-center gap-2 cursor-pointer mt-6"
          >
            {loading ? (
              <div className="flex items-center gap-2 text-xs">
                <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin shrink-0" />
                <span>Processing... (Render server loading / waking up)</span>
              </div>
            ) : (
              <>
                <span>{isLogin ? 'Sign In' : 'Create Account'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>

          {loading && (
            <p className="text-[11px] text-amber-400/90 text-center mt-3 bg-amber-500/10 border border-amber-500/20 py-2 px-3 rounded-lg leading-relaxed">
              ⏳ <strong>Render free tier waking up:</strong> If the server has been idle, Render takes ~30–50s to spin up. Please wait...
            </p>
          )}
        </form>

        {/* Toggle Mode */}
        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
              setSuccessMessage('');
            }}
            className="text-xs text-slate-400 hover:text-indigo-400 transition-colors cursor-pointer"
          >
            {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Log in'}
          </button>
        </div>
      </div>
    </div>
  );
}
