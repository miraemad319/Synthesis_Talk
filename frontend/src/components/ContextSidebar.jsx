import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import api from '../utils/api';

const ContextSidebar = forwardRef((props, ref) => {
  const [contexts, setContexts] = useState([]);
  const [current, setCurrent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Expose fetchContexts so parent can call it
  useImperativeHandle(ref, () => ({ fetchContexts }));

  useEffect(() => {
    fetchContexts();
  }, []);

  const fetchContexts = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/context/');
      setContexts(res.data.contexts || []);
      setCurrent(res.data.current || null);
    } catch (err) {
      console.error('Context fetch error:', err);
      setError(err.userMessage || 'Failed to load contexts.');
      // Set some mock data for development
      setContexts([
        { 
          id: 'getting-started', 
          topic: 'Getting Started', 
          sources: ['Lecture 15 Computational Intelligence (Rev).docx'] 
        }
      ]);
      setCurrent('getting-started');
    }
    setLoading(false);
  };

  const switchContext = async (id) => {
    setLoading(true);
    setError('');
    try {
      await api.post('/context/', { context_id: id });
      setCurrent(id);
    } catch (err) {
      console.error('Context switch error:', err);
      setError(err.userMessage || 'Failed to switch context.');
      // For development, still update the UI
      setCurrent(id);
    }
    setLoading(false);
  };

  return (
    <div className="h-full p-4 overflow-auto">
      <h2 className="text-lg font-semibold mb-4">Research Contexts</h2>
      
      {loading && <p className="text-gray-500 text-sm">Loading...</p>}
      {error && (
        <div className="mb-4 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}
      
      <div className="space-y-2">
        {contexts.map((ctx) => (
          <div key={ctx.id}>
            <button
              onClick={() => switchContext(ctx.id)}
              className={`w-full text-left p-3 rounded-lg transition-colors ${
                ctx.id === current 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              <div className="font-medium">{ctx.topic}</div>
              {ctx.sources && ctx.sources.length > 0 && (
                <div className="text-xs mt-1 opacity-75">
                  {ctx.sources.length} file{ctx.sources.length !== 1 ? 's' : ''}
                </div>
              )}
            </button>
            
            {ctx.id === current && ctx.sources && ctx.sources.length > 0 && (
              <div className="mt-2 ml-4 space-y-1">
                {ctx.sources.map((source, i) => (
                  <div key={i} className="text-xs text-gray-600 flex items-center">
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-2"></span>
                    {source}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      
      {contexts.length === 0 && !loading && (
        <p className="text-gray-500 text-sm mt-4">
          No contexts available. Upload a file to get started.
        </p>
      )}
    </div>
  );
});

ContextSidebar.displayName = 'ContextSidebar';

export default ContextSidebar;

