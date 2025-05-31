import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 120000, // Increased timeout for LLM operations
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request counter for tracking concurrent requests
let activeRequests = 0;

// Request queue for managing concurrent operations
const requestQueue = new Map();

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
      error.userMessage = 'Unable to connect to server. Please check if the backend is running on the correct port.';
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

// Utility functions for the API
export const apiUtils = {
  // Get active request count
  getActiveRequestCount: () => activeRequests,
  
  // Cancel all pending requests
  cancelAllRequests: () => {
    requestQueue.forEach((source) => {
      source.cancel('Operation cancelled by user');
    });
    requestQueue.clear();
  },
  
  // Create a cancellable request
  createCancellableRequest: (requestConfig) => {
    const source = axios.CancelToken.source();
    const requestId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    requestQueue.set(requestId, source);
    
    const request = api({
      ...requestConfig,
      cancelToken: source.token
    }).finally(() => {
      requestQueue.delete(requestId);
    });
    
    return {
      request,
      cancel: () => source.cancel('Request cancelled'),
      requestId
    };
  },
  
  // Check if server is reachable
  healthCheck: async () => {
    try {
      const response = await api.get('/health', { timeout: 5000 });
      return { healthy: true, response };
    } catch (error) {
      return { healthy: false, error };
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
  
  // Stream response for chat
  streamResponse: async (url, data, onData, onError) => {
    try {
      const response = await fetch(`${api.defaults.baseURL}${url}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...api.defaults.headers,
        },
        body: JSON.stringify(data),
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.trim() && line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              onData(data);
            } catch (e) {
              console.warn('Failed to parse SSE data:', line);
            }
          }
        }
      }
    } catch (error) {
      onError(error);
    }
  }
};

// Specialized API methods for SynthesisTalk
export const synthesisAPI = {
  // Chat operations
  chat: {
    send: (message, context = {}) => 
      api.post('/chat/', { message, ...context }),
    
    stream: (message, context = {}, onData, onError) =>
      apiUtils.streamResponse('/chat/stream', { message, ...context }, onData, onError),
    
    getHistory: (sessionId) => 
      api.get(`/chat/history/${sessionId}`),
    
    clearHistory: (sessionId) => 
      api.delete(`/chat/history/${sessionId}`)
  },
  
  // Document operations
  documents: {
    upload: (file, onProgress) => {
      const formData = new FormData();
      formData.append('file', file);
      return apiUtils.uploadWithProgress('/upload/', formData, onProgress);
    },
    
    list: () => api.get('/documents/'),
    
    delete: (fileId) => api.delete(`/documents/${fileId}`),
    
    analyze: (fileId) => api.post(`/documents/${fileId}/analyze`),
    
    extract: (fileId) => api.get(`/documents/${fileId}/extract`)
  },
  
  // Search operations
  search: {
    web: (query, filters = {}) => 
      api.post('/search/web', { query, ...filters }),
    
    documents: (query, filters = {}) => 
      api.post('/search/documents', { query, ...filters }),
    
    combined: (query, filters = {}) => 
      api.post('/search/combined', { query, ...filters })
  },
  
  // Insights and analysis
  insights: {
    generate: (context = {}) => 
      api.post('/insights/', context),
    
    getTopics: () => 
      api.get('/insights/topics'),
    
    getConnections: () => 
      api.get('/insights/connections'),
    
    getSummary: (format = 'default') => 
      api.get(`/insights/summary?format=${format}`)
  },
  
  // Visualization
  visualization: {
    generate: (type = 'auto', data = {}) => 
      api.post('/visualize/', { type, ...data }),
    
    getChart: (chartId) => 
      api.get(`/visualize/${chartId}`),
    
    getTypes: () => 
      api.get('/visualize/types')
  },
  
  // Export operations
  export: {
    pdf: (format = 'summary') => 
      api.get(`/export/pdf?format=${format}`, { responseType: 'blob' }),
    
    markdown: (format = 'summary') => 
      api.get(`/export/markdown?format=${format}`),
    
    json: () => 
      api.get('/export/json'),
    
    formats: () => 
      api.get('/export/formats')
  },
  
  // Context management
  context: {
    get: () => api.get('/context/'),
    
    update: (context) => api.put('/context/', context),
    
    clear: () => api.delete('/context/'),
    
    addSource: (source) => api.post('/context/sources', source),
    
    removeSource: (sourceId) => api.delete(`/context/sources/${sourceId}`)
  },
  
  // Tools and utilities
  tools: {
    list: () => api.get('/tools/'),
    
    execute: (toolName, params = {}) => 
      api.post(`/tools/${toolName}`, params),
    
    getStatus: (toolName) => 
      api.get(`/tools/${toolName}/status`)
  }
};

export default api;



