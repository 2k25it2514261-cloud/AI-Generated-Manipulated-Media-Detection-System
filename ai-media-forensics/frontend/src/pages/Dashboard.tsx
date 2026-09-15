import React, { useState } from 'react';
import { UploadZone } from '../components/UploadZone';
import { ForensicReport } from '../components/ForensicReport';
import { PipelineOverview } from '../components/PipelineOverview';
import { HealthStatus } from '../components/HealthStatus';

interface DashboardProps {
  health: any;
  error: string | null;
  loading: boolean;
}

export const Dashboard: React.FC<DashboardProps> = ({ health, error, loading }) => {
  const [result, setResult] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px 24px' }}>

      {/* Hero Header */}
      <div className="animate-in" style={{ textAlign: 'center', marginBottom: '48px' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '8px',
          background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)',
          borderRadius: '100px', padding: '6px 16px', marginBottom: '20px',
          fontSize: '12px', color: 'var(--accent-blue)', fontWeight: 600,
        }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-green)', display: 'inline-block', animation: 'pulse-glow 2s ease infinite' }} />
          AI Forensics Engine · Multi-Pipeline Detection
        </div>
        <h1 style={{
          fontSize: 'clamp(28px, 5vw, 48px)',
          fontWeight: 800,
          lineHeight: 1.1,
          background: 'linear-gradient(135deg, #F1F5F9 0%, #94A3B8 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          marginBottom: '16px',
        }}>
          AI-Generated & Manipulated<br />Media Detection System
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '16px', maxWidth: '580px', margin: '0 auto' }}>
          Upload any image or video to run a comprehensive forensic analysis across 5 independent AI detection pipelines.
        </p>
      </div>

      {/* Status bar */}
      {(health || error) && (
        <div style={{ marginBottom: '32px' }}>
          <HealthStatus health={health} loading={loading} />
        </div>
      )}

      {/* Main Layout */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: result ? '1fr 1fr' : '1fr',
        gap: '28px',
        alignItems: 'start',
      }}>

        {/* Left: Upload + Pipeline Overview */}
        <div style={{ display: 'grid', gap: '24px' }}>
          {/* Upload Card */}
          <div className="card" style={{ padding: '28px' }}>
            <div style={{ marginBottom: '20px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '4px' }}>Analyze Media</h2>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                Submit image or video for forensic inspection
              </p>
            </div>
            <UploadZone
              onResult={setResult}
              onLoading={setAnalyzing}
              loading={analyzing}
            />
          </div>

          {/* Pipeline overview (always visible) */}
          <PipelineOverview />
        </div>

        {/* Right: Results (only after analysis) */}
        {result && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: 700 }}>Forensic Report</h2>
              <button
                className="btn-ghost"
                onClick={() => setResult(null)}
                style={{ fontSize: '12px', padding: '6px 14px' }}
              >
                Clear ✕
              </button>
            </div>
            <ForensicReport result={result} />
          </div>
        )}
      </div>
    </div>
  );
};
