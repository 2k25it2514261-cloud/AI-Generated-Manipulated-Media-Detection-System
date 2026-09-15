import React from 'react';
import { Layers, Eye, Cpu, Activity, Video, Hash, GitMerge } from 'lucide-react';
import { PipelineModule } from '../types';

const modules: PipelineModule[] = [
  {
    id: 'foundation',
    name: 'Foundation & Core API',
    description: 'FastAPI Gateway, PostgreSQL/SQLite ORM, Health telemetry, Docker configs',
    status: 'active',
    phase: 1,
    category: 'visual'
  },
  {
    id: 'ingestion',
    name: 'Media Ingestion & Hashing',
    description: 'SHA-256 pre-calculation, MIME validation, Non-destructive evidence copies',
    status: 'ready',
    phase: 2,
    category: 'provenance'
  },
  {
    id: 'cnn',
    name: 'CNN Artifact Detector',
    description: 'Modular EfficientNet-B0 / ConvNeXt synthetic artifact classifier',
    status: 'phase_planned',
    phase: 3,
    category: 'visual'
  },
  {
    id: 'frequency',
    name: 'Frequency-Domain FFT',
    description: '2D FFT, magnitude spectrum analysis, periodic spectral anomaly detection',
    status: 'phase_planned',
    phase: 4,
    category: 'frequency'
  },
  {
    id: 'facial',
    name: 'Facial Landmark Consistency',
    description: 'Geometric landmarks, eye/nose/mouth symmetry, natural asymmetry calibration',
    status: 'phase_planned',
    phase: 5,
    category: 'facial'
  },
  {
    id: 'gradcam',
    name: 'Explainable AI (Grad-CAM)',
    description: 'Visual activation heatmaps highlighting synthetic texture regions',
    status: 'phase_planned',
    phase: 6,
    category: 'visual'
  },
  {
    id: 'temporal',
    name: 'Blink & Temporal Consistency',
    description: 'EAR blink tracking, frame-to-frame sequence consistency via Celery workers',
    status: 'phase_planned',
    phase: 7,
    category: 'temporal'
  },
  {
    id: 'fusion',
    name: 'Multi-Signal Fusion & Calibration',
    description: 'Calibrated confidence fusion (Temperature / Platt scaling), evidence reasoning',
    status: 'phase_planned',
    phase: 8,
    category: 'fusion'
  },
  {
    id: 'provenance',
    name: 'Provenance & C2PA Registry',
    description: 'Content Credentials, invisible watermarks, chain of custody verification',
    status: 'phase_planned',
    phase: 9,
    category: 'provenance'
  },
  {
    id: 'extension',
    name: 'Browser Extension & Reporting',
    description: 'Manifest V3 social media overlay, downloadable forensic PDF/JSON dossiers',
    status: 'phase_planned',
    phase: 10,
    category: 'provenance'
  }
];

export const PipelineOverview: React.FC = () => {
  const getIcon = (category: string) => {
    switch (category) {
      case 'visual': return <Cpu className="w-4 h-4 text-cyan-400" />;
      case 'frequency': return <Activity className="w-4 h-4 text-emerald-400" />;
      case 'facial': return <Eye className="w-4 h-4 text-purple-400" />;
      case 'temporal': return <Video className="w-4 h-4 text-amber-400" />;
      case 'provenance': return <Hash className="w-4 h-4 text-blue-400" />;
      case 'fusion': return <GitMerge className="w-4 h-4 text-pink-400" />;
      default: return <Layers className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center space-x-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            <span>Forensics Pipeline Scaffolding</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Architecture roadmap & modular detector lifecycle</p>
        </div>
        <div className="text-xs text-slate-400">
          <span className="font-semibold text-cyan-400">10 Modules</span> Configured
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {modules.map((mod) => (
          <div
            key={mod.id}
            className={`p-4 rounded-xl border transition-all ${
              mod.status === 'active'
                ? 'bg-gradient-to-b from-cyan-950/40 to-slate-950/80 border-cyan-500/40 shadow-lg shadow-cyan-950/20 ring-1 ring-cyan-500/20'
                : 'bg-slate-950/50 border-slate-800/80 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800">
                  {getIcon(mod.category)}
                </div>
                <span className="text-xs font-semibold text-slate-200">{mod.name}</span>
              </div>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                  mod.status === 'active'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}
              >
                {mod.status === 'active' ? 'Phase 1 Active' : `Phase ${mod.phase}`}
              </span>
            </div>
            <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{mod.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
