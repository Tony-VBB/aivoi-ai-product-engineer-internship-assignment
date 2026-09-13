import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60s for LLM processing
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    // Resilient host failover: if port 8000 drops connection due to host system conflict, retry on 8001
    if (
      config &&
      !config._retried &&
      (!error.response || error.code === 'ERR_NETWORK' || error.code === 'ECONNRESET' || error.code === 'ECONNABORTED' || (error.message && error.message.includes('Network Error')))
    ) {
      const currentBase = config.baseURL || API_BASE_URL;
      if (currentBase.includes(':8000')) {
        config._retried = true;
        config.baseURL = currentBase.replace(':8000', ':8001');
        try {
          return await axios(config);
        } catch (retryErr) {
          error = retryErr;
        }
      }
    }

    const detail = error.response?.data?.detail;
    let errorMsg = 'An unexpected network or server error occurred.';
    if (typeof detail === 'string') {
      errorMsg = detail;
    } else if (Array.isArray(detail)) {
      errorMsg = detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
    } else if (detail && typeof detail === 'object') {
      errorMsg = JSON.stringify(detail);
    } else if (error.message) {
      errorMsg = error.message;
    }
    return Promise.reject(new Error(errorMsg));
  }
);

export const api = {
  getHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  analyzeDocument: async (file, onUploadProgress, threadId) => {
    const formData = new FormData();
    formData.append('file', file);
    if (threadId) {
      formData.append('thread_id', threadId);
    }

    const res = await apiClient.post('/api/ai/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    });
    return res.data;
  },

  sendCopilotMessage: async (threadId, message, formData = null) => {
    const payload = {
      thread_id: threadId,
      message,
    };
    if (formData) {
      payload.form_data = formData;
    }
    const res = await apiClient.post('/api/ai/chat', payload);
    return res.data;
  },

  saveComplaint: async (complaintData) => {
    const res = await apiClient.post('/api/complaints', complaintData);
    return res.data;
  },

  listComplaints: async () => {
    const res = await apiClient.get('/api/complaints');
    return res.data;
  },

  getComplaint: async (id) => {
    const res = await apiClient.get(`/api/complaints/${id}`);
    return res.data;
  },
};

export default api;
