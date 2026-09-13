import React from 'react';
import { useSelector } from 'react-redux';
import { ShieldAlert, AlertOctagon, CheckCircle2, FileSearch, Quote } from 'lucide-react';

export default function RiskAssessmentCard() {
  const { riskAssessment, aiSummary, completeness } = useSelector(
    (state) => state.aiCopilot
  );

  if (!riskAssessment) return null;

  const riskLevel = riskAssessment.risk_level || 'Medium';

  const getBadgeStyle = (level) => {
    switch (level.toLowerCase()) {
      case 'high':
        return 'bg-rose-950/60 border-rose-500/40 text-rose-300';
      case 'medium':
        return 'bg-amber-950/60 border-amber-500/40 text-amber-300';
      case 'low':
        return 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300';
      default:
        return 'bg-slate-800 border-slate-700 text-slate-300';
    }
  };

  return (
    <div className="space-y-4">
      {/* AI Summary Card */}
      {aiSummary && (
        <div className="p-4 bg-slate-900/90 border border-slate-800 rounded-xl space-y-2">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
            <FileSearch className="w-4 h-4 text-blue-400" />
            <span>AI Executive Summary</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            {aiSummary}
          </p>
        </div>
      )}

      {/* ICH Q9 Risk Assessment Box */}
      <div className="p-4 bg-slate-900/90 border border-slate-800 rounded-xl space-y-3.5">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-indigo-400" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              ICH Q9 Risk Assessment
            </h4>
          </div>
          <span
            className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getBadgeStyle(
              riskLevel
            )}`}
          >
            {riskLevel.toUpperCase()} RISK
          </span>
        </div>

        {/* Rationale */}
        {riskAssessment.rationale && (
          <div className="space-y-1">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Assessment Rationale
            </span>
            <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/50 p-2.5 rounded-lg border border-slate-800/60">
              {riskAssessment.rationale}
            </p>
          </div>
        )}

        {/* Key Risk Factors */}
        {riskAssessment.key_risk_factors?.length > 0 && (
          <div className="space-y-1.5">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Key Hazard Factors
            </span>
            <ul className="space-y-1">
              {riskAssessment.key_risk_factors.map((factor, idx) => (
                <li
                  key={idx}
                  className="flex items-start space-x-2 text-xs text-slate-300"
                >
                  <AlertOctagon className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                  <span>{factor}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Extracted Evidence */}
        {riskAssessment.extracted_evidence?.length > 0 && (
          <div className="space-y-1.5">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1">
              <Quote className="w-3 h-3 text-slate-400" />
              <span>Extracted Source Citations</span>
            </span>
            <div className="space-y-1">
              {riskAssessment.extracted_evidence.map((evidence, idx) => (
                <p
                  key={idx}
                  className="text-xs italic text-slate-400 bg-slate-950/30 px-2.5 py-1.5 rounded border border-slate-800/40"
                >
                  "{evidence}"
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Completeness Status */}
        {completeness && (
          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <span className="text-slate-400">Intake Completeness:</span>
            <span
              className={`font-semibold flex items-center space-x-1 ${
                completeness.completeness_status === 'Complete'
                  ? 'text-emerald-400'
                  : completeness.completeness_status === 'Partially Complete'
                  ? 'text-amber-400'
                  : 'text-rose-400'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{completeness.completeness_status}</span>
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
