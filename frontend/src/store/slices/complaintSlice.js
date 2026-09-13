import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../api/apiClient';

export const saveComplaintToDb = createAsyncThunk(
  'complaint/saveComplaintToDb',
  async (complaintData, { rejectWithValue }) => {
    try {
      const payloadToSend = {
        ...complaintData,
        ai_risk_assessment: complaintData.initial_risk_assessment
          ? { ...(complaintData.ai_risk_assessment || {}), rationale: complaintData.initial_risk_assessment }
          : complaintData.ai_risk_assessment
      };
      const result = await api.saveComplaint(payloadToSend);
      return result;
    } catch (err) {
      return rejectWithValue(err.message || 'Failed to persist complaint to PostgreSQL.');
    }
  }
);

const initialFormState = {
  complaint_id: '',
  complaint_date: new Date().toISOString().split('T')[0],
  received_date: new Date().toISOString().split('T')[0],
  status: 'Under Review',
  product_name: '',
  product_strength: '',
  product_type: '',
  batch_number: '',
  manufacturing_site: '',
  manufacturing_date: '',
  expiry_date: '',
  quantity_affected: '',
  customer_name: '',
  customer_contact: '',
  reported_by: '',
  event_date: '',
  complaint_description: '',
  complaint_category: '',
  initial_severity: 'Major',
  priority: 'Medium',
  completeness_status: 'Incomplete',
  missing_information: [],
  ai_summary: '',
  initial_risk_assessment: '',
  ai_risk_assessment: {},
};

