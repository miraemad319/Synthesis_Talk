import { useState } from 'react';
import api from '../utils/api';

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = async (text) => {
    setLoading(true);
    setError(null);
    
    // Append user message immediately
    setMessages((prev) => [...prev, { user: text }]);
    
    try {
      const res = await api.post('/chat/', { message: text });
      const botReply = res.data.reply || res.data.response || 'No response received';
      setMessages((prev) => [...prev, { bot: botReply }]);
    } catch (e) {
      console.error('Chat error:', e);
      const errorMessage = e.userMessage || 'Unable to reach server. Please check your connection.';
      setMessages((prev) => [...prev, { bot: `Error: ${errorMessage}` }]);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  return { messages, sendMessage, loading, error, clearChat };
}
