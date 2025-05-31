import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import api from '../utils/api';

export default function VisualizationPanel() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasAttemptedLoad, setHasAttemptedLoad] = useState(false);

  // Don't auto-load on mount - wait for user interaction
  const fetchVisualization = async () => {
    setLoading(true);
    setError("");
    setHasAttemptedLoad(true);
    
    try {
      const res = await api.get("/visualize/");
      setData(res.data.data || []);
    } catch (err) {
      console.error('Visualization fetch error:', err);
      setError(err.userMessage || "Failed to load visualization.");
      setData([]);
    }
    setLoading(false);
  };

  const refreshVisualization = () => {
    fetchVisualization();
  };

  return (
    <div className="p-4 flex-1 overflow-auto bg-white">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Visualization</h2>
        <button
          onClick={refreshVisualization}
          disabled={loading}
          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Loading..." : hasAttemptedLoad ? "Refresh" : "Load Chart"}
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">Loading chart...</div>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm mb-4">
          {error}
        </div>
      )}

      {!loading && !error && hasAttemptedLoad && data.length > 0 && (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={data}
            margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="name" 
              fontSize={12}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis fontSize={12} />
            <Tooltip />
            <Bar dataKey="value" fill="#4F46E5" />
          </BarChart>
        </ResponsiveContainer>
      )}

      {!loading && !error && hasAttemptedLoad && data.length === 0 && (
        <div className="text-center py-8">
          <div className="text-gray-500 mb-2">No data to display</div>
          <div className="text-sm text-gray-400">
            Upload files and chat to generate visualizations
          </div>
        </div>
      )}

      {!hasAttemptedLoad && (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <div className="text-gray-500 mb-2">Ready to visualize your data</div>
            <div className="text-sm text-gray-400">
              Click "Load Chart" when you have data to visualize
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
