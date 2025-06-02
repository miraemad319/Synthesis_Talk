// IMMEDIATE FIX 3: src/App.jsx
// Replace your current App.jsx with this fixed version

import React, { useRef, useState, useEffect } from 'react';
import ChatWindow from './components/ChatWindow';
import UploadArea from './components/UploadArea';
import InsightsPanel from './components/InsightsPanel';
import VisualizationPanel from './components/VisualizationPanel';
import ContextSidebar from './components/ContextSidebar';
import LoadingIndicator from './components/LoadingIndicator';
import ExportPanel from './components/ExportPanel';
import SearchPanel from './components/SearchPanel';
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline';

export default function App() {
  const contextSidebarRef = useRef();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeRightPanel, setActiveRightPanel] = useState('insights');
  const [isConnected, setIsConnected] = useState(true);

  // Check backend connection on mount
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch("http://localhost:8000/health");
        setIsConnected(response.ok);
      } catch {
        setIsConnected(false);
      }
    };
    checkConnection();
  }, []);

  const handleFileUploaded = () => {
    contextSidebarRef.current?.fetchContexts();
  };

  const rightPanelTabs = [
    { id: 'insights', label: 'Insights', icon: '💡' },
    { id: 'visualization', label: 'Charts', icon: '📊' },
    { id: 'search', label: 'Search', icon: '🔍' },
    { id: 'export', label: 'Export', icon: '📄' }
  ];

  return (
    <div className="h-screen flex overflow-hidden bg-gray-50">
      {/* Connection Status Banner */}
      {!isConnected && (
        <div className="absolute top-0 left-0 right-0 bg-red-500 text-white text-center py-2 text-sm z-50">
          ⚠️ Backend connection failed. Please ensure the server is running on port 8000.
        </div>
      )}

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Left: Context Sidebar */}
      <div className={`
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        fixed lg:static inset-y-0 left-0 z-50 w-72 bg-white border-r
        transition-transform duration-300 ease-in-out
      `}>
        <div className="flex items-center justify-between p-4 border-b lg:hidden">
          <h2 className="text-lg font-semibold">Research Contexts</h2>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-2 rounded-md hover:bg-gray-100"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
        <ContextSidebar ref={contextSidebarRef} />
      </div>

      {/* Center: Upload + Chat - FIXED LAYOUT */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Header with mobile menu button */}
        <div className="bg-white border-b p-4 lg:hidden flex-shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-md hover:bg-gray-100"
          >
            <Bars3Icon className="h-5 w-5" />
          </button>
        </div>

        {/* FIXED: Upload Area - Compact and scrollable */}
        <div className="border-b bg-white flex-shrink-0 max-h-48 overflow-y-auto">
          <UploadArea onUploaded={handleFileUploaded} className="p-4" />
        </div>

        {/* FIXED: Chat Window - Takes remaining space and scrollable */}
        <div className="flex-1 min-h-0 overflow-hidden">
          <ChatWindow />
        </div>
      </div>

      {/* Right: Insights + Visualization + Tools - FIXED LAYOUT */}
      <div className="w-96 border-l flex flex-col overflow-hidden bg-white hidden lg:flex">
        {/* Tab Navigation */}
        <div className="border-b bg-gray-50 flex-shrink-0">
          <div className="flex">
            {rightPanelTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveRightPanel(tab.id)}
                className={`
                  flex-1 px-3 py-3 text-sm font-medium text-center border-b-2 transition-colors
                  ${activeRightPanel === tab.id
                    ? 'border-blue-500 text-blue-600 bg-white'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                  }
                `}
              >
                <span className="mr-1">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Panel Content - FIXED: Proper scrolling */}
        <div className="flex-1 min-h-0 overflow-hidden">
          {activeRightPanel === 'insights' && <InsightsPanel />}
          {activeRightPanel === 'visualization' && <VisualizationPanel />}
          {activeRightPanel === 'search' && <SearchPanel />}
          {activeRightPanel === 'export' && <ExportPanel />}
        </div>
      </div>

      {/* Mobile Right Panel - Bottom Sheet Style - FIXED */}
      <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t max-h-96 overflow-hidden z-30">
        {/* Mobile Tab Navigation */}
        <div className="flex border-b bg-gray-50 flex-shrink-0">
          {rightPanelTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveRightPanel(tab.id)}
              className={`
                flex-1 px-2 py-2 text-xs font-medium text-center border-b-2 transition-colors
                ${activeRightPanel === tab.id
                  ? 'border-blue-500 text-blue-600 bg-white'
                  : 'border-transparent text-gray-500'
                }
              `}
            >
              <div className="flex flex-col items-center">
                <span className="text-sm">{tab.icon}</span>
                <span className="mt-1">{tab.label}</span>
              </div>
            </button>
          ))}
        </div>

        {/* Mobile Panel Content - FIXED: Scrollable */}
        <div className="flex-1 overflow-auto min-h-0">
          {activeRightPanel === 'insights' && <InsightsPanel />}
          {activeRightPanel === 'visualization' && <VisualizationPanel />}
          {activeRightPanel === 'search' && <SearchPanel />}
          {activeRightPanel === 'export' && <ExportPanel />}
        </div>
      </div>

      {/* Global loader overlay */}
      <LoadingIndicator />
    </div>
  );
}
