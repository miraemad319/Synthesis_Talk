import React from 'react';
import ChatWindow from './components/ChatWindow';
import UploadArea from './components/UploadArea';
import InsightsPanel from './components/InsightsPanel';
import VisualizationPanel from './components/VisualizationPanel';
import ContextSidebar from './components/ContextSidebar';
import LoadingIndicator from './components/LoadingIndicator';

export default function App() {
  return (
    <div className="flex h-screen relative">
      <ContextSidebar />
      <div className="flex flex-col flex-1">
        <UploadArea />
        <ChatWindow />
      </div>
      <div className="w-1/3 flex flex-col border-l">
        <InsightsPanel />
        <VisualizationPanel />
      </div>
      <LoadingIndicator />
    </div>
  );
}