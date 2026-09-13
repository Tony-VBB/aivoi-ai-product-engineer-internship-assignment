import React, { useState, useRef, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Send,
  Bot,
  User,
  Sparkles,
  Loader2,
  Paperclip,
  AlertCircle,
  UploadCloud,
  FileText,
  CheckCircle2,
  Wrench,
} from 'lucide-react';
import {
  sendCopilotMessage,
  analyzeUploadedDocument,
  setFileInfo,
} from '../../store/slices/aiCopilotSlice';
import { populateFromAI, applyFormUpdates } from '../../store/slices/complaintSlice';
import ExtractionProgress from './ExtractionProgress';


const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.eml'];

const PRESET_PROMPTS_DOC = [
  'Change the batch number to CT-99824',
  'The affected quantity was actually 500 vials',
  'Summarize this complaint.',
  'What are the key risk factors?',
];

const PRESET_PROMPTS_TEXT = [
  'Apollo Pharmacy reported 12 discolored capsules in a sealed bottle. Product: Amoxicillin Capsules 500 mg, batch AMX240602, mfg March 2026, expiry Feb 2028.',
  'Change the batch number to CT-99824',
  'The affected quantity was actually 500 vials',
  'What are the ICH Q9 risk classification guidelines?',
];

export default function CopilotChat() {
  const dispatch = useDispatch();
  const [inputMessage, setInputMessage] = useState('');
  const [composerError, setComposerError] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const messagesEndRef = useRef(null);
  const composerFileInputRef = useRef(null);

  const { threadId, chatMessages, isChatResponding, fileName, fileSize, uploadState } = useSelector(
    (state) => state.aiCopilot
  );

  const hasDocument = Boolean(fileName && uploadState === 'completed');
  const isBusy = uploadState === 'uploading' || uploadState === 'analyzing';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages, isChatResponding]);

  const handleSend = (textToSend) => {
    const query = (textToSend || inputMessage).trim();
    if (!query || isChatResponding) return;

    dispatch(sendCopilotMessage({ threadId, message: query }));
    setInputMessage('');
    setComposerError(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const validateAndUpload = (file) => {
    setComposerError(null);
    if (!file) return;

    // 1. Check extension
    const nameLower = file.name.toLowerCase();
    const hasValidExt = ALLOWED_EXTENSIONS.some((ext) => nameLower.endsWith(ext));
    if (!hasValidExt) {
      setComposerError('Unsupported file type. Please upload a PDF, DOCX, TXT, or EML document.');
      return;
    }

    // 2. Check empty file
    if (file.size === 0) {
      setComposerError('The selected file is empty. Please select a non-empty document.');
      return;
    }

    // 3. Check 10 MB size limit
    if (file.size > MAX_SIZE_BYTES) {
      setComposerError(
        `File exceeds maximum 10 MB limit (${(file.size / (1024 * 1024)).toFixed(2)} MB).`
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

  const handleComposerFileAttach = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      validateAndUpload(file);
    }
    e.target.value = ''; // reset file input
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    if (!isBusy) setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (isBusy) return;
    const file = e.dataTransfer.files?.[0];
    if (file) {
      validateAndUpload(file);
    }
  };

  const activePresets = hasDocument ? PRESET_PROMPTS_DOC : PRESET_PROMPTS_TEXT;

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className="relative flex flex-col h-[540px] bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl"
    >
      {/* Drag & Drop Visual Overlay */}
      {isDragOver && (
        <div className="absolute inset-0 bg-slate-950/90 border-2 border-dashed border-blue-400 rounded-xl z-50 flex flex-col items-center justify-center p-6 text-center backdrop-blur-sm pointer-events-none">
          <UploadCloud className="w-10 h-10 text-blue-400 mb-2 animate-bounce" />
          <p className="font-semibold text-sm text-slate-100">Drop Complaint Document Here</p>
          <p className="text-xs text-slate-400 mt-1">
            Supports PDF, DOCX, TXT, or EML (up to 10 MB)
          </p>
        </div>
      )}

      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between bg-slate-900 shrink-0">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Bot className="w-3.5 h-3.5" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-200">AI Quality Copilot</h4>
            <p className="text-[10px] text-slate-400">
              {hasDocument ? 'Document-assisted complaint analysis' : 'Interactive QMS consultation mode'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="flex items-center space-x-1 text-[10px] text-emerald-400 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>{hasDocument ? 'Document Linked' : 'Chat Ready'}</span>
          </span>
        </div>
      </div>

      {/* Linked Document Strip */}
      {hasDocument && (
        <div className="px-3.5 py-2 bg-blue-950/30 border-b border-slate-800 flex items-center justify-between text-xs shrink-0">
          <div className="flex items-center space-x-2 truncate">
            <FileText className="w-3.5 h-3.5 text-blue-400 shrink-0" />
            <span className="font-medium text-slate-200 truncate">{fileName}</span>
            {fileSize && <span className="text-slate-400 font-mono text-[11px]">({fileSize})</span>}
          </div>
          <div className="flex items-center space-x-1 shrink-0 text-emerald-400 text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Ingested & Linked</span>
          </div>
        </div>
      )}

      {/* In-chat Document Pipeline Progress (when uploading or processing) */}
      {uploadState !== 'idle' && uploadState !== 'completed' && (
        <div className="px-3 py-2 border-b border-slate-800 bg-slate-900/60 shrink-0">
          <ExtractionProgress />
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3.5 text-xs">
        {chatMessages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400 space-y-2">
            <Sparkles className="w-8 h-8 text-blue-400/50" />
            <p className="font-medium text-slate-300">
              {hasDocument ? 'Complaint Record Active' : 'AI Copilot Ready'}
            </p>
            <p className="text-[11px] text-slate-500 max-w-xs">
              {hasDocument
                ? 'Ask questions about this complaint, investigate missing fields, or examine ICH Q9 risk factors.'
                : 'Upload a complaint document using the 📎 button below (or drag and drop into this chat) to begin automated ingestion, or ask any QMS compliance question.'}
            </p>
          </div>
        )}

        {chatMessages.map((msg, idx) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={idx}
              className={`flex items-start space-x-2.5 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${isUser
                    ? 'bg-blue-600 text-white'
                    : msg.isError
                      ? 'bg-rose-950 text-rose-300 border border-rose-500/30'
                      : 'bg-slate-800 text-indigo-300 border border-slate-700'
                  }`}
              >
                {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>

              <div
                className={`p-3 rounded-2xl max-w-[85%] leading-relaxed ${isUser
                    ? 'bg-blue-600 text-white rounded-br-sm'
                    : msg.isError
                      ? 'bg-rose-950/60 text-rose-200 border border-rose-500/30 rounded-bl-sm'
                      : 'bg-slate-800 text-slate-200 border border-slate-700/60 rounded-bl-sm'
                  }`}
              >
                {/* Tool Execution Card: Fill Form */}
                {msg.toolCall && msg.toolCall.name === 'fill_form' && (
                  <div className="mb-2.5 p-2.5 bg-slate-900/90 border border-blue-500/30 rounded-xl space-y-1.5 text-[11px]">
                    <div className="flex items-center justify-between font-semibold text-blue-300">
                      <span className="flex items-center space-x-1.5">
                        <Wrench className="w-3.5 h-3.5 text-blue-400" />
                        <span>Tool: Auto-Filled Complaint Form</span>
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          dispatch(applyFormUpdates(msg.toolCall.fields));
                          if (msg.toolCall.severity?.initial_severity) {
                            dispatch(applyFormUpdates({ initial_severity: msg.toolCall.severity.initial_severity }));
                          }
                        }}
                        className="px-2 py-0.5 rounded text-[10px] bg-blue-600/30 hover:bg-blue-600/50 text-blue-200 border border-blue-500/30 transition flex items-center space-x-1"
                        title="Re-apply these fields into the complaint form"
                      >
                        <span>Sync to Form</span>
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1 pt-0.5">
                      {Object.entries(msg.toolCall.fields).map(([k, v]) => (
                        <span
                          key={k}
                          className="inline-flex items-center px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-300 font-mono text-[10px]"
                        >
                          <span className="text-slate-400 mr-1">{k.replace(/_/g, ' ')}:</span>
                          <span className="text-blue-200 font-medium">{String(v)}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="whitespace-pre-wrap">{msg.content}</div>
                {msg.timestamp && (
                  <span
                    className={`block mt-1 text-[9px] ${isUser ? 'text-blue-200/70 text-right' : 'text-slate-400'
                      }`}
                  >
                    {msg.timestamp}
                  </span>
                )}
              </div>
            </div>
          );
        })}

        {isChatResponding && (
          <div className="flex items-start space-x-2.5">
            <div className="w-6 h-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-indigo-300 shrink-0">
              <Bot className="w-3.5 h-3.5" />
            </div>
            <div className="p-3 bg-slate-800/80 border border-slate-700/60 rounded-2xl rounded-bl-sm flex items-center space-x-2 text-slate-400">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
              <span>Analyzing QMS records...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Composer Error Notification */}
      {composerError && (
        <div className="px-3 py-2 bg-rose-950/60 border-t border-rose-500/30 flex items-center space-x-2 text-[11px] text-rose-300 shrink-0">
          <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
          <span className="truncate">{composerError}</span>
        </div>
      )}

      {/* Preset Prompt Pills */}
      <div className="px-3 py-2 border-t border-slate-800/80 bg-slate-900/60 overflow-x-auto flex items-center gap-1.5 no-scrollbar shrink-0">
        {activePresets.map((preset, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(preset)}
            disabled={isChatResponding || isBusy}
            className="px-2.5 py-1 rounded-full text-[11px] whitespace-nowrap bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition disabled:opacity-50"
          >
            {preset}
          </button>
        ))}
      </div>

      {/* Input Composer */}
      <div className="p-3 border-t border-slate-800 bg-slate-900 flex items-center space-x-2 shrink-0">
        <input
          ref={composerFileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.eml"
          onChange={handleComposerFileAttach}
          disabled={isBusy}
          className="hidden"
        />

        {/* Integrated Inline Attachment Control ([ + / attachment ]) */}
        <button
          type="button"
          onClick={() => composerFileInputRef.current?.click()}
          disabled={isChatResponding || isBusy}
          title="Attach document to session (.pdf, .docx, .txt, .eml up to 10MB)"
          className={`flex items-center space-x-1 px-2 py-1.5 rounded-lg border transition shrink-0 ${isBusy
              ? 'bg-slate-800/50 border-slate-800 text-slate-600 cursor-not-allowed'
              : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-300 hover:text-white'
            }`}
        >
          {isBusy ? (
            <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
          ) : (
            <>
              <span className="text-xs font-bold text-blue-400">+</span>
              <Paperclip className="w-3.5 h-3.5" />
            </>
          )}
        </button>

        <textarea
          rows="1"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isBusy
              ? 'AI document ingestion pipeline in progress...'
              : hasDocument
                ? 'Instruct Copilot (e.g. "Change batch number to CT-99824") or ask quality question...'
                : 'Type complaint narrative to auto-fill form, ask a question, or attach document (+)...'
          }
          disabled={isChatResponding || isBusy}
          className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none disabled:bg-slate-900/50"
        />
        <button
          onClick={() => handleSend()}
          disabled={!inputMessage.trim() || isChatResponding || isBusy}
          className="p-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-lg transition shrink-0"
          title="Send message"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

