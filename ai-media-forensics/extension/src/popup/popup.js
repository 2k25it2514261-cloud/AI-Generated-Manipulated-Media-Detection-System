// Extension Popup Script
const API_BASE = 'http://localhost:8000/api/v1';

const statusDot = document.getElementById('statusDot');
const analyzeBtn = document.getElementById('analyzeBtn');
const urlInput = document.getElementById('urlInput');
const resultDiv = document.getElementById('result');
const autoScanToggle = document.getElementById('autoScanToggle');
const sizeFilterToggle = document.getElementById('sizeFilterToggle');
const scanPageBtn = document.getElementById('scanPageBtn');
const openDashboardBtn = document.getElementById('openDashboardBtn');

// ────────────────────────────────────────────────
// Backend Health Check
// ────────────────────────────────────────────────
async function checkBackend() {
  try {
    const resp = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
    if (resp.ok) {
      statusDot.style.background = '#10B981';
      statusDot.title = 'Backend online';
    } else {
      statusDot.style.background = '#F59E0B';
      statusDot.title = `Backend degraded (${resp.status})`;
    }
  } catch {
    statusDot.style.background = '#EF4444';
    statusDot.title = 'Backend offline — start the FastAPI server';
  }
}

// ────────────────────────────────────────────────
// URL Analysis
// ────────────────────────────────────────────────
analyzeBtn.addEventListener('click', analyzeUrl);
urlInput.addEventListener('keydown', e => { if (e.key === 'Enter') analyzeUrl(); });

async function analyzeUrl() {
  const url = urlInput.value.trim();
  if (!url) return;

  analyzeBtn.disabled = true;
  analyzeBtn.innerHTML = '<span class="spinner"></span>';
  resultDiv.style.display = 'none';

  try {
    const resp = await fetch(
      `${API_BASE}/detection/url?url=${encodeURIComponent(url)}`,
      { method: 'POST', signal: AbortSignal.timeout(30000) }
    );
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`);
    renderResult(data);
  } catch (err) {
    resultDiv.innerHTML = `<div class="error">⚠️ ${err.message}</div>`;
    resultDiv.style.display = 'block';
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = 'Scan';
  }
}

function renderResult(data) {
  const score = data?.fusion?.overall_synthetic_probability ?? 0.5;
  const verdict = data?.fusion?.verdict ?? 'UNKNOWN';
  const pct = Math.round(score * 100);
  const color = score >= 0.65 ? '#EF4444' : score >= 0.45 ? '#F59E0B' : '#10B981';
  const bg = `${color}18`;
  const border = `${color}30`;

  const pipelineRows = Object.entries(data?.pipelines || {}).map(([k, v]) => {
    const p = v?.synthetic_probability;
    const pc = p >= 0.65 ? '#EF4444' : p >= 0.45 ? '#F59E0B' : '#10B981';
    const icons = { cnn: '🧠', frequency: '📊', facial_landmark: '👁️', metadata: '🏷️', video_temporal: '🎬' };
    return `
      <div class="pipe-row">
        <span>${icons[k] || '🔧'} ${k.replace(/_/g, ' ')}</span>
        <span style="color:${pc};font-weight:700">${p != null ? Math.round(p * 100) + '%' : v.status}</span>
      </div>`;
  }).join('');

  resultDiv.innerHTML = `
    <div class="result-card">
      <div style="display:flex;align-items:baseline;gap:6px">
        <span class="score-big" style="color:${color}">${pct}%</span>
        <span style="color:#64748B;font-size:11px">synthetic probability</span>
      </div>
      <span class="verdict-badge" style="background:${bg};border:1px solid ${border};color:${color}">
        ${verdict.replace(/_/g, ' ')}
      </span>
      <div style="margin-top:10px">${pipelineRows}</div>
    </div>
  `;
  resultDiv.style.display = 'block';
}

// ────────────────────────────────────────────────
// Scan page images
// ────────────────────────────────────────────────
scanPageBtn.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    chrome.tabs.sendMessage(tab.id, { type: 'SCAN_ALL_IMAGES' });
    scanPageBtn.textContent = '✅ Scanning…';
    setTimeout(() => { scanPageBtn.textContent = '🔍 Scan all images on this page'; }, 3000);
  }
  window.close();
});

// ────────────────────────────────────────────────
// Open Dashboard
// ────────────────────────────────────────────────
openDashboardBtn.addEventListener('click', () => {
  chrome.tabs.create({ url: 'http://localhost:5173' });
});

// ────────────────────────────────────────────────
// Settings persistence
// ────────────────────────────────────────────────
chrome.storage.sync.get(['autoScan', 'sizeFilter'], (settings) => {
  autoScanToggle.checked = !!settings.autoScan;
  sizeFilterToggle.checked = settings.sizeFilter !== false;
});

autoScanToggle.addEventListener('change', () => {
  chrome.storage.sync.set({ autoScan: autoScanToggle.checked });
});
sizeFilterToggle.addEventListener('change', () => {
  chrome.storage.sync.set({ sizeFilter: sizeFilterToggle.checked });
});

// ────────────────────────────────────────────────
// Init
// ────────────────────────────────────────────────
checkBackend();

// Pre-fill URL from current tab's active image if available
chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
  if (tab?.url && !tab.url.startsWith('chrome')) {
    // Don't pre-fill, let user input
  }
});
