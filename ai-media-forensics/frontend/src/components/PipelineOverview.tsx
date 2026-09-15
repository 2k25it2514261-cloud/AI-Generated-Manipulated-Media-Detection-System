import React from 'react';

const PIPELINES = [
  {
    icon: '🧠',
    name: 'CNN Visual Artifacts',
    desc: 'EfficientNet-B0 binary classifier detects GAN/diffusion synthetic patterns.',
    weight: '40%',
    color: 'var(--accent-blue)',
  },
  {
    icon: '📊',
    name: 'Frequency Domain',
    desc: 'FFT/DCT analysis exposes checkerboard artifacts and GAN spectral signatures.',
    weight: '20%',
    color: 'var(--accent-violet)',
  },
  {
    icon: '👁️',
    name: 'Facial Landmarks',
    desc: 'MediaPipe Face Mesh bilateral symmetry and eye blink pattern analysis.',
    weight: '20%',
    color: 'var(--accent-cyan)',
  },
  {
    icon: '🏷️',
    name: 'EXIF Metadata',
    desc: 'Flags absent camera data, AI tool software tags, and malformed date fields.',
    weight: '20%',
    color: 'var(--accent-amber)',
  },
  {
    icon: '🎬',
    name: 'Video Temporal',
    desc: 'Optical flow variance, frame-diff inconsistency, and blink frequency analysis.',
    weight: 'Video',
    color: 'var(--accent-green)',
  },
  {
    icon: '🔏',
    name: 'Provenance / C2PA',
    desc: 'C2PA Content Credentials detection, perceptual hash, and PNG metadata scan.',
    weight: 'Via API',
    color: '#A78BFA',
  },
];

export const PipelineOverview: React.FC = () => (
  <div className="card" style={{ padding: '24px' }}>
    <div style={{ marginBottom: '16px' }}>
      <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Detection Pipelines
      </h3>
      <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
        Six independent forensic approaches fused into a single confidence score.
      </p>
    </div>
    <div style={{ display: 'grid', gap: '12px' }}>
      {PIPELINES.map((p) => (
        <div
          key={p.name}
          style={{
            display: 'grid',
            gridTemplateColumns: '32px 1fr auto',
            gap: '12px',
            alignItems: 'center',
            padding: '10px 12px',
            background: 'rgba(255,255,255,0.02)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-md)',
            transition: 'background 0.2s, border-color 0.2s',
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLDivElement).style.background = 'rgba(255,255,255,0.04)';
            (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border-bright)';
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLDivElement).style.background = 'rgba(255,255,255,0.02)';
            (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border)';
          }}
        >
          <span style={{ fontSize: '18px', textAlign: 'center' }}>{p.icon}</span>
          <div>
            <p style={{ fontSize: '13px', fontWeight: 600, marginBottom: '2px' }}>{p.name}</p>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.4 }}>{p.desc}</p>
          </div>
          <span style={{
            fontSize: '10px', fontWeight: 700,
            color: p.color,
            background: `${p.color}18`,
            border: `1px solid ${p.color}30`,
            borderRadius: '6px',
            padding: '3px 8px',
            whiteSpace: 'nowrap',
          }}>
            {p.weight}
          </span>
        </div>
      ))}
    </div>
  </div>
);
