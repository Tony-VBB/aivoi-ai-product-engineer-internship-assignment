import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Activity, Database, Sparkles, RefreshCw } from 'lucide-react';
import api from '../api/apiClient';
import { resetCopilotSession } from '../store/slices/aiCopilotSlice';
import { resetForm } from '../store/slices/complaintSlice';

export default function Navbar() {
  const dispatch = useDispatch();
  const threadId = useSelector((state) => state.aiCopilot.threadId);
  const [healthStatus, setHealthStatus] = useState({
    checked: false,
    healthy: false,
    db: false,
    groq: false,
  });

  const checkHealth = async () => {
    try {
      const data = await api.getHealth();
      setHealthStatus({
        checked: true,
        healthy: data.status === 'healthy' || data.status === 'degraded',
        db: data.database_connected,
        groq: data.groq_configured,
      });
    } catch {
      setHealthStatus({
        checked: true,
        healthy: false,
        db: false,
        groq: false,
      });
    }
  };

  useEffect(() => {
    checkHealth();
    const timer = setInterval(checkHealth, 30000);
    return () => clearInterval(timer);
  }, []);

  const handleReset = () => {
    if (window.confirm('Reset current complaint session and start a new intake?')) {
      dispatch(resetCopilotSession());
      dispatch(resetForm());
    }
  };

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand & Subtitle */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-sky-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold tracking-tight text-white">AIVOA</h1>
              <span className="px-2 py-0.5 text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-full">
                Pharma QMS
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              AI Customer Complaint Management & ICH Q9 Triage System
            </p>
          </div>
        </div>

        {/* System & Session Indicators */}
        <div className="flex items-center space-x-4">
          {/* Thread ID Badge */}
          {threadId ? (
            <div className="hidden md:flex items-center space-x-1.5 px-3 py-1 bg-slate-800/80 border border-slate-700/70 rounded-full text-xs text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="text-slate-400">Session:</span>
              <span className="font-mono text-blue-300">{threadId.slice(0, 8)}...</span>
            </div>
          ) : (
            <div className="hidden md:flex items-center space-x-1.5 px-3 py-1 bg-slate-800/40 border border-slate-800 rounded-full text-xs text-slate-400">
              <span>Ready for document intake</span>
            </div>
          )}

          {/* Backend Connection Status */}
          <div className="flex items-center space-x-2 text-xs">
            <div
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full border ${
                healthStatus.healthy
                  ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300'
                  : 'bg-rose-950/40 border-rose-500/30 text-rose-300'
              }`}
              title={
                healthStatus.healthy
                  ? `Backend active | DB: ${healthStatus.db ? 'Connected' : 'Offline'} | Groq: ${healthStatus.groq ? 'Ready' : 'Missing'}`
                  : 'FastAPI backend unreachable at localhost:8000'
              }
            >
              <Activity className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">
                {healthStatus.healthy ? 'API Connected' : 'API Offline'}
              </span>
            </div>

            {/* DB indicator */}
            <div
              className={`hidden lg:flex items-center space-x-1 px-2.5 py-1 rounded-full border ${
                healthStatus.db
                  ? 'bg-blue-950/40 border-blue-500/30 text-blue-300'
                  : 'bg-amber-950/40 border-amber-500/30 text-amber-300'
              }`}
              title={healthStatus.db ? 'PostgreSQL connection live' : 'PostgreSQL not connected'}
            >
              <Database className="w-3.5 h-3.5" />
              <span>{healthStatus.db ? 'PostgreSQL' : 'DB Offline'}</span>
            </div>
          </div>

          {/* New / Reset Intake */}
          <button
            onClick={handleReset}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition"
            title="Start new intake"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">New Intake</span>
          </button>
        </div>
      </div>
    </header>
  );
}