const complaintSlice = createSlice({
  name: 'complaint',
  initialState: {
    formData: { ...initialFormState },
    // Tracks origin: 'AI', 'USER', or 'MISSING'
    fieldMetadata: {},
    recentlyUpdatedFields: [],
    isSaving: false,
    saveSuccess: false,
    saveError: null,
    savedRecord: null,
    isDirty: false,
  },
  reducers: {
    updateField: (state, action) => {
      const { field, value } = action.payload;
      state.formData[field] = value;
      state.fieldMetadata[field] = 'USER';
      state.isDirty = true;
      state.saveSuccess = false;
      state.saveError = null;
    },
    applyFormUpdates: (state, action) => {
      const updates = action.payload || {};
      const touchedFields = [];

      const aliasMap = {
        complaint_source: 'reported_by',
        source: 'reported_by',
        suggested_action: 'ai_summary',
        suggested_next_action: 'ai_summary',
        initial_risk_assessment: 'initial_risk_assessment',
        risk_rationale: 'initial_risk_assessment',
        batch_lot_number: 'batch_number',
        lot_number: 'batch_number',
        affected_quantity: 'quantity_affected',
      };

      Object.entries(updates).forEach(([rawKey, val]) => {
        if (val === null || val === undefined || val === '') return;
        const key = aliasMap[rawKey] || rawKey;

        if (key === 'initial_risk_assessment') {
          const strVal = typeof val === 'string' ? val : (val.rationale || JSON.stringify(val));
          state.formData.initial_risk_assessment = strVal;
          state.formData.ai_risk_assessment = typeof val === 'object' ? val : { rationale: strVal };
          state.fieldMetadata.initial_risk_assessment = 'AI';
          touchedFields.push('initial_risk_assessment');
        } else if (key in state.formData) {
          state.formData[key] = val;
          state.fieldMetadata[key] = 'AI';
          touchedFields.push(key);
        }
      });

      state.recentlyUpdatedFields = touchedFields;
      state.isDirty = true;
      state.saveSuccess = false;
      state.saveError = null;
    },
    clearRecentlyUpdated: (state) => {
      state.recentlyUpdatedFields = [];
    },
    populateFromAI: (state, action) => {
      const { extracted_fields, completeness, severity, risk_assessment, ai_summary } = action.payload;

      const newMetadata = { ...state.fieldMetadata };

      Object.entries(extracted_fields || {}).forEach(([rawKey, val]) => {
        const aliasMap = {
          complaint_source: 'reported_by',
          source: 'reported_by',
          suggested_action: 'ai_summary',
          suggested_next_action: 'ai_summary',
          initial_risk_assessment: 'initial_risk_assessment',
          risk_rationale: 'initial_risk_assessment',
          batch_lot_number: 'batch_number',
          lot_number: 'batch_number',
          affected_quantity: 'quantity_affected',
        };
        const key = aliasMap[rawKey] || rawKey;

        // Preserve user edits - must not be overwritten by later Redux updates
        if (state.fieldMetadata[key] === 'USER') {
          return;
        }

        if (val !== null && val !== undefined && val !== '') {
          state.formData[key] = val;
          newMetadata[key] = 'AI';
        } else {
          if (!state.formData[key]) {
            state.formData[key] = '';
          }
          newMetadata[key] = 'MISSING';
        }
      });

      if (state.fieldMetadata.initial_severity !== 'USER' && severity?.initial_severity) {
        state.formData.initial_severity = severity.initial_severity;
        newMetadata.initial_severity = 'AI';
      }
      if (state.fieldMetadata.priority !== 'USER' && severity?.priority) {
        state.formData.priority = severity.priority;
        newMetadata.priority = 'AI';
      }
      if (state.fieldMetadata.completeness_status !== 'USER' && completeness?.completeness_status) {
        state.formData.completeness_status = completeness.completeness_status;
        newMetadata.completeness_status = 'AI';
      }
      if (state.fieldMetadata.missing_information !== 'USER' && completeness?.missing_fields) {
        state.formData.missing_information = completeness.missing_fields;
        newMetadata.missing_information = 'AI';
      }
      const actionText = severity?.suggested_action || ai_summary;
      if (state.fieldMetadata.ai_summary !== 'USER' && actionText) {
        state.formData.ai_summary = actionText;
        newMetadata.ai_summary = 'AI';
      }
      if (state.fieldMetadata.initial_risk_assessment !== 'USER') {
        const riskText = risk_assessment?.rationale || risk_assessment?.initial_risk_assessment;
        if (riskText) {
          state.formData.initial_risk_assessment = riskText;
          newMetadata.initial_risk_assessment = 'AI';
        }
      }
      if (state.fieldMetadata.ai_risk_assessment !== 'USER' && risk_assessment) {
        state.formData.ai_risk_assessment = risk_assessment;
        newMetadata.ai_risk_assessment = 'AI';
      }

      state.fieldMetadata = newMetadata;
      state.recentlyUpdatedFields = Object.keys(extracted_fields || {});
      state.isDirty = false;
      state.saveSuccess = false;
      state.saveError = null;
    },
    resetForm: (state) => {
      state.formData = { ...initialFormState };
      state.fieldMetadata = {};
      state.recentlyUpdatedFields = [];
      state.isDirty = false;
      state.saveSuccess = false;
      state.saveError = null;
      state.savedRecord = null;
    },
    dismissSaveStatus: (state) => {
      state.saveSuccess = false;
      state.saveError = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(saveComplaintToDb.pending, (state) => {
        state.isSaving = true;
        state.saveSuccess = false;
        state.saveError = null;
      })
      .addCase(saveComplaintToDb.fulfilled, (state, action) => {
        state.isSaving = false;
        state.saveSuccess = true;
        state.savedRecord = action.payload;
        state.formData.complaint_id = action.payload.complaint_id;
        state.isDirty = false;
      })
      .addCase(saveComplaintToDb.rejected, (state, action) => {
        state.isSaving = false;
        state.saveSuccess = false;
        state.saveError = action.payload || 'Database save error';
      });
  },
});

export const {
  updateField,
  applyFormUpdates,
  clearRecentlyUpdated,
  populateFromAI,
  resetForm,
  dismissSaveStatus
} = complaintSlice.actions;
export default complaintSlice.reducer;
