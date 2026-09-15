import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { Dashboard } from './pages/Dashboard';
import { fetchHealth } from './services/api';
import { HealthResponse } from './types';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchHealth();
      setHealth(data);
      setError(null);
    } catch (err: any) {
      console.error('Health check failed:', err);
      setError(err.message || 'Unable to connect to backend server at http://localhost:8000');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    // Poll health status periodically every 15 seconds
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return (
    <div className="min-h-screen bg-[#0B0F19] flex flex-col font-sans text-slate-100">
      <Header health={health} loading={loading} onRefresh={checkHealth} />
      <main className="flex-1">
        <Dashboard health={health} error={error} loading={loading} />
      </main>
      <footer className="border-t border-slate-900/80 py-6 bg-[#080B12] text-center text-xs text-slate-400">
        <p>AI-Generated & Manipulated Media Detection System &bull; Phase 1 Foundation &bull; Evidence-Based Forensics</p>
      </footer>
    </div>
  );
};

export default App;
