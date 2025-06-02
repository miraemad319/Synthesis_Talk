// IMMEDIATE FIX 2: src/hooks/useChat.js
// Replace your current useChat.js with this fixed version

import { useState, useCallback, useRef } from 'react';
import { synthesisAPI } from '../utils/api';

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const abortControllerRef = useRef(null);

  const sendMessage = useCallback(async (content, options = {}) => {
    if (!content.trim()) return;
    
    // Create user message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      user: content, // For backward compatibility with ChatWindow
      content,
      timestamp: new Date().toISOString(),
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setError('');

    try {
      console.log('🚀 Sending chat message:', content);
      
      const response = await synthesisAPI.chat.send(content, {
        use_reasoning: options.useReasoning !== false,
      });

      console.log('✅ Raw chat response:', response.data);

      // FIXED: Proper response handling to prevent [object Object]
      let assistantReply = '';
      
      if (typeof response.data === 'string') {
        assistantReply = response.data;
      } else if (response.data && typeof response.data.reply === 'string') {
        assistantReply = response.data.reply;
      } else if (response.data && typeof response.data.content === 'string') {
        assistantReply = response.data.content;
      } else if (response.data && typeof response.data.message === 'string') {
        assistantReply = response.data.message;
      } else {
        // Last resort: try to extract any string value
        console.warn('Unexpected response format:', response.data);
        assistantReply = 'I received your message but had trouble formatting my response. Please try again.';
      }

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        bot: assistantReply, // For backward compatibility
        content: assistantReply,
        timestamp: new Date().toISOString(),
        metadata: {
          session_id: response.data?.session_id,
          processing_time: response.data?.processing_time
        }
      };

      console.log('✅ Adding assistant message:', assistantMessage);
      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (err) {
      console.error('❌ Chat error:', err);
      
      let errorMessage = 'Failed to send message';
      
      if (err.code === 'ECONNREFUSED' || err.code === 'ERR_NETWORK') {
        errorMessage = '🔌 Cannot connect to server. Please check if the backend is running on port 8000.';
      } else if (err.code === 'ECONNABORTED') {
        errorMessage = '⏱️ Request timed out. Please try again.';
      } else if (err.response?.status === 500) {
        errorMessage = '🔧 Server error. Please try again or restart the backend.';
      } else if (err.response?.data?.detail) {
        errorMessage = `❌ ${err.response.data.detail}`;
      } else if (err.userMessage) {
        errorMessage = `❌ ${err.userMessage}`;
      }
      
      setError(errorMessage);
      
      // Add error message to chat
      const errorMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        bot: errorMessage,
        content: errorMessage,
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMsg]);
      
    } finally {
      setLoading(false);
    }
  }, []);

  const clearMessages = useCallback(async () => {
    setMessages([]);
    setError('');
    console.log('✅ Chat messages cleared');
  }, []);

  return {
    messages,
    loading,
    error,
    sendMessage,
    clearMessages,
    clearChat: clearMessages, // Backward compatibility
  };
}