import React, { useState, useEffect } from 'react';
import api from '../utils/api';

export default function LoadingIndicator() {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Intercept requests to track loading state
    const req = api.interceptors.request.use(config => {
      setLoading(true);
      return config;
    });
    const res = api.interceptors.response.use(
      response => {
        setLoading(false);
        return response;
      },
      error => {
        setLoading(false);
        return Promise.reject(error);
      }
    );
    return () => {
      api.interceptors.request.eject(req);
      api.interceptors.response.eject(res);
    };
  }, []);

  if (!loading) return null;
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30">
      <div className="loader border-4 border-t-4 rounded-full w-12 h-12 border-blue-600 animate-spin" />
    </div>
  );
}