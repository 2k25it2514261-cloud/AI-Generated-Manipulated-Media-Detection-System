import React from 'react';
import { HealthStatus } from '../components/HealthStatus';
import { PipelineOverview } from '../components/PipelineOverview';
import { HealthResponse } from '../types';
import { Shield, Sparkles, FolderLock, Scale } from 'lucide-react';

interface DashboardProps {
  health: HealthResponse | null;
  error: string | null;
  loading: boolean;
}

export const Dashboard: React.FC<DashboardProps> = ({ health, error, loading }) => {
  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero / System Banner */}
      <div className="relative rounded-2xl p-8 bg-gradient-to-r from-slate-900 via-[#0E1726] to-slate-900 border border-slate-800 shadow-2xl overflow-hidden">
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Digital Media Forensics Platform</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl">
            Evidence-Based AI Media Forensics
          </h1>
          <p className="mt-3 text-sm sm:text-base text-slate-300 leading-relaxed">
            A production-grade, multi-pipeline forensics engine. Combining CNN artifact detectors, 2D FFT spectral analysis, facial landmark geometry, blink/temporal sequence models, metadata extraction, and C2PA provenance credentials into calibrated forensic assessments.
          </p>
          
          <div className="mt-6 flex flex-wrap gap-4 text-xs text-slate-400">
            <div className="flex items-center space-x-1.5 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800">
              <FolderLock className="w-4 h-4 text-cyan-400" />
              <span>Immutable Chain of Custody (SHA-256)</span>
            </div>
            <div className="flex items-center space-x-1.5 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800">
              <Scale className="w-4 h-4 text-emerald-400" />
              <span>Probabilistic Calibrated Evidence</span>
            </div>
            <div className="flex items-center space-x-1.5 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800">
              <Shield className="w-4 h-4 text-purple-400" />
              <span>Explainable AI Heatmaps (Grad-CAM)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Backend Health Check Status */}
      <HealthStatus health={health} error={error} loading={loading} />

      {/* Modular Pipeline Architecture Overview */}
      <PipelineOverview />
    </div>
  );
};
