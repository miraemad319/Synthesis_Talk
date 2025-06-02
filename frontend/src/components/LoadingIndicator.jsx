import React, { useState, useEffect, useRef } from 'react';
import { Loader2, FileText, Search, Brain, Download, Upload, MessageSquare } from 'lucide-react';
import api from '../utils/api';

const loadingMessages = {
  upload: [
    "Processing your document...",
    "Extracting key information...",
    "Analyzing content structure...",
    "Preparing document for analysis..."
  ],
  search: [
    "Searching the web...",
    "Finding relevant sources...",
    "Gathering information...",
    "Analyzing search results..."
  ],
  chat: [
    "Thinking through your question...",
    "Applying reasoning techniques...",
    "Synthesizing information...",
    "Generating response..."
  ],
  insights: [
    "Analyzing patterns...",
    "Extracting key insights...",
    "Connecting related concepts...",
    "Generating summaries..."
  ],
  export: [
    "Preparing export...",
    "Formatting document...",
    "Finalizing output...",
    "Almost ready..."
  ],
  visualize: [
    "Creating visualization...",
    "Processing data points...",
    "Generating charts...",
    "Rendering graphics..."
  ],
  default: [
    "Processing request...",
    "Working on it...",
    "Almost there...",
    "Just a moment..."
  ]
};

const getIconForType = (type) => {
  switch (type) {
    case 'upload': return Upload;
    case 'search': return Search;
    case 'chat': return MessageSquare;
    case 'insights': return Brain;
    case 'export': return Download;
    case 'visualize': return FileText;
    default: return Loader2;
  }
};

export default function LoadingIndicator() {
  const [loading, setLoading] = useState(false);
  const [loadingType, setLoadingType] = useState('default');
  const [currentMessage, setCurrentMessage] = useState('');
  const [messageIndex, setMessageIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const intervalRef = useRef(null);
  const progressRef = useRef(null);

  // Determine loading type from URL
  const getLoadingTypeFromUrl = (url) => {
    if (url.includes('/upload')) return 'upload';
    if (url.includes('/search')) return 'search';
    if (url.includes('/chat')) return 'chat';
    if (url.includes('/insights')) return 'insights';
    if (url.includes('/export')) return 'export';
    if (url.includes('/visualize')) return 'visualize';
    return 'default';
  };

  useEffect(() => {
    // Intercept requests to track loading state
    const req = api.interceptors.request.use(config => {
      const type = getLoadingTypeFromUrl(config.url || '');
      setLoadingType(type);
      setLoading(true);
      setMessageIndex(0);
      setProgress(0);
      return config;
    });

    const res = api.interceptors.response.use(
      response => {
        setLoading(false);
        setProgress(100);
        // Clear intervals
        if (intervalRef.current) clearInterval(intervalRef.current);
        if (progressRef.current) clearInterval(progressRef.current);
        return response;
      },
      error => {
        setLoading(false);
        setProgress(0);
        // Clear intervals
        if (intervalRef.current) clearInterval(intervalRef.current);
        if (progressRef.current) clearInterval(progressRef.current);
        return Promise.reject(error);
      }
    );

    return () => {
      api.interceptors.request.eject(req);
      api.interceptors.response.eject(res);
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (progressRef.current) clearInterval(progressRef.current);
    };
  }, []);

  // Cycle through loading messages
  useEffect(() => {
    if (loading) {
      const messages = loadingMessages[loadingType] || loadingMessages.default;
      setCurrentMessage(messages[0]);
      
      intervalRef.current = setInterval(() => {
        setMessageIndex(prev => {
          const next = (prev + 1) % messages.length;
          setCurrentMessage(messages[next]);
          return next;
        });
      }, 2000);

      // Simulate progress for better UX
      let progressValue = 0;
      progressRef.current = setInterval(() => {
        progressValue += Math.random() * 15;
        if (progressValue > 90) progressValue = 90; // Don't reach 100% until complete
        setProgress(progressValue);
      }, 500);

      return () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
        if (progressRef.current) clearInterval(progressRef.current);
      };
    }
  }, [loading, loadingType]);

  if (!loading) return null;

  const IconComponent = getIconForType(loadingType);

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm z-50">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4 text-center transform transition-all duration-300 scale-100">
        {/* Animated Icon */}
        <div className="mb-6 flex justify-center">
          <div className="relative">
            <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center animate-pulse">
              <IconComponent className="w-8 h-8 text-white animate-spin" />
            </div>
            {/* Ripple effect */}
            <div className="absolute inset-0 w-16 h-16 rounded-full border-4 border-blue-300 animate-ping opacity-30"></div>
          </div>
        </div>

        {/* Loading Message */}
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-2">
            {loadingType.charAt(0).toUpperCase() + loadingType.slice(1)} in Progress
          </h3>
          <p className="text-gray-600 animate-fade-in-out" key={currentMessage}>
            {currentMessage}
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-purple-600 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-sm text-gray-500 mt-2">{Math.round(progress)}% complete</p>
        </div>

        {/* Additional Context for Different Operations */}
        {loadingType === 'upload' && (
          <div className="text-sm text-gray-500 bg-blue-50 rounded-lg p-3">
            <p>We're extracting and analyzing your document content to enhance your research experience.</p>
          </div>
        )}
        
        {loadingType === 'search' && (
          <div className="text-sm text-gray-500 bg-green-50 rounded-lg p-3">
            <p>Searching across multiple sources to find the most relevant information for your query.</p>
          </div>
        )}
        
        {loadingType === 'chat' && (
          <div className="text-sm text-gray-500 bg-purple-50 rounded-lg p-3">
            <p>Applying advanced reasoning techniques to provide you with a comprehensive response.</p>
          </div>
        )}
        
        {loadingType === 'insights' && (
          <div className="text-sm text-gray-500 bg-yellow-50 rounded-lg p-3">
            <p>Analyzing patterns and connections across your research materials to generate insights.</p>
          </div>
        )}

        {loadingType === 'visualize' && (
          <div className="text-sm text-gray-500 bg-indigo-50 rounded-lg p-3">
            <p>Creating visual representations of your research data and findings.</p>
          </div>
        )}

        {loadingType === 'export' && (
          <div className="text-sm text-gray-500 bg-pink-50 rounded-lg p-3">
            <p>Preparing your research findings in the requested format for download.</p>
          </div>
        )}

        {/* Breathing dots animation */}
        <div className="flex justify-center space-x-1 mt-4">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>

       <style>{`
        @keyframes fade-in-out {
          0%, 100% { opacity: 0.7; }
          50% { opacity: 1; }
        }
        .animate-fade-in-out {
          animation: fade-in-out 2s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}