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
import { synthesisAPI } from '../utils/api';

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
    console.log('📁 Files dropped:', { acceptedFiles, rejectedFiles });

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
      console.log('✅ Accepted files:', acceptedFiles.map(f => f.name));
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

    console.log('🚀 Starting upload process for files:', uploadState.files.map(f => f.name));
    setUploadState(prev => ({ ...prev, uploading: true, progress: {}, errors: [], success: [] }));

    const uploadPromises = uploadState.files.map(async (file, index) => {
      console.log(`📤 Uploading file ${index + 1}/${uploadState.files.length}: ${file.name}`);
      
      try {
        // Initialize progress
        setUploadState(prev => ({
          ...prev,
          progress: { ...prev.progress, [file.name]: 0 }
        }));

        const response = await synthesisAPI.documents.upload(
          file, 
          'paragraph',
          (progress) => {
            console.log(`📊 Upload progress for ${file.name}: ${progress}%`);
            setUploadState(prev => ({
              ...prev,
              progress: { ...prev.progress, [file.name]: progress }
            }));
          }
        );

        console.log(`✅ Upload successful for ${file.name}:`, response.data);
        return { file: file.name, success: true, data: response.data };

      } catch (error) {
        console.error(`❌ Upload failed for ${file.name}:`, error);
        
        let errorMessage = 'Upload failed';
        if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.userMessage) {
          errorMessage = error.userMessage;
        } else if (error.message) {
          errorMessage = error.message;
        }

        return { 
          file: file.name, 
          success: false, 
          error: errorMessage
        };
      }
    });

    try {
      console.log('⏳ Waiting for all uploads to complete...');
      const results = await Promise.all(uploadPromises);
      
      const successfulUploads = results.filter(r => r.success);
      const failedUploads = results.filter(r => !r.success);

      console.log('📊 Upload results:', { 
        successful: successfulUploads.length, 
        failed: failedUploads.length 
      });

      setUploadState(prev => ({
        ...prev,
        uploading: false,
        files: [], // Clear files after upload attempt
        progress: {},
        success: successfulUploads.map(r => r.file),
        errors: [...prev.errors, ...failedUploads.map(r => ({ file: r.file, message: r.error }))]
      }));

      // Clear success messages after 5 seconds
      if (successfulUploads.length > 0) {
        setTimeout(() => {
          setUploadState(prev => ({ ...prev, success: [] }));
        }, 5000);
      }

      // Notify parent component
      if (onUploaded && successfulUploads.length > 0) {
        console.log('📢 Notifying parent component of successful uploads');
        onUploaded(successfulUploads);
      }

    } catch (error) {
      console.error('💥 Critical error during upload process:', error);
      setUploadState(prev => ({
        ...prev,
        uploading: false,
        errors: [...prev.errors, { file: 'System', message: 'Critical upload error occurred' }]
      }));
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

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={`space-y-3 ${className}`}>
      {/* COMPACT Drop Zone */}
      <motion.div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg p-4 text-center cursor-pointer
          transition-all duration-200 ease-in-out
          ${isDragActive 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }
          ${uploadState.uploading ? 'pointer-events-none opacity-60' : ''}
        `}
        whileHover={{ scale: uploadState.uploading ? 1 : 1.01 }}
      >
        <input {...getInputProps()} />
        
        <div className="flex items-center justify-center space-x-2">
          <CloudArrowUpIcon className="h-6 w-6 text-gray-400" />
          
          {isDragActive ? (
            <p className="text-sm font-medium text-primary-600">Drop files here</p>
          ) : (
            <div className="flex items-center space-x-2">
              <p className="text-sm font-medium text-gray-900">Drop files or click</p>
              <span className="text-xs text-gray-500">(PDF, TXT, DOC, DOCX)</span>
            </div>
          )}
        </div>
      </motion.div>

      {/* COMPACT File List */}
      <AnimatePresence>
        {uploadState.files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">
                {uploadState.files.length} file(s) ready
              </span>
              <button
                onClick={uploadFiles}
                disabled={uploadState.uploading}
                className="px-3 py-1 bg-primary-600 text-white rounded text-sm hover:bg-primary-700 disabled:opacity-50"
              >
                {uploadState.uploading ? 'Uploading...' : 'Upload'}
              </button>
            </div>

            <div className="max-h-24 overflow-y-auto space-y-1">
              {uploadState.files.map((file) => (
                <motion.div
                  key={file.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm"
                >
                  <div className="flex items-center space-x-2 flex-1 min-w-0">
                    <DocumentTextIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
                    <span className="truncate font-medium" title={file.name}>
                      {file.name}
                    </span>
                    <span className="text-xs text-gray-500 flex-shrink-0">
                      {formatFileSize(file.size)}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2 flex-shrink-0">
                    {uploadState.progress[file.name] !== undefined && (
                      <div className="w-16">
                        <div className="w-full bg-gray-200 rounded-full h-1">
                          <div
                            className="bg-primary-600 h-1 rounded-full transition-all duration-300"
                            style={{ width: `${uploadState.progress[file.name]}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">
                          {uploadState.progress[file.name]}%
                        </span>
                      </div>
                    )}
                    
                    {!uploadState.uploading && (
                      <button
                        onClick={() => removeFile(file.name)}
                        className="p-1 text-gray-400 hover:text-red-500"
                        title="Remove file"
                      >
                        <XMarkIcon className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* COMPACT Success Messages */}
      <AnimatePresence>
        {uploadState.success.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-1"
          >
            {uploadState.success.map((fileName) => (
              <motion.div
                key={fileName}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-center space-x-2 p-2 bg-green-50 border border-green-200 rounded text-sm"
              >
                <CheckCircleIcon className="h-4 w-4 text-green-500 flex-shrink-0" />
                <span className="text-green-700 flex-1 truncate">
                  {fileName} uploaded successfully
                </span>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* COMPACT Error Messages */}
      <AnimatePresence>
        {uploadState.errors.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-1"
          >
            {uploadState.errors.map((error, index) => (
              <motion.div
                key={`${error.file}-${index}`}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-start justify-between p-2 bg-red-50 border border-red-200 rounded text-sm"
              >
                <div className="flex items-start space-x-2 flex-1 min-w-0">
                  <ExclamationTriangleIcon className="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <span className="text-red-700 font-medium">{error.file}:</span>
                    <span className="text-red-600 ml-1">{error.message}</span>
                  </div>
                </div>
                <button
                  onClick={() => clearError(error.file)}
                  className="p-1 text-red-400 hover:text-red-600 flex-shrink-0"
                  title="Dismiss error"
                >
                  <XMarkIcon className="h-3 w-3" />
                </button>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}