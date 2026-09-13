import React from 'react';
import ComplaintForm from '../components/ComplaintForm/ComplaintForm';
import AICopilot from '../components/AICopilot/AICopilot';

export default function ComplaintDashboard() {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Pane: Structured Complaint Form (7 cols on lg) */}
        <section className="lg:col-span-7 space-y-6">
          <ComplaintForm />
        </section>

        {/* Right Pane: AI Ingestion, ICH Q9 Risk Assessment & Copilot Chat (5 cols on lg) */}
        <section className="lg:col-span-5 space-y-6 lg:sticky lg:top-20">
          <AICopilot />
        </section>
      </div>
    </main>
  );
}
