import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Save,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  Building2,
  Package,
  FileSpreadsheet,
  ShieldAlert,
  Loader2,
  AlertCircle,
  Activity
} from 'lucide-react';
import {
  updateField,
  saveComplaintToDb,
  dismissSaveStatus,
  clearRecentlyUpdated
} from '../../store/slices/complaintSlice';

const REQUIRED_FIELDS = [
  'reported_by',
  'customer_name',
  'product_name',
  'batch_number',
  'complaint_description',
];

export default function ComplaintForm() {
  const dispatch = useDispatch();
  const [attemptedSubmit, setAttemptedSubmit] = useState(false);

  const {
    formData,
    fieldMetadata,
    recentlyUpdatedFields,
    isSaving,
    saveSuccess,
    saveError,
    isDirty,
    savedRecord
  } = useSelector((state) => state.complaint);

  // Clear highlight flash animation after 3 seconds
  useEffect(() => {
    if (recentlyUpdatedFields && recentlyUpdatedFields.length > 0) {
      const timer = setTimeout(() => {
        dispatch(clearRecentlyUpdated());
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [recentlyUpdatedFields, dispatch]);

  const handleChange = (field, value) => {
    dispatch(updateField({ field, value }));
  };

  const handleSave = (e) => {
    e.preventDefault();
    setAttemptedSubmit(true);

    const hasMissing = REQUIRED_FIELDS.some(
      (field) => !formData[field] || String(formData[field]).trim() === ''
    );

    if (hasMissing) {
      return;
    }

    dispatch(saveComplaintToDb(formData));
  };

  // Check if a field was attempted to submit while missing/empty
  const isFieldMissingOnSubmit = (fieldName) => {
    return (
      attemptedSubmit &&
      REQUIRED_FIELDS.includes(fieldName) &&
      (!formData[fieldName] || String(formData[fieldName]).trim() === '')
    );
  };

  // Check if field was populated or updated by AI
  const isFieldAIUpdated = (fieldName) => {
    return (
      fieldMetadata[fieldName]?.toUpperCase() === 'AI' &&
      formData[fieldName] !== null &&
      formData[fieldName] !== undefined &&
      String(formData[fieldName]).trim() !== ''
    );
  };

  // Check if a field was recently updated conversationally or via text ingestion
  const isFieldRecentlyUpdated = (fieldName) => {
    return recentlyUpdatedFields && recentlyUpdatedFields.includes(fieldName);
  };

  // Helper for origin badges: AI, USER, MISSING, or REQUIRED on submit
  const renderFieldBadge = (fieldName) => {
    if (isFieldMissingOnSubmit(fieldName)) {
      return (
        <span className="inline-flex items-center space-x-0.5 px-1.5 py-0.5 rounded text-[10px] bg-rose-500/20 text-rose-300 border border-rose-500/40 font-semibold animate-fadeIn">
          <AlertCircle className="w-2.5 h-2.5" />
          <span>Required</span>
        </span>
      );
    }

    const origin = fieldMetadata[fieldName]?.toUpperCase();
    if (origin === 'AI' && formData[fieldName]) {
      return (
        <span className="inline-flex items-center space-x-0.5 px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-medium animate-fadeIn">
          <Sparkles className="w-2.5 h-2.5" />
          <span>AI Updated</span>
        </span>
      );
    }
    if (origin === 'USER') {
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-medium">
          USER
        </span>
      );
    }
    if (origin === 'MISSING') {
      return (
        <span className="inline-flex items-center space-x-0.5 px-1.5 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
          <AlertTriangle className="w-2.5 h-2.5" />
          <span>MISSING</span>
        </span>
      );
    }
    return null;
  };

  const getFieldClass = (fieldName, isTextarea = false) => {
    const base = isTextarea
      ? 'w-full bg-slate-950 rounded-lg p-3 text-xs text-slate-200 focus:outline-none transition-all duration-300 leading-relaxed'
      : 'w-full bg-slate-950 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none transition-all duration-300';

    // 1. Red highlight if attempted to submit with missing value
    if (isFieldMissingOnSubmit(fieldName)) {
      return `${base} border-2 border-rose-500 ring-2 ring-rose-500/40 bg-rose-950/25 text-rose-100 placeholder-rose-400/60 shadow-md shadow-rose-500/10 focus:border-rose-400`;
    }

    // 2. Green highlight if updated by AI
    if (isFieldAIUpdated(fieldName)) {
      const pulse = isFieldRecentlyUpdated(fieldName) ? ' animate-pulse' : '';
      return `${base} border-2 border-emerald-500 ring-2 ring-emerald-500/30 bg-emerald-950/15 text-emerald-100 shadow-md shadow-emerald-500/10 focus:border-emerald-400${pulse}`;
    }

    // 3. Default styling
    return `${base} border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20`;
  };

  return (
    <form onSubmit={handleSave} className="space-y-5">
      {/* Top Banner & Save Action */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-slate-900/90 border border-slate-800 rounded-2xl shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100 flex items-center space-x-2">
              <span>Pharmaceutical Complaint Intake Record</span>
              {isDirty && (
                <span className="text-[10px] font-normal text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                  Unsaved changes
                </span>
              )}
            </h2>
            <p className="text-xs text-slate-400">
              Verified intake details and AI Copilot triage assessment
            </p>
          </div>
        </div>

        {/* Save Button */}
        <button
          type="submit"
          disabled={isSaving}
          className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-500/20 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Saving to Database...</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>Save Complaint</span>
            </>
          )}
        </button>
      </div>

      {/* Save Status Notifications */}
      {saveSuccess && (
        <div className="p-3.5 bg-emerald-950/40 border border-emerald-500/30 rounded-xl flex items-center justify-between text-xs text-emerald-300 animate-fadeIn">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              Complaint record <strong>{savedRecord?.complaint_id || formData.complaint_id}</strong> successfully saved to PostgreSQL database!
            </span>
          </div>
          <button
            type="button"
            onClick={() => dispatch(dismissSaveStatus())}
            className="text-emerald-400 hover:text-white font-bold text-xs"
          >
            ✕
          </button>
        </div>
      )}

      {saveError && (
        <div className="p-3.5 bg-rose-950/40 border border-rose-500/30 rounded-xl flex items-center justify-between text-xs text-rose-300 animate-fadeIn">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{saveError}</span>
          </div>
          <button
            type="button"
            onClick={() => dispatch(dismissSaveStatus())}
            className="text-rose-400 hover:text-white font-bold text-xs"
          >
            ✕
          </button>
        </div>
      )}

      {attemptedSubmit && REQUIRED_FIELDS.some((f) => !formData[f] || String(formData[f]).trim() === '') && (
        <div className="p-3.5 bg-rose-950/40 border border-rose-500/40 rounded-xl flex items-center justify-between text-xs text-rose-300 animate-fadeIn">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>
              <strong>Submission Blocked:</strong> Please complete all required complaint fields highlighted in red below before saving.
            </span>
          </div>
        </div>
      )}

      {/* SECTION 1: Origin & Customer Details */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl space-y-4">
        <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800/80 pb-2.5">
          <Building2 className="w-4 h-4 text-sky-400" />
          <span>Origin & Customer Details</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">Complaint Source</label>
              {renderFieldBadge('reported_by')}
            </div>
            <input
              type="text"
              list="complaint-sources"
              value={formData.reported_by || ''}
              onChange={(e) => handleChange('reported_by', e.target.value)}
              placeholder="e.g. Pharmacy, Hospital, Patient"
              className={getFieldClass('reported_by')}
            />
            <datalist id="complaint-sources">
              <option value="Pharmacy" />
              <option value="Hospital" />
              <option value="Patient" />
              <option value="Clinic" />
              <option value="Distributor" />
              <option value="Regulatory Agency" />
            </datalist>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">Customer Name</label>
              {renderFieldBadge('customer_name')}
            </div>
            <input
              type="text"
              value={formData.customer_name || ''}
              onChange={(e) => handleChange('customer_name', e.target.value)}
              placeholder="e.g. Apollo Pharmacy"
              className={getFieldClass('customer_name')}
            />
          </div>
        </div>
      </div>

      {/* SECTION 2: Product & Batch Identification */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl space-y-4">
        <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800/80 pb-2.5">
          <Package className="w-4 h-4 text-indigo-400" />
          <span>Product & Batch Identification</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">Product Name</label>
              {renderFieldBadge('product_name')}
            </div>
            <input
              type="text"
              value={formData.product_name || ''}
              onChange={(e) => handleChange('product_name', e.target.value)}
              placeholder="e.g. Amoxicillin Capsules"
              className={getFieldClass('product_name')}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">Product Strength</label>
              {renderFieldBadge('product_strength')}
            </div>
            <input
              type="text"
              value={formData.product_strength || ''}
              onChange={(e) => handleChange('product_strength', e.target.value)}
              placeholder="e.g. 500 mg"
              className={getFieldClass('product_strength')}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">Batch / Lot Number</label>
              {renderFieldBadge('batch_number')}
            </div>
            <input
              type="text"
              value={formData.batch_number || ''}
              onChange={(e) => handleChange('batch_number', e.target.value)}
              placeholder="e.g. AMX240602"
              className={`${getFieldClass('batch_number')} font-mono`}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">Affected Quantity</label>
              {renderFieldBadge('quantity_affected')}
            </div>
            <input
              type="text"
              value={formData.quantity_affected || ''}
              onChange={(e) => handleChange('quantity_affected', e.target.value)}
              placeholder="e.g. 12 capsules"
              className={getFieldClass('quantity_affected')}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">Manufacturing Date</label>
              {renderFieldBadge('manufacturing_date')}
            </div>
            <input
              type="text"
              value={formData.manufacturing_date || ''}
              onChange={(e) => handleChange('manufacturing_date', e.target.value)}
              placeholder="e.g. March 2026"
              className={getFieldClass('manufacturing_date')}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">Expiry Date</label>
              {renderFieldBadge('expiry_date')}
            </div>
            <input
              type="text"
              value={formData.expiry_date || ''}
              onChange={(e) => handleChange('expiry_date', e.target.value)}
              placeholder="e.g. February 2028"
              className={getFieldClass('expiry_date')}
            />
          </div>
        </div>
      </div>

      {/* SECTION 3: Defect Analysis */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl space-y-4">
        <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800/80 pb-2.5">
          <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
          <span>Defect Analysis</span>
        </div>

        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">Complaint Category</label>
              {renderFieldBadge('complaint_category')}
            </div>
            <input
              type="text"
              list="complaint-categories"
              value={formData.complaint_category || ''}
              onChange={(e) => handleChange('complaint_category', e.target.value)}
              placeholder="e.g. Product Defect - Discoloration"
              className={getFieldClass('complaint_category')}
            />
            <datalist id="complaint-categories">
              <option value="Product Defect - Discoloration" />
              <option value="Particulate Contamination" />
              <option value="Packaging Defect / Seal Failure" />
              <option value="Subpotency / Efficacy Issue" />
              <option value="Labelling Error" />
              <option value="Adverse Reaction Inquiry" />
            </datalist>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">Complaint Description</label>
              {renderFieldBadge('complaint_description')}
            </div>
            <textarea
              rows="3"
              value={formData.complaint_description || ''}
              onChange={(e) => handleChange('complaint_description', e.target.value)}
              placeholder="Apollo Pharmacy reported 12 discolored capsules in a sealed bottle. Requesting investigation and replacement."
              className={getFieldClass('complaint_description', true)}
            />
          </div>
        </div>
      </div>

      {/* SECTION 4: AI Copilot Risk Assessment */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400">
            <ShieldAlert className="w-4 h-4 text-blue-400" />
            <span>AI Copilot Risk Assessment</span>
          </div>
          <span className="text-[10px] text-blue-400/80 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20 font-medium">
            ICH Q9 Triage Analysis
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">Severity (Suggested)</label>
              {renderFieldBadge('initial_severity')}
            </div>
            <select
              value={formData.initial_severity || 'Major'}
              onChange={(e) => handleChange('initial_severity', e.target.value)}
              className={`${getFieldClass('initial_severity')} font-semibold`}
            >
              <option value="Critical">Critical (Immediate Hazard)</option>
              <option value="Major">Major (Defect / Non-compliance)</option>
              <option value="Minor">Minor (Cosmetic / Inquiry)</option>
            </select>
          </div>

          <div className="sm:col-span-2">
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">Suggested Next Action</label>
              {renderFieldBadge('ai_summary')}
            </div>
            <input
              type="text"
              value={formData.ai_summary || ''}
              onChange={(e) => handleChange('ai_summary', e.target.value)}
              placeholder="e.g. Route to QA Investigation & Issue Replacement"
              className={getFieldClass('ai_summary')}
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-medium text-slate-300">Initial Risk Assessment</label>
            {renderFieldBadge('initial_risk_assessment')}
          </div>
          <textarea
            rows="3"
            value={formData.initial_risk_assessment || ''}
            onChange={(e) => handleChange('initial_risk_assessment', e.target.value)}
            placeholder="Potential moisture ingress or primary packaging seal failure leading to capsule discoloration."
            className={getFieldClass('initial_risk_assessment', true)}
          />
        </div>
      </div>
    </form>
  );
}
