import React, { useState, useRef, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  DocumentTextIcon, 
  CloudArrowUpIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../utils/api';

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'text/plain': ['.txt'],
  'application/msword': ['.doc'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/markdown': ['.md'],
  'text/csv': ['.csv'],
};

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export default function UploadArea({ onUploaded, className = '' }) {
  const [uploadState, setUploadState] = useState({
    files: [],
    uploading: false,
    progress: {},
    errors: [],
    success: []
  });

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      const newErrors = rejectedFiles.map(({ file, errors }) => ({
        file: file.name,
        message: errors.map(e => e.message).join(', ')
      }));
      setUploadState(prev => ({
        ...prev,
        errors: [...prev.errors, ...newErrors]
      }));
    }

    // Handle accepted files
    if (acceptedFiles.length > 0) {
      setUploadState(prev => ({
        ...prev,
        files: [...prev.files, ...acceptedFiles],
        errors: prev.errors.filter(e => 
          !acceptedFiles.some(f => f.name === e.file)
        )
      }));
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: true,
  });

  const uploadFiles = async () => {
    if (uploadState.files.length === 0) return;

    setUploadState(prev => ({ ...prev, uploading: true, progress: {} }));

    const uploadPromises = uploadState.files.map(async (file) => {
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await api.post('/upload/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              (progressEvent.loaded / progressEvent.total) * 100
            );
            setUploadState(prev => ({
              ...prev,
              progress: { ...prev.progress, [file.name]: progress }
            }));
          },
        });

        return { file: file.name, success: true, data: response.data };
      } catch (error) {
        return { 
          file: file.name, 
          success: false, 
          error: error.response?.data?.detail || 'Upload failed' 
        };
      }
    });

    const results = await Promise.all(uploadPromises);
    
    const successfulUploads = results.filter(r => r.success);
    const failedUploads = results.filter(r => !r.success);

    setUploadState(prev => ({
      ...prev,
      uploading: false,
      files: [],
      progress: {},
      success: successfulUploads.map(r => r.file),
      errors: [...prev.errors, ...failedUploads.map(r => ({ file: r.file, message: r.error }))]
    }));

    // Clear success messages after 3 seconds
    if (successfulUploads.length > 0) {
      setTimeout(() => {
        setUploadState(prev => ({ ...prev, success: [] }));
      }, 3000);
    }

    // Notify parent component
    if (onUploaded && successfulUploads.length > 0) {
      onUploaded(successfulUploads);
    }
  };

  const removeFile = (fileName) => {
    setUploadState(prev => ({
      ...prev,
      files: prev.files.filter(f => f.name !== fileName)
    }));
  };

  const clearError = (fileName) => {
    setUploadState(prev => ({
      ...prev,
      errors: prev.errors.filter(e => e.file !== fileName)
    }));
  };

  const getFileIcon = (file) => {
    if (file.type.includes('pdf')) return '📄';
    if (file.type.includes('text')) return '📝';
    if (file.type.includes('word')) return '📃';
    if (file.type.includes('csv')) return '📊';
    return '📄';
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Drop Zone */}
      <motion.div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-all duration-200 ease-in-out
          ${isDragActive 
            ? 'border-primary-500 bg-primary-50 scale-105' 
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }
          ${uploadState.uploading ? 'pointer-events-none opacity-60' : ''}
        `}
        whileHover={{ scale: uploadState.uploading ? 1 : 1.02 }}
        whileTap={{ scale: uploadState.uploading ? 1 : 0.98 }}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
          
          {isDragActive ? (
            <div>
              <p className="text-lg font-medium text-primary-600">
                Drop files here
              </p>
              <p className="text-sm text-primary-500">
                Release to upload
              </p>
            </div>
          ) : (
            <div>
              <p className="text-lg font-medium text-gray-900">
                Drop files here or click to browse
              </p>
              <p className="text-sm text-gray-500">
                Supports PDF, TXT, DOC, DOCX, MD, CSV (max 10MB each)
              </p>
            </div>
          )}
        </div>
      </motion.div>

      {/* File List */}
      <AnimatePresence>
        {uploadState.files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2"
          >
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-gray-900">
                Files to upload ({uploadState.files.length})
              </h4>
              <button
                onClick={uploadFiles}
                disabled={uploadState.uploading}
                className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {uploadState.uploading ? 'Uploading...' : 'Upload All'}
              </button>
            </div>

            <div className="space-y-2 max-h-32 overflow-y-auto">
              {uploadState.files.map((file) => (
                <motion.div
                  key={file.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-xl">{getFileIcon(file)}</span>
                    <div>
                      <p className="text-sm font-medium text-gray-900 truncate max-w-48">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {uploadState.progress[file.name] !== undefined && (
                      <div className="w-20">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${uploadState.progress[file.name]}%` }}
                          />
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {uploadState.progress[file.name]}%
                        </p>
                      </div>
                    )}
                    
                    {!uploadState.uploading && (
                      <button
                        onClick={() => removeFile(file.name)}
                        className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                      >
                        <XMarkIcon className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Success Messages */}
      <AnimatePresence>
        {uploadState.success.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-1"
          >
            {uploadState.success.map((fileName) => (
              <div
                key={fileName}
                className="flex items-center space-x-2 p-2 bg-green-50 border border-green-200 rounded-md"
              >
                <CheckCircleIcon className="h-4 w-4 text-green-500" />
                <p className="text-sm text-green-700">
                  {fileName} uploaded successfully
                </p>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Messages */}
      <AnimatePresence>
        {uploadState.errors.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-1"
          >
            {uploadState.errors.map((error, index) => (
              <div
                key={`${error.file}-${index}`}
                className="flex items-center justify-between p-2 bg-red-50 border border-red-200 rounded-md"
              >
                <div className="flex items-center space-x-2">
                  <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />
                  <p className="text-sm text-red-700">
                    <span className="font-medium">{error.file}:</span> {error.message}
                  </p>
                </div>
                <button
                  onClick={() => clearError(error.file)}
                  className="p-1 text-red-400 hover:text-red-600 transition-colors"
                >
                  <XMarkIcon className="h-3 w-3" />
                </button>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

