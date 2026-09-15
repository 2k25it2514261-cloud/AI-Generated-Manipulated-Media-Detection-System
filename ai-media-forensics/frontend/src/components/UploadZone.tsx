import React, { useState, useCallback, useRef } from 'react';

interface UploadZoneProps {
  onResult: (result: any) => void;
  onLoading: (v: boolean) => void;
  loading: boolean;
}

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const UploadZone: React.FC<UploadZoneProps> = ({ onResult, onLoading, loading }) => {
  const [dragOver, setDragOver] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [includeGradcam, setIncludeGradcam] = useState(false);
  const [urlInput, setUrlInput] = useState('');
  const [mode, setMode] = useState<'file' | 'url'>('file');
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const processFile = useCallback(async (file: File) => {
    setError(null);
    const objectUrl = URL.createObjectURL(file);
    setPreview(objectUrl);
    setFileName(file.name);
    onLoading(true);

    try {
      const form = new FormData();
      form.append('file', file);
      const endpoint = file.type.startsWith('video/')
        ? `${API}/detection/video`
        : `${API}/detection/image?include_gradcam=${includeGradcam}`;

      const resp = await fetch(endpoint, { method: 'POST', body: form });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      onResult(data);
    } catch (e: any) {
      setError(e.message);
      onResult(null);
    } finally {
      onLoading(false);
    }
  }, [includeGradcam, onResult, onLoading]);

  const processUrl = useCallback(async () => {
    if (!urlInput.trim()) return;
    setError(null);
    setPreview(urlInput);
    setFileName(urlInput);
    onLoading(true);
    try {
      const resp = await fetch(
        `${API}/detection/url?url=${encodeURIComponent(urlInput)}&include_gradcam=${includeGradcam}`,
        { method: 'POST' }
      );
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }
      const data = await resp.json();
      onResult(data);
    } catch (e: any) {
      setError(e.message);
      onResult(null);
    } finally {
      onLoading(false);
    }
  }, [urlInput, includeGradcam, onResult, onLoading]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  }, [processFile]);

  return (
    <div className="animate-in" style={{ animationDelay: '0.1s' }}>
      {/* Mode Toggle */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
        {(['file', 'url'] as const).map(m => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={mode === m ? 'btn-primary' : 'btn-ghost'}
            style={{ padding: '8px 20px', fontSize: '13px' }}
          >
            {m === 'file' ? '📁 Upload File' : '🔗 From URL'}
          </button>
        ))}
      </div>

      {mode === 'file' ? (
        <div
          className={`drop-zone${dragOver ? ' drag-over' : ''}`}
          style={{ padding: '60px 40px', textAlign: 'center', position: 'relative' }}
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
        >
          <input
            ref={fileRef}
            type="file"
            accept="image/*,video/mp4,video/webm,video/quicktime"
            style={{ display: 'none' }}
            onChange={e => { if (e.target.files?.[0]) processFile(e.target.files[0]); }}
          />
          {preview && !preview.startsWith('http') ? (
            <img
              src={preview}
              alt="preview"
              style={{ maxHeight: '180px', maxWidth: '100%', borderRadius: '12px', marginBottom: '16px', objectFit: 'contain' }}
            />
          ) : (
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔬</div>
          )}
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '8px' }}>
            {fileName ? (
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{fileName}</span>
            ) : (
              <>Drop image or video here, or <span style={{ color: 'var(--accent-blue)' }}>click to browse</span></>
            )}
          </p>
          <p style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
            JPEG · PNG · WebP · GIF · BMP · MP4 · MOV · WebM — max 50 MB
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', gap: '12px', alignItems: 'stretch' }}>
          <input
            type="url"
            placeholder="https://example.com/image.jpg"
            value={urlInput}
            onChange={e => setUrlInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && processUrl()}
            style={{
              flex: 1,
              background: 'var(--bg-card)',
              border: '1px solid var(--border-bright)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 16px',
              color: 'var(--text-primary)',
              fontSize: '14px',
              outline: 'none',
              fontFamily: 'inherit',
            }}
          />
          <button className="btn-primary" onClick={processUrl} disabled={loading || !urlInput.trim()}>
            Analyze
          </button>
        </div>
      )}

      {/* Options */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '16px' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', userSelect: 'none' }}>
          <input
            type="checkbox"
            checked={includeGradcam}
            onChange={e => setIncludeGradcam(e.target.checked)}
            style={{ accentColor: 'var(--accent-blue)', width: '16px', height: '16px' }}
          />
          <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Include GradCAM saliency map (slower)
          </span>
        </label>
      </div>

      {error && (
        <div style={{
          marginTop: '16px',
          padding: '12px 16px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.25)',
          borderRadius: 'var(--radius-md)',
          color: '#F87171',
          fontSize: '13px',
        }}>
          ⚠️ {error}
        </div>
      )}

      {loading && (
        <div style={{
          marginTop: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '16px',
          background: 'rgba(59, 130, 246, 0.06)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid rgba(59, 130, 246, 0.15)',
        }}>
          <div className="animate-spin" style={{
            width: '20px', height: '20px',
            border: '2px solid rgba(59, 130, 246, 0.3)',
            borderTopColor: 'var(--accent-blue)',
            borderRadius: '50%',
          }} />
          <div>
            <p style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              Running multi-pipeline forensic analysis…
            </p>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              CNN • Frequency Domain • Facial Landmarks • Metadata
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
