import React from 'react';
import { CheckCircle2, AlertCircle, Server, Database, Clock, Terminal } from 'lucide-react';
import { HealthResponse } from '../types';

interface HealthStatusProps {
  health: HealthResponse | null;
  error: string | null;
  loading: boolean;
}

export const HealthStatus: React.FC<HealthStatusProps> = ({ health, error, loading }) => {
  const isHealthy = health?.status === 'ok';

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden backdrop-blur-sm">
      <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center space-x-2">
            <Server className="w-5 h-5 text-cyan-400" />
            <span>Backend Engine Status</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Verification of Phase 1 REST API endpoint <code className="text-cyan-300">GET /api/v1/health</code></p>
        </div>
        <div className="flex items-center space-x-2">
          {loading ? (
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Validating...
            </span>
          ) : isHealthy ? (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
              SYSTEM ONLINE
            </span>
          ) : (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <AlertCircle className="w-3.5 h-3.5 mr-1.5" />
              OFFLINE / ERROR
            </span>
          )}
        </div>
      </div>

      {error ? (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          <p className="font-semibold mb-1">Communication Error:</p>
          <p className="mono-font">{error}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Status Card */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span>API Gateway</span>
              <Terminal className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-xl font-bold text-slate-100 flex items-center space-x-2">
              <span className="uppercase">{health?.status || 'Unknown'}</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">FastAPI 0.110+ on Python 3.13</p>
          </div>

          {/* Database Card */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span>Database Connection</span>
              <Database className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-xl font-bold text-slate-100 capitalize">
              {health?.database?.status === 'connected' ? (
                <span className="text-emerald-400">Connected</span>
              ) : (
                <span className="text-amber-400">{health?.database?.status || 'Pending'}</span>
              )}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Dialect: <span className="mono-font text-slate-300">{health?.database?.type || 'SQLAlchemy'}</span>
            </p>
          </div>

          {/* Timestamp Card */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span>Last Heartbeat</span>
              <Clock className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-sm font-semibold text-slate-100 mono-font truncate">
              {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : 'N/A'}
            </div>
            <p className="text-[11px] text-slate-400 mt-1 truncate">
              Version: {health?.version || '1.0.0'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
