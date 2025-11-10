import axios from 'axios';

// Create axios instance - Updated to use direct backend URLs
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8005';
// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const authApi = {
  register: (email, password) =>
    axios.post(`${baseUrl}/api/auth/register`, { email, password }),
  
  login: (email, password) =>
    axios.post(`${baseUrl}/api/auth/login`, { email, password }),
  
  getMe: () => axios.get(`${baseUrl}/api/auth/me`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('auth_token')}`
    }
  }),
};

// Document endpoints
export const documentsApi = {
  upload: (file, summaryLlmProvider = 'gpt', summaryLlmModel = 'gpt-4o-mini') => {
    const formData = new FormData();
    formData.append('file', file);
    // Note: embedding_provider is ALWAYS openai_small (text-embedding-3-small) - handled by backend
    formData.append('summary_llm_provider', summaryLlmProvider);
    formData.append('summary_llm_model', summaryLlmModel);
    
    // Log what we're sending for debugging
    console.log('Uploading document with:', {
      llm_provider: summaryLlmProvider,
      llm_model: summaryLlmModel,
      embedding: 'openai_small (text-embedding-3-small) - fixed'
    });
    
    const token = localStorage.getItem('auth_token');
    return axios.post(`${baseUrl}/api/documents/upload`, formData, {
      headers: { 
        'Content-Type': 'multipart/form-data',
        Authorization: `Bearer ${token}`
      },
    });
  },
  
  list: () => {
    const token = localStorage.getItem('auth_token');
    return axios.get(`${baseUrl}/api/documents`, {
      headers: { Authorization: `Bearer ${token}` }
    });
  },
  
  get: (docId) => {
    const token = localStorage.getItem('auth_token');
    return axios.get(`${baseUrl}/api/documents/${docId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
  },
  
  delete: (docId) => {
    const token = localStorage.getItem('auth_token');
    return axios.delete(`${baseUrl}/api/documents/${docId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
  },

  getPdf: (docId) => {
    const token = localStorage.getItem('auth_token');
    return axios.get(`${baseUrl}/api/documents/${docId}/pdf`, {
      headers: { Authorization: `Bearer ${token}` },
      responseType: 'blob'
    });
  },
};

// Page endpoints
export const pagesApi = {
  list: (docId, offset = 0, limit = 100) => {
    const token = localStorage.getItem('auth_token');
    return axios.get(`${baseUrl}/api/documents/${docId}/pages`, { 
      params: { offset, limit },
      headers: { Authorization: `Bearer ${token}` }
    });
  },
  
  get: (docId, pageNo) => {
    const token = localStorage.getItem('auth_token');
    return axios.get(`${baseUrl}/api/documents/${docId}/page/${pageNo}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
  },
  
  getPreview: (docId, pageNo) => {
    const token = localStorage.getItem('auth_token');
    return axios.get(`${baseUrl}/api/documents/${docId}/page/${pageNo}/preview`, {
      headers: { Authorization: `Bearer ${token}` },
      responseType: 'blob'
    });
  },
};

// Q&A endpoints
export const qaApi = {
  ask: (docId, pageNo, question, scopeMode, llmProvider, llmModel, embeddingProvider) => {
    const token = localStorage.getItem('auth_token');
    const url = `${baseUrl}/api/documents/${docId}/page/${pageNo}/qa`;
    
    const body = {
      question,
      scope_mode: scopeMode,
      llm_provider: llmProvider,
      llm_model: llmModel,
      embedding_provider: embeddingProvider,
    };
    
    return { url, body, token };
  },
  
  getDocumentQA: (docId, offset = 0, limit = 50) => {
    const token = localStorage.getItem('auth_token');
    return axios.get(`${baseUrl}/api/documents/${docId}/qa`, { 
      params: { offset, limit },
      headers: { Authorization: `Bearer ${token}` }
    });
  },
};

// Search endpoints
export const searchApi = {
  search: (query, docId = null, limit = 20) => {
    const token = localStorage.getItem('auth_token');
    return axios.get(`${baseUrl}/api/search`, { 
      params: { q: query, doc_id: docId, limit },
      headers: { Authorization: `Bearer ${token}` }
    });
  },
};

// Providers endpoints
export const providersApi = {
  getProviders: () => {
    const token = localStorage.getItem('auth_token');
    return axios.get(`${baseUrl}/api/documents/providers`, {
      headers: { Authorization: `Bearer ${token}` }
    });
  },
};

export default api;

