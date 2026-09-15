import React from 'react';
import { 
  ShieldAlert, ShieldCheck, HelpCircle, AlertTriangle, 
  Cpu, FileSearch, Hash, Layers, CheckCircle2, Info
} from 'lucide-react';

export interface DetectionResultData {
  detection_id: string;
  media_type: string;
  classification: string;
  confidence: number;
  scores: {
    cnn?: number | null;
    frequency?: number | null;
    facial?: number | null;
    temporal?: number | null;
    blink?: number | null;
    metadata?: number | null;
    provenance?: number | null;
  };
  evidence: string[];
  provenance: {
    hash: string;
    watermark_detected: boolean;
    content_credentials: boolean;
    c2pa_status: string;
  };
  timestamp?: string;
}

interface DetectionResultsProps {
  result: DetectionResultData;
  onReset?: () => void;
}

export const DetectionResults: React.FC<DetectionResultsProps> = ({ result }) => {
  const getClassificationBadge = (classification: string) => {
    switch (classification.toLowerCase()) {
      case 'strong_evidence':
        return {
          label: 'Strong Evidence of Synthetic Media',
          color: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          icon: <ShieldAlert className="w-5 h-5 text-rose-400" />
        };
      case 'suspicious':
        return {
          label: 'Suspicious Artifacts Detected',
          color: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          icon: <AlertTriangle className="w-5 h-5 text-amber-400" />
        };
      case 'inconclusive':
        return {
          label: 'Inconclusive Evidence',
          color: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
          icon: <HelpCircle className="w-5 h-5 text-blue-400" />
        };
      case 'low_evidence':
      default:
        return {
          label: 'Low Evidence of Manipulation',
          color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          icon: <ShieldCheck className="w-5 h-5 text-emerald-400" />
        };
    }
  };

  const badge = getClassificationBadge(result.classification);
  const confidencePercent = Math.round(result.confidence * 100);
  const cnnScorePercent = result.scores.cnn !== null && result.scores.cnn !== undefined 
    ? Math.round(result.scores.cnn * 100) 
    : null;
  const metadataScore = typeof result.scores.metadata === 'number' ? result.scores.metadata : 0;
  const metadataScorePercent = Math.round(metadataScore * 100);

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-md space-y-6">
      {/* Classification Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <span className="mono-font text-xs font-semibold px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              {result.detection_id}
            </span>
            <span className="text-xs text-slate-500">Forensics Report</span>
          </div>
          <div className="mt-2 flex items-center space-x-2.5">
            {badge.icon}
            <h3 className="text-lg font-bold text-white tracking-tight">{badge.label}</h3>
          </div>
        </div>

        <div className={`px-4 py-2 rounded-xl border flex items-center space-x-3 ${badge.color}`}>
          <div className="text-right">
            <span className="text-[10px] uppercase font-bold tracking-wider block opacity-80">Calibrated Confidence</span>
            <span className="text-2xl font-black">{confidencePercent}%</span>
          </div>
        </div>
      </div>

      {/* Signal Scores Breakdown */}
      <div>
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center space-x-1.5">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span>Multi-Pipeline Signal Breakdown</span>
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
          {/* CNN Artifact Detector */}
          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400 flex items-center space-x-1.5">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                <span>CNN Detector</span>
              </span>
              <span className="mono-font font-bold text-slate-200">
                {cnnScorePercent !== null ? `${cnnScorePercent}%` : 'N/A'}
              </span>
            </div>
            {/* Progress bar */}
            <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
              <div 
                className={`h-full rounded-full transition-all duration-500 ${
                  (cnnScorePercent || 0) > 70 ? 'bg-rose-500' : (cnnScorePercent || 0) > 40 ? 'bg-amber-400' : 'bg-emerald-400'
                }`}
                style={{ width: `${cnnScorePercent || 0}%` }}
              />
            </div>
            <p className="text-[10px] text-slate-500">EfficientNet-B0 Micro-Artifact Classifier</p>
          </div>

          {/* Metadata Signal */}
          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400 flex items-center space-x-1.5">
                <FileSearch className="w-3.5 h-3.5 text-emerald-400" />
                <span>Metadata Inconsistency</span>
              </span>
              <span className="mono-font font-bold text-slate-200">
                {metadataScorePercent}%
              </span>
            </div>
            <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
              <div 
                className="h-full bg-emerald-500 rounded-full"
                style={{ width: `${metadataScorePercent}%` }}
              />
            </div>
            <p className="text-[10px] text-slate-500">EXIF & Synthetic Generator Signature Inspection</p>
          </div>

          {/* SHA-256 Provenance Proof */}
          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400 flex items-center space-x-1.5">
                <Hash className="w-3.5 h-3.5 text-purple-400" />
                <span>Provenance Record</span>
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                Vault Verified
              </span>
            </div>
            <p className="mono-font text-[11px] text-cyan-300 truncate">
              {result.provenance.hash}
            </p>
            <p className="text-[10px] text-slate-500">Immutable Evidence Hash Recorded</p>
          </div>
        </div>
      </div>

      {/* Forensic Evidence Items */}
      <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2.5">
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
          <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
          <span>Observed Forensic Evidence</span>
        </h4>
        <ul className="space-y-1.5">
          {result.evidence.map((item, idx) => (
            <li key={idx} className="text-xs text-slate-300 flex items-start space-x-2">
              <span className="text-cyan-400 mt-0.5">&bull;</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Legal & Forensic Disclaimer */}
      <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800/80 flex items-start space-x-2.5 text-xs text-slate-400">
        <Info className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-slate-300 font-medium">Evidence-Based Assessment:</strong> This system combines multiple independent probabilistic forensic models. No automated detection model should be treated as absolute proof of falsification. Results must be interpreted alongside chain-of-custody documentation and investigative context.
        </p>
      </div>
    </div>
  );
};
