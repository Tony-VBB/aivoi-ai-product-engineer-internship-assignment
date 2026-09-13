import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../api/apiClient';
import { populateFromAI, applyFormUpdates } from './complaintSlice';

const generateUUID = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

export const analyzeUploadedDocument = createAsyncThunk(
  'aiCopilot/analyzeUploadedDocument',
  async (file, { dispatch, getState, rejectWithValue }) => {
    try {
      dispatch(setUploadState('uploading'));
      dispatch(setUploadProgress(20));

      const currentThreadId = getState().aiCopilot.threadId;

      const result = await api.analyzeDocument(
        file,
        (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            dispatch(setUploadProgress(Math.min(percent, 80)));
          }
        },
        currentThreadId
      );

      dispatch(setUploadProgress(100));
      dispatch(setUploadState('analyzing'));

      // Automatically sync extracted result into complaint form Redux slice
      dispatch(populateFromAI(result));

      return result;
    } catch (err) {
      return rejectWithValue(err.message || 'Analysis pipeline failed.');
    }
  }
);

export const sendCopilotMessage = createAsyncThunk(
  'aiCopilot/sendCopilotMessage',
  async ({ threadId, message }, { dispatch, getState, rejectWithValue }) => {
    try {
      const state = getState();
      const activeThreadId = threadId || state.aiCopilot.threadId || generateUUID();
      const currentFormData = state.complaint?.formData || null;
      const result = await api.sendCopilotMessage(activeThreadId, message, currentFormData);

      // If the AI returned form_updates or invoked fill_form tool, patch complaint form immediately
      if (result.form_updates && Object.keys(result.form_updates).length > 0) {
        dispatch(applyFormUpdates(result.form_updates));
      }
      if (result.severity) {
        dispatch(applyFormUpdates({
          initial_severity: result.severity.initial_severity,
          suggested_action: result.severity.suggested_action
        }));
      }
      if (result.risk_assessment?.rationale) {
        dispatch(applyFormUpdates({
          initial_risk_assessment: result.risk_assessment.rationale
        }));
      }

      return result;
    } catch (err) {
      return rejectWithValue(err.message || 'Copilot chat error.');
    }
  }
);


const aiCopilotSlice = createSlice({
  name: 'aiCopilot',
  initialState: {
    threadId: generateUUID(),
    uploadState: 'idle', // 'idle' | 'uploading' | 'analyzing' | 'completed' | 'error'
    uploadProgress: 0,
    currentStep: '',
    fileName: null,
    fileSize: null,
    riskAssessment: null,
    completeness: null,
    aiSummary: '',
    rawTextPreview: '',
    chatMessages: [],
    isChatResponding: false,
    chatError: null,
    error: null,
  },
  reducers: {
    setUploadState: (state, action) => {
      state.uploadState = action.payload;
      if (action.payload === 'uploading') {
        state.error = null;
      }
    },
    setUploadProgress: (state, action) => {
      state.uploadProgress = action.payload;
    },
    setFileInfo: (state, action) => {
      state.fileName = action.payload.name;
      state.fileSize = action.payload.size;
    },
    clearAnalysisError: (state) => {
      state.error = null;
    },
    resetCopilotSession: (state) => {
      state.threadId = generateUUID();
      state.uploadState = 'idle';
      state.uploadProgress = 0;
      state.fileName = null;
      state.fileSize = null;
      state.riskAssessment = null;
      state.completeness = null;
      state.aiSummary = '';
      state.rawTextPreview = '';
      state.chatMessages = [];
      state.error = null;
      state.chatError = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Document Analysis
      .addCase(analyzeUploadedDocument.pending, (state) => {
        state.uploadState = 'uploading';
        state.error = null;
      })
      .addCase(analyzeUploadedDocument.fulfilled, (state, action) => {
        const payload = action.payload;
        state.uploadState = 'completed';
        state.threadId = payload.thread_id;
        state.riskAssessment = payload.risk_assessment;
        state.completeness = payload.completeness;
        state.aiSummary = payload.ai_summary;
        state.rawTextPreview = payload.raw_text_preview;

        // Initialize welcome message from Copilot
        state.chatMessages = [
          {
            role: 'assistant',
            content: `I have analyzed **${state.fileName || 'your document'}** and loaded the complaint details. Initial triage: **${payload.severity?.initial_severity || 'Major'} Severity** / **${payload.risk_assessment?.risk_level || 'Medium'} Risk**. You can ask me questions about missing fields, risk rationale, or product details.`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ];
      })
      .addCase(analyzeUploadedDocument.rejected, (state, action) => {
        state.uploadState = 'error';
        state.error = action.payload || 'An error occurred during AI analysis.';
      })

      // Copilot Chat
      .addCase(sendCopilotMessage.pending, (state, action) => {
        state.isChatResponding = true;
        state.chatError = null;
        // Optimistically add user query to chat
        state.chatMessages.push({
          role: 'user',
          content: action.meta.arg.message,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        });
      })
      .addCase(sendCopilotMessage.fulfilled, (state, action) => {
        state.isChatResponding = false;
        const payload = action.payload;
        const hasFormUpdates =
          payload &&
          (payload.action === 'fill_form' || payload.form_updates) &&
          payload.form_updates &&
          Object.keys(payload.form_updates).length > 0;

        state.chatMessages.push({
          role: 'assistant',
          content: payload.reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          toolCall: hasFormUpdates
            ? {
              name: 'fill_form',
              fields: payload.form_updates,
              severity: payload.severity,
              completeness: payload.completeness,
            }
            : null,
        });
      })

      .addCase(sendCopilotMessage.rejected, (state, action) => {
        state.isChatResponding = false;
        state.chatError = action.payload || 'Failed to receive response from Copilot.';
        state.chatMessages.push({
          role: 'assistant',
          content: `⚠️ Error: ${action.payload || 'Could not contact AI Copilot.'}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isError: true,
        });
      });
  },
});

export const {
  setUploadState,
  setUploadProgress,
  setFileInfo,
  clearAnalysisError,
  resetCopilotSession,
} = aiCopilotSlice.actions;

export default aiCopilotSlice.reducer;
