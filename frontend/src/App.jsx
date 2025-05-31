import React, { useRef } from 'react';
import ChatWindow from './components/ChatWindow';
import UploadArea from './components/UploadArea';
import InsightsPanel from './components/InsightsPanel';
import VisualizationPanel from './components/VisualizationPanel';
import ContextSidebar from './components/ContextSidebar';
import LoadingIndicator from './components/LoadingIndicator';

export default function App() {
  const contextSidebarRef = useRef();

  return (
    <div className="h-screen flex overflow-hidden bg-gray-50">
      {/* Left: Context Sidebar */}
      <div className="w-72 border-r bg-white">
        <ContextSidebar ref={contextSidebarRef} />
      </div>

      {/* Center: Upload + Chat */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <div className="border-b bg-white">
          <UploadArea onUploaded={() => contextSidebarRef.current?.fetchContexts()} />
        </div>
        <div className="flex-1 flex flex-col">
          <ChatWindow />
        </div>
      </div>

      {/* Right: Insights + Visualization */}
      <div className="w-96 border-l flex flex-col overflow-hidden bg-white">
        <div className="flex-1">
          <InsightsPanel />
        </div>
        <div className="border-t flex-1">
          <VisualizationPanel />
        </div>
      </div>

      {/* Global loader overlay */}
      <LoadingIndicator />
    </div>
  );
}

