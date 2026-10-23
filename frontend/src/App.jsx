// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import AuthModal from './components/AuthModal';
import RepoCard from './components/RepoCard';
import SkillOnboardingModal from './components/SkillOnboardingModal';
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
  Search,
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
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showOnboarding, setShowOnboarding] = useState(false);

  // AI Modal State
  const [selectedRepoForAI, setSelectedRepoForAI] = useState(null);
  const [aiData, setAiData] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      loadInitialData();
    }
  }, [isAuthenticated]);

  // Infinite Scroll Event Listener
  useEffect(() => {
    const handleScroll = () => {
      if (
        window.innerHeight + document.documentElement.scrollTop >=
          document.documentElement.offsetHeight - 300 &&
        !loadingMore &&
        !loading &&
        hasMore &&
        activeTab === 'explore'
      ) {
        loadMoreRepos();
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [loadingMore, loading, hasMore, page, searchQuery, activeTab]);

  const loadInitialData = async (queryOverride = null) => {
    setLoading(true);
    setPage(1);
    setHasMore(true);
    try {
      const profile = await fetchUserProfile();
      setUser(profile);

      const activeQuery = queryOverride !== null ? queryOverride : searchQuery;

      const [recData, bookmarkData] = await Promise.all([
        fetchRecommendations(activeQuery, 1),
        fetchBookmarks(),
      ]);

      setRepos(recData);
      setBookmarks(bookmarkData);
      if (recData.length < 12) setHasMore(false);

      const hasOnboarded = localStorage.getItem(`onboarded_${profile.username}`);
      if (!hasOnboarded && queryOverride === null) {
        setShowOnboarding(true);
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      if (err.response?.status === 401) {
        handleLogout();
      }
    } finally {
      setLoading(false);
    }
  };

  const loadMoreRepos = async () => {
    setLoadingMore(true);
    const nextPage = page + 1;
    try {
      const nextData = await fetchRecommendations(searchQuery, nextPage);
      if (nextData.length === 0) {
        setHasMore(false);
      } else {
        // Prevent duplicates
        setRepos((prev) => {
          const existingIds = new Set(prev.map((r) => r.github_id));
          const filteredNew = nextData.filter((r) => !existingIds.has(r.github_id));
          return [...prev, ...filteredNew];
        });
        setPage(nextPage);
      }
    } catch (err) {
      console.error('Failed to fetch more repositories:', err);
    } finally {
      setLoadingMore(false);
    }
  };

  const handleHomeClick = () => {
    setActiveTab('explore');
    setSearchQuery('');
    loadInitialData('');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setUser(null);
  };

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearchQuery(val);
    if (val.trim() === '') {
      loadInitialData('');
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadInitialData(searchQuery);
  };

  const handleOnboardingSkills = (selectedSkillsQuery) => {
    if (user?.username) {
      localStorage.setItem(`onboarded_${user.username}`, 'true');
    }
    setShowOnboarding(false);
    if (selectedSkillsQuery) {
      setSearchQuery(selectedSkillsQuery);
      loadInitialData(selectedSkillsQuery);
    }
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
      {/* Onboarding Modal */}
      {showOnboarding && (
        <SkillOnboardingModal onSelectSkills={handleOnboardingSkills} />
      )}

      {/* Navigation Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Clickable Home Brand Header */}
          <button
            onClick={handleHomeClick}
            className="flex items-center gap-3 group text-left cursor-pointer focus:outline-none"
            title="Go to Home"
          >
            <div className="w-9 h-9 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center group-hover:bg-indigo-600 group-hover:text-white transition-all">
              <Sparkles className="w-5 h-5" />
            </div>
            <span className="font-bold text-lg text-white group-hover:text-indigo-400 transition-colors">
              OpenSource Navigator
            </span>
          </button>

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
        {/* Navigation Tabs & Search */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 mb-8 border-b border-slate-800 pb-6">
          <div className="flex items-center gap-3 w-full md:w-auto">
            <button
              onClick={() => setActiveTab('explore')}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
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
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'bookmarks'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                  : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              <Bookmark className="w-4 h-4" />
              <span>Saved Bookmarks ({bookmarks.length})</span>
            </button>
          </div>

          {activeTab === 'explore' && (
            <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={handleSearchChange}
                placeholder="Search skills, topics, languages..."
                className="w-full pl-10 pr-9 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => {
                    setSearchQuery('');
                    loadInitialData('');
                  }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </form>
          )}
        </div>

        {/* Repository Grid Feed */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
            <Loader2 className="w-8 h-8 animate-spin mb-3 text-indigo-500" />
            <p className="text-sm">Fetching repository metrics...</p>
          </div>
        ) : displayedRepos.length === 0 ? (
          <div className="text-center py-20 bg-slate-900/40 rounded-2xl border border-slate-800">
            <p className="text-slate-400 text-sm">
              {activeTab === 'bookmarks'
                ? 'No saved repositories yet. Explore and bookmark your favorite projects!'
                : 'No repositories found for your search query.'}
            </p>
          </div>
        ) : (
          <>
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

            {/* Bottom Infinite Scroll Spinner */}
            {activeTab === 'explore' && loadingMore && (
              <div className="flex items-center justify-center py-8 text-slate-400">
                <Loader2 className="w-6 h-6 animate-spin text-indigo-400 mr-2" />
                <span className="text-xs font-medium">Loading more projects...</span>
              </div>
            )}
          </>
        )}
      </main>

      {/* AI Insights Modal */}
      {selectedRepoForAI && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setSelectedRepoForAI(null)}
              className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <h2 className="text-lg font-bold text-white">
                AI Analysis: {selectedRepoForAI.name}
              </h2>
            </div>

            {aiLoading ? (
              <div className="py-12 flex flex-col items-center justify-center text-slate-400">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-400 mb-3" />
                <p className="text-xs">Analyzing...Please wait...(5 minutes)</p>
              </div>
            ) : aiData ? (
              <div className="space-y-6">
                <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                  <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-2">
                    Project Summary
                  </h4>
                  <p className="text-sm text-slate-200 leading-relaxed">
                    {aiData.summary}
                  </p>
                </div>

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