// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import AuthModal from './components/AuthModal';
import RepoCard from './components/RepoCard';
import {
  fetchUserProfile,
  fetchRecommendations,
  fetchBookmarks,
  bookmarkRepo,
  fetchAIInsights,
} from './api';
import {
  Sparkles,
  LogOut,
  Bookmark,
  Compass,
  X,
  CheckCircle2,
  Loader2,
} from 'lucide-react';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('token')
  );
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('explore'); // 'explore' or 'bookmarks'
  const [repos, setRepos] = useState([]);
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(false);

  // AI Modal State
  const [selectedRepoForAI, setSelectedRepoForAI] = useState(null);
  const [aiData, setAiData] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      loadInitialData();
    }
  }, [isAuthenticated]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const profile = await fetchUserProfile();
      setUser(profile);

      const [recData, bookmarkData] = await Promise.all([
        fetchRecommendations(),
        fetchBookmarks(),
      ]);

      setRepos(recData);
      setBookmarks(bookmarkData);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      if (err.response?.status === 401) {
        handleLogout();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setUser(null);
  };

  const handleBookmarkToggle = async (githubId) => {
    try {
      await bookmarkRepo(githubId);
      const updatedBookmarks = await fetchBookmarks();
      setBookmarks(updatedBookmarks);
    } catch (err) {
      console.error('Bookmark action failed:', err);
    }
  };

  const handleOpenAIModal = async (repo) => {
    setSelectedRepoForAI(repo);
    setAiData(null);
    setAiLoading(true);

    try {
      const data = await fetchAIInsights(repo.github_id);
      setAiData(data.ai_insights);
    } catch (err) {
      console.error('AI Insights fetch failed:', err);
    } finally {
      setAiLoading(false);
    }
  };

  if (!isAuthenticated) {
    return <AuthModal onAuthSuccess={() => setIsAuthenticated(true)} />;
  }

  const bookmarkedIds = new Set(bookmarks.map((b) => b.github_id));
  const displayedRepos = activeTab === 'explore' ? repos : bookmarks;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Navigation Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <span className="font-bold text-lg text-white">OpenSource Navigator</span>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-xs text-slate-400 bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700">
              Logged in as <strong className="text-white">{user?.username}</strong>
            </span>
            <button
              onClick={handleLogout}
              className="p-2 hover:bg-slate-800 text-slate-400 hover:text-red-400 rounded-xl transition-colors cursor-pointer"
              title="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-3 mb-8 border-b border-slate-800 pb-4">
          <button
            onClick={() => setActiveTab('explore')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all cursor-pointer ${
              activeTab === 'explore'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <Compass className="w-4 h-4" />
            <span>Explore Repositories</span>
          </button>

          <button
            onClick={() => setActiveTab('bookmarks')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all cursor-pointer ${
              activeTab === 'bookmarks'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <Bookmark className="w-4 h-4" />
            <span>Saved Bookmarks ({bookmarks.length})</span>
          </button>
        </div>

        {/* Repository Grid Feed */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
            <Loader2 className="w-8 h-8 animate-spin mb-3 text-indigo-500" />
            <p className="text-sm">Fetching repository metrics from backend...</p>
          </div>
        ) : displayedRepos.length === 0 ? (
          <div className="text-center py-20 bg-slate-900/40 rounded-2xl border border-slate-800">
            <p className="text-slate-400 text-sm">
              {activeTab === 'bookmarks'
                ? 'No saved repositories yet. Explore and bookmark your favorite projects!'
                : 'No repositories found.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displayedRepos.map((repo) => (
              <RepoCard
                key={repo.github_id}
                repo={repo}
                isBookmarked={bookmarkedIds.has(repo.github_id)}
                onBookmarkToggle={handleBookmarkToggle}
                onOpenAI={handleOpenAIModal}
              />
            ))}
          </div>
        )}
      </main>

      {/* AI Insights Modal Overlay */}
      {selectedRepoForAI && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative">
            {/* Close Button */}
            <button
              onClick={() => setSelectedRepoForAI(null)}
              className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Modal Title */}
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <h2 className="text-lg font-bold text-white">
                AI Analysis: {selectedRepoForAI.name}
              </h2>
            </div>

            {/* Modal Body */}
            {aiLoading ? (
              <div className="py-12 flex flex-col items-center justify-center text-slate-400">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-400 mb-3" />
                <p className="text-xs">Analyzing codebase with Gemini AI...</p>
              </div>
            ) : aiData ? (
              <div className="space-y-6">
                {/* AI Summary */}
                <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                  <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-2">
                    Project Summary
                  </h4>
                  <p className="text-sm text-slate-200 leading-relaxed">
                    {aiData.summary}
                  </p>
                </div>

                {/* Beginner Contribution Roadmap */}
                <div>
                  <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-3">
                    Beginner Contribution Roadmap
                  </h4>
                  <ul className="space-y-2.5">
                    {aiData.roadmap?.map((step, idx) => (
                      <li
                        key={idx}
                        className="flex items-start gap-2.5 text-xs text-slate-300 bg-slate-800/30 p-3 rounded-xl border border-slate-800"
                      >
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <p className="text-xs text-red-400 py-6 text-center">
                Failed to load AI insights. Please check backend connection.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}