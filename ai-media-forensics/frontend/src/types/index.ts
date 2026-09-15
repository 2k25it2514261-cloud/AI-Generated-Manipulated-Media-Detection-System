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
