import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { 
  UploadCloud, FileImage, CheckCircle, AlertTriangle, 
  Copy, Check, ShieldAlert, Cpu, FileText, RefreshCw
} from 'lucide-react';
import { uploadMedia, getMediaFileUrl } from '../services/api';
import { MediaUploadResult } from '../types';

interface MediaUploadProps {
  onMediaUploaded?: (media: MediaUploadResult) => void;
}

export const MediaUpload: React.FC<MediaUploadProps> = ({ onMediaUploaded }) => {
  const [dragOver, setDragOver] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedMedia, setUploadedMedia] = useState<MediaUploadResult | null>(null);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);
  const [previewMode, setPreviewMode] = useState<'original' | 'analysis'>('original');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = async (file: File) => {
    setError(null);
    setUploading(true);

    try {
      const result = await uploadMedia(file);
      setUploadedMedia(result);
      if (onMediaUploaded) {
        onMediaUploaded(result);
      }
    } catch (err: any) {
      setError(err.message || 'Media ingestion failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const copyHashToClipboard = () => {
    if (uploadedMedia) {
      navigator.clipboard.writeText(uploadedMedia.sha256);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  const resetUpload = () => {
    setUploadedMedia(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center space-x-2">
            <UploadCloud className="w-5 h-5 text-cyan-400" />
            <span>Forensic Media Ingestion (Phase 2)</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Cryptographic SHA-256 pre-hashing, MIME verification, and non-destructive evidence preservation.
          </p>
        </div>

        {uploadedMedia && (
          <button
            onClick={resetUpload}
            className="flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Ingest Another File</span>
          </button>
        )}
      </div>

      {!uploadedMedia ? (
        <div>
          {/* Drag and Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
              dragOver
                ? 'border-cyan-400 bg-cyan-500/10'
                : 'border-slate-700 hover:border-slate-500 bg-slate-950/40'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/tiff,video/mp4,video/quicktime,video/x-msvideo,video/webm"
              onChange={handleFileSelect}
              className="hidden"
            />

            <div className="flex flex-col items-center justify-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                <FileImage className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-200">
                  {uploading ? 'Ingesting and hashing media...' : 'Drag & drop media here, or browse file'}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Supports JPG, JPEG, PNG, WEBP, TIFF, MP4, MOV, AVI, WEBM (Max 100MB)
                </p>
              </div>

              {uploading && (
                <div className="flex items-center space-x-2 text-xs text-cyan-400">
                  <div className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
                  <span>Calculating SHA-256 & preserving original evidence...</span>
                </div>
              )}
            </div>
          </div>

          {error && (
            <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>
      ) : (
        /* Uploaded Media Forensic Dossier */
        <div className="space-y-6">
          {/* Top Bar: Media ID & Chain of Custody */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <span className="px-3 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-mono font-bold text-sm">
                {uploadedMedia.media_id}
              </span>
              <div>
                <h3 className="text-sm font-semibold text-white">{uploadedMedia.filename}</h3>
                <p className="text-xs text-slate-400">
                  {uploadedMedia.mime_type} &bull; {(uploadedMedia.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle className="w-3.5 h-3.5 mr-1" />
                Evidence Vault Preserved
              </span>
            </div>
          </div>

          {/* Cryptographic SHA-256 Hash Box */}
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
            <div className="flex-1 min-w-0 pr-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Cryptographic SHA-256 Signature (Immutable Proof of Custody)
              </span>
              <p className="mono-font text-xs text-cyan-300 truncate">
                {uploadedMedia.sha256}
              </p>
            </div>
            <button
              onClick={copyHashToClipboard}
              className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition border border-slate-700"
              title="Copy SHA-256 hash"
            >
              {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedHash ? 'Copied' : 'Copy'}</span>
            </button>
          </div>

          {/* Side by Side Preview & Technical Inspection */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Visual Preview */}
            <div className="lg:col-span-5 bg-slate-950/60 rounded-xl border border-slate-800 p-4 flex flex-col items-center">
              <div className="w-full flex items-center justify-between mb-3 text-xs text-slate-400">
                <span>Media Preview</span>
                <div className="flex bg-slate-900 rounded-lg p-0.5 border border-slate-800">
                  <button
                    onClick={() => setPreviewMode('original')}
                    className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
                      previewMode === 'original' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Original
                  </button>
                  <button
                    onClick={() => setPreviewMode('analysis')}
                    className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
                      previewMode === 'analysis' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Analysis Copy
                  </button>
                </div>
              </div>

              <div className="w-full h-56 rounded-lg bg-slate-900/50 border border-slate-800/80 flex items-center justify-center overflow-hidden">
                {uploadedMedia.mime_type.startsWith('image/') ? (
                  <img
                    src={getMediaFileUrl(uploadedMedia.media_id, previewMode)}
                    alt="Media preview"
                    className="max-h-full max-w-full object-contain"
                  />
                ) : (
                  <div className="text-center p-4">
                    <FileText className="w-8 h-8 text-cyan-400 mx-auto mb-2" />
                    <p className="text-xs text-slate-400">Video Evidence Ingested</p>
                  </div>
                )}
              </div>

              <p className="text-[11px] text-slate-500 mt-2 text-center">
                {previewMode === 'original'
                  ? 'Original evidentiary file stored in immutable vault.'
                  : 'Normalized 3-channel RGB analysis copy for downstream models.'}
              </p>
            </div>

            {/* Technical Specifications & Metadata Findings */}
            <div className="lg:col-span-7 space-y-4">
              {/* Image Geometry */}
              <div className="grid grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-slate-500 block">Resolution</span>
                  <span className="font-semibold text-slate-200">
                    {uploadedMedia.preprocess_info.width && uploadedMedia.preprocess_info.height
                      ? `${uploadedMedia.preprocess_info.width} × ${uploadedMedia.preprocess_info.height}`
                      : 'N/A'}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-slate-500 block">Color Mode</span>
                  <span className="font-semibold text-slate-200 uppercase">
                    {uploadedMedia.preprocess_info.mode || 'RGB'}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-slate-500 block">Format</span>
                  <span className="font-semibold text-slate-200 uppercase">
                    {uploadedMedia.preprocess_info.format || 'PNG'}
                  </span>
                </div>
              </div>

              {/* Metadata & EXIF Analysis */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-2.5">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className="font-semibold text-slate-200">EXIF & Technical Metadata</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    uploadedMedia.metadata.has_exif 
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                      : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  }`}>
                    {uploadedMedia.metadata.has_exif ? 'EXIF Found' : 'No Camera EXIF'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-slate-400 text-[11px]">
                  <div>Camera Make: <span className="text-slate-200">{uploadedMedia.metadata.camera_make || 'None'}</span></div>
                  <div>Camera Model: <span className="text-slate-200">{uploadedMedia.metadata.camera_model || 'None'}</span></div>
                  <div>Software: <span className="text-slate-200">{uploadedMedia.metadata.software || 'None'}</span></div>
                  <div>Date Captured: <span className="text-slate-200">{uploadedMedia.metadata.datetime_original || 'Unknown'}</span></div>
                </div>

                {/* Anomalies / Synthetic flags */}
                {uploadedMedia.metadata.anomaly_indicators.length > 0 && (
                  <div className="pt-2 border-t border-slate-800/80 space-y-1.5">
                    <span className="text-[11px] font-semibold text-amber-400 flex items-center space-x-1">
                      <ShieldAlert className="w-3.5 h-3.5" />
                      <span>Metadata Observations:</span>
                    </span>
                    <ul className="list-disc list-inside text-[11px] text-slate-300 space-y-0.5">
                      {uploadedMedia.metadata.anomaly_indicators.map((ind, idx) => (
                        <li key={idx}>{ind}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Action Banner for Subsequent Phases */}
              <div className="p-3.5 rounded-xl bg-cyan-950/30 border border-cyan-500/30 flex items-center justify-between">
                <div className="flex items-center space-x-2 text-xs text-cyan-300">
                  <Cpu className="w-4 h-4 text-cyan-400" />
                  <span>Media ingested & ready for Phase 3 CNN & Phase 4 Frequency Analysis.</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
