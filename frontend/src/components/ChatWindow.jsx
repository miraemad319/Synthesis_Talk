import React, { useState, useEffect, useRef } from 'react';
import { useChat } from '../hooks/useChat';

export default function ChatWindow() {
  const { messages, sendMessage, loading } = useChat();
  const [input, setInput] = useState('');
  const containerRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  const onSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage(input);
    setInput('');
  };

  return (
    <div className="flex-1 p-4 overflow-auto flex flex-col" ref={containerRef}>
      <div className="flex-1 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.user ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs p-2 rounded-lg ${msg.user ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-900'}`}
            >
              {msg.user || msg.bot}
            </div>
          </div>
        ))}
      </div>
      <form onSubmit={onSubmit} className="mt-4 flex items-center">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={loading ? 'Waiting for response...' : 'Type your message...'}
          disabled={loading}
          className="flex-1 p-2 border rounded mr-2"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}