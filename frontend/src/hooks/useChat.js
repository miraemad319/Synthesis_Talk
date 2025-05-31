import { useState, useEffect } from 'react';
import api from '../utils/api';

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (text) => {
    setLoading(true);
    setMessages((prev) => [...prev, { user: text }]);
    try {
      const res = await api.post('/chat', { message: text });
      setMessages((prev) => [...prev, { bot: res.data.reply }]);
    } catch (e) {
      setMessages((prev) => [...prev, { bot: 'Error: Unable to reach server.' }]);
    }
    setLoading(false);
  };

  return { messages, sendMessage, loading };
}