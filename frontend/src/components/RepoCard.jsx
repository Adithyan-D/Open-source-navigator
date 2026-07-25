// frontend/src/components/RepoCard.jsx
import React from 'react';
import { Star, GitFork, AlertCircle, Bookmark, Sparkles, Code2, ExternalLink } from 'lucide-react';

export default function RepoCard({ repo, isBookmarked, onBookmarkToggle, onOpenAI }) {
  const githubUrl = `https://github.com/${repo.owner}/${repo.name}`;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-all shadow-lg flex flex-col justify-between group">
      <div>
        {/* Top bar: Language & Bookmark Button */}
        <div className="flex items-center justify-between mb-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-indigo-400 border border-slate-700">
            <Code2 className="w-3.5 h-3.5" />
            {repo.languages || 'General'}
          </span>
          <button
            onClick={() => onBookmarkToggle(repo.github_id)}
            className={`p-2 rounded-xl border transition-all cursor-pointer ${
              isBookmarked
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                : 'bg-slate-800/50 border-slate-700/50 text-slate-400 hover:text-white'
            }`}
            title={isBookmarked ? 'Bookmarked' : 'Bookmark repository'}
          >
            <Bookmark className={`w-4 h-4 ${isBookmarked ? 'fill-amber-400' : ''}`} />
          </button>
        </div>

        {/* Clickable Repo Title & GitHub Link */}
        <a
          href={githubUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-lg font-semibold text-white hover:text-indigo-400 transition-colors mb-1 tracking-tight"
          title="Open Repository on GitHub"
        >
          <span>
            {repo.owner} / <span className="text-indigo-400">{repo.name}</span>
          </span>
          <ExternalLink className="w-4 h-4 text-slate-500 hover:text-indigo-400 shrink-0" />
        </a>

        {/* Description */}
        <p className="text-sm text-slate-400 line-clamp-2 mb-4 min-h-[2.5rem]">
          {repo.description || 'No description provided.'}
        </p>

        {/* GitHub Stats */}
        <div className="grid grid-cols-3 gap-2 py-3 border-y border-slate-800 text-xs text-slate-300 mb-4">
          <div className="flex items-center gap-1.5">
            <Star className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{repo.stars?.toLocaleString()}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <GitFork className="w-4 h-4 text-blue-400 shrink-0" />
            <span>{repo.forks?.toLocaleString()}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <AlertCircle className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{repo.open_issues?.toLocaleString()} issues</span>
          </div>
        </div>

        {/* Dynamic Metric Badges */}
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 bg-slate-800/60 p-2.5 rounded-xl border border-slate-800 text-center">
            <span className="block text-[10px] text-slate-400 uppercase font-bold tracking-wider">
              Complexity
            </span>
            <span className="text-sm font-bold text-indigo-400">
              {repo.complexity_score} / 99
            </span>
          </div>
          <div className="flex-1 bg-slate-800/60 p-2.5 rounded-xl border border-slate-800 text-center">
            <span className="block text-[10px] text-slate-400 uppercase font-bold tracking-wider">
              Health Score
            </span>
            <span className="text-sm font-bold text-emerald-400">
              {repo.health_score} / 99
            </span>
          </div>
        </div>
      </div>

      {/* AI Insights Action Button */}
      <button
        onClick={() => onOpenAI(repo)}
        className="w-full py-2.5 px-4 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 rounded-xl font-medium text-xs transition-all flex items-center justify-center gap-2 cursor-pointer mt-2"
      >
        <Sparkles className="w-4 h-4 text-indigo-400" />
        <span>Generate AI Insights</span>
      </button>
    </div>
  );
}