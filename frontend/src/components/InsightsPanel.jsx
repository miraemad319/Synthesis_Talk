import React, { useState, useEffect } from 'react';
import api from '../utils/api';

export default function InsightsPanel() {
  const [insights, setInsights] = useState({ paragraph: "", bullets: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [mode, setMode] = useState("paragraph"); // or "bullets"

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get("/insights/");
      setInsights({
        paragraph: res.data.paragraph || "",
        bullets: res.data.bullets || [],
      });
    } catch (err) {
      setError("Failed to load insights.");
    }
    setLoading(false);
  };

  return (
    <div className="p-4 flex-1 overflow-auto bg-white">
      <h2 className="text-lg font-semibold mb-2">Insights</h2>

      <div className="mb-4 space-x-2">
        <button
          onClick={() => setMode("paragraph")}
          className={`px-4 py-1 rounded ${
            mode === "paragraph" ? "bg-blue-500 text-white" : "bg-gray-200"
          }`}
        >
          Paragraph
        </button>
        <button
          onClick={() => setMode("bullets")}
          className={`px-4 py-1 rounded ${
            mode === "bullets" ? "bg-blue-500 text-white" : "bg-gray-200"
          }`}
        >
          Bullets
        </button>
      </div>

      {loading && <p className="text-gray-500">Loading insights...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && !error && mode === "paragraph" && (
        <p className="text-gray-800">{insights.paragraph}</p>
      )}

      {!loading && !error && mode === "bullets" && (
        <ul className="list-disc ml-5 text-gray-800 space-y-1">
          {insights.bullets.map((b, i) => (
            <li key={i}>{b}</li>
          ))}
        </ul>
      )}

      {/* If both paragraph and bullets are empty, show a placeholder */}
      {!loading && !error && !insights.paragraph && insights.bullets.length === 0 && (
        <p className="text-gray-500">No insights to display.</p>
      )}
    </div>
  );
}
