import React, { useState } from 'react';
import { DocumentArrowDownIcon, DocumentTextIcon, TableCellsIcon } from '@heroicons/react/24/outline';
import api from '../utils/api';

export default function ExportPanel() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [exportHistory, setExportHistory] = useState([]);
  const [selectedFormat, setSelectedFormat] = useState('summary');

  const exportFormats = [
    {
      id: 'summary',
      name: 'Research Summary',
      description: 'Comprehensive summary with key findings and sources',
      icon: DocumentTextIcon,
      extension: 'docx'
    },
    {
      id: 'report',
      name: 'Detailed Report',
      description: 'Full report with analysis, insights, and recommendations',
      icon: DocumentTextIcon,
      extension: 'docx'
    },
    {
      id: 'markdown',
      name: 'Markdown Notes',
      description: 'Structured notes in markdown format',
      icon: DocumentTextIcon,
      extension: 'md'
    },
    {
      id: 'csv',
      name: 'Data Export',
      description: 'Export extracted data and insights as CSV',
      icon: TableCellsIcon,
      extension: 'csv'
    }
  ];

  const handleExport = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/export/', { 
        format: selectedFormat,
        include_chat: true,
        include_insights: true,
        include_sources: true
      }, {
        responseType: 'blob'
      });

      // Create download link
      const selectedFormatInfo = exportFormats.find(f => f.id === selectedFormat);
      const filename = `synthesis_export_${new Date().toISOString().split('T')[0]}.${selectedFormatInfo.extension}`;
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      // Add to export history
      setExportHistory(prev => [
        {
          format: selectedFormat,
          filename,
          timestamp: new Date(),
          size: response.data.size
        },
        ...prev.slice(0, 9) // Keep last 10 exports
      ]);

    } catch (err) {
      console.error('Export error:', err);
      setError(err.userMessage || 'Export failed. Please try again.');
    }
    setLoading(false);
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown size';
    const kb = bytes / 1024;
    return kb > 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${Math.round(kb)} KB`;
  };

  return (
    <div className="p-4 flex-1 overflow-auto bg-white">
      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-2">Export Research</h2>
        <p className="text-sm text-gray-600">
          Export your research findings, conversations, and insights in various formats
        </p>
      </div>

      {/* Format Selection */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Choose Export Format</h3>
        <div className="grid grid-cols-1 gap-3">
          {exportFormats.map((format) => {
            const IconComponent = format.icon;
            return (
              <label key={format.id} className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="radio"
                  name="exportFormat"
                  value={format.id}
                  checked={selectedFormat === format.id}
                  onChange={(e) => setSelectedFormat(e.target.value)}
                  className="mt-1 text-blue-600 focus:ring-blue-500"
                />
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <IconComponent className="h-5 w-5 text-gray-400" />
                    <span className="font-medium text-gray-900">{format.name}</span>
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      .{format.extension}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{format.description}</p>
                </div>
              </label>
            );
          })}
        </div>
      </div>

      {/* Export Options */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Export Options</h3>
        <div className="space-y-2">
          <label className="flex items-center space-x-2">
            <input type="checkbox" defaultChecked className="text-blue-600 focus:ring-blue-500" />
            <span className="text-sm text-gray-700">Include conversation history</span>
          </label>
          <label className="flex items-center space-x-2">
            <input type="checkbox" defaultChecked className="text-blue-600 focus:ring-blue-500" />
            <span className="text-sm text-gray-700">Include generated insights</span>
          </label>
          <label className="flex items-center space-x-2">
            <input type="checkbox" defaultChecked className="text-blue-600 focus:ring-blue-500" />
            <span className="text-sm text-gray-700">Include source references</span>
          </label>
          <label className="flex items-center space-x-2">
            <input type="checkbox" className="text-blue-600 focus:ring-blue-500" />
            <span className="text-sm text-gray-700">Include visualizations (where supported)</span>
          </label>
        </div>
      </div>

      {/* Export Button */}
      <div className="mb-6">
        <button
          onClick={handleExport}
          disabled={loading}
          className="w-full bg-blue-500 text-white py-3 px-4 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
        >
          <DocumentArrowDownIcon className="h-5 w-5" />
          <span>{loading ? 'Exporting...' : 'Export Research'}</span>
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Export History */}
      {exportHistory.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Exports</h3>
          <div className="space-y-2">
            {exportHistory.map((export_, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-medium text-sm text-gray-900">{export_.filename}</div>
                  <div className="text-xs text-gray-500">
                    {export_.timestamp.toLocaleDateString()} • {formatFileSize(export_.size)}
                  </div>
                </div>
                <div className="text-xs text-gray-500 capitalize">
                  {export_.format.replace('_', ' ')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {exportHistory.length === 0 && !loading && !error && (
        <div className="text-center py-8">
          <div className="text-gray-400 mb-4">
            <DocumentArrowDownIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <div className="text-gray-500 mb-2">Ready to export your research</div>
            <div className="text-sm text-gray-400 max-w-sm mx-auto">
              Once you've uploaded files and had conversations, you can export comprehensive research documents
            </div>
          </div>
        </div>
      )}
    </div>
  );
}