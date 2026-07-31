// frontend/src/components/SkillOnboardingModal.jsx
import React, { useState } from 'react';
import { Sparkles, Code2, ArrowRight } from 'lucide-react';

const SUGGESTED_SKILLS = [
  'Python',
  'React',
  'JavaScript',
  'TypeScript',
  'Machine Learning',
  'Deep Learning',
  'Django',
  'FastAPI',
  'Cryptography',
  'Rust',
  'Go',
  'C++',
];

export default function SkillOnboardingModal({ onSelectSkills }) {
  const [selectedSkills, setSelectedSkills] = useState([]);

  const toggleSkill = (skill) => {
    if (selectedSkills.includes(skill)) {
      setSelectedSkills(selectedSkills.filter((s) => s !== skill));
    } else {
      setSelectedSkills([...selectedSkills, skill]);
    }
  };

  const handleContinue = () => {
    const query = selectedSkills.join(' ');
    onSelectSkills(query);
  };

  return (
    <div className="fixed inset-0 bg-slate-950/90 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="max-w-lg w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-indigo-600/20 text-indigo-400 mb-3 border border-indigo-500/30">
            <Sparkles className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Tailor Your Experience
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Select technologies you are interested in to personalize your repository feed.
          </p>
        </div>

        {/* Skill Badges Selection Grid */}
        <div className="flex flex-wrap gap-2.5 justify-center mb-8">
          {SUGGESTED_SKILLS.map((skill) => {
            const isSelected = selectedSkills.includes(skill);
            return (
              <button
                key={skill}
                type="button"
                onClick={() => toggleSkill(skill)}
                className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 border ${
                  isSelected
                    ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30 scale-105'
                    : 'bg-slate-800/60 text-slate-300 border-slate-700/60 hover:border-slate-500'
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>{skill}</span>
              </button>
            );
          })}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => onSelectSkills('')}
            className="flex-1 py-3 px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium rounded-xl text-xs transition-colors cursor-pointer"
          >
            Skip for now
          </button>
          <button
            onClick={handleContinue}
            className="flex-1 py-3 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl text-xs transition-all shadow-lg shadow-indigo-600/20 flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>Explore Projects</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}