import { configureStore } from '@reduxjs/toolkit';
import complaintReducer from './slices/complaintSlice';
import aiCopilotReducer from './slices/aiCopilotSlice';

export const store = configureStore({
  reducer: {
    complaint: complaintReducer,
    aiCopilot: aiCopilotReducer,
  },
  devTools: process.env.NODE_ENV !== 'production',
});

export default store;
