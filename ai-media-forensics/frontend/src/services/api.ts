import { HealthResponse, MediaUploadResult } from '../types';
import { DetectionResultData } from '../components/DetectionResults';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
    headers: {
      'Accept': 'application/json',
    },
  });
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }
  return response.json();
}

export async function uploadMedia(file: File): Promise<MediaUploadResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/v1/media/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(errorData.detail || `Upload failed with status: ${response.status}`);
  }

  return response.json();
}

export async function runDetection(mediaId: string): Promise<DetectionResultData> {
  const formData = new FormData();
  formData.append('media_id', mediaId);

  const response = await fetch(`${API_BASE_URL}/api/v1/detect/image`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Detection failed' }));
    throw new Error(errorData.detail || `Detection failed with status: ${response.status}`);
  }

  return response.json();
}

export function getMediaFileUrl(mediaId: string, target: 'original' | 'analysis' = 'original'): string {
  return `${API_BASE_URL}/api/v1/media/${mediaId}/file?target=${target}`;
}
