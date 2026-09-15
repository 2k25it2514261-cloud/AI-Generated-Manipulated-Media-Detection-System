import React from 'react';

interface ForensicResult {
  filename?: string;
  source_url?: string;
  media_type?: string;
  fusion?: {
    overall_synthetic_probability: number;
    verdict: string;
    confidence: string;
    active_pipelines: string[];
  };
  pipelines?: Record<string, any>;
  gradcam?: {
    heatmap_b64?: string;
    top_regions?: Array<{ x: number; y: number; w: number; h: number; mean_intensity: number }>;
    explanation_text?: string;
    status: string;
  };
  processing_time_seconds?: number;
}

interface ForensicReportProps {
  result: ForensicResult;
}

const PIPELINE_LABELS: Record<string, { label: string; icon: string }> = {
  cnn: { label: 'CNN Visual Artifacts', icon: '🧠' },
  frequency: { label: 'Frequency Domain', icon: '📊' },
  facial_landmark: { label: 'Facial Landmarks', icon: '👁️' },
  metadata: { label: 'EXIF Metadata', icon: '🏷️' },
  video_temporal: { label: 'Video Temporal', icon: '🎬' },
  provenance: { label: 'Provenance / C2PA', icon: '🔏' },
};

function getVerdictClass(verdict: string) {
  if (verdict?.includes('AI_GENERATED')) return 'verdict-ai';
  if (verdict?.includes('SUSPICIOUS')) return 'verdict-suspicious';
  return 'verdict-authentic';
}

function getVerdictLabel(verdict: string) {
  if (verdict?.includes('AI_GENERATED')) return '⚠️ Likely AI-Generated';
  if (verdict?.includes('SUSPICIOUS')) return '🔍 Suspicious';
  return '✅ Likely Authentic';
}

function getScoreColor(score: number): string {
  if (score >= 0.65) return 'var(--accent-red)';
  if (score >= 0.45) return 'var(--accent-amber)';
  return 'var(--accent-green)';
}

function ScoreGauge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = getScoreColor(score);
  const r = 52;
  const circ = 2 * Math.PI * r;
  const dash = circ * (1 - score);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
      <svg width="128" height="128" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="64" cy="64" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
        <circle
          cx="64" cy="64" r={r}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={circ}
          strokeDashoffset={dash}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s cubic-bezier(.4,0,.2,1)', filter: `drop-shadow(0 0 8px ${color}60)` }}
        />
      </svg>
      <div style={{ marginTop: '-80px', textAlign: 'center', pointerEvents: 'none' }}>
        <div style={{ fontSize: '28px', fontWeight: 800, color }}>{pct}%</div>
        <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>SYNTHETIC</div>
      </div>
      <div style={{ height: '52px' }} />
    </div>
  );
}

function PipelineRow({ pipelineKey, data }: { pipelineKey: string; data: any }) {
  const meta = PIPELINE_LABELS[pipelineKey] || { label: pipelineKey, icon: '🔧' };
  const prob = data?.synthetic_probability ?? null;
  const status = data?.status ?? 'unknown';
  const color = prob != null ? getScoreColor(prob) : 'var(--text-muted)';

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '24px 1fr auto',
      gap: '12px',
      alignItems: 'center',
      padding: '12px 0',
      borderBottom: '1px solid var(--border)',
    }}>
      <span style={{ fontSize: '16px' }}>{meta.icon}</span>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
          <span style={{ fontSize: '13px', fontWeight: 500 }}>{meta.label}</span>
          <span style={{ fontSize: '12px', color, fontWeight: 700 }}>
            {prob != null ? `${Math.round(prob * 100)}%` : status}
          </span>
        </div>
        <div className="pipeline-bar-track">
          <div
            className="pipeline-bar-fill"
            style={{
              width: prob != null ? `${Math.round(prob * 100)}%` : '0%',
              background: color,
              boxShadow: `0 0 6px ${color}60`,
            }}
          />
        </div>
        {/* Flags */}
        {data?.suspicious_flags?.length > 0 && (
          <div style={{ marginTop: '6px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
            {data.suspicious_flags.slice(0, 4).map((f: string) => (
              <span key={f} style={{
                background: 'rgba(245,158,11,0.1)', color: '#FCD34D',
                border: '1px solid rgba(245,158,11,0.2)',
                borderRadius: '4px', fontSize: '10px', padding: '1px 6px',
              }}>{f}</span>
            ))}
          </div>
        )}
        {data?.note && (
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>{data.note}</p>
        )}
      </div>
    </div>
  );
}

function MetadataRow({ label, value }: { label: string; value: any }) {
  if (value == null || value === '') return null;
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '8px 0', borderBottom: '1px solid var(--border)', gap: '12px' }}>
      <span style={{ fontSize: '12px', color: 'var(--text-muted)', flexShrink: 0 }}>{label}</span>
      <span className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)', textAlign: 'right', wordBreak: 'break-all' }}>
        {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
      </span>
    </div>
  );
}

