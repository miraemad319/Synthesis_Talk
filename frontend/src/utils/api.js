// src/utils/api.js - FIXED VERSION

import axios from 'axios';

const api = axios.create({
  // FIXED: Use environment variable properly
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
  timeout: 120000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request counter for tracking concurrent requests
let activeRequests = 0;

// Add request interceptor for debugging and request management
api.interceptors.request.use(
  (config) => {
    activeRequests++;
    
    // Generate unique request ID for tracking
    const requestId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    config.metadata = { requestId, startTime: Date.now() };
    
    console.log('API Request:', {
      id: requestId,
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
      fullURL: `${config.baseURL}${config.url}`,
      activeRequests,
      timeout: config.timeout
    });
    
    return config;
  },
  (error) => {
    activeRequests = Math.max(0, activeRequests - 1);
    console.error('Request Setup Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for better error handling and performance tracking
api.interceptors.response.use(
  (response) => {
    activeRequests = Math.max(0, activeRequests - 1);
    
    const duration = response.config.metadata 
      ? Date.now() - response.config.metadata.startTime 
      : 'unknown';
    
    console.log('API Response:', {
      id: response.config.metadata?.requestId,
      status: response.status,
      url: response.config.url,
      duration: `${duration}ms`,
      activeRequests,
      dataSize: JSON.stringify(response.data).length
    });
    
    return response;
  },
  (error) => {
    activeRequests = Math.max(0, activeRequests - 1);
    
    const duration = error.config?.metadata 
      ? Date.now() - error.config.metadata.startTime 
      : 'unknown';
    
    console.error('API Error:', {
      id: error.config?.metadata?.requestId,
      message: error.message,
      code: error.code,
      status: error.response?.status,
      url: error.config?.url,
      baseURL: error.config?.baseURL,
      duration: `${duration}ms`,
      activeRequests
    });
    
    // Enhanced error message handling
    if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      error.userMessage = 'Unable to connect to server. Please check if the backend is running on http://localhost:8000';
    } else if (error.code === 'ECONNABORTED') {
      error.userMessage = 'Request timed out. The operation may be taking longer than expected.';
    } else if (error.response?.status === 400) {
      error.userMessage = error.response?.data?.detail || 'Invalid request. Please check your input.';
    } else if (error.response?.status === 401) {
      error.userMessage = 'Authentication required. Please refresh the page.';
    } else if (error.response?.status === 403) {
      error.userMessage = 'Access denied. You may not have permission for this operation.';
    } else if (error.response?.status === 404) {
      error.userMessage = 'API endpoint not found. The service may be unavailable.';
    } else if (error.response?.status === 429) {
      error.userMessage = 'Too many requests. Please wait a moment before trying again.';
    } else if (error.response?.status >= 500) {
      error.userMessage = 'Server error. Please try again later or contact support.';
    } else {
      error.userMessage = error.response?.data?.detail || error.response?.data?.message || 'An unexpected error occurred.';
    }
    
    // Add retry suggestion for certain errors
    if (error.code === 'ECONNABORTED' || (error.response?.status >= 500 && error.response?.status < 600)) {
      error.canRetry = true;
    }
    
    return Promise.reject(error);
  }
);

// FIXED: Specialized API methods for SynthesisTalk with proper endpoint paths
export const synthesisAPI = {
  // Chat operations
  chat: {
    send: (message, context = {}) => 
      api.post('/chat/', { message, ...context }),
    
    getHistory: () => 
      api.get('/chat/history'),
    
    clearHistory: () => 
      api.post('/chat/clear'),
    
    provideFeedback: (feedback) =>
      api.post('/chat/feedback', feedback)
  },
  
  // Document operations - FIXED: Use proper endpoints
  documents: {
    upload: (file, format = 'paragraph', onProgress) => {
      const formData = new FormData();
      formData.append('file', file);
      const url = `/upload/?format=${format}`;
      return apiUtils.uploadWithProgress(url, formData, onProgress);
    },
    
    getHistory: () => 
      api.get('/upload/sessions'),
    
    remove: (filename) => 
      api.delete(`/upload/${encodeURIComponent(filename)}`)
  },
  
  // Search operations - FIXED: Use proper query parameters
  search: {
    web: (query, filters = {}) => 
      api.get('/search/', { params: { query, ...filters } }),
    
    documents: (query, filters = {}) => 
      api.post('/search/documents', { query, ...filters }),
    
    combined: (query, filters = {}) => 
      api.post('/search/combined', { query, ...filters }),
    
    verify: (claim) =>
      api.post('/search/verify/', null, { params: { claim } })
  },
  
  // Insights and analysis - FIXED: Handle async task-based insights
  insights: {
    generate: async (insight_type = 'comprehensive') => {
      // Start background task
      const startResponse = await api.post('/insights/', null, {
        params: { insight_type }
      });
      
      // Return task ID for polling
      return startResponse;
    },
    
    status: (taskId) =>
      api.get(`/insights/status/${taskId}`),
    
    // Helper method to generate and wait for completion
    generateAndWait: async (insight_type = 'comprehensive', pollInterval = 2000, maxWait = 120000) => {
      const startResponse = await synthesisAPI.insights.generate(insight_type);
      const taskId = startResponse.data.task_id;
      
      const startTime = Date.now();
      
      while (Date.now() - startTime < maxWait) {
        const statusResponse = await synthesisAPI.insights.status(taskId);
        const status = statusResponse.data;
        
        if (status.status === 'completed') {
          return status.result;
        }
        
        if (status.status === 'failed') {
          throw new Error(status.message || 'Insight generation failed');
        }
        
        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      }
      
      throw new Error('Insight generation timed out');
    },
    
    getSummary: (format = 'default') => 
      api.get(`/insights/summary?format=${format}`)
  },
  
  // Visualization - FIXED: Proper endpoint paths
  visualization: {
    generate: (type = 'auto', data = {}) => 
      api.post('/visualize/', { type, ...data }),
    
    getKeywords: (top_k = 10) =>
      api.get('/visualize/keywords', { params: { top_k } }),
    
    getSources: () =>
      api.get('/visualize/sources'),
    
    getConversationFlow: () =>
      api.get('/visualize/conversation-flow'),
    
    getTopicAnalysis: () =>
      api.get('/visualize/topic-analysis'),
    
    getResearchTimeline: () =>
      api.get('/visualize/research-timeline'),
    
    getAvailable: () =>
      api.get('/visualize/')
  },
  
  // Export operations - FIXED: Handle blob responses properly
  export: {
    conversation: (format = 'txt', include_metadata = true) => 
      api.get('/export/', { 
        params: { format, include_metadata },
        responseType: 'blob' 
      }),
    
    preview: (format = 'txt', lines = 20) =>
      api.get('/export/preview', { params: { format, lines } }),
    
    formats: () => 
      api.get('/export/formats')
  },
  
  // Context management - FIXED: Proper request formats
  context: {
    get: () => api.get('/context/'),
    
    switch: (context_id) => api.post('/context/', { context_id }),
    
    create: (topic, description = '') => 
      api.post('/context/new', { topic, description }),
    
    update: (context_id, updates) => 
      api.put(`/context/${context_id}`, updates),
    
    delete: (context_id) => 
      api.delete(`/context/${context_id}`),
    
    getSummary: (context_id) =>
      api.get(`/context/${context_id}/summary`),
    
    getCurrent: () =>
      api.get('/context/current')
  },
  
  // Tools and utilities - FIXED: Proper parameter passing
  tools: {
    list: () => api.get('/tools/available/'),
    
    note: (note, category = 'general', tags = []) => 
      api.post('/tools/note/', { note, category, tags }),
    
    explain: (query, detail_level = 'medium', format = 'paragraph') => 
      api.post('/tools/explain/', { query, detail_level, format }),
    
    organize: (content_type = 'notes', organization_method = 'topic') => 
      api.post('/tools/organize/', { content_type, organization_method }),
    
    analyze: (analysis_type, focus_areas = [], output_format = 'structured') =>
      api.post('/tools/analyze/', { analysis_type, focus_areas, output_format }),
    
    getRecommendations: (query) =>
      api.get('/tools/recommendations/', { params: { query } }),
    
    getUsageStats: () =>
      api.get('/tools/usage/')
  }
};

// Utility functions for the API
export const apiUtils = {
  // Get active request count
  getActiveRequestCount: () => activeRequests,
  
  // Health check with better error reporting
  healthCheck: async () => {
    try {
      // Test both root and health endpoints
      const response = await api.get('/health', { timeout: 5000 });
      return { healthy: true, response };
    } catch (error) {
      console.error('Health check failed:', error);
      return { 
        healthy: false, 
        error: error.userMessage || error.message,
        suggestion: error.code === 'ECONNREFUSED' 
          ? 'Make sure the backend server is running on http://localhost:8000' 
          : 'Check network connection and server status'
      };
    }
  },
  
  // Upload file with progress tracking
  uploadWithProgress: (url, formData, onProgress) => {
    return api.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress?.(percentCompleted);
      },
      timeout: 300000, // 5 minutes for file uploads
    });
  },
  
  // Test all major endpoints
  testEndpoints: async () => {
    const results = {};
    const endpoints = [
      { name: 'Health', path: '/health' },
      { name: 'Context', path: '/context/' },
      { name: 'Upload Test', path: '/upload/test' },
      { name: 'Chat Test', path: '/chat/test' },
      { name: 'Visualizations', path: '/visualize/' },
      { name: 'Export Formats', path: '/export/formats' }
    ];
    
    for (const endpoint of endpoints) {
      try {
        const response = await api.get(endpoint.path, { timeout: 10000 });
        results[endpoint.name] = { 
          status: 'success', 
          code: response.status,
          data: response.data 
        };
      } catch (error) {
        results[endpoint.name] = { 
          status: 'failed', 
          error: error.userMessage || error.message,
          code: error.response?.status || 'NO_RESPONSE'
        };
      }
    }
    
    return results;
  },
  
  // Connection diagnostics
  diagnoseConnection: async () => {
    const diagnosis = {
      timestamp: new Date().toISOString(),
      baseURL: api.defaults.baseURL,
      issues: [],
      suggestions: []
    };
    
    try {
      // Test basic connectivity
      const response = await fetch(api.defaults.baseURL.replace('/api/v1', ''), {
        method: 'GET',
        mode: 'cors',
        credentials: 'include'
      });
      
      if (!response.ok) {
        diagnosis.issues.push(`Server returned ${response.status}: ${response.statusText}`);
      }
      
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        diagnosis.issues.push('Cannot reach server - connection refused');
        diagnosis.suggestions.push('Ensure backend server is running on http://localhost:8000');
        diagnosis.suggestions.push('Check if port 8000 is not blocked by firewall');
      } else {
        diagnosis.issues.push(`Connection error: ${error.message}`);
      }
    }
    
    // Test CORS
    try {
      await api.get('/health', { timeout: 5000 });
    } catch (error) {
      if (error.message.includes('CORS')) {
        diagnosis.issues.push('CORS policy blocking requests');
        diagnosis.suggestions.push('Verify CORS configuration in backend allows localhost:3000');
      }
    }
    
    return diagnosis;
  }
};

export default api;