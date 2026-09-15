export interface HealthResponse {
  status: string;
  version: string;
  database: {
    status: string;
    type?: string;
    error?: string;
  };
  timestamp: string;
}

export interface PipelineModule {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'ready' | 'phase_planned';
  phase: number;
  category: 'visual' | 'frequency' | 'facial' | 'temporal' | 'provenance' | 'fusion';
}

export interface MediaUploadResult {
  media_id: string;
  filename: string;
  mime_type: string;
  size: number;
  sha256: string;
  storage_path: string;
  analysis_copy_path?: string;
  preprocess_info: {
    width?: number;
    height?: number;
    format?: string;
    mode?: string;
    analysis_ready?: boolean;
    [key: string]: any;
  };
  metadata: {
    has_exif: boolean;
    camera_make?: string | null;
    camera_model?: string | null;
    software?: string | null;
    datetime_original?: string | null;
    ai_generator_signatures_found: string[];
    editing_software_detected: string[];
    anomaly_indicators: string[];
    embedded_text_chunks?: Record<string, string>;
    raw_exif?: Record<string, any>;
    [key: string]: any;
  };
  created_at: string;
}
