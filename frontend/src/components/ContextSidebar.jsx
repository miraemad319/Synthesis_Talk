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
      setContexts(res.data.contexts);
      setCurrent(res.data.current);
    } catch (err) {
      setError('Failed to load contexts.');
    }
    setLoading(false);
  };

  const switchContext = async (id) => {
    setLoading(true);
    try {
      await api.post('/context/', { context_id: id });
      setCurrent(id);
    } catch {
      setError('Failed to switch context.');
    }
    setLoading(false);
  };

  return (
    <div className="w-64 p-4 border-r overflow-auto bg-white">
      <h2 className="text-lg font-semibold mb-4">Research Contexts</h2>
      {loading && <p className="text-gray-500">Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}
      <ul className="space-y-2">
        {contexts.map((ctx) => (
          <li key={ctx.id}>
            <button
              onClick={() => switchContext(ctx.id)}
              className={`w-full text-left p-2 rounded ${
                ctx.id === current ? 'bg-blue-500 text-white' : 'bg-gray-100'
              }`}
            >
              {ctx.topic}
            </button>
            {ctx.id === current && ctx.sources.length > 0 && (
              <ul className="mt-1 ml-4 list-disc text-sm">
                {ctx.sources.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
});

export default ContextSidebar;

