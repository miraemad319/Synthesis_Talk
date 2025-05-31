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

  useEffect(() => {
    fetchVisualization();
  }, []);

  const fetchVisualization = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get("/visualize/");
      setData(res.data.data || []);
    } catch (err) {
      setError("Failed to load visualization.");
      setData([]);
    }
    setLoading(false);
  };

  return (
    <div className="p-4 flex-1 overflow-auto bg-white">
      <h2 className="text-lg font-semibold mb-2">Visualization</h2>
      {loading && <p className="text-gray-500">Loading chart...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && !error && data.length > 0 && (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart
            data={data}
            margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#4F46E5" />
          </BarChart>
        </ResponsiveContainer>
      )}

      {!loading && !error && data.length === 0 && (
        <p className="text-gray-500">No data to display.</p>
      )}
    </div>
  );
}
