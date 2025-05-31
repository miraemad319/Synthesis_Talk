import React, { useState, useRef } from 'react';
import api from '../utils/api';

export default function UploadArea() {
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  const onFileChange = (e) => {
    setError('');
    if (e.target.files.length) setFile(e.target.files[0]);
  };

  const onUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (ev) => {
          setProgress(Math.round((ev.loaded / ev.total) * 100));
        },
      });
      // handle successful upload (e.g., show toast)
      setFile(null);
      setProgress(0);
      inputRef.current.value = '';
    } catch (err) {
      setError('Upload failed. Try again.');
      setProgress(0);
    }
  };

  return (
    <div className="p-4 border-b flex items-center">
      <input
        type="file"
        ref={inputRef}
        onChange={onFileChange}
        className="mr-4"
      />
      <button
        onClick={onUpload}
        disabled={!file}
        className="px-4 py-2 bg-green-600 text-white rounded disabled:opacity-50"
      >
        Upload
      </button>
      {progress > 0 && (
        <div className="ml-4 flex-1 bg-gray-200 rounded h-2 overflow-hidden">
          <div
            className="h-full bg-green-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
      {error && <p className="text-red-500 ml-4">{error}</p>}
    </div>
  );
}