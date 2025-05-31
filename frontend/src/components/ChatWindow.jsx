import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat';
import { useTypewriter } from '../hooks/useTypewriter';
import { PaperAirplaneIcon, TrashIcon, ClipboardDocumentIcon } from '@heroicons/react/24/outline';

export default function ChatWindow() {
  const { messages, sendMessage, loading, error, clearChat } = useChat();
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when not loading
  useEffect(() => {
    if (!loading) {
      inputRef.current?.focus();
    }
  }, [loading]);

  // We will track the last bot reply and animate it
  const lastMessage = messages.length ? messages[messages.length - 1] : null;
  const isLastBot = lastMessage && lastMessage.bot;
  const typedReply = useTypewriter(isLastBot ? lastMessage.bot : "", 20);

  // Update typing state based on typewriter progress
  useEffect(() => {
    if (isLastBot && typedReply.length < lastMessage.bot.length) {
      setIsTyping(true);
    } else {
      setIsTyping(false);
    }
  }, [isLastBot, typedReply, lastMessage]);

  const onSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    sendMessage(input.trim());
    setInput("");
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit(e);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      // Could add a toast notification here
    });
  };

  const formatMessage = (text) => {
    // Basic markdown-like formatting
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 rounded">$1</code>');
  };

  return (
    <div className="flex flex-col flex-1 p-4 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-2 border-b">
        <div>
          <h1 className="text-xl font-semibold text-gray-800">SynthesisTalk</h1>
          <p className="text-sm text-gray-500">AI Research Assistant</p>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            title="Clear conversation"
          >
            <TrashIcon className="h-4 w-4" />
            Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <div className="text-gray-500 mb-2">Welcome to SynthesisTalk!</div>
              <div className="text-sm text-gray-400 max-w-md mx-auto">
                Start by uploading documents or asking questions about your research topic. 
                I can help you analyze, synthesize, and explore complex information.
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, i) => {
          // If it's a user message
          if (msg.user) {
            return (
              <div key={i} className="flex justify-end">
                <div className="max-w-xs lg:max-w-md">
                  <div className="bg-blue-500 text-white px-4 py-3 rounded-2xl rounded-br-md shadow-sm">
                    <div className="whitespace-pre-wrap">{msg.user}</div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1 text-right">
                    {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            );
          }
          
          // If it's a bot message
          if (msg.bot) {
            // If this is the last message, use typedReply
            const content = i === messages.length - 1 ? typedReply : msg.bot;
            const isError = msg.bot.startsWith('Error:');
            
            return (
              <div key={i} className="flex justify-start">
                <div className="max-w-xs lg:max-w-2xl">
                  <div className="flex items-start gap-3">
                    {/* Bot avatar */}
                    <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                      AI
                    </div>
                    
                    <div className="flex-1">
                      <div className={`px-4 py-3 rounded-2xl rounded-bl-md shadow-sm ${
                        isError ? 'bg-red-50 text-red-800 border border-red-200' : 'bg-gray-100 text-gray-800'
                      }`}>
                        <div 
                          className="whitespace-pre-wrap"
                          dangerouslySetInnerHTML={{ __html: formatMessage(content) }}
                        />
                        
                        {/* Show typing indicator */}
                        {i === messages.length - 1 && isTyping && (
                          <span className="inline-block w-2 h-4 bg-gray-400 ml-1 animate-pulse">|</span>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-2 mt-1">
                        <div className="text-xs text-gray-500">
                          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                        {!isError && (
                          <button
                            onClick={() => copyToClipboard(msg.bot)}
                            className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
                            title="Copy message"
                          >
                            <ClipboardDocumentIcon className="h-3 w-3" />
                            Copy
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          }
          return null;
        })}
        
        {/* Loading indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                AI
              </div>
              <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-md">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Error display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <strong>Connection Error:</strong> {error}
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={onSubmit} className="flex gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={inputRef}
            className="w-full border border-gray-300 rounded-lg px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            placeholder="Ask me about your research, upload documents, or request analysis..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
            rows={1}
            style={{ minHeight: '52px', maxHeight: '120px' }}
            onInput={(e) => {
              e.target.style.height = 'auto';
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
            }}
          />
          <button
            type="submit"
            className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            disabled={loading || !input.trim()}
          >
            <PaperAirplaneIcon className="h-4 w-4" />
          </button>
        </div>
      </form>

      {/* Quick Actions */}
      <div className="flex gap-2 mt-2">
        <button
          onClick={() => setInput("Summarize the key points from my uploaded documents")}
          className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
          disabled={loading}
        >
          📄 Summarize Docs
        </button>
        <button
          onClick={() => setInput("What are the main themes in this research?")}
          className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
          disabled={loading}
        >
          🎯 Find Themes
        </button>
        <button
          onClick={() => setInput("Generate insights and connections from the content")}
          className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
          disabled={loading}
        >
          💡 Generate Insights
        </button>
      </div>
    </div>
  );
}
