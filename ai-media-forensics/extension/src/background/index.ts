// Manifest V3 Background Service Worker
chrome.runtime.onInstalled.addListener(() => {
  console.log('[AI Forensics] Sentinel Extension background worker initialized.');
});

export {};
