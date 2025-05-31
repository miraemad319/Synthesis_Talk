import React, { useState, useRef } from 'react';
import api from '../utils/api';

export default function UploadArea({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const inputRef = useRef();

  const onUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (ev) => {
          setProgress(Math.round((ev.loaded / ev.total) * 100));
        },
      });

      // Clear file and progress
      setFile(null);
      setProgress(0);
      inputRef.current.value = "";

      // Trigger parent callback to re-fetch contexts
      if (onUploaded) {
        onUploaded();
      }
    } catch (err) {
      setError('Upload failed. Please try again.');
      setProgress(0);
    }
  };

  return (
    <div className="p-4 border-b bg-white flex items-center gap-2">
      <input
        type="file"
        ref={inputRef}
        onChange={(e) => {
          setFile(e.target.files[0]);
          setError('');
        }}
        className="border border-gray-300 rounded px-2 py-1"
      />
      <button
        onClick={onUpload}
        className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:opacity-50"
        disabled={!file}
      >
        Upload
      </button>
      {progress > 0 && (
        <div className="flex-1">
          <div className="w-full bg-gray-200 h-2 rounded mt-1">
            <div
              className="h-2 bg-green-500 rounded"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
      {error && <p className="text-red-500 ml-4">{error}</p>}
    </div>
  );
}

