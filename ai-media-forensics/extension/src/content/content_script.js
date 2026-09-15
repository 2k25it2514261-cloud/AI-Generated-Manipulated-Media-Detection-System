// Content Script — injects forensic overlays onto social media images
const API_BASE = 'http://localhost:8000/api/v1';

// Configuration: auto-scan images above this dimension threshold
const MIN_IMAGE_SIZE = 150; // px
const SCAN_DELAY_MS = 2000; // wait after page load

// Track scanned images to avoid duplicates
const scannedUrls = new Set();
const overlayMap = new WeakMap();

// ────────────────────────────────────────────────
// Overlay Injection
// ────────────────────────────────────────────────
function injectOverlay(imgEl, state, data) {
  // Remove existing overlay
  const existing = overlayMap.get(imgEl);
  if (existing) existing.remove();

  const wrapper = getOrCreateWrapper(imgEl);

  const overlay = document.createElement('div');
  overlay.className = 'amf-overlay';
  overlay.setAttribute('data-amf', 'true');

  const colors = {
    scanning: '#3B82F6',
    ai: '#EF4444',
    suspicious: '#F59E0B',
    authentic: '#10B981',
    error: '#6B7280',
  };
  const color = colors[state] || colors.error;

  const icons = { scanning: '🔬', ai: '⚠️', suspicious: '🔍', authentic: '✅', error: '❌' };
  const labels = {
    scanning: 'Scanning…',
    ai: 'AI-Generated',
    suspicious: 'Suspicious',
    authentic: 'Authentic',
    error: 'Analysis Failed',
  };

  const score = data?.fusion?.overall_synthetic_probability;
  const scoreText = score != null ? ` (${Math.round(score * 100)}%)` : '';

  overlay.innerHTML = `
    <style>
      .amf-overlay {
        position: absolute;
        top: 6px;
        left: 6px;
        z-index: 99999;
        display: flex;
        align-items: center;
        gap: 5px;
        background: rgba(7,11,20,0.88);
        border: 1px solid ${color}60;
        border-radius: 6px;
        padding: 4px 9px;
        font-family: -apple-system, Inter, sans-serif;
        font-size: 11px;
        font-weight: 600;
        color: ${color};
        cursor: pointer;
        backdrop-filter: blur(6px);
        box-shadow: 0 2px 12px rgba(0,0,0,0.4);
        transition: transform 0.15s, box-shadow 0.15s;
        pointer-events: all;
      }
      .amf-overlay:hover {
        transform: scale(1.04);
        box-shadow: 0 4px 16px rgba(0,0,0,0.5);
      }
      .amf-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: ${color};
        flex-shrink: 0;
        ${state === 'scanning' ? 'animation: amf-pulse 1s ease infinite;' : ''}
      }
      @keyframes amf-pulse {
        0%,100%{opacity:1} 50%{opacity:0.3}
      }
    </style>
    <span class="amf-dot"></span>
    <span>${icons[state]} ${labels[state]}${scoreText}</span>
  `;

  overlay.addEventListener('click', (e) => {
    e.stopPropagation();
    e.preventDefault();
    showDetailPanel(data, imgEl.src || imgEl.currentSrc);
  });

  wrapper.appendChild(overlay);
  overlayMap.set(imgEl, overlay);
}

function getOrCreateWrapper(imgEl) {
  let parent = imgEl.parentElement;
  if (parent && parent.getAttribute('data-amf-wrapper')) return parent;

  const wrapper = document.createElement('div');
  wrapper.setAttribute('data-amf-wrapper', 'true');
  wrapper.style.cssText = 'position:relative;display:inline-block;';
  imgEl.parentNode.insertBefore(wrapper, imgEl);
  wrapper.appendChild(imgEl);
  return wrapper;
}

