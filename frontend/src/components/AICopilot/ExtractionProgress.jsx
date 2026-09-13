import React from 'react';
import { useSelector } from 'react-redux';
import { Loader2, CheckCircle, AlertTriangle } from 'lucide-react';

export default function ExtractionProgress() {
  const { uploadState, uploadProgress, error } = useSelector((state) => state.aiCopilot);

  if (uploadState === 'idle') return null;

  if (uploadState === 'error') {
    return (
      <div className="p-3.5 bg-rose-950/40 border border-rose-500/30 rounded-xl space-y-1.5 text-xs text-rose-300">
        <div className="flex items-center space-x-2 font-semibold text-rose-200">
          <AlertTriangle className="w-4 h-4 text-rose-400" />
          <span>Document Analysis Error</span>
        </div>
        <p className="text-slate-300 leading-relaxed">{error}</p>
      </div>
    );
  }

  const isUploading = uploadState === 'uploading';
  const isAnalyzing = uploadState === 'analyzing';

  return (
    <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl space-y-3">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2 font-medium text-slate-200">
          {(isUploading || isAnalyzing) && (
            <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
          )}
          {uploadState === 'completed' && (
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          )}
          <span>
            {isUploading && 'Uploading Document...'}
            {isAnalyzing && 'LangGraph AI Pipeline Processing...'}
            {uploadState === 'completed' && 'Analysis Complete'}
          </span>
        </div>
        <span className="text-slate-400 font-mono">
          {isUploading ? `${uploadProgress}%` : isAnalyzing ? 'Running' : '100%'}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${
            uploadState === 'completed'
              ? 'bg-emerald-500 w-full'
              : isAnalyzing
              ? 'bg-gradient-to-r from-blue-500 via-indigo-500 to-sky-400 w-full animate-pulse'
              : 'bg-blue-600'
          }`}
          style={{ width: isAnalyzing || uploadState === 'completed' ? '100%' : `${uploadProgress}%` }}
        />
      </div>

      {/* Step Indicators */}
      <div className="grid grid-cols-4 gap-1 text-[10px] text-center pt-1 text-slate-400">
        <span className={uploadProgress > 10 ? 'text-blue-400 font-medium' : ''}>1. Parse File</span>
        <span className={uploadProgress > 50 || isAnalyzing ? 'text-blue-400 font-medium' : ''}>2. Extract Fields</span>
        <span className={isAnalyzing || uploadState === 'completed' ? 'text-blue-400 font-medium' : ''}>3. Triage & Risk</span>
        <span className={uploadState === 'completed' ? 'text-emerald-400 font-medium' : ''}>4. Complete</span>
      </div>
    </div>
  );
}
