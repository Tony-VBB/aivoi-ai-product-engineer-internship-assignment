import React from 'react';
import Navbar from './components/Navbar';
import ComplaintDashboard from './pages/ComplaintDashboard';

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />
      <div className="flex-1">
        <ComplaintDashboard />
      </div>
      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-500">
        AIVOA Pharmaceutical AI Customer Complaint Management Prototype &bull; Round 1 AI Product Engineer
      </footer>
    </div>
  );
}
