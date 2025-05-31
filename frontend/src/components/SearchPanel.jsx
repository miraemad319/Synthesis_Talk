import React, { useState } from 'react';
import { MagnifyingGlassIcon, LinkIcon, CalendarIcon } from '@heroicons/react/24/outline';
import api from '../utils/api';

export default function SearchPanel() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchHistory, setSearchHistory] = useState([]);

  const performSearch = async (searchQuery = query) => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      const res = await api.post('/search/', { query: searchQuery });
      setResults(res.data.results || []);
      
      // Add to search history
      setSearchHistory(prev => [
        { query: searchQuery, timestamp: new Date() },
        ...prev.slice(0, 4) // Keep only last 5 searches
      ]);
      
    } catch (err) {
      console.error('Search error:', err);
      setError(err.userMessage || 'Search failed. Please try again.');
      setResults([]);
    }
    setLoading(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    performSearch();
  };

  const formatDate = (dateStr) => {
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return 'Recent';
    }
  };

  const truncateText = (text, maxLength = 150) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="p-4 flex-1 overflow-auto bg-white">
      <div className="mb-4">
        <h2 className="text-lg font-semibold mb-3">Web Search</h2>
        
        {/* Search Form */}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for additional information..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
          </div>
          
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Searching...' : 'Search Web'}
          </button>
        </form>

        {/* Search History */}
        {searchHistory.length > 0 && (
          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Recent Searches</h3>
            <div className="space-y-1">
              {searchHistory.map((item, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setQuery(item.query);
                    performSearch(item.query);
                  }}
                  className="w-full text-left text-sm text-gray-600 hover:text-blue-600 hover:bg-blue-50 px-2 py-1 rounded transition-colors"
                >
                  {item.query}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">Searching the web...</div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm mb-4">
          {error}
        </div>
      )}

      {/* Search Results */}
      {!loading && !error && results.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-700">
            Found {results.length} result{results.length !== 1 ? 's' : ''}
          </h3>
          
          {results.map((result, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="space-y-2">
                {/* Title and URL */}
                <div>
                  <h4 className="font-medium text-gray-900 hover:text-blue-600">
                    <a 
                      href={result.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-start gap-2"
                    >
                      <span className="flex-1">{result.title}</span>
                      <LinkIcon className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    </a>
                  </h4>
                  <div className="text-xs text-green-600 mt-1">{result.url}</div>
                </div>

                {/* Snippet/Description */}
                {result.snippet && (
                  <p className="text-sm text-gray-600 leading-relaxed">
                    {truncateText(result.snippet)}
                  </p>
                )}

                {/* Metadata */}
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  {result.publishedDate && (
                    <div className="flex items-center gap-1">
                      <CalendarIcon className="h-3 w-3" />
                      {formatDate(result.publishedDate)}
                    </div>
                  )}
                  {result.source && (
                    <div>Source: {result.source}</div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 pt-2">
                  <button
                    onClick={() => {
                      // Could integrate this with chat - send a message to analyze this result
                      const message = `Analyze this search result: "${result.title}" - ${result.snippet}`;
                      // This would require access to the chat function
                    }}
                    className="text-xs px-3 py-1 bg-blue-50 text-blue-600 rounded hover:bg-blue-100 transition-colors"
                  >
                    💬 Discuss
                  </button>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(`${result.title}\n${result.url}\n${result.snippet}`);
                    }}
                    className="text-xs px-3 py-1 bg-gray-50 text-gray-600 rounded hover:bg-gray-100 transition-colors"
                  >
                    📋 Copy
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && results.length === 0 && query && (
        <div className="text-center py-8">
          <div className="text-gray-500 mb-2">No results found</div>
          <div className="text-sm text-gray-400">
            Try different keywords or check your spelling
          </div>
        </div>
      )}

      {/* Initial State */}
      {!loading && !error && results.length === 0 && !query && (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <MagnifyingGlassIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <div className="text-gray-500 mb-2">Search the web for information</div>
            <div className="text-sm text-gray-400 max-w-sm mx-auto">
              Find additional sources, verify facts, or explore related topics to enhance your research
            </div>
          </div>
        </div>
      )}
    </div>
  );
}