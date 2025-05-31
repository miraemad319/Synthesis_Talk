import React, { useState } from 'react';
import api from '../utils/api';

export default function InsightsPanel() {
  const [insights, setInsights] = useState({ paragraph: "", bullets: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [mode, setMode] = useState("paragraph");
  const [hasAttemptedLoad, setHasAttemptedLoad] = useState(false);

  const fetchInsights = async () => {
    setLoading(true);
    setError("");
    setHasAttemptedLoad(true);
    
    try {
      const res = await api.get("/insights/");
      setInsights({
        paragraph: res.data.paragraph || "",
        bullets: res.data.bullets || [],
      });
    } catch (err) {
      console.error('Insights fetch error:', err);
      setError(err.userMessage || "Failed to load insights.");
    }
    setLoading(false);
  };

  const refreshInsights = () => {
    fetchInsights();
  };

  return (
    <div className="p-4 flex-1 overflow-auto bg-white">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Insights</h2>
        <button
          onClick={refreshInsights}
          disabled={loading}
          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Loading..." : hasAttemptedLoad ? "Refresh" : "Generate"}
        </button>
      </div>

      {hasAttemptedLoad && (
        <div className="mb-4 space-x-2">
          <button
            onClick={() => setMode("paragraph")}
            className={`px-4 py-1 rounded text-sm ${
              mode === "paragraph" ? "bg-blue-500 text-white" : "bg-gray-200 hover:bg-gray-300"
            }`}
          >
            Paragraph
          </button>
          <button
            onClick={() => setMode("bullets")}
            className={`px-4 py-1 rounded text-sm ${
              mode === "bullets" ? "bg-blue-500 text-white" : "bg-gray-200 hover:bg-gray-300"
            }`}
          >
            Bullets
          </button>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">Generating insights...</div>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm mb-4">
          {error}
        </div>
      )}

      {!loading && !error && hasAttemptedLoad && mode === "paragraph" && (
        <div className="text-gray-800 leading-relaxed">
          {insights.paragraph || "No paragraph insights available."}
        </div>
      )}

      {!loading && !error && hasAttemptedLoad && mode === "bullets" && (
        <ul className="list-disc ml-5 text-gray-800 space-y-2">
          {insights.bullets.length > 0 ? (
            insights.bullets.map((bullet, i) => (
              <li key={i} className="leading-relaxed">{bullet}</li>
            ))
          ) : (
            <li className="text-gray-500">No bullet point insights available.</li>
          )}
        </ul>
      )}

      {!hasAttemptedLoad && (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <div className="text-gray-500 mb-2">Ready to generate insights</div>
            <div className="text-sm text-gray-400">
              Upload files and click "Generate" to create insights
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
