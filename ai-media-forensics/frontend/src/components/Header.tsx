import React from 'react';
import { ShieldCheck, Activity, Database } from 'lucide-react';
import { HealthResponse } from '../types';

interface HeaderProps {
  health: HealthResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health, loading, onRefresh }) => {
  const isHealthy = health?.status === 'ok';

  return (
    <header className="border-b border-slate-800 bg-[#0F172A]/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Logo and System Title */}
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-cyan-600 via-cyan-500 to-emerald-400 p-[2px] shadow-lg shadow-cyan-500/20">
            <div className="w-full h-full bg-[#0B0F19] rounded-[10px] flex items-center justify-center">
              <ShieldCheck className="w-6 h-6 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold text-white tracking-tight">AI MEDIA FORENSICS</h1>
              <span className="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                Phase 1 Foundation
              </span>
            </div>
            <p className="text-xs text-slate-400">Multi-Pipeline Synthetic & Manipulated Media Detection Platform</p>
          </div>
        </div>

        {/* Backend & DB Health Indicator */}
        <div className="flex items-center space-x-4">
          <div className="hidden md:flex items-center space-x-3 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
            <div className="flex items-center space-x-1.5">
              <div className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
              <span className="text-slate-300 font-medium">FastAPI Engine</span>
            </div>
            <span className="text-slate-600">|</span>
            <div className="flex items-center space-x-1.5">
              <Database className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-300 capitalize">{health?.database?.type || 'DB'}</span>
            </div>
            <span className="text-slate-600">|</span>
            <span className="mono-font text-slate-400">v{health?.version || '1.0.0'}</span>
          </div>

          <button
            onClick={onRefresh}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition border border-slate-700 disabled:opacity-50"
            title="Refresh backend status"
          >
            <Activity className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : 'text-slate-300'}`} />
            <span>{loading ? 'Checking...' : 'Ping Engine'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
