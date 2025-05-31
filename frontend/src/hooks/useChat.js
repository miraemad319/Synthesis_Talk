// frontend/src/hooks/useChat.js

import { useState } from 'react';
import api from '../utils/api';

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (text) => {
    setLoading(true);
    // Append user message
    setMessages((prev) => [...prev, { user: text }]);
    try {
      const res = await api.post('/chat/', { message: text });
      // Now read the “reply” field, not “response”
      const botReply = res.data.reply;
      setMessages((prev) => [...prev, { bot: botReply }]);
    } catch (e) {
      setMessages((prev) => [...prev, { bot: 'Error: Unable to reach server.' }]);
    }
    setLoading(false);
  };

  return { messages, sendMessage, loading };
}
