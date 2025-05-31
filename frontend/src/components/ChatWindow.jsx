// frontend/src/components/ChatWindow.jsx

import React from 'react';
import { useChat } from '../hooks/useChat';
import { useTypewriter } from '../hooks/useTypewriter';

export default function ChatWindow() {
  const { messages, sendMessage, loading } = useChat();
  const [input, setInput] = React.useState("");

  // We will track the last bot reply and animate it
  const lastMessage = messages.length ? messages[messages.length - 1] : null;
  const isLastBot = lastMessage && lastMessage.bot;
  const typedReply = useTypewriter(isLastBot ? lastMessage.bot : "");

  const onSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage(input.trim());
    setInput("");
  };

  return (
    <div className="flex flex-col flex-1 p-4 overflow-y-auto">
      <div className="flex-1 space-y-4">
        {messages.map((msg, i) => {
          // If it’s a user message
          if (msg.user) {
            return (
              <div key={i} className="text-right">
                <span className="inline-block bg-blue-500 text-white px-3 py-1 rounded-lg">
                  {msg.user}
                </span>
              </div>
            );
          }
          // If it’s a bot message
          if (msg.bot) {
            // If this is the last message, use typedReply
            const content = i === messages.length - 1 ? typedReply : msg.bot;
            return (
              <div key={i} className="text-left">
                <span className="inline-block bg-gray-200 text-gray-800 px-3 py-1 rounded-lg">
                  {content}
                  {/* Show a blinking cursor if this is still typing */}
                  {i === messages.length - 1 && typedReply.length < msg.bot.length ? (
                    <span className="animate-pulse">|</span>
                  ) : null}
                </span>
              </div>
            );
          }
          return null;
        })}
      </div>

      <form onSubmit={onSubmit} className="mt-4 flex">
        <input
          type="text"
          className="flex-1 border border-gray-300 rounded-l px-3 py-2 focus:outline-none"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          className="bg-blue-500 text-white px-4 py-2 rounded-r hover:bg-blue-600 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
