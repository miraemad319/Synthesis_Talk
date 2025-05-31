import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'; // make sure you've installed recharts
import api from '../utils/api';

export default function VisualizationPanel() {
  // Ensure data always starts as an array
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchVisualization();
  }, []);

  const fetchVisualization = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/visualize');
      // If the backend returns { data: [...] }, use that.
      // Otherwise, fall back to an empty array.
      const incoming = res.data?.data;
      if (Array.isArray(incoming)) {
        setData(incoming);
      } else {
        setData([]);
      }
    } catch (err) {
      setError('Failed to load visualization.');
      setData([]); // reset to empty array on error
    }
    setLoading(false);
  };

  return (
    <div className="p-4 flex-1 overflow-auto">
      <h2 className="text-lg font-semibold mb-2">Visualization</h2>
      {loading && <p>Loading chart...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loading && !error && Array.isArray(data) && data.length > 0 && (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart
            data={data}
            margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      )}

      {/* If data is empty and there’s no error/loading, maybe show a placeholder */}
      {!loading && !error && (!Array.isArray(data) || data.length === 0) && (
        <p>No data to display.</p>
      )}
    </div>
  );
}