// ────────────────────────────────────────────────
// Detail Panel
// ────────────────────────────────────────────────
function showDetailPanel(data, imageUrl) {
  const existing = document.getElementById('amf-detail-panel');
  if (existing) existing.remove();

  const panel = document.createElement('div');
  panel.id = 'amf-detail-panel';

  const score = data?.fusion?.overall_synthetic_probability ?? 0.5;
  const verdict = data?.fusion?.verdict ?? 'UNKNOWN';
  const pct = Math.round(score * 100);

  const verdictColor = score >= 0.65 ? '#EF4444' : score >= 0.45 ? '#F59E0B' : '#10B981';

  panel.innerHTML = `
    <style>
      #amf-detail-panel {
        position: fixed;
        top: 20px;
        right: 20px;
        width: 320px;
        max-height: 80vh;
        overflow-y: auto;
        z-index: 2147483647;
        background: #0D1424;
        border: 1px solid rgba(99,120,180,0.2);
        border-radius: 14px;
        padding: 20px;
        font-family: -apple-system, Inter, sans-serif;
        color: #F1F5F9;
        box-shadow: 0 20px 60px rgba(0,0,0,0.6), 0 0 0 1px rgba(59,130,246,0.1);
        animation: amf-slide-in 0.2s ease;
      }
      @keyframes amf-slide-in {
        from{opacity:0;transform:translateX(20px)}
        to{opacity:1;transform:translateX(0)}
      }
      #amf-close-btn {
        position: absolute; top: 12px; right: 14px;
        background: none; border: none; color: #64748B;
        font-size: 18px; cursor: pointer; padding: 0;
        line-height: 1;
      }
      #amf-close-btn:hover { color: #F1F5F9; }
      .amf-score-big {
        font-size: 36px; font-weight: 800;
        color: ${verdictColor};
        font-variant-numeric: tabular-nums;
      }
      .amf-pipe-row { padding: 8px 0; border-bottom: 1px solid rgba(99,120,180,0.1); }
      .amf-pipe-bar-track { width: 100%; height: 4px; background: rgba(255,255,255,0.06); border-radius: 2px; margin-top: 4px; }
      .amf-pipe-bar { height: 4px; border-radius: 2px; }
      .amf-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: #475569; }
    </style>
    <button id="amf-close-btn" onclick="this.parentElement.remove()">✕</button>
    <div style="margin-bottom:12px">
      <div class="amf-label" style="margin-bottom:4px">🔬 AI Forensics Analysis</div>
      <div style="display:flex;align-items:baseline;gap:8px">
        <span class="amf-score-big">${pct}%</span>
        <span style="font-size:12px;color:#94A3B8">synthetic probability</span>
      </div>
      <div style="margin-top:8px;font-size:11px;font-weight:700;color:${verdictColor};
        background:${verdictColor}18;border:1px solid ${verdictColor}30;
        display:inline-block;padding:3px 10px;border-radius:100px;letter-spacing:0.08em">
        ${verdict.replace(/_/g, ' ')}
      </div>
    </div>
    ${Object.entries(data?.pipelines || {}).map(([k, v]) => {
      const p = v.synthetic_probability;
      const pipeColor = p >= 0.65 ? '#EF4444' : p >= 0.45 ? '#F59E0B' : '#10B981';
      const icons2 = { cnn:'🧠', frequency:'📊', facial_landmark:'👁️', metadata:'🏷️', video_temporal:'🎬' };
      return `
        <div class="amf-pipe-row">
          <div style="display:flex;justify-content:space-between;font-size:12px">
            <span>${icons2[k] || '🔧'} ${k.replace(/_/g,' ')}</span>
            <span style="color:${pipeColor};font-weight:700">${p != null ? Math.round(p*100)+'%' : v.status}</span>
          </div>
          <div class="amf-pipe-bar-track">
            <div class="amf-pipe-bar" style="width:${p!=null?Math.round(p*100):0}%;background:${pipeColor}"></div>
          </div>
        </div>`;
    }).join('')}
    <div style="margin-top:14px;padding-top:10px;font-size:10px;color:#475569">
      Source: ${(imageUrl||'').slice(0,60)}${imageUrl?.length>60?'…':''}
    </div>
  `;

  document.body.appendChild(panel);
}

// ────────────────────────────────────────────────
// Image Scanner
// ────────────────────────────────────────────────
async function scanImage(imgEl) {
  const src = imgEl.currentSrc || imgEl.src;
  if (!src || scannedUrls.has(src)) return;
  if (imgEl.naturalWidth < MIN_IMAGE_SIZE || imgEl.naturalHeight < MIN_IMAGE_SIZE) return;

  // Skip data: URLs, SVGs, extension-internal URLs
  if (src.startsWith('data:') || src.endsWith('.svg') || src.startsWith('chrome-extension://')) return;

  scannedUrls.add(src);
  injectOverlay(imgEl, 'scanning', null);

  try {
    const resp = await new Promise((resolve, reject) => {
      chrome.runtime.sendMessage({ type: 'ANALYZE_URL', url: src }, (response) => {
        if (chrome.runtime.lastError) reject(chrome.runtime.lastError);
        else resolve(response);
      });
    });

    if (!resp.ok) throw new Error(resp.error);
    const data = resp.result;
    const score = data?.fusion?.overall_synthetic_probability ?? 0.5;
    const state = score >= 0.65 ? 'ai' : score >= 0.45 ? 'suspicious' : 'authentic';
    injectOverlay(imgEl, state, data);
  } catch (err) {
    injectOverlay(imgEl, 'error', { error: String(err) });
  }
}

// ────────────────────────────────────────────────
// MutationObserver — auto-scan new images
// ────────────────────────────────────────────────
function observeImages() {
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (node.nodeType !== 1) continue;
        const imgs = node.tagName === 'IMG' ? [node] : [...node.querySelectorAll('img')];
        imgs.forEach(img => {
          if (img.complete) scanImage(img);
          else img.addEventListener('load', () => scanImage(img), { once: true });
        });
      }
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
}

// ────────────────────────────────────────────────
// Listen for messages from background
// ────────────────────────────────────────────────
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'FORENSICS_SCANNING') {
    // Highlight the image being scanned
    document.querySelectorAll(`img[src="${msg.url}"]`).forEach(img => {
      injectOverlay(img, 'scanning', null);
    });
  }
  if (msg.type === 'FORENSICS_RESULT') {
    const score = msg.result?.fusion?.overall_synthetic_probability ?? 0.5;
    const state = score >= 0.65 ? 'ai' : score >= 0.45 ? 'suspicious' : 'authentic';
    document.querySelectorAll(`img[src="${msg.url}"]`).forEach(img => {
      injectOverlay(img, state, msg.result);
    });
    showDetailPanel(msg.result, msg.url);
  }
  if (msg.type === 'FORENSICS_ERROR') {
    document.querySelectorAll(`img[src="${msg.url}"]`).forEach(img => {
      injectOverlay(img, 'error', {});
    });
  }
});

// ────────────────────────────────────────────────
// Init
// ────────────────────────────────────────────────
window.addEventListener('load', () => {
  setTimeout(() => {
    document.querySelectorAll('img').forEach(img => {
      if (img.complete) scanImage(img);
      else img.addEventListener('load', () => scanImage(img), { once: true });
    });
    observeImages();
  }, SCAN_DELAY_MS);
});
