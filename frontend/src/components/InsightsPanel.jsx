import React, { useState, useEffect } from 'react';
import api from '../utils/api';

export default function InsightsPanel() {
  const [insights, setInsights] = useState('');
  const [format, setFormat] = useState('paragraph');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/insights');
      // assume API returns { paragraph: string, bullets: string[] }
      const data = res.data;
      setInsights(data);
    } catch (err) {
      setError('Failed to load insights.');
    }
    setLoading(false);
  };

  const renderContent = () => {
    if (!insights) return null;
    if (format === 'paragraph') {
      return <p className="whitespace-pre-line">{insights.paragraph}</p>;
    }
    // bullets
    return (
      <ul className="list-disc pl-5">
        {insights.bullets.map((b, i) => (
          <li key={i}>{b}</li>
        ))}
      </ul>
    );
  };

  return (
    <div className="p-4 border-b h-1/2 overflow-auto">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-lg font-semibold">Insights</h2>
        <div>
          <button
            onClick={() => setFormat('paragraph')}
            className={`px-2 py-1 mr-1 rounded ${format === 'paragraph' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            Paragraph
          </button>
          <button
            onClick={() => setFormat('bullets')}
            className={`px-2 py-1 rounded ${format === 'bullets' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            Bullets
          </button>
        </div>
      </div>
      {loading && <p>Loading insights...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loading && !error && renderContent()}
    </div>
  );
}