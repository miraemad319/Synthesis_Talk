import { useState, useCallback, useRef } from 'react';
import api from '../utils/api';

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
      content,
      timestamp: new Date().toISOString(),
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setError('');

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController();

    try {
      const response = await api.post('/chat/', {
        message: content,
        context_id: options.contextId,
        use_tools: options.useTools !== false, // default to true
        reasoning_type: options.reasoningType || 'chain_of_thought',
      }, {
        signal: abortControllerRef.current.signal,
      });

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.response || response.data.message || 'No response received',
        timestamp: new Date().toISOString(),
        tools_used: response.data.tools_used || [],
        reasoning_steps: response.data.reasoning_steps || [],
        sources: response.data.sources || [],
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      if (err.name === 'AbortError' || err.code === 'ERR_CANCELED') {
        console.log('Chat request was cancelled');
        return;
      }
      
      console.error('Chat error:', err);
      const errorMessage = err.userMessage || err.response?.data?.detail || 'Failed to send message';
      setError(errorMessage);
      
      // Add error message to chat
      const errorMsg = {
        id: Date.now() + 1,
        role: 'system',
        content: `Error: ${errorMessage}`,
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, []);

  const cancelMessage = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError('');
  }, []);

  const regenerateLastMessage = useCallback(async (options = {}) => {
    if (messages.length === 0) return;
    
    // Find the last user message
    const lastUserMessage = messages
      .slice()
      .reverse()
      .find(msg => msg.role === 'user');
    
    if (!lastUserMessage) return;

    // Remove messages after the last user message
    const userMessageIndex = messages.findIndex(msg => msg.id === lastUserMessage.id);
    setMessages(prev => prev.slice(0, userMessageIndex + 1));

    // Resend the message
    await sendMessage(lastUserMessage.content, options);
  }, [messages, sendMessage]);

  const addSystemMessage = useCallback((content, type = 'info') => {
    const systemMessage = {
      id: Date.now(),
      role: 'system',
      content,
      timestamp: new Date().toISOString(),
      type,
    };
    setMessages(prev => [...prev, systemMessage]);
  }, []);

  return {
    messages,
    loading,
    error,
    sendMessage,
    cancelMessage,
    clearMessages,
    regenerateLastMessage,
    addSystemMessage,
  };
}
