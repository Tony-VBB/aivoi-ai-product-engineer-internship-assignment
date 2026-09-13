import React, { useState, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { UploadCloud, FileText, AlertCircle, CheckCircle2 } from 'lucide-react';
import {
  analyzeUploadedDocument,
  setFileInfo,
} from '../../store/slices/aiCopilotSlice';

const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.eml'];

export default function FileDropzone() {
  const dispatch = useDispatch();
  const fileInputRef = useRef(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [clientError, setClientError] = useState(null);

  const { uploadState, fileName, fileSize } = useSelector(
    (state) => state.aiCopilot
  );

  const validateAndUpload = (file) => {
    setClientError(null);
    if (!file) return;

    // Check extension
    const nameLower = file.name.toLowerCase();
    const hasValidExt = ALLOWED_EXTENSIONS.some((ext) => nameLower.endsWith(ext));
    if (!hasValidExt) {
      setClientError(
        `Unsupported file type. Please upload a PDF, DOCX, TXT, or EML file.`
      );
      return;
    }

    // Check empty file
    if (file.size === 0) {
      setClientError(
        `The uploaded file is empty. Please select a non-empty document.`
      );
      return;
    }

    // Check size limit (10 MB)
    if (file.size > MAX_SIZE_BYTES) {
      setClientError(
        `File exceeds maximum 10 MB limit (${(file.size / (1024 * 1024)).toFixed(2)} MB). Please select a smaller file.`
      );
      return;
    }

    dispatch(
      setFileInfo({
        name: file.name,
        size: (file.size / 1024).toFixed(1) + ' KB',
      })
    );

    dispatch(analyzeUploadedDocument(file));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndUpload(e.target.files[0]);
    }
  };

  const isBusy = uploadState === 'uploading' || uploadState === 'analyzing';

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!isBusy) setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => {
          if (!isBusy) fileInputRef.current?.click();
        }}
        className={`relative border-2 border-dashed rounded-xl p-6 text-center transition cursor-pointer flex flex-col items-center justify-center ${
          isDragOver
            ? 'border-blue-500 bg-blue-500/10'
            : isBusy
            ? 'border-slate-700 bg-slate-800/30 cursor-not-allowed opacity-80'
            : 'border-slate-700 hover:border-blue-500/60 bg-slate-900/40 hover:bg-slate-900/70'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.eml"
          onChange={handleFileChange}
          disabled={isBusy}
          className="hidden"
        />

        <div className="w-12 h-12 mb-3 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
          <UploadCloud className="w-6 h-6" />
        </div>

        <h3 className="text-sm font-semibold text-slate-200">
          {isBusy ? 'Processing Document...' : 'Upload Complaint Document'}
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          Drag & drop your file here, or <span className="text-blue-400 underline">browse</span>
        </p>

        {/* Format Tags & Limits */}
        <div className="flex flex-wrap items-center justify-center gap-1.5 mt-3 text-[11px]">
          {['PDF', 'DOCX', 'TXT', 'EML'].map((ext) => (
            <span
              key={ext}
              className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/60 font-mono"
            >
              {ext}
            </span>
          ))}
          <span className="text-slate-500 ml-1">• Max 10 MB</span>
        </div>
      </div>

      {/* Client Validation Error */}
      {clientError && (
        <div className="flex items-start space-x-2 p-3 bg-rose-950/40 border border-rose-500/30 rounded-lg text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
          <span>{clientError}</span>
        </div>
      )}

      {/* Active File Banner */}
      {fileName && !clientError && (
        <div className="flex items-center justify-between px-3.5 py-2.5 bg-slate-900/90 border border-slate-800 rounded-lg text-xs">
          <div className="flex items-center space-x-2 truncate">
            <FileText className="w-4 h-4 text-blue-400 shrink-0" />
            <span className="font-medium text-slate-200 truncate">{fileName}</span>
            <span className="text-slate-500">({fileSize})</span>
          </div>
          {uploadState === 'completed' && (
            <div className="flex items-center space-x-1 text-emerald-400 shrink-0">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Extracted</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
