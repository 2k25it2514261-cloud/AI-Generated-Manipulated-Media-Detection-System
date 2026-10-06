# AI-Generated and Manipulated Media Detection System

A production-grade, multi-pipeline digital media forensics platform capable of identifying potentially AI-generated or manipulated images and videos.

Rather than relying on a single AI model, this system combines independent detection pipelines:
1. **CNN-Based Visual Artifact Detection** (EfficientNet-B0 / ConvNeXt)
2. **Frequency-Domain Analysis** (2D FFT, spectral peaks, high-frequency anomalies)
3. **Facial Landmark Inconsistency** (Geometric proportions, eye/mouth symmetry, natural variance calibration)
4. **Video Temporal Consistency** (Frame-to-frame sequence analysis, LSTM / Temporal models)
5. **Blinking-Pattern Analysis** (Eye Aspect Ratio (EAR) tracking, left/right synchronization)
6. **Metadata Analysis** (EXIF, encoder, container, software manipulation flags)
7. **Digital Watermarking & Provenance** (C2PA Content Credentials, invisible watermarks, SHA-256 chain of custody)
8. **Explainable AI** (Grad-CAM heatmaps showing influential synthetic regions)
9. **Confidence Calibration & Fusion** (Temperature/Platt scaling across independent signals)
10. **Browser Extension Sentinel** (Manifest V3 overlay for social media platforms)

---

## Directory Structure

```
ai-media-forensics/
├── backend/          # FastAPI REST API & Forensic Engine
├── frontend/         # React + TypeScript + Vite + Tailwind CSS Dashboard
├── ml/               # Training pipelines, checkpoints, and datasets
├── extension/        # Manifest V3 browser extension
├── storage/          # Non-destructive evidence storage (uploads, frames, heatmaps, reports)
├── docker-compose.yml
├── README.md
└── .env.example
```

---

## Getting Started (Phase 1 Foundation)

### Prerequisites
- Python 3.11+
- Node.js 18+ / npm
- (Optional) Docker & Docker Compose

### 1. Backend Setup

```bash
cd backend
python -m venv .venv

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify backend health:
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": {
    "status": "connected",
    "type": "sqlite"
  },
  "timestamp": "2026-09-15T16:40:00Z"
}
```

Run automated backend tests:
```bash
pytest tests/test_health.py -v
```

### 2. Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser to inspect the forensic dashboard and real-time backend telemetry.

### 3. Docker Compose (Production Deployment)

```bash
docker-compose up --build -d
```
- Frontend Dashboard: `http://localhost:3000`
- FastAPI Backend: `http://localhost:8000`
- Interactive API Docs: `http://localhost:8000/docs`

---

## Development Phases

- [x] **Phase 1 — Project Foundation** (FastAPI, SQLite/PostgreSQL ORM, React UI, Health API, Docker configs)
- [ ] **Phase 2 — Image Upload & Evidence Ingestion** (SHA-256 pre-calculation, MIME validation, non-destructive storage)
- [ ] **Phase 3 — CNN Baseline** (EfficientNet-B0 artifact classifier)
- [ ] **Phase 4 — Frequency-Domain Analysis** (2D FFT magnitude spectrum)
- [ ] **Phase 5 — Facial Landmark Analysis** (Face mesh, geometric consistency)
- [ ] **Phase 6 — Explainability** (Grad-CAM heatmaps & textual evidence)
- [ ] **Phase 7 — Video & Temporal Analysis** (Frame sampling, EAR blinking, Celery workers)
- [ ] **Phase 8 — Score Fusion & Confidence Calibration**
- [ ] **Phase 9 — Provenance & C2PA Registry**
- [ ] **Phase 10 — Downloadable Forensic Reports**
- [ ] **Phase 11 — Manifest V3 Browser Extension**
- [ ] **Phase 12 — Security & Audit Logging**
- [ ] **Phase 13 — Testing & ML Evaluation**
- [ ] **Phase 14 — Production Deployment**
