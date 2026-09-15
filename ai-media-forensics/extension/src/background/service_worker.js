// Background Service Worker — AI Media Forensics Extension
const API_BASE = 'http://localhost:8000/api/v1';

// Context menu item
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'forensics-check-image',
    title: '🔬 Check with AI Forensics',
    contexts: ['image'],
  });
  chrome.contextMenus.create({
    id: 'forensics-check-link',
    title: '🔬 Analyze linked media (AI Forensics)',
    contexts: ['link'],
  });
  console.log('[AI Forensics] Extension installed and context menus created.');
});

// Context menu click handler
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const url = info.srcUrl || info.linkUrl;
  if (!url || !tab?.id) return;

  // Show scanning overlay on the page
  chrome.tabs.sendMessage(tab.id, { type: 'FORENSICS_SCANNING', url });

  try {
    const result = await analyzeUrl(url);
    chrome.tabs.sendMessage(tab.id, { type: 'FORENSICS_RESULT', url, result });
    // Update badge
    const score = result?.fusion?.overall_synthetic_probability ?? 0.5;
    setBadge(tab.id, score);
  } catch (err) {
    chrome.tabs.sendMessage(tab.id, { type: 'FORENSICS_ERROR', url, error: String(err) });
  }
});

// Message handler from content scripts
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'ANALYZE_URL') {
    analyzeUrl(msg.url)
      .then(result => sendResponse({ ok: true, result }))
      .catch(err => sendResponse({ ok: false, error: String(err) }));
    return true; // keep channel open for async
  }

  if (msg.type === 'GET_BADGE_SCORE') {
    sendResponse({ score: badgeScores[sender.tab?.id ?? -1] ?? null });
  }
});

// URL analysis via backend
async function analyzeUrl(imageUrl) {
  const endpoint = `${API_BASE}/detection/url?url=${encodeURIComponent(imageUrl)}`;
  const resp = await fetch(endpoint, { method: 'POST' });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

// Badge management
const badgeScores = {};

function setBadge(tabId, score) {
  badgeScores[tabId] = score;
  let text, color;
  if (score >= 0.65) { text = '!'; color = '#EF4444'; }
  else if (score >= 0.45) { text = '?'; color = '#F59E0B'; }
  else { text = '✓'; color = '#10B981'; }

  chrome.action.setBadgeText({ text, tabId });
  chrome.action.setBadgeBackgroundColor({ color, tabId });
}