export const ForensicReport: React.FC<ForensicReportProps> = ({ result }) => {
  const fusion = result.fusion;
  const score = fusion?.overall_synthetic_probability ?? 0.5;
  const verdict = fusion?.verdict ?? 'UNKNOWN';
  const pipelines = result.pipelines ?? {};
  const gradcam = result.gradcam;
  const metaPipeline = pipelines.metadata;

  return (
    <div className="animate-in" style={{ display: 'grid', gap: '20px' }}>

      {/* Header Score Card */}
      <div className="card" style={{
        padding: '28px',
        background: `linear-gradient(135deg, var(--bg-card) 0%, rgba(${score >= 0.65 ? '239,68,68' : score >= 0.45 ? '245,158,11' : '16,185,129'},0.08) 100%)`,
        display: 'grid',
        gridTemplateColumns: '1fr auto',
        gap: '24px',
        alignItems: 'center',
      }}>
        <div>
          <div style={{ marginBottom: '12px' }}>
            <span className={`verdict-badge ${getVerdictClass(verdict)}`} style={{ fontSize: '13px' }}>
              {getVerdictLabel(verdict)}
            </span>
            <span style={{ marginLeft: '10px', fontSize: '12px', color: 'var(--text-muted)' }}>
              Confidence: <strong style={{ color: 'var(--text-secondary)' }}>{fusion?.confidence}</strong>
            </span>
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '4px', lineHeight: 1.3 }}>
            {result.filename || result.source_url || 'Media Analysis'}
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            {result.media_type?.toUpperCase()} · {fusion?.active_pipelines?.length} pipeline(s) active
            {result.processing_time_seconds != null && ` · ${result.processing_time_seconds}s`}
          </p>
        </div>
        <ScoreGauge score={score} />
      </div>

      {/* Pipeline Results */}
      <div className="card" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>
          Detection Pipelines
        </h3>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Each pipeline runs independently — results are weighted and fused.
        </p>
        {Object.entries(pipelines).map(([key, data]) => (
          <PipelineRow key={key} pipelineKey={key} data={data} />
        ))}
      </div>

      {/* Metadata Details */}
      {metaPipeline && (
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '16px' }}>
            🏷️ EXIF / Metadata Details
          </h3>
          <MetadataRow label="Has EXIF" value={metaPipeline.has_exif} />
          <MetadataRow label="Software" value={metaPipeline.software_tag} />
          <MetadataRow label="AI Software Detected" value={metaPipeline.ai_software_detected} />
          <MetadataRow label="Camera Make/Model" value={metaPipeline.make_model} />
          <MetadataRow label="Original DateTime" value={metaPipeline.original_datetime} />
          <MetadataRow label="GPS Present" value={metaPipeline.gps_present} />
        </div>
      )}

      {/* Facial Landmark Details */}
      {pipelines.facial_landmark?.faces_detected > 0 && (
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '16px' }}>
            👁️ Facial Landmark Analysis
          </h3>
          <MetadataRow label="Faces Detected" value={pipelines.facial_landmark.faces_detected} />
          <MetadataRow label="Symmetry Score" value={pipelines.facial_landmark.symmetry_score != null ? `${(pipelines.facial_landmark.symmetry_score * 100).toFixed(1)}%` : null} />
          <MetadataRow label="Left Eye EAR" value={pipelines.facial_landmark.left_ear} />
          <MetadataRow label="Right Eye EAR" value={pipelines.facial_landmark.right_ear} />
          <MetadataRow label="EAR Asymmetry" value={pipelines.facial_landmark.ear_asymmetry} />
        </div>
      )}

      {/* Frequency Details */}
      {pipelines.frequency && (
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '16px' }}>
            📊 Frequency Domain Analysis
          </h3>
          <MetadataRow label="FFT High-Freq Ratio" value={pipelines.frequency.fft_mean_high_freq_ratio} />
          <MetadataRow label="Checkerboard Score" value={pipelines.frequency.checkerboard_score} />
          <MetadataRow label="DCT Uniformity" value={pipelines.frequency.dct_uniformity} />
        </div>
      )}

      {/* GradCAM */}
      {gradcam?.status === 'success' && gradcam.heatmap_b64 && (
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>
            🔥 GradCAM Saliency Map
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
            {gradcam.explanation_text}
          </p>
          <img
            src={`data:image/png;base64,${gradcam.heatmap_b64}`}
            alt="GradCAM heatmap"
            style={{ width: '100%', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}
          />
        </div>
      )}

      {/* Video Temporal */}
      {pipelines.video_temporal && (
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '16px' }}>
            🎬 Video Temporal Analysis
          </h3>
          <MetadataRow label="Frames Analyzed" value={pipelines.video_temporal.frames_analyzed} />
          <MetadataRow label="FPS" value={pipelines.video_temporal.fps} />
          <MetadataRow label="Mean Optical Flow" value={pipelines.video_temporal.mean_flow} />
          <MetadataRow label="Flow Variance" value={pipelines.video_temporal.flow_variance} />
          <MetadataRow label="Blink Count" value={pipelines.video_temporal.blink_count} />
          <MetadataRow label="Blink Rate (per min)" value={pipelines.video_temporal.blink_rate_per_min} />
          <MetadataRow label="Temporal Consistency Score" value={pipelines.video_temporal.temporal_consistency_score} />
        </div>
      )}

    </div>
  );
};
