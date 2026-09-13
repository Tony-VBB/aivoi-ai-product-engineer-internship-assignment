import React from 'react';
import RiskAssessmentCard from './RiskAssessmentCard';
import CopilotChat from './CopilotChat';

export default function AICopilot() {
  return (
    <div className="space-y-4">
      {/* 1. Conversational AI Copilot Chat with integrated document upload */}
      <CopilotChat />

      {/* 2. AI Risk Assessment & Triage (renders once document is analyzed) */}
      <RiskAssessmentCard />
    </div>
  );
}

